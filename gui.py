#!/usr/bin/env python3
import os
import sys
import time
import socket
import subprocess
import signal
import threading
import json
import urllib.request
import shlex
from datetime import datetime, timezone
from bottle import route, run, static_file, request, response

# Bitcoin Price Widget (Phase 4.1)
from api.routes_bitcoin_price import setup_price_routes
# Portfolio Dashboard (Phase 4.2)
from api.portfolio import PortfolioManager
from api.routes_portfolio import setup_portfolio_routes

# Define paths (portable — relative to this script)
ORACLE_KNOTS_DIR = os.path.dirname(os.path.abspath(__file__))
GUI_DIR = os.path.join(ORACLE_KNOTS_DIR, "gui")

def _resolve_binary(name: str) -> str:
    for subpath in ("build/bin", "build/src"):
        path = os.path.join(ORACLE_KNOTS_DIR, subpath, name)
        if os.path.isfile(path):
            return path
    return os.path.join(ORACLE_KNOTS_DIR, "build", "bin", name)

BITCOIND_PATH = _resolve_binary("bitcoind")
BITCOIN_CLI_PATH = _resolve_binary("bitcoin-cli")

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_available_port(start_port: int = 8080) -> int:
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port

# ----------------------------------------------------
# Node Process Management Utilities
# ----------------------------------------------------
def check_node_running():
    try:
        pgrep = subprocess.run(["pgrep", "-x", "bitcoind"], capture_output=True, text=True)
        if pgrep.returncode == 0:
            pid = int(pgrep.stdout.strip().split('\n')[0])
            return True, pid
    except Exception:
        pass
    return False, None

def get_node_datadir(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline_bytes = f.read()
        args = cmdline_bytes.decode().split('\x00')
        for arg in args:
            if arg.startswith("-datadir="):
                return os.path.expanduser(arg.split("=", 1)[1])
    except Exception:
        pass
    return os.path.expanduser("~/.bitcoin")

def get_node_network(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline_bytes = f.read()
        args = cmdline_bytes.decode().split('\x00')
        for arg in args:
            if arg == "-testnet" or arg == "-testnet3":
                return "testnet"
            elif arg == "-regtest":
                return "regtest"
            elif arg == "-signet":
                return "signet"
    except Exception:
        pass
    return "mainnet"

def get_prometheus_port(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline_bytes = f.read()
        args = cmdline_bytes.decode().split('\x00')
        for arg in args:
            if arg.startswith("-prometheusport="):
                return int(arg.split("=", 1)[1])
    except Exception:
        pass
    return 9332

def run_bitcoin_cli(args_list, datadir=None, network="mainnet", wallet_name=None, timeout=5.0):
    cmd = [BITCOIN_CLI_PATH]
    if datadir:
        cmd.append(f"-datadir={datadir}")
    if network == "testnet":
        cmd.append("-testnet")
    elif network == "regtest":
        cmd.append("-regtest")
    elif network == "signet":
        cmd.append("-signet")
    if wallet_name:
        cmd.append(f"-rpcwallet={wallet_name}")
    cmd.extend(args_list)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if res.returncode == 0:
            return True, res.stdout.strip()
        else:
            return False, res.stderr.strip()
    except Exception as e:
        return False, str(e)

def get_network_dir(datadir, network):
    root_datadir = os.path.abspath(datadir)
    if network == "testnet":
        return os.path.join(root_datadir, "testnet3")
    if network == "regtest":
        return os.path.join(root_datadir, "regtest")
    if network == "signet":
        return os.path.join(root_datadir, "signet")
    return root_datadir

def get_config_paths(datadir, network):
    root_datadir = os.path.abspath(datadir)
    bitcoin_conf_path = os.path.join(root_datadir, "bitcoin.conf")
    net_dir = get_network_dir(datadir, network)
    policy_toml_path = os.path.join(net_dir, "policy.toml")
    return bitcoin_conf_path, policy_toml_path

def get_node_context():
    """Return (running, datadir, network) for the active bitcoind process."""
    running, pid = check_node_running()
    if not running:
        return False, os.path.expanduser("~/.bitcoin"), "mainnet"
    return True, get_node_datadir(pid), get_node_network(pid)

def list_wallets_on_disk(datadir, network):
    net_dir = get_network_dir(datadir, network)
    wallets_dir = os.path.join(net_dir, "wallets")
    if not os.path.isdir(wallets_dir):
        return []
    return sorted(
        name for name in os.listdir(wallets_dir)
        if os.path.isdir(os.path.join(wallets_dir, name))
    )

def fetch_prometheus_metrics(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1.0) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                return parse_prometheus_metrics(content)
    except Exception:
        pass
    return None

def parse_prometheus_metrics(raw_data):
    metrics = {
        "block_height": 0,
        "mempool_size": 0,
        "mempool_bytes": 0,
        "mempool_usage": 0,
        "peers": 0,
        "peers_inbound": 0,
        "peers_outbound": 0,
        "policy_profile": "unknown",
        "bip110_mode": "unknown",
        "rejections": {},
        "uptime": 0
    }
    for line in raw_data.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if ' ' in line:
            name_part, val_str = line.rsplit(' ', 1)
            try:
                val = float(val_str)
                if val.is_integer():
                    val = int(val)
            except ValueError:
                continue
            
            if name_part == "bitcoin_blocks":
                metrics["block_height"] = val
            elif name_part == "bitcoin_mempool_size":
                metrics["mempool_size"] = val
            elif name_part == "bitcoin_mempool_bytes":
                metrics["mempool_bytes"] = val
            elif name_part == "bitcoin_mempool_usage":
                metrics["mempool_usage"] = val
            elif name_part == "bitcoin_peers":
                metrics["peers"] = val
            elif name_part == "bitcoin_peers_inbound":
                metrics["peers_inbound"] = val
            elif name_part == "bitcoin_peers_outbound":
                metrics["peers_outbound"] = val
            elif name_part == "bitcoin_uptime":
                metrics["uptime"] = val
            elif name_part.startswith("bitcoin_oracle_policy_profile"):
                if 'profile="' in name_part:
                    metrics["policy_profile"] = name_part.split('profile="')[1].split('"')[0]
            elif name_part.startswith("bitcoin_oracle_bip110_mode"):
                if 'mode="' in name_part:
                    metrics["bip110_mode"] = name_part.split('mode="')[1].split('"')[0]
            elif name_part.startswith("bitcoin_rejected_tx_total"):
                if 'reason="' in name_part:
                    reason = name_part.split('reason="')[1].split('"')[0]
                    metrics["rejections"][reason] = val
    return metrics

REJECTION_LABELS = {
    "inscription": "Ordinals inscriptions",
    "tokens-runes": "Runes / BRC-20 tokens",
    "tokens-olga": "OLGA tokens",
    "dust-nonanchor": "Dust (non-anchor)",
    "dust-nonzero": "Dust (non-zero)",
    "bare-pubkey": "Bare pubkey outputs",
    "bare-multisig": "Bare multisig outputs",
    "parasite-cat21": "Parasite CAT-21 overlays",
    "max-op-returns": "Excess OP_RETURN outputs",
}

POLICY_PRESETS = {
    "maximalist": {
        "custom_rules.datacarrier_size": 0,
        "custom_rules.reject_tokens": True,
        "custom_rules.reject_inscriptions": True,
        "custom_rules.dust_relay_fee": 3000,
        "custom_rules.permit_bare_multisig": False,
        "custom_rules.permit_bare_pubkey": False,
        "custom_rules.reject_parasites": True,
        "custom_rules.max_op_return_outputs": 0,
    },
    "bip110-strict": {
        "custom_rules.datacarrier_size": 83,
        "custom_rules.reject_tokens": True,
        "custom_rules.reject_inscriptions": True,
        "custom_rules.dust_relay_fee": 3000,
        "custom_rules.permit_bare_multisig": False,
        "custom_rules.permit_bare_pubkey": False,
        "custom_rules.reject_parasites": True,
        "custom_rules.max_op_return_outputs": 1,
    },
    "monetary-only": {
        "custom_rules.datacarrier_size": 0,
        "custom_rules.reject_tokens": True,
        "custom_rules.reject_inscriptions": True,
        "custom_rules.dust_relay_fee": 3000,
        "custom_rules.permit_bare_multisig": False,
        "custom_rules.permit_bare_pubkey": False,
        "custom_rules.reject_parasites": True,
        "custom_rules.max_op_return_outputs": 0,
    },
    "default-knots": {
        "custom_rules.datacarrier_size": 83,
        "custom_rules.reject_tokens": False,
        "custom_rules.reject_inscriptions": False,
        "custom_rules.dust_relay_fee": 3000,
        "custom_rules.permit_bare_multisig": False,
        "custom_rules.permit_bare_pubkey": False,
        "custom_rules.reject_parasites": True,
        "custom_rules.max_op_return_outputs": 1,
    },
}

GUI_STATE_DIR = os.path.expanduser("~/.oracle-knots-gui")
_dashboard_cache = {"ts": 0.0, "data": None}
DASHBOARD_CACHE_TTL = 2.0
_mempool_txs_cache = {"ts": 0.0, "key": None, "data": []}
MEMPOOL_TXS_CACHE_TTL = 15.0
_chain_strip_cache = {"ts": 0.0, "tip_height": None, "data": None}
CHAIN_STRIP_CACHE_TTL = 30.0
CHAIN_STRIP_BLOCK_COUNT = 12


def _normalize_chain_block(raw):
    """Normalize one block entry from getrecentblockpolicyaudit for the GUI."""
    if not raw or not isinstance(raw, dict):
        return None
    height = raw.get("height")
    if height is None:
        return None
    available = bool(raw.get("available", False))
    n_tx = int(raw.get("n_tx") or 0)
    policy_fail = int(raw.get("policy_fail") or 0) if available else 0
    policy_pass = int(raw.get("policy_pass") or 0) if available else 0
    fail_pct = round((policy_fail / n_tx) * 100, 2) if available and n_tx > 0 else 0.0
    return {
        "height": int(height),
        "hash": raw.get("hash", ""),
        "time": int(raw.get("time") or 0),
        "n_tx": n_tx,
        "available": available,
        "bip110_compliant": raw.get("bip110_compliant") if available else None,
        "policy_pass": policy_pass,
        "policy_fail": policy_fail,
        "policy_clean": bool(raw.get("policy_clean")) if available else None,
        "policy_fail_pct": fail_pct,
        "subsidy": raw.get("subsidy") if available else None,
        "fees": raw.get("fees") if available else None,
        "coinbase_reward": raw.get("coinbase_reward") if available else None,
        "fees_sats": int(raw.get("fees_sats") or 0) if available else None,
        "miner_tag": raw.get("miner_tag") if available else None,
    }


def _build_chain_strip(running, pid, count=CHAIN_STRIP_BLOCK_COUNT):
    if not running:
        return {
            "online": False,
            "blocks": [],
            "tip_height": 0,
            "active_policy_profile": None,
        }
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    audit = _rpc_json("getrecentblockpolicyaudit", datadir, network, timeout=45.0)
    if not audit:
        chain = _rpc_json("getblockchaininfo", datadir, network) or {}
        tip = int(chain.get("blocks") or 0)
        return {
            "online": True,
            "blocks": [],
            "tip_height": tip,
            "active_policy_profile": None,
            "rpc_unavailable": True,
        }
    blocks = [
        b for b in (_normalize_chain_block(x) for x in (audit.get("blocks") or []))
        if b is not None
    ]
    return {
        "online": True,
        "blocks": blocks,
        "tip_height": int(audit.get("tip_height") or 0),
        "active_policy_profile": audit.get("active_policy_profile"),
    }

def _bool_cli(val):
    return "true" if val else "false"

def _summarize_peers(peerinfo):
    summary = {
        "total": len(peerinfo),
        "inbound": 0,
        "outbound": 0,
        "tor": 0,
        "i2p": 0,
        "clearnet": 0,
    }
    for peer in peerinfo:
        inbound = peer.get("inbound", False)
        if inbound:
            summary["inbound"] += 1
        else:
            summary["outbound"] += 1
        addr = (peer.get("addr") or "").lower()
        network = (peer.get("network") or "").lower()
        if ".onion" in addr or network == "onion":
            summary["tor"] += 1
        elif ".i2p" in addr or network == "i2p":
            summary["i2p"] += 1
        else:
            summary["clearnet"] += 1
    return summary

def _parse_rdts_deployment(deployment_info):
    result = {
        "status": "unknown",
        "signaling_pct": 0.0,
        "blocks_signaling": 0,
        "period": 0,
        "threshold": 0,
        "active": False,
    }
    if not deployment_info:
        return result
    softforks = deployment_info.get("softforks", {})
    rdts = softforks.get("reduced_data", {})
    if not rdts:
        return result
    bip9 = rdts.get("bip9", {})
    result["status"] = bip9.get("status", "unknown")
    result["active"] = rdts.get("active", False)
    stats = bip9.get("statistics", {})
    if stats:
        period = stats.get("period") or 0
        count = stats.get("count") or 0
        threshold = stats.get("threshold") or 0
        result["blocks_signaling"] = count
        result["period"] = period
        result["threshold"] = threshold
        if period > 0:
            result["signaling_pct"] = round((count / period) * 100, 1)
        if threshold > 0:
            result["threshold_pct"] = round((threshold / period) * 100, 1) if period else 0
            result["progress_to_lockin_pct"] = round(min(100.0, (count / threshold) * 100), 1)
            result["blocks_to_threshold"] = max(0, threshold - count)
    return result

def _top_rejections(rejections, limit=5):
    items = []
    for reason, count in rejections.items():
        if reason == "total":
            continue
        try:
            count = int(count)
        except (TypeError, ValueError):
            continue
        if count <= 0:
            continue
        items.append({
            "reason": reason,
            "label": REJECTION_LABELS.get(reason, reason),
            "count": count,
        })
    items.sort(key=lambda x: x["count"], reverse=True)
    total = sum(x["count"] for x in items)
    for item in items:
        item["pct"] = round((item["count"] / total) * 100, 1) if total else 0.0
    return items[:limit], total

def _rejection_stats(rejections, mempool_size):
    total = int(rejections.get("total", 0) or 0)
    if total == 0:
        for reason, count in rejections.items():
            if reason != "total":
                total += int(count or 0)
    evaluated = total + int(mempool_size or 0)
    rate = round((total / evaluated) * 100, 2) if evaluated > 0 else 0.0
    pass_rate = round(100.0 - rate, 2) if evaluated > 0 else 100.0
    return {
        "total": total,
        "rate_pct": rate,
        "pass_rate_pct": pass_rate,
        "evaluated": evaluated,
    }

def _load_rejection_baseline():
    path = os.path.join(GUI_STATE_DIR, "rejection-baseline.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _write_rejection_baseline(data):
    os.makedirs(GUI_STATE_DIR, exist_ok=True)
    path = os.path.join(GUI_STATE_DIR, "rejection-baseline.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)

def _rejection_deltas(total):
    now = datetime.now(timezone.utc)
    day_key = now.strftime("%Y-%m-%d")
    baseline = _load_rejection_baseline() or {}
    if baseline.get("day") != day_key:
        baseline = {"day": day_key, "midnight_total": total, "session_total": total}
        _write_rejection_baseline(baseline)
    elif "session_total" not in baseline:
        baseline["session_total"] = total
        _write_rejection_baseline(baseline)
    return {
        "today": max(0, total - int(baseline.get("midnight_total", total))),
        "session": max(0, total - int(baseline.get("session_total", total))),
    }

def _policy_settings_from_parsed(parsed):
    settings = dict(parsed)
    profile = settings.get("profile", "maximalist")
    if profile != "custom" and profile in POLICY_PRESETS:
        preset = POLICY_PRESETS[profile]
        for key, val in preset.items():
            if key in settings and settings.get(key) != val:
                settings["profile"] = "custom"
                break
    return settings

def _build_setsovereignpolicy_args(settings):
    settings = _policy_settings_from_parsed(settings)
    profile = settings.get("profile", "maximalist")
    if profile != "custom":
        return ["setsovereignpolicy", str(profile)]
    return [
        "setsovereignpolicy", "custom",
        _bool_cli(settings.get("custom_rules.reject_inscriptions", True)),
        str(settings.get("custom_rules.max_op_return_outputs", 0)),
        _bool_cli(settings.get("custom_rules.reject_tokens", True)),
        str(settings.get("custom_rules.datacarrier_size", 0)),
        str(settings.get("custom_rules.dust_relay_fee", 3000)),
        _bool_cli(settings.get("custom_rules.permit_bare_multisig", False)),
        _bool_cli(settings.get("custom_rules.permit_bare_pubkey", False)),
        _bool_cli(settings.get("custom_rules.reject_parasites", True)),
    ]

def _backup_policy_file(path):
    if not os.path.exists(path):
        return
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{path}.bak.{stamp}"
    try:
        with open(path, "r", encoding="utf-8") as src, open(backup, "w", encoding="utf-8") as dst:
            dst.write(src.read())
    except Exception:
        pass

def _rpc_json(method, datadir, network, extra_args=None, timeout=5.0):
    cmd = [method]
    if extra_args:
        cmd.extend(str(a) for a in extra_args)
    success, output = run_bitcoin_cli(cmd, datadir, network, timeout=timeout)
    if not success:
        return None
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None


def _build_preflight(running, datadir, network):
    checks = []
    bitcoin_conf_path, policy_path = get_config_paths(datadir, network)
    bitcoin_conf = parse_bitcoin_conf(bitcoin_conf_path)
    parsed_policy = parse_policy_toml(policy_path)

    if not os.path.isfile(BITCOIND_PATH):
        checks.append({
            "id": "binary", "severity": "critical",
            "message": f"bitcoind not found at {BITCOIND_PATH}",
            "recommendation": "Run ./build.sh to compile Oracle Knots.",
        })
    else:
        checks.append({"id": "binary", "severity": "info", "message": "bitcoind binary found."})

    if running:
        diag = _rpc_json("getsovereigndiagnostics", datadir, network)
        if diag and diag.get("checks"):
            checks.extend(diag["checks"])
    else:
        checks.append({
            "id": "node_offline", "severity": "warning",
            "message": "Node is not running.",
            "recommendation": "Start the node to enable mempool audit and template stats.",
        })
        if network == "mainnet":
            if not bitcoin_conf.get("onion") and not bitcoin_conf.get("proxy"):
                checks.append({
                    "id": "privacy_tor", "severity": "warning",
                    "message": "No Tor proxy (onion/proxy) in bitcoin.conf.",
                    "recommendation": "Set onion=127.0.0.1:9050 and run scripts/setup-tor-i2p.sh.",
                })
            if bitcoin_conf.get("i2pacceptincoming") in (1, "1") and not bitcoin_conf.get("i2psam"):
                checks.append({
                    "id": "privacy_i2p", "severity": "warning",
                    "message": "I2P incoming enabled but i2psam is not set.",
                    "recommendation": "Set i2psam=127.0.0.1:7656 and run scripts/setup-tor-i2p.sh.",
                })

    conf_profile = bitcoin_conf.get("policyprofile")
    if conf_profile and conf_profile != parsed_policy.get("profile"):
        checks.append({
            "id": "policy_conflict", "severity": "warning",
            "message": f"policy.toml profile '{parsed_policy.get('profile')}' differs from bitcoin.conf policyprofile={conf_profile}",
            "recommendation": "Align both files before restart.",
        })

    severity_rank = {"critical": 0, "warning": 1, "info": 2}
    checks.sort(key=lambda c: severity_rank.get(c.get("severity", "info"), 9))
    return {"checks": checks, "online": running}

def _build_dashboard(running, pid):
    if not running:
        return {
            "online": False,
            "policy": {},
            "mempool": {},
            "rejections": {"top": [], "stats": {}, "deltas": {"today": 0, "session": 0}},
            "peers": {},
            "rdts": {},
            "sync": {},
            "network": {},
            "conflict": None,
            "mining": {},
            "mempool_audit": {},
            "recent_rejections": [],
            "preflight": _build_preflight(False, os.path.expanduser("~/.bitcoin"), "mainnet"),
        }

    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    prom_port = get_prometheus_port(pid)
    metrics = fetch_prometheus_metrics(prom_port) or {}
    prom_rejections = metrics.get("rejections", {})

    policy = _rpc_json("checkbip110status", datadir, network) or {}
    mempool = _rpc_json("getmempoolinfo", datadir, network) or {}
    peers_raw = _rpc_json("getpeerinfo", datadir, network) or []
    deployment = _rpc_json("getdeploymentinfo", datadir, network) or {}
    chain = _rpc_json("getblockchaininfo", datadir, network) or {}
    netinfo = _rpc_json("getnetworkinfo", datadir, network) or {}

    rejections_by_reason = policy.get("rejections_by_reason") or prom_rejections
    mempool_size = mempool.get("size", metrics.get("mempool_size", 0))
    rej_stats = _rejection_stats(rejections_by_reason, mempool_size)
    top, _ = _top_rejections(rejections_by_reason, 5)
    deltas = _rejection_deltas(rej_stats["total"])

    _, policy_path = get_config_paths(datadir, network)
    parsed_policy = parse_policy_toml(policy_path)
    bitcoin_conf_path, _ = get_config_paths(datadir, network)
    bitcoin_conf = parse_bitcoin_conf(bitcoin_conf_path)
    conflict = None
    conf_profile = bitcoin_conf.get("policyprofile")
    if conf_profile and conf_profile != parsed_policy.get("profile"):
        conflict = {
            "toml_profile": parsed_policy.get("profile"),
            "conf_profile": conf_profile,
        }

    max_mempool = mempool.get("maxmempool", bitcoin_conf.get("maxmempool", 100))
    usage = mempool.get("usage", metrics.get("mempool_usage", 0))
    usage_pct = round((usage / max_mempool) * 100, 1) if max_mempool else 0.0

    active_profile = policy.get("active_policy_profile", metrics.get("policy_profile", "unknown"))
    return {
        "online": True,
        "policy": {
            "profile": active_profile,
            "active_policy_profile": active_profile,
            "bip110_mode": policy.get("bip110_mode", metrics.get("bip110_mode", "unknown")),
            "bip110_enforced": policy.get("bip110_enforced", False),
            "reject_inscriptions": policy.get("reject_inscriptions"),
            "max_op_return_outputs": policy.get("max_op_return_outputs"),
            "reject_tokens": parsed_policy.get("custom_rules.reject_tokens"),
            "datacarrier_size": parsed_policy.get("custom_rules.datacarrier_size"),
            "dust_relay_fee": parsed_policy.get("custom_rules.dust_relay_fee"),
            "permit_bare_multisig": parsed_policy.get("custom_rules.permit_bare_multisig"),
            "reject_parasites": parsed_policy.get("custom_rules.reject_parasites"),
            "rejections_by_reason": rejections_by_reason,
        },
        "mempool": {
            "size": mempool_size,
            "bytes": mempool.get("bytes", metrics.get("mempool_bytes", 0)),
            "usage": usage,
            "maxmempool": max_mempool,
            "usage_pct": usage_pct,
            "loaded": mempool.get("loaded", False),
            "mempoolminfee": mempool.get("mempoolminfee"),
            "minrelaytxfee": mempool.get("minrelaytxfee"),
        },
        "rejections": {
            "top": top,
            "stats": rej_stats,
            "deltas": deltas,
        },
        "peers": _summarize_peers(peers_raw if isinstance(peers_raw, list) else []),
        "rdts": _parse_rdts_deployment(deployment),
        "sync": {
            "progress_pct": round((chain.get("verificationprogress", 0) or 0) * 100, 2),
            "blocks": chain.get("blocks", metrics.get("block_height", 0)),
            "headers": chain.get("headers", 0),
            "chain": chain.get("chain", network),
        },
        "network": {
            "subversion": netinfo.get("subversion", "Unknown"),
            "connections": netinfo.get("connections", metrics.get("peers", 0)),
        },
        "metrics": {
            "block_height": metrics.get("block_height", chain.get("blocks", 0)),
            "uptime": metrics.get("uptime", 0),
            "prometheus_port": prom_port,
        },
        "conflict": conflict,
        "mining": _rpc_json("getsovereigntemplatestats", datadir, network) or {},
        "mempool_audit": _rpc_json("getmempoolpolicyaudit", datadir, network, ["200"]) or {},
        "recent_rejections": _rpc_json("getrecentpolicyrejections", datadir, network, ["25"]) or [],
        "preflight": _build_preflight(True, datadir, network),
        "datum": _fetch_datum_status(),
        "top_mempool_txs": _fetch_top_mempool_txs(datadir, network, 5),
    }


def _fetch_datum_status():
    """Scrape the local Datum Gateway status page and return key mining stats."""
    import re
    from html import unescape
    try:
        with urllib.request.urlopen("http://127.0.0.1:7152/", timeout=1.5) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return {}

    def _extract(label):
        pattern = re.escape(label) + r"</td>\s*<td[^>]*>(.*?)</td>"
        m = re.search(pattern, html, re.DOTALL)
        if not m:
            return None
        return unescape(re.sub(r"<[^>]+>", "", m.group(1)).strip())

    shares_raw = _extract("Shares Accepted:") or ""
    shares_num = shares_raw.split()[0] if shares_raw else "0"
    try:
        workers = int(_extract("Total Connections:") or "0")
    except ValueError:
        workers = 0

    return {
        "hashrate": _extract("Estimated Hashrate:"),
        "workers": workers,
        "shares_accepted": shares_num,
        "coinbase_tag": (_extract("Secondary/Miner Tag:") or "").strip('"'),
        "pool_tag": (_extract("Pool Tag:") or "").strip('"'),
        "status": _extract("Status:"),
        "block_value": _extract("Block Value:"),
    }


def _fetch_top_mempool_txs(datadir, network, n=5):
    """Return top N mempool transactions sorted by fee rate (sat/vB)."""
    global _mempool_txs_cache
    now = time.time()
    cache_key = (datadir, network, n)
    if (
        _mempool_txs_cache["data"]
        and _mempool_txs_cache["key"] == cache_key
        and (now - _mempool_txs_cache["ts"]) < MEMPOOL_TXS_CACHE_TTL
    ):
        return _mempool_txs_cache["data"]

    raw = _rpc_json("getrawmempool", datadir, network, ["true"])
    if not raw or not isinstance(raw, dict):
        return []
    txs = []
    for txid, info in raw.items():
        try:
            fee_btc = info.get("fees", {}).get("modified") or info.get("fee", 0)
            vsize = info.get("vsize") or info.get("size") or 1
            fee_sat = round(fee_btc * 1e8)
            fee_rate = round(fee_sat / vsize, 1)
            txs.append({"txid": txid[:12], "fee_sat": fee_sat, "vsize": vsize, "fee_rate": fee_rate})
        except Exception:
            continue
    txs.sort(key=lambda x: x["fee_rate"], reverse=True)
    result = txs[:n]
    _mempool_txs_cache = {"ts": now, "key": cache_key, "data": result}
    return result


# ----------------------------------------------------
# Configuration Parsing / Updating Utilities
# ----------------------------------------------------
UA_COMMENT_UNSAFE = set("/:()")
UA_COMMENT_MAX_LEN = 64


def _sanitize_uacomment(value):
    """Sanitize -uacomment per Bitcoin Core rules (BIP-14 subset)."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if len(text) > UA_COMMENT_MAX_LEN:
        raise ValueError(
            f"User Agent comment must be {UA_COMMENT_MAX_LEN} characters or fewer"
        )
    for ch in text:
        if ch in UA_COMMENT_UNSAFE:
            raise ValueError(
                f"User Agent comment contains unsafe character: {ch!r} (forbidden: / : ( ))"
            )
        if ord(ch) > 127:
            raise ValueError(
                f"User Agent comment contains non-ASCII character: {ch!r}"
            )
    return text


def parse_bitcoin_conf(file_path):
    config = {}
    if not os.path.exists(file_path):
        return config
    try:
        repeating_keys = ["onlynet", "addnode", "connect"]
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip()
                    if '#' in v:
                        v = v.split('#', 1)[0].strip()
                    
                    if k in repeating_keys:
                        if k not in config:
                            config[k] = []
                        config[k].append(v)
                    else:
                        try:
                            if v.isdigit():
                                v = int(v)
                        except ValueError:
                            pass
                        config[k] = v
    except Exception:
        pass
    return config

def update_bitcoin_conf(file_path, new_settings):
    repeating_keys = ["onlynet", "addnode", "connect"]
    lines = []
    keys_written = set()
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#') and '=' in stripped:
                        k, v = stripped.split('=', 1)
                        k = k.strip()
                        # If this is a repeating key, we will write them all at the end
                        if k in repeating_keys:
                            continue
                        if k in new_settings:
                            val = new_settings[k]
                            if val is None or val == "":
                                lines.append(f"# {k} is disabled/unset\n")
                            else:
                                if isinstance(val, float):
                                    val_str = f"{val:.8f}".rstrip('0').rstrip('.')
                                else:
                                    val_str = str(val)
                                lines.append(f"{k}={val_str}\n")
                            keys_written.add(k)
                            continue
                    lines.append(line)
        except Exception:
            pass
            
    # Write non-repeating keys that were not in the file
    for k, val in new_settings.items():
        if k not in repeating_keys and k not in keys_written:
            if val is not None and val != "":
                if isinstance(val, float):
                    val_str = f"{val:.8f}".rstrip('0').rstrip('.')
                else:
                    val_str = str(val)
                lines.append(f"{k}={val_str}\n")
                
    # Write repeating keys (onlynet, addnode, connect) if they exist in new_settings
    for k in repeating_keys:
        if k in new_settings:
            val = new_settings[k]
            # val can be a list or a comma-separated string
            if isinstance(val, list):
                for item in val:
                    if item:
                        lines.append(f"{k}={item}\n")
            elif isinstance(val, str) and val.strip():
                # split by commas or spaces
                items = val.replace(',', ' ').split()
                for item in items:
                    item = item.strip()
                    if item:
                        lines.append(f"{k}={item}\n")
                        
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def parse_policy_toml(file_path):
    config = {}
    if not os.path.exists(file_path):
        return config
    try:
        in_custom_rules = False
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line == "[custom_rules]":
                    in_custom_rules = True
                    continue
                if line.startswith("[") and line.endswith("]"):
                    in_custom_rules = False
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip()
                    if v.startswith('"') and v.endswith('"'):
                        v = v[1:-1]
                    elif v == "true":
                        v = True
                    elif v == "false":
                        v = False
                    else:
                        try:
                            v = int(v)
                        except ValueError:
                            pass
                    
                    if in_custom_rules:
                        config[f"custom_rules.{k}"] = v
                    else:
                        config[k] = v
    except Exception:
        pass
    return config

def update_policy_toml(file_path, new_settings):
    lines = []
    
    profile = new_settings.get("profile", "maximalist")
    bip110_mode = new_settings.get("bip110_mode", "auto")
    
    lines.append(f'profile = "{profile}"\n')
    lines.append(f'bip110_mode = "{bip110_mode}"\n\n')
    lines.append('[custom_rules]\n')
    
    custom_keys = [
        "datacarrier_size", "reject_tokens", "reject_inscriptions", 
        "dust_relay_fee", "permit_bare_multisig", "permit_bare_pubkey", 
        "reject_parasites", "max_op_return_outputs"
    ]
    
    for k in custom_keys:
        val = new_settings.get(f"custom_rules.{k}")
        if val is None:
            val = new_settings.get(k)
        
        if val is not None:
            if isinstance(val, bool):
                val_str = "true" if val else "false"
            else:
                val_str = str(val)
            lines.append(f"{k} = {val_str}\n")
            
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

# ----------------------------------------------------
# Bottle Web Server API Endpoints
# ----------------------------------------------------
@route('/')
def index():
    return static_file('index.html', root=GUI_DIR)

@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root=GUI_DIR)

@route('/static/assets/<filename:path>')
def send_assets(filename):
    return static_file(filename, root=os.path.join(GUI_DIR, 'assets'))

@route('/api/status')
def api_status():
    running, pid = check_node_running()
    if running:
        datadir = get_node_datadir(pid)
        network = get_node_network(pid)
        return {
            "running": True,
            "pid": pid,
            "datadir": datadir,
            "network": network
        }
    else:
        return {
            "running": False,
            "pid": None,
            "datadir": os.path.expanduser("~/.bitcoin"),
            "network": "mainnet"
        }

@route('/api/clipboard', method='POST')
def api_clipboard():
    """Clipboard proxy — non-blocking. wl-copy/xclip run as detached subprocesses so
    they never block the Bottle server thread. On Wayland, wl-copy stays alive as a
    daemon serving clipboard requests; we don't wait for it to exit."""
    data = request.json or {}
    text = data.get('text', '')
    response.content_type = 'application/json'
    if not text:
        return json.dumps({'success': False, 'error': 'no text'})

    if sys.platform != 'linux':
        return json.dumps({'success': False, 'error': 'non-linux'})

    env = dict(os.environ)
    session = env.get('XDG_SESSION_TYPE', '').lower()

    if session == 'wayland':
        # wl-copy reads stdin then stays alive serving clipboard requests.
        # Use Popen + communicate (no timeout) — it finishes reading stdin quickly.
        try:
            proc = subprocess.Popen(
                ['wl-copy'],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                close_fds=True
            )
            proc.stdin.write(text.encode('utf-8'))
            proc.stdin.close()
            # Don't wait — wl-copy runs as daemon. Assume success if Popen didn't throw.
            return json.dumps({'success': True})
        except FileNotFoundError:
            pass
        except Exception as e:
            sys.stderr.write(f'[clipboard] wl-copy error: {e}\n')

    # X11 fallback (xclip / xsel) — these exit after writing, so run() is fine
    for cmd in (['xclip', '-selection', 'clipboard'], ['xsel', '--clipboard', '--input']):
        try:
            subprocess.run(cmd, input=text.encode('utf-8'), check=True,
                           capture_output=True, timeout=3)
            return json.dumps({'success': True})
        except (FileNotFoundError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired):
            continue

    return json.dumps({'success': False, 'error': 'no clipboard tool available'})

@route('/api/start', method='POST')
def api_start():
    data = request.json or {}
    network = data.get("network", "mainnet")
    datadir = data.get("datadir", "").strip()
    extra_args = data.get("extra_args", "").strip()
    
    # Build command
    cmd = [BITCOIND_PATH, "-daemon", "-prometheus=1", "-prometheusport=9332"]
    if network == "testnet":
        cmd.append("-testnet")
    elif network == "regtest":
        cmd.append("-regtest")
    elif network == "signet":
        cmd.append("-signet")
        
    if datadir:
        datadir_expanded = os.path.expanduser(datadir)
        os.makedirs(datadir_expanded, exist_ok=True)
        cmd.append(f"-datadir={datadir_expanded}")
        
    if extra_args:
        cmd.extend(shlex.split(extra_args))
        
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@route('/api/stop', method='POST')
def api_stop():
    running, pid = check_node_running()
    if not running:
        return {"success": True}
        
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    
    success, output = run_bitcoin_cli(["stop"], datadir, network)
    if success:
        for _ in range(15):
            running, _ = check_node_running()
            if not running:
                return {"success": True}
            time.sleep(0.5)
            
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(10):
            running, _ = check_node_running()
            if not running:
                return {"success": True}
            time.sleep(0.5)
        os.kill(pid, signal.SIGKILL)
        return {"success": True, "note": "Killed process forcefully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@route('/api/metrics')
def api_metrics():
    running, pid = check_node_running()
    if not running:
        return {"error": "Node is not running"}
        
    prom_port = get_prometheus_port(pid)
    metrics = fetch_prometheus_metrics(prom_port)
    if metrics:
        metrics["prometheus_port"] = prom_port
        return metrics
    else:
        return {
            "block_height": 0,
            "mempool_size": 0,
            "mempool_bytes": 0,
            "mempool_usage": 0,
            "peers": 0,
            "peers_inbound": 0,
            "peers_outbound": 0,
            "policy_profile": "unknown",
            "bip110_mode": "unknown",
            "rejections": {},
            "uptime": 0,
            "prometheus_port": prom_port
        }

@route('/api/preflight')
def api_preflight():
    running, pid = check_node_running()
    datadir = get_node_datadir(pid) if running else os.path.expanduser("~/.bitcoin")
    network = get_node_network(pid) if running else "mainnet"
    return _build_preflight(running, datadir, network)

@route('/api/mempool-audit')
def api_mempool_audit():
    running, pid = check_node_running()
    if not running:
        return {"success": False, "error": "Node is offline"}
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    limit = request.query.get("limit", "500")
    audit = _rpc_json("getmempoolpolicyaudit", datadir, network, [limit])
    if audit is None:
        return {"success": False, "error": "getmempoolpolicyaudit unavailable — rebuild bitcoind"}
    return {"success": True, "audit": audit}

@route('/api/chain-strip')
def api_chain_strip():
    global _chain_strip_cache
    now = time.time()
    running, pid = check_node_running()
    tip_height = None
    if running:
        chain = _rpc_json(
            "getblockchaininfo",
            get_node_datadir(pid),
            get_node_network(pid),
        ) or {}
        tip_height = chain.get("blocks")

    cached = _chain_strip_cache.get("data")
    cache_tip = _chain_strip_cache.get("tip_height")
    cache_age = now - _chain_strip_cache.get("ts", 0.0)
    if (
        cached is not None
        and cache_age < CHAIN_STRIP_CACHE_TTL
        and (tip_height is None or tip_height == cache_tip)
    ):
        return cached

    data = _build_chain_strip(running, pid)
    _chain_strip_cache = {"ts": now, "tip_height": tip_height, "data": data}
    return data


@route('/api/dashboard')
def api_dashboard():
    global _dashboard_cache
    now = time.time()
    if _dashboard_cache["data"] and (now - _dashboard_cache["ts"]) < DASHBOARD_CACHE_TTL:
        return _dashboard_cache["data"]
    running, pid = check_node_running()
    data = _build_dashboard(running, pid)
    _dashboard_cache = {"ts": now, "data": data}
    return data

@route('/api/rpc/<method>')
def api_rpc(method):
    running, pid = check_node_running()
    if not running:
        return {"success": False, "output": "Node is offline"}
        
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    
    safe_methods = [
        "getblockchaininfo", "getpeerinfo", "checkbip110status",
        "getnetworkinfo", "getmempoolinfo", "getdeploymentinfo",
        "getindexinfo",
    ]
    if method not in safe_methods:
        return {"success": False, "output": f"RPC method {method} not allowed"}
        
    success, output = run_bitcoin_cli([method], datadir, network)
    return {"success": success, "output": output}

# ----------------------------------------------------
# Mempool Explorer API
# ----------------------------------------------------

EXPLORER_MAX_TXS = 2500
EXPLORER_BLOCK_WEIGHT = 4_000_000
EXPLORER_COINBASE_RESERVE_VB = 4_000
EXPLORER_PROJECTED_BLOCKS = 3
EXPLORER_FEE_BUCKETS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 40, 50, 70, 100, 150, 200, 300]

_explorer_mempool_cache = {"ts": 0.0, "key": None, "data": None}
EXPLORER_MEMPOOL_CACHE_TTL = 10.0
_explorer_block_cache = {}   # (hash, page, per_page) -> {"ts", "data"}
EXPLORER_BLOCK_CACHE_TTL = 60.0
_explorer_tx_cache = {}      # txid -> {"ts", "ttl", "data"}
_scan_job = {"address": None, "thread": None, "done": True, "result": None,
             "error": None, "started_at": 0.0}
_scan_results_cache = {}     # address -> {"ts", "data"}
SCAN_RESULT_CACHE_TTL = 300.0


def _fee_bucket_label(rate):
    prev = 0
    for b in EXPLORER_FEE_BUCKETS:
        if rate < b:
            return f"{prev}-{b}"
        prev = b
    return f"{EXPLORER_FEE_BUCKETS[-1]}+"


def _build_explorer_mempool(datadir, network):
    info = _rpc_json("getmempoolinfo", datadir, network) or {}
    raw = _rpc_json("getrawmempool", datadir, network, ["true"], timeout=20.0)
    if raw is None or not isinstance(raw, dict):
        return {
            "online": True,
            "degraded": True,
            "mempoolinfo": info,
            "projected_blocks": [],
            "histogram": [],
            "updated_at": int(time.time()),
        }

    entries = []
    for txid, e in raw.items():
        try:
            vsize = int(e.get("vsize") or e.get("size") or 1)
            fee_btc = (e.get("fees") or {}).get("base")
            if fee_btc is None:
                fee_btc = e.get("fee", 0)
            fee_sat = round(float(fee_btc) * 1e8)
            rate = fee_sat / max(vsize, 1)
            anc = int(e.get("ancestorcount") or 1)
            entries.append((txid, vsize, rate, fee_sat, anc))
        except Exception:
            continue
    entries.sort(key=lambda x: x[2], reverse=True)

    block_cap_vb = (EXPLORER_BLOCK_WEIGHT // 4) - EXPLORER_COINBASE_RESERVE_VB
    projected = []
    cur = {"txs": [], "total_vsize": 0, "total_fees": 0, "rates": []}
    emitted = 0
    for txid, vsize, rate, fee_sat, anc in entries:
        if emitted >= EXPLORER_MAX_TXS:
            break
        if cur["total_vsize"] + vsize > block_cap_vb and cur["txs"]:
            projected.append(cur)
            if len(projected) >= EXPLORER_PROJECTED_BLOCKS:
                cur = None
                break
            cur = {"txs": [], "total_vsize": 0, "total_fees": 0, "rates": []}
        cur["txs"].append([txid, vsize, round(rate, 1), anc])
        cur["total_vsize"] += vsize
        cur["total_fees"] += fee_sat
        cur["rates"].append(rate)
        emitted += 1
    if cur and cur["txs"]:
        projected.append(cur)

    blocks_out = []
    for b in projected:
        rates = sorted(b["rates"])
        median = rates[len(rates) // 2] if rates else 0
        blocks_out.append({
            "txs": b["txs"],
            "tx_count": len(b["txs"]),
            "total_vsize": b["total_vsize"],
            "total_fees_sat": b["total_fees"],
            "median_feerate": round(median, 1),
            "min_feerate": round(rates[0], 1) if rates else 0,
            "max_feerate": round(rates[-1], 1) if rates else 0,
            "fill_pct": round(min(100.0, b["total_vsize"] / block_cap_vb * 100), 1),
        })

    # Tail histogram: everything not emitted individually
    hist = {}
    tail_vsize = 0
    for txid, vsize, rate, fee_sat, anc in entries[emitted:]:
        label = _fee_bucket_label(rate)
        h = hist.setdefault(label, {"bucket": label, "count": 0, "total_vsize": 0})
        h["count"] += 1
        h["total_vsize"] += vsize
        tail_vsize += vsize
    # keep bucket order high→low fee
    ordered_labels = [f"{EXPLORER_FEE_BUCKETS[-1]}+"] + [
        f"{a}-{b}" for a, b in zip([0] + EXPLORER_FEE_BUCKETS, EXPLORER_FEE_BUCKETS)
    ][::-1]
    histogram = [hist[l] for l in ordered_labels if l in hist]

    return {
        "online": True,
        "degraded": False,
        "mempoolinfo": {
            "size": info.get("size"),
            "bytes": info.get("bytes"),
            "usage": info.get("usage"),
            "mempoolminfee": info.get("mempoolminfee"),
        },
        "projected_blocks": blocks_out,
        "histogram": histogram,
        "tail_tx_count": max(0, len(entries) - emitted),
        "tail_vsize": tail_vsize,
        "tail_full_blocks": round(tail_vsize / block_cap_vb, 1) if tail_vsize else 0,
        "updated_at": int(time.time()),
    }


@route('/api/explorer/mempool')
def api_explorer_mempool():
    global _explorer_mempool_cache
    running, datadir, network = get_node_context()
    if not running:
        return {"online": False}
    now = time.time()
    key = (datadir, network)
    if (
        _explorer_mempool_cache["data"] is not None
        and _explorer_mempool_cache["key"] == key
        and (now - _explorer_mempool_cache["ts"]) < EXPLORER_MEMPOOL_CACHE_TTL
    ):
        return _explorer_mempool_cache["data"]
    data = _build_explorer_mempool(datadir, network)
    _explorer_mempool_cache = {"ts": now, "key": key, "data": data}
    return data


@route('/api/explorer/capabilities')
def api_explorer_capabilities():
    running, datadir, network = get_node_context()
    if not running:
        return {"online": False}
    idx = _rpc_json("getindexinfo", datadir, network) or {}
    chain = _rpc_json("getblockchaininfo", datadir, network) or {}
    tip = int(chain.get("blocks") or 0)
    tx = idx.get("txindex")
    if tx is None:
        txinfo = {"available": False, "synced": False, "progress": 0}
    else:
        best = int(tx.get("best_block_height") or 0)
        synced = bool(tx.get("synced"))
        progress = 100.0 if synced else round(best / tip * 100, 1) if tip else 0
        txinfo = {"available": True, "synced": synced, "progress": progress}
    return {"online": True, "txindex": txinfo, "tip_height": tip}


def _explorer_tx_summary(tx):
    """Compact per-tx summary for block page listings."""
    total_out = sum(float(o.get("value") or 0) for o in tx.get("vout", []))
    return {
        "txid": tx.get("txid"),
        "vsize": tx.get("vsize"),
        "n_in": len(tx.get("vin", [])),
        "n_out": len(tx.get("vout", [])),
        "total_out_btc": round(total_out, 8),
        "is_coinbase": any("coinbase" in vin for vin in tx.get("vin", [])),
    }


@route('/api/explorer/block/<query>')
def api_explorer_block(query):
    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}
    try:
        page = max(0, int(request.query.get("page", "0")))
        per_page = min(100, max(5, int(request.query.get("per_page", "25"))))
    except ValueError:
        page, per_page = 0, 25

    block_hash = query
    if query.isdigit():
        ok, out = run_bitcoin_cli(["getblockhash", query], datadir, network)
        if not ok:
            return {"success": False, "error": f"Block height {query} not found"}
        block_hash = out.strip()

    now = time.time()
    ck = (block_hash, page, per_page)
    cached = _explorer_block_cache.get(ck)
    if cached and (now - cached["ts"]) < EXPLORER_BLOCK_CACHE_TTL:
        return cached["data"]

    block = _rpc_json("getblock", datadir, network, [block_hash, "1"], timeout=15.0)
    if not block:
        return {"success": False, "error": "Block not found"}

    txids = block.get("tx", [])
    start = page * per_page
    page_txids = txids[start:start + per_page]
    page_txs = []
    for txid in page_txids:
        tx = _rpc_json("getrawtransaction", datadir, network,
                       [txid, "true", block_hash], timeout=10.0)
        page_txs.append(_explorer_tx_summary(tx) if tx else {"txid": txid})

    # Merge policy audit when this block is in the recent audit window
    policy = None
    audit = _rpc_json("getrecentblockpolicyaudit", datadir, network, timeout=20.0)
    if audit:
        for b in audit.get("blocks", []):
            if b.get("hash") == block_hash:
                policy = _normalize_chain_block(b)
                break

    data = {
        "success": True,
        "block": {
            "hash": block.get("hash"),
            "height": block.get("height"),
            "time": block.get("time"),
            "n_tx": block.get("nTx") or len(txids),
            "size": block.get("size"),
            "weight": block.get("weight"),
            "version_hex": block.get("versionHex"),
            "merkleroot": block.get("merkleroot"),
            "difficulty": block.get("difficulty"),
            "previousblockhash": block.get("previousblockhash"),
            "nextblockhash": block.get("nextblockhash"),
            "confirmations": block.get("confirmations"),
        },
        "policy": policy,
        "txs": page_txs,
        "page": page,
        "per_page": per_page,
        "total_pages": (len(txids) + per_page - 1) // per_page,
    }
    _explorer_block_cache[ck] = {"ts": now, "data": data}
    if len(_explorer_block_cache) > 64:
        oldest = min(_explorer_block_cache, key=lambda k: _explorer_block_cache[k]["ts"])
        _explorer_block_cache.pop(oldest, None)
    return data


@route('/api/explorer/tx/<txid>')
def api_explorer_tx(txid):
    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}
    txid = txid.strip().lower()
    if len(txid) != 64 or any(c not in "0123456789abcdef" for c in txid):
        return {"success": False, "error": "Invalid txid"}

    now = time.time()
    cached = _explorer_tx_cache.get(txid)
    if cached and (now - cached["ts"]) < cached["ttl"]:
        return cached["data"]

    blockhash_hint = request.query.get("blockhash", "").strip()
    args = [txid, "true"] + ([blockhash_hint] if blockhash_hint else [])
    tx = _rpc_json("getrawtransaction", datadir, network, args, timeout=10.0)
    if not tx:
        # Distinguish "needs txindex" from "not found"
        idx = _rpc_json("getindexinfo", datadir, network) or {}
        needs_txindex = "txindex" not in idx
        return {
            "success": False,
            "error": ("Transaction not found. Confirmed transactions require txindex "
                      "(not enabled on this node)." if needs_txindex
                      else "Transaction not found."),
            "needs_txindex": needs_txindex,
        }

    confirmed = bool(tx.get("blockhash"))
    mempool_entry = None
    if not confirmed:
        mempool_entry = _rpc_json("getmempoolentry", datadir, network, [txid])

    # Resolve input values/addresses (cap 25)
    vins = tx.get("vin", [])
    inputs = []
    total_in = 0.0
    resolved_all = True
    for i, vin in enumerate(vins):
        if "coinbase" in vin:
            inputs.append({"coinbase": True})
            continue
        if i >= 25:
            resolved_all = False
            break
        prev = _rpc_json("getrawtransaction", datadir, network,
                         [vin.get("txid", ""), "true"], timeout=8.0)
        entry = {"txid": vin.get("txid"), "vout": vin.get("vout")}
        if prev:
            try:
                po = prev["vout"][vin["vout"]]
                entry["value"] = po.get("value")
                entry["address"] = (po.get("scriptPubKey") or {}).get("address")
                total_in += float(po.get("value") or 0)
            except (KeyError, IndexError, TypeError):
                resolved_all = False
        else:
            resolved_all = False
        inputs.append(entry)

    outputs = []
    total_out = 0.0
    for o in tx.get("vout", []):
        spk = o.get("scriptPubKey") or {}
        outputs.append({
            "n": o.get("n"),
            "value": o.get("value"),
            "address": spk.get("address"),
            "type": spk.get("type"),
        })
        total_out += float(o.get("value") or 0)

    is_coinbase = any("coinbase" in v for v in vins)
    fee_sat = None
    if mempool_entry:
        try:
            fee_sat = round(float(mempool_entry["fees"]["base"]) * 1e8)
        except (KeyError, TypeError):
            pass
    elif resolved_all and not is_coinbase:
        fee_sat = round((total_in - total_out) * 1e8)

    # Policy verdict for unconfirmed txs
    policy_verdict = None
    if not confirmed:
        audit = _rpc_json("getmempoolpolicyaudit", datadir, network, ["500"])
        if audit and isinstance(audit, dict):
            for item in audit.get("transactions", audit.get("txs", []) or []):
                if isinstance(item, dict) and item.get("txid") == txid:
                    policy_verdict = item
                    break

    data = {
        "success": True,
        "tx": {
            "txid": tx.get("txid"),
            "confirmed": confirmed,
            "blockhash": tx.get("blockhash"),
            "confirmations": tx.get("confirmations", 0),
            "blocktime": tx.get("blocktime"),
            "vsize": tx.get("vsize"),
            "weight": tx.get("weight"),
            "size": tx.get("size"),
            "version": tx.get("version"),
            "locktime": tx.get("locktime"),
            "is_coinbase": is_coinbase,
            "inputs": inputs,
            "inputs_truncated": len(vins) > 25,
            "outputs": outputs,
            "total_out_btc": round(total_out, 8),
            "fee_sat": fee_sat,
            "feerate_satvb": round(fee_sat / tx["vsize"], 1) if fee_sat and tx.get("vsize") else None,
            "mempool_entry": {
                "time": mempool_entry.get("time"),
                "ancestorcount": mempool_entry.get("ancestorcount"),
                "descendantcount": mempool_entry.get("descendantcount"),
            } if mempool_entry else None,
            "policy_verdict": policy_verdict,
        },
    }
    ttl = 300.0 if confirmed else 10.0
    _explorer_tx_cache[txid] = {"ts": now, "ttl": ttl, "data": data}
    if len(_explorer_tx_cache) > 128:
        oldest = min(_explorer_tx_cache, key=lambda k: _explorer_tx_cache[k]["ts"])
        _explorer_tx_cache.pop(oldest, None)
    return data


def _run_address_scan(address, datadir, network):
    global _scan_job
    descriptor = json.dumps([f"addr({address})"])
    result = _rpc_json("scantxoutset", datadir, network,
                       ["start", descriptor], timeout=300.0)
    if result and result.get("success"):
        utxos = [{
            "txid": u.get("txid"),
            "vout": u.get("vout"),
            "amount": u.get("amount"),
            "height": u.get("height"),
        } for u in result.get("unspents", [])]
        data = {
            "done": True, "success": True, "address": address,
            "utxos": utxos,
            "utxo_count": len(utxos),
            "total_amount": result.get("total_amount"),
            "height": result.get("height"),
        }
        _scan_results_cache[address] = {"ts": time.time(), "data": data}
        _scan_job["result"] = data
    else:
        _scan_job["error"] = "Scan failed or was aborted"
    _scan_job["done"] = True


@route('/api/explorer/address/scan', method='POST')
def api_explorer_address_scan():
    global _scan_job
    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}
    body = request.json or {}
    address = (body.get("address") or "").strip()
    if not address:
        return {"success": False, "error": "Address missing"}

    cached = _scan_results_cache.get(address)
    if cached and (time.time() - cached["ts"]) < SCAN_RESULT_CACHE_TTL:
        return {"success": True, "cached": True, "result": cached["data"]}

    valid = _rpc_json("validateaddress", datadir, network, [address])
    if not valid or not valid.get("isvalid"):
        return {"success": False, "error": "Invalid address for this network"}

    if not _scan_job["done"]:
        response.status = 409
        return {"success": False, "error": "A scan is already running",
                "in_flight": _scan_job["address"]}

    _scan_job = {"address": address, "thread": None, "done": False,
                 "result": None, "error": None, "started_at": time.time()}
    t = threading.Thread(target=_run_address_scan,
                         args=(address, datadir, network), daemon=True)
    _scan_job["thread"] = t
    t.start()
    return {"success": True, "started": True, "address": address}


@route('/api/explorer/address/status')
def api_explorer_address_status():
    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}
    if _scan_job["address"] is None:
        return {"success": True, "idle": True}
    if not _scan_job["done"]:
        st = _rpc_json("scantxoutset", datadir, network, ["status"]) or {}
        return {"success": True, "done": False, "address": _scan_job["address"],
                "progress": st.get("progress", 0)}
    if _scan_job["error"]:
        return {"success": False, "done": True, "error": _scan_job["error"]}
    return {"success": True, "done": True, "result": _scan_job["result"]}


@route('/api/explorer/address/abort', method='POST')
def api_explorer_address_abort():
    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}
    run_bitcoin_cli(["scantxoutset", "abort"], datadir, network)
    return {"success": True}


@route('/api/explorer/search')
def api_explorer_search():
    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}
    q = (request.query.get("q") or "").strip()
    if not q:
        return {"success": False, "error": "Empty query"}

    if q.isdigit() and len(q) <= 9:
        return {"success": True, "type": "block", "target": q}

    ql = q.lower()
    if len(ql) == 64 and all(c in "0123456789abcdef" for c in ql):
        ok, _ = run_bitcoin_cli(["getblockheader", ql], datadir, network)
        if ok:
            return {"success": True, "type": "block", "target": ql}
        return {"success": True, "type": "tx", "target": ql}

    valid = _rpc_json("validateaddress", datadir, network, [q])
    if valid and valid.get("isvalid"):
        return {"success": True, "type": "address", "target": q}

    return {"success": False, "error": "Not a valid txid, block, or address"}


@route('/api/rpc/set-policy', method='POST')
def api_rpc_set_policy():
    running, pid = check_node_running()
    if not running:
        return {"success": False, "output": "Node is offline"}
        
    data = request.json or {}
    profile = data.get("profile")
    if not profile:
        return {"success": False, "output": "Profile missing"}
        
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    settings = {"profile": profile}
    for key in ("reject_inscriptions", "reject_tokens", "datacarrier_size",
                "max_op_return_outputs", "dust_relay_fee", "permit_bare_multisig",
                "permit_bare_pubkey", "reject_parasites"):
        if key in data:
            settings[f"custom_rules.{key}"] = data[key]
    args = _build_setsovereignpolicy_args(settings)
    success, output = run_bitcoin_cli(args, datadir, network)
    return {"success": success, "output": output}

@route('/api/policy/apply', method='POST')
def api_policy_apply():
    running, pid = check_node_running()
    datadir = get_node_datadir(pid) if running else os.path.expanduser("~/.bitcoin")
    network = get_node_network(pid) if running else "mainnet"
    _, policy_path = get_config_paths(datadir, network)

    if not os.path.exists(policy_path):
        return {"success": False, "error": "policy.toml not found"}

    settings = parse_policy_toml(policy_path)
    if not running:
        return {"success": True, "applied": False, "message": "Saved on disk; start node to apply"}

    args = _build_setsovereignpolicy_args(settings)
    success, output = run_bitcoin_cli(args, datadir, network)
    status = _rpc_json("checkbip110status", datadir, network) if success else None
    return {
        "success": success,
        "output": output,
        "policy": status,
        "applied": success,
    }

@route('/api/rpc/reload-policy', method='POST')
def api_rpc_reload_policy():
    return api_policy_apply()

# ----------------------------------------------------
# Configuration Endpoints (Visual Settings Form Support)
# ----------------------------------------------------
@route('/api/config')
def api_get_config():
    running, pid = check_node_running()
    datadir = get_node_datadir(pid) if running else os.path.expanduser("~/.bitcoin")
    network = get_node_network(pid) if running else "mainnet"
    
    bitcoin_conf_path, policy_toml_path = get_config_paths(datadir, network)
    response_data = {
        "success": True,
        "bitcoin_conf": "",
        "policy_toml": ""
    }
    
    try:
        if os.path.exists(bitcoin_conf_path):
            with open(bitcoin_conf_path, "r", encoding="utf-8") as f:
                response_data["bitcoin_conf"] = f.read()
    except Exception as e:
        response_data["bitcoin_conf_error"] = str(e)
        
    try:
        if os.path.exists(policy_toml_path):
            with open(policy_toml_path, "r", encoding="utf-8") as f:
                response_data["policy_toml"] = f.read()
    except Exception as e:
        response_data["policy_toml_error"] = str(e)
        
    return response_data

@route('/api/config', method='POST')
def api_save_config():
    data = request.json or {}
    filename = data.get("filename")
    content = data.get("content", "")
    
    if filename not in ["bitcoin.conf", "policy.toml"]:
        return {"success": False, "error": "Invalid filename"}
        
    running, pid = check_node_running()
    datadir = get_node_datadir(pid) if running else os.path.expanduser("~/.bitcoin")
    network = get_node_network(pid) if running else "mainnet"
    
    bitcoin_conf_path, policy_toml_path = get_config_paths(datadir, network)
    target_path = bitcoin_conf_path if filename == "bitcoin.conf" else policy_toml_path
    
    try:
        if filename == "policy.toml":
            _backup_policy_file(target_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        if filename == "policy.toml" and data.get("apply_now") and running:
            settings = parse_policy_toml(target_path)
            args = _build_setsovereignpolicy_args(settings)
            ok, out = run_bitcoin_cli(args, datadir, network)
            return {"success": True, "applied": ok, "apply_output": out}
        return {"success": True, "applied": False}
    except Exception as e:
        return {"success": False, "error": str(e)}

@route('/api/config/parsed')
def api_get_parsed_config():
    running, pid = check_node_running()
    datadir = get_node_datadir(pid) if running else os.path.expanduser("~/.bitcoin")
    network = get_node_network(pid) if running else "mainnet"
    
    bitcoin_conf_path, policy_toml_path = get_config_paths(datadir, network)
    
    merged_settings = {}
    
    bitcoin_settings = parse_bitcoin_conf(bitcoin_conf_path)
    merged_settings.update(bitcoin_settings)
    
    policy_settings = parse_policy_toml(policy_toml_path)
    merged_settings.update(policy_settings)
    
    return {"success": True, "settings": merged_settings}

@route('/api/config/parsed', method='POST')
def api_save_parsed_config():
    data = request.json or {}
    
    running, pid = check_node_running()
    datadir = get_node_datadir(pid) if running else os.path.expanduser("~/.bitcoin")
    network = get_node_network(pid) if running else "mainnet"
    
    bitcoin_conf_path, policy_toml_path = get_config_paths(datadir, network)
    
    # Fully expanded key mappings from forms
    bitcoin_keys = [
        "maxmempool", "dbcache", "maxconnections", "txindex", 
        "blocksonly", "proxy", "onion", "i2psam", "torcontrol", "listenonion", "discover",
        "prometheus", "prometheusport", "prune", "listen",
        "connect", "addnode", "par", "server", "rpcport", "rpcallowip",
        "onlynet", "i2pacceptincoming", "peerblockfilters", "blockfilterindex",
        "peerbloomfilters", "bantime", "maxreceivebuffer", "maxsendbuffer",
        "peertimeout", "timeout", "maxuploadtarget",
        "datacarrier", "datacarriersize", "permitbaremultisig", "rejectparasites",
        "rejecttokens", "permitbarepubkey", "permitbaredatacarrier", "datacarriercost",
        "acceptnonstddatacarrier", "maxscriptsize", "blockmaxsize", "blockmaxweight",
        "blockmintxfee", "minrelaytxfee", "incrementalrelayfee",
        "blockreconstructionextratxn", "blockreconstructionextratxnsize",
        "coinstatsindex", "mempoolexpiry", "persistmempool", "maxorphantx", "datum",
        "chain", "rest", "rpcworkqueue",
        "policyprofile", "bip110", "rejectinscriptions", "uacomment",
    ]




    
    bitcoin_settings = {}
    policy_settings = {}
    
    for k, val in data.items():
        if k in bitcoin_keys:
            bitcoin_settings[k] = val
        elif k.startswith("custom_rules.") or k in ["profile", "bip110_mode"]:
            policy_settings[k] = val

    if "uacomment" in bitcoin_settings:
        try:
            bitcoin_settings["uacomment"] = _sanitize_uacomment(
                bitcoin_settings["uacomment"]
            )
        except ValueError as e:
            return {"success": False, "error": str(e)}
            
    try:
        _backup_policy_file(policy_toml_path)
        update_bitcoin_conf(bitcoin_conf_path, bitcoin_settings)
        update_policy_toml(policy_toml_path, policy_settings)
        apply_now = data.get("apply_now", False)
        if apply_now:
            running, pid = check_node_running()
            if running:
                merged = {**policy_settings}
                for k, v in bitcoin_settings.items():
                    merged[k] = v
                args = _build_setsovereignpolicy_args(merged)
                ok, out = run_bitcoin_cli(args, get_node_datadir(pid), get_node_network(pid))
                return {"success": True, "applied": ok, "apply_output": out}
        return {"success": True, "applied": False}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ----------------------------------------------------
# Wallet PSBT / Send Helpers
# ----------------------------------------------------
def _btc_kvb_to_sat_vb(feerate_btc_kvb):
    if feerate_btc_kvb is None or feerate_btc_kvb < 0:
        return None
    return round(feerate_btc_kvb * 1e5)

def _execute_psbt_send(datadir, network, wallet_name, address, amount, inputs=None, fee_rate=None):
    """Create, sign, finalize and broadcast a funded PSBT."""
    inputs_json = json.dumps(inputs or [])
    outputs_json = json.dumps({address: float(amount)})
    options = {}
    if fee_rate is not None:
        options["fee_rate"] = int(fee_rate)
    if inputs:
        options["add_inputs"] = False
    options_json = json.dumps(options)

    ok, out = run_bitcoin_cli(
        ["walletcreatefundedpsbt", inputs_json, outputs_json, "0", options_json],
        datadir, network, wallet_name, timeout=60.0,
    )
    if not ok:
        return False, out

    try:
        created = json.loads(out)
        psbt = created.get("psbt", "")
        fee = created.get("fee")
    except json.JSONDecodeError:
        return False, f"Unexpected walletcreatefundedpsbt response: {out}"

    if not psbt:
        return False, "walletcreatefundedpsbt did not return a PSBT"

    ok, out = run_bitcoin_cli(
        ["walletprocesspsbt", psbt], datadir, network, wallet_name, timeout=60.0,
    )
    if not ok:
        return False, out

    try:
        processed = json.loads(out)
        psbt = processed.get("psbt", psbt)
    except json.JSONDecodeError:
        return False, f"Unexpected walletprocesspsbt response: {out}"

    ok, out = run_bitcoin_cli(
        ["finalizepsbt", psbt], datadir, network, wallet_name, timeout=30.0,
    )
    if not ok:
        return False, out

    try:
        finalized = json.loads(out)
        hex_tx = finalized.get("hex", "")
        complete = finalized.get("complete", False)
    except json.JSONDecodeError:
        return False, f"Unexpected finalizepsbt response: {out}"

    if not complete or not hex_tx:
        return False, "PSBT is not fully signed"

    ok, txid = run_bitcoin_cli(
        ["sendrawtransaction", hex_tx], datadir, network, timeout=30.0,
    )
    if not ok:
        return False, txid

    return True, {"txid": txid, "fee": fee, "hex": hex_tx}

# ----------------------------------------------------
# Wallet Management API Endpoints
# ----------------------------------------------------
@route('/api/wallet/status')
def api_wallet_status():
    running, datadir, network = get_node_context()
    on_disk = list_wallets_on_disk(datadir, network)
    if not running:
        return {"loaded": False, "wallets": [], "on_disk": on_disk}

    success, output = run_bitcoin_cli(["listwallets"], datadir, network)
    if success:
        try:
            wallets = json.loads(output)
            return {
                "loaded": len(wallets) > 0,
                "wallets": wallets,
                "on_disk": on_disk,
            }
        except Exception as e:
            return {"loaded": False, "wallets": [], "on_disk": on_disk, "error": str(e)}
    return {"loaded": False, "wallets": [], "on_disk": on_disk, "error": output}

@route('/api/wallet/create', method='POST')
def api_wallet_create():
    data = request.json or {}
    name = data.get("name", "sovereign_wallet")
    
    running, pid = check_node_running()
    if not running:
        return {"success": False, "error": "Node is offline"}
        
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    
    success, output = run_bitcoin_cli(["createwallet", name], datadir, network)
    if success:
        return {"success": True, "output": output}
    else:
        return {"success": False, "error": output}

@route('/api/wallet/load', method='POST')
def api_wallet_load():
    data = request.json or {}
    name = data.get("name", "sovereign_wallet")
    
    running, pid = check_node_running()
    if not running:
        return {"success": False, "error": "Node is offline"}
        
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    
    success, output = run_bitcoin_cli(["loadwallet", name], datadir, network)
    if success:
        return {"success": True, "output": output}
    else:
        return {"success": False, "error": output}

@route('/api/wallet/info')
def api_wallet_info():
    name = request.query.get("name")
    if not name:
        return {"success": False, "error": "Wallet name parameter is required"}
        
    running, pid = check_node_running()
    if not running:
        return {"success": False, "error": "Node is offline"}
        
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    
    success, output = run_bitcoin_cli(["getwalletinfo"], datadir, network, wallet_name=name)
    return {"success": success, "output": output}

@route('/api/wallet/transactions')
def api_wallet_transactions():
    name = request.query.get("name")
    if not name:
        return {"success": False, "error": "Wallet name parameter is required"}
        
    running, pid = check_node_running()
    if not running:
        return {"success": False, "error": "Node is offline"}
        
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    
    success, output = run_bitcoin_cli(["listtransactions", "*", "50"], datadir, network, wallet_name=name)
    return {"success": success, "output": output}

@route('/api/wallet/address', method='POST')
def api_wallet_address():
    data = request.json or {}
    name = data.get("name")
    addr_type = data.get("type", "bech32m")
    
    if not name:
        return {"success": False, "error": "Wallet name is required"}
        
    running, pid = check_node_running()
    if not running:
        return {"success": False, "error": "Node is offline"}
        
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    
    success, output = run_bitcoin_cli(["getnewaddress", "", addr_type], datadir, network, wallet_name=name)
    if success:
        return {"success": True, "address": output}
    else:
        return {"success": False, "error": output}

@route('/api/wallet/send', method='POST')
def api_wallet_send():
    data = request.json or {}
    name = data.get("name")
    address = data.get("address", "").strip()
    amount = data.get("amount")
    fee_rate = data.get("fee_rate")

    if not name or not address or amount is None:
        return {"success": False, "error": "Wallet name, address, and amount are required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    if fee_rate is not None:
        outputs_json = json.dumps({address: float(amount)})
        options_json = json.dumps({"fee_rate": int(fee_rate)})
        success, output = run_bitcoin_cli(
            ["send", outputs_json, options_json],
            datadir, network, wallet_name=name, timeout=60.0,
        )
        if success:
            return {"success": True, "txid": output.strip('"')}
        return {"success": False, "error": output}

    success, output = run_bitcoin_cli(
        ["sendtoaddress", address, str(amount)],
        datadir, network, wallet_name=name, timeout=60.0,
    )
    if success:
        return {"success": True, "txid": output}
    return {"success": False, "error": output}

@route('/api/wallet/send-advanced', method='POST')
def api_wallet_send_advanced():
    data = request.json or {}
    name = data.get("name")
    address = data.get("address", "").strip()
    amount = data.get("amount")
    fee_rate = data.get("fee_rate")
    inputs = data.get("inputs", [])

    if not name or not address or amount is None:
        return {"success": False, "error": "Wallet name, address, and amount are required"}
    if not inputs:
        return {"success": False, "error": "Select at least one UTXO for coin control"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    for inp in inputs:
        if not inp.get("txid") or inp.get("vout") is None:
            return {"success": False, "error": "Each input must have txid and vout"}

    success, result = _execute_psbt_send(
        datadir, network, name, address, amount, inputs=inputs, fee_rate=fee_rate,
    )
    if success:
        return {"success": True, **result}
    return {"success": False, "error": result}

@route('/api/wallet/utxos')
def api_wallet_utxos():
    name = request.query.get("name")
    if not name:
        return {"success": False, "error": "Wallet name parameter is required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["listunspent", "0", "9999999"], datadir, network, wallet_name=name, timeout=30.0,
    )
    if not success:
        return {"success": False, "error": output}

    locked_set = set()
    ok_lock, lock_out = run_bitcoin_cli(
        ["listlockunspent"], datadir, network, wallet_name=name, timeout=10.0,
    )
    if ok_lock:
        try:
            for item in json.loads(lock_out):
                locked_set.add((item["txid"], item["vout"]))
        except json.JSONDecodeError:
            pass

    try:
        utxos = json.loads(output)
        for utxo in utxos:
            utxo["locked"] = (utxo["txid"], utxo["vout"]) in locked_set
        return {"success": True, "utxos": utxos}
    except json.JSONDecodeError as e:
        return {"success": False, "error": str(e)}

@route('/api/wallet/lock-utxo', method='POST')
def api_wallet_lock_utxo():
    data = request.json or {}
    name = data.get("name")
    unlock = bool(data.get("unlock", False))
    inputs = data.get("inputs", [])

    if not name:
        return {"success": False, "error": "Wallet name is required"}
    if not inputs:
        return {"success": False, "error": "At least one UTXO input is required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    inputs_json = json.dumps(inputs)
    flag = "true" if unlock else "false"
    success, output = run_bitcoin_cli(
        ["lockunspent", flag, inputs_json],
        datadir, network, wallet_name=name, timeout=15.0,
    )
    if success:
        return {"success": True, "unlocked" if unlock else "locked": True}
    return {"success": False, "error": output}

@route('/api/wallet/fee-estimate')
def api_wallet_fee_estimate():
    blocks = request.query.get("blocks", "6")
    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["estimatesmartfee", str(blocks)], datadir, network, timeout=10.0,
    )
    if not success:
        return {"success": False, "error": output}

    try:
        estimate = json.loads(output)
        feerate = estimate.get("feerate")
        sat_vb = _btc_kvb_to_sat_vb(feerate) if feerate is not None else None
        return {
            "success": True,
            "feerate_btc_kvb": feerate,
            "sat_vb": sat_vb,
            "blocks": estimate.get("blocks"),
            "errors": estimate.get("errors", []),
        }
    except json.JSONDecodeError:
        return {"success": False, "error": output}

@route('/api/wallet/unload', method='POST')
def api_wallet_unload():
    data = request.json or {}
    name = data.get("name")
    if not name:
        return {"success": False, "error": "Wallet name is required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(["unloadwallet", name], datadir, network)
    if success:
        return {"success": True, "output": output}
    return {"success": False, "error": output}

@route('/api/wallet/addresses')
def api_wallet_addresses():
    name = request.query.get("name")
    if not name:
        return {"success": False, "error": "Wallet name parameter is required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["listreceivedbyaddress", "0", "true", "true"],
        datadir, network, wallet_name=name,
    )
    return {"success": success, "output": output}

@route('/api/wallet/label', method='POST')
def api_wallet_label():
    data = request.json or {}
    name = data.get("name")
    address = data.get("address", "").strip()
    label = data.get("label", "").strip()
    if not name or not address:
        return {"success": False, "error": "Wallet name and address are required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["setlabel", address, label], datadir, network, wallet_name=name,
    )
    if success:
        return {"success": True}
    return {"success": False, "error": output}

@route('/api/wallet/sign-message', method='POST')
def api_wallet_sign_message():
    data = request.json or {}
    name = data.get("name")
    address = data.get("address", "").strip()
    message = data.get("message", "")
    if not name or not address or not message:
        return {"success": False, "error": "Wallet name, address, and message are required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["signmessage", address, message], datadir, network, wallet_name=name,
    )
    if success:
        return {"success": True, "signature": output}
    return {"success": False, "error": output}

@route('/api/wallet/verify-message', method='POST')
def api_wallet_verify_message():
    data = request.json or {}
    address = data.get("address", "").strip()
    signature = data.get("signature", "").strip()
    message = data.get("message", "")
    if not address or not signature or not message:
        return {"success": False, "error": "Address, signature, and message are required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(["verifymessage", address, signature, message], datadir, network)
    if success:
        valid = output.lower() == "true"
        return {"success": True, "valid": valid, "output": output}
    return {"success": False, "error": output}

@route('/api/wallet/psbt/decode', method='POST')
def api_wallet_psbt_decode():
    data = request.json or {}
    name = data.get("name")
    psbt = data.get("psbt", "").strip()
    if not name or not psbt:
        return {"success": False, "error": "Wallet name and PSBT data are required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["decodepsbt", psbt], datadir, network, wallet_name=name,
    )
    if success:
        return {"success": True, "output": output}
    return {"success": False, "error": output}

@route('/api/wallet/psbt/sign', method='POST')
def api_wallet_psbt_sign():
    data = request.json or {}
    name = data.get("name")
    psbt = data.get("psbt", "").strip()
    if not name or not psbt:
        return {"success": False, "error": "Wallet name and PSBT data are required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["walletprocesspsbt", psbt], datadir, network, wallet_name=name,
    )
    if success:
        try:
            result = json.loads(output)
            return {
                "success": True,
                "psbt": result.get("psbt", ""),
                "complete": result.get("complete", False),
                "output": output,
            }
        except json.JSONDecodeError:
            return {"success": True, "output": output}
    return {"success": False, "error": output}

@route('/api/wallet/psbt/finalize', method='POST')
def api_wallet_psbt_finalize():
    data = request.json or {}
    name = data.get("name")
    psbt = data.get("psbt", "").strip()
    broadcast = data.get("broadcast", True)
    if not name or not psbt:
        return {"success": False, "error": "Wallet name and PSBT data are required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["finalizepsbt", psbt], datadir, network, wallet_name=name,
    )
    if not success:
        return {"success": False, "error": output}

    try:
        result = json.loads(output)
        hex_tx = result.get("hex", "")
        complete = result.get("complete", False)
    except json.JSONDecodeError:
        return {"success": False, "error": f"Unexpected finalizepsbt response: {output}"}

    if not complete or not hex_tx:
        return {"success": False, "error": "PSBT is not fully signed yet", "complete": complete}

    if not broadcast:
        return {"success": True, "hex": hex_tx, "complete": True, "broadcast": False}

    ok, tx_output = run_bitcoin_cli(["sendrawtransaction", hex_tx], datadir, network)
    if ok:
        return {"success": True, "txid": tx_output, "hex": hex_tx, "complete": True, "broadcast": True}
    return {"success": False, "error": tx_output, "hex": hex_tx, "complete": True}

# ----------------------------------------------------
# Wallet Security & Import/Export
# ----------------------------------------------------
def _wallet_backups_dir(datadir, network):
    net_dir = get_network_dir(datadir, network)
    path = os.path.join(net_dir, "backups")
    os.makedirs(path, exist_ok=True)
    return path

@route('/api/wallet/backup-path')
def api_wallet_backup_path():
    running, datadir, network = get_node_context()
    backups = _wallet_backups_dir(datadir, network) if running else os.path.expanduser("~/.bitcoin/backups")
    return {"success": True, "path": backups}

@route('/api/wallet/encrypt', method='POST')
def api_wallet_encrypt():
    data = request.json or {}
    name = data.get("name")
    passphrase = data.get("passphrase", "")
    if not name or not passphrase:
        return {"success": False, "error": "Wallet name and passphrase are required"}
    if len(passphrase) < 8:
        return {"success": False, "error": "Passphrase must be at least 8 characters"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["encryptwallet", passphrase], datadir, network, wallet_name=name, timeout=120.0,
    )
    if success:
        return {"success": True, "output": output}
    return {"success": False, "error": output}

@route('/api/wallet/unlock', method='POST')
def api_wallet_unlock():
    data = request.json or {}
    name = data.get("name")
    passphrase = data.get("passphrase", "")
    timeout_secs = int(data.get("timeout", 600))
    if not name or not passphrase:
        return {"success": False, "error": "Wallet name and passphrase are required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["walletpassphrase", passphrase, str(timeout_secs)],
        datadir, network, wallet_name=name, timeout=30.0,
    )
    if success:
        return {"success": True}
    return {"success": False, "error": output}

@route('/api/wallet/lock', method='POST')
def api_wallet_lock():
    data = request.json or {}
    name = data.get("name")
    if not name:
        return {"success": False, "error": "Wallet name is required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["walletlock"], datadir, network, wallet_name=name, timeout=15.0,
    )
    if success:
        return {"success": True}
    return {"success": False, "error": output}

@route('/api/wallet/change-passphrase', method='POST')
def api_wallet_change_passphrase():
    data = request.json or {}
    name = data.get("name")
    old_pass = data.get("old_passphrase", "")
    new_pass = data.get("new_passphrase", "")
    if not name or not old_pass or not new_pass:
        return {"success": False, "error": "Wallet name, old and new passphrases are required"}
    if len(new_pass) < 8:
        return {"success": False, "error": "New passphrase must be at least 8 characters"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["walletpassphrasechange", old_pass, new_pass],
        datadir, network, wallet_name=name, timeout=120.0,
    )
    if success:
        return {"success": True}
    return {"success": False, "error": output}

@route('/api/wallet/backup', method='POST')
def api_wallet_backup():
    data = request.json or {}
    name = data.get("name")
    if not name:
        return {"success": False, "error": "Wallet name is required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    backups_dir = _wallet_backups_dir(datadir, network)
    filename = data.get("filename", "").strip()
    if not filename:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{stamp}.dat"
    if not filename.endswith(".dat"):
        filename += ".dat"
    dest = os.path.join(backups_dir, os.path.basename(filename))

    success, output = run_bitcoin_cli(
        ["backupwallet", dest], datadir, network, wallet_name=name, timeout=120.0,
    )
    if success:
        return {"success": True, "path": dest}
    return {"success": False, "error": output}

@route('/api/wallet/dump', method='POST')
def api_wallet_dump():
    data = request.json or {}
    name = data.get("name")
    if not name:
        return {"success": False, "error": "Wallet name is required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    backups_dir = _wallet_backups_dir(datadir, network)
    filename = data.get("filename", "").strip()
    if not filename:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_dump_{stamp}.txt"
    dest = os.path.join(backups_dir, os.path.basename(filename))

    success, output = run_bitcoin_cli(
        ["dumpwallet", dest], datadir, network, wallet_name=name, timeout=120.0,
    )
    if success:
        return {"success": True, "path": dest}
    return {"success": False, "error": output}

@route('/api/wallet/import-wallet', method='POST')
def api_wallet_import_wallet():
    data = request.json or {}
    filepath = data.get("filepath", "").strip()
    if not filepath:
        return {"success": False, "error": "Wallet dump file path is required"}
    if not os.path.isfile(filepath):
        return {"success": False, "error": f"File not found: {filepath}"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    success, output = run_bitcoin_cli(
        ["importwallet", filepath], datadir, network, timeout=300.0,
    )
    if success:
        return {"success": True, "output": output}
    return {"success": False, "error": output}

@route('/api/wallet/create-watchonly', method='POST')
def api_wallet_create_watchonly():
    data = request.json or {}
    name = data.get("name", "").strip()
    if not name:
        return {"success": False, "error": "Wallet name is required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    options = json.dumps({"disable_private_keys": True, "blank": True})
    success, output = run_bitcoin_cli(
        ["createwallet", name, "false", "true", options],
        datadir, network, timeout=30.0,
    )
    if success:
        return {"success": True, "output": output}
    return {"success": False, "error": output}

@route('/api/wallet/import-descriptors', method='POST')
def api_wallet_import_descriptors():
    data = request.json or {}
    name = data.get("name")
    descriptor = data.get("descriptor", "").strip()
    if not name or not descriptor:
        return {"success": False, "error": "Wallet name and descriptor are required"}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    req = json.dumps([{
        "desc": descriptor,
        "timestamp": "now",
        "active": True,
        "internal": False,
    }])
    success, output = run_bitcoin_cli(
        ["importdescriptors", req], datadir, network, wallet_name=name, timeout=120.0,
    )
    if success:
        try:
            result = json.loads(output)
            return {"success": True, "output": output, "result": result}
        except json.JSONDecodeError:
            return {"success": True, "output": output}
    return {"success": False, "error": output}

# ----------------------------------------------------
# Oracle CLI Terminal
# ----------------------------------------------------
BLOCKED_CLI_COMMANDS = frozenset({
    "stop", "shutdown", "invalidateblock", "reconsiderblock",
    "submitblock", "submitheader", "addnode", "disconnectnode",
    "setban", "clearbanned",
})

@route('/api/cli', method='POST')
def api_cli():
    data = request.json or {}
    command = data.get("command", "").strip()
    wallet_name = data.get("wallet_name") or None
    if wallet_name == "":
        wallet_name = None

    if not command:
        return {"success": False, "error": "Command is required"}

    try:
        parts = shlex.split(command)
    except ValueError as e:
        return {"success": False, "error": f"Invalid command syntax: {e}"}

    if not parts:
        return {"success": False, "error": "Empty command"}

    method = parts[0].lower()
    if method in BLOCKED_CLI_COMMANDS:
        return {"success": False, "error": f"Command '{method}' is blocked. Use the dashboard for node control."}

    running, datadir, network = get_node_context()
    if not running:
        return {"success": False, "error": "Node is offline"}

    timeout = 120.0
    if method in ("importwallet", "rescanblockchain", "createwallet"):
        timeout = 300.0

    success, output = run_bitcoin_cli(
        parts, datadir, network, wallet_name=wallet_name, timeout=timeout,
    )
    return {"success": success, "output": output, "command": command}

# ----------------------------------------------------
# Log and General Endpoints
# ----------------------------------------------------
@route('/api/logs')
def api_get_logs():
    running, pid = check_node_running()
    datadir = get_node_datadir(pid) if running else os.path.expanduser("~/.bitcoin")
    network = get_node_network(pid) if running else "mainnet"
    log_filter = request.query.get("filter", "all")

    _, policy_toml_path = get_config_paths(datadir, network)
    net_dir = os.path.dirname(policy_toml_path)
    log_path = os.path.join(net_dir, "debug.log")

    if not os.path.exists(log_path):
        return {"success": False, "error": f"debug.log not found at {log_path}"}

    try:
        num_lines = 400 if log_filter == "policy" else 200
        lines = []
        with open(log_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()

            block_size = 8192 if log_filter == "policy" else 4096
            data = b""
            offset = file_size

            while len(lines) <= num_lines and offset > 0:
                read_size = min(block_size, offset)
                offset -= read_size
                f.seek(offset)
                block_data = f.read(read_size)
                data = block_data + data
                lines = data.split(b"\n")

        last_lines = [line.decode("utf-8", errors="replace") for line in lines[-num_lines:]]
        if log_filter == "policy":
            keywords = ("Oracle Policy", "Oracle Sovereign Mining", "Sovereign Mining")
            last_lines = [ln for ln in last_lines if any(k in ln for k in keywords)]

        if log_filter == "policy" and running:
            recent = _rpc_json("getrecentpolicyrejections", datadir, network, ["30"]) or []
            if recent:
                rpc_lines = [
                    f"[rpc] {e.get('context','?')}: {e.get('message','')} (wtxid={e.get('wtxid','')})"
                    for e in recent
                ]
                last_lines = rpc_lines + last_lines

        return {"success": True, "logs": "\n".join(last_lines[-200:]), "filter": log_filter}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ----------------------------------------------------
# Bitcoin Price & Portfolio Routes (Phase 4.1 + 4.2)
# ----------------------------------------------------
from bottle import default_app as _bottle_default_app
setup_price_routes(_bottle_default_app())
_portfolio_manager = PortfolioManager(run_bitcoin_cli, get_node_context)
setup_portfolio_routes(_bottle_default_app(), _portfolio_manager)

# ----------------------------------------------------
# Main Program Launch & Threading
# ----------------------------------------------------
def start_bottle_server(port):
    run(host='127.0.0.1', port=port, quiet=True, server='wsgiref')

def main():
    dashboard_port = find_available_port(8080)
    
    # Start Bottle server in background thread
    server_thread = threading.Thread(target=start_bottle_server, args=(dashboard_port,), daemon=True)
    server_thread.start()

    # Start portfolio daily snapshot scheduler
    snapshot_thread = threading.Thread(target=_portfolio_manager.start_daily_scheduler, daemon=True)
    snapshot_thread.start()

    time.sleep(0.5)
    
    try:
        import webview
    except ImportError:
        print("Error: pywebview library is missing in virtual environment.")
        sys.exit(1)

    try:
        print(f"Opening Oracle Knots Control Center on port {dashboard_port}...")
        window = webview.create_window(
            title="Oracle Knots — The Oracle Watches",
            url=f"http://127.0.0.1:{dashboard_port}",
            width=1250,
            height=850,
            background_color="#05070e",
            min_size=(1000, 700)
        )
        webview.start()
        
    except Exception as e:
        print(f"Failed to start desktop window: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
