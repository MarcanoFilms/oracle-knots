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
from bottle import route, run, static_file, request, response

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

# ----------------------------------------------------
# Configuration Parsing / Updating Utilities
# ----------------------------------------------------
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

@route('/api/rpc/<method>')
def api_rpc(method):
    running, pid = check_node_running()
    if not running:
        return {"success": False, "output": "Node is offline"}
        
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    
    safe_methods = ["getblockchaininfo", "getpeerinfo", "checkbip110status", "getnetworkinfo", "getmempoolinfo"]
    if method not in safe_methods:
        return {"success": False, "output": f"RPC method {method} not allowed"}
        
    success, output = run_bitcoin_cli([method], datadir, network)
    return {"success": success, "output": output}

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
    
    success, output = run_bitcoin_cli(["setsovereignpolicy", profile], datadir, network)
    return {"success": success, "output": output}

@route('/api/rpc/reload-policy', method='POST')
def api_rpc_reload_policy():
    running, pid = check_node_running()
    if not running:
        return {"success": False, "output": "Node is offline"}
        
    prom_port = get_prometheus_port(pid)
    metrics = fetch_prometheus_metrics(prom_port)
    profile = metrics.get("policy_profile", "maximalist") if metrics else "maximalist"
    
    datadir = get_node_datadir(pid)
    network = get_node_network(pid)
    
    success, output = run_bitcoin_cli(["setsovereignpolicy", profile], datadir, network)
    return {"success": success, "output": output}

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
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True}
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
        "blocksonly", "proxy", "onion", "listenonion", "discover",
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
        "chain", "rest", "rpcworkqueue"
    ]




    
    bitcoin_settings = {}
    policy_settings = {}
    
    for k, val in data.items():
        if k in bitcoin_keys:
            bitcoin_settings[k] = val
        elif k.startswith("custom_rules.") or k in ["profile", "bip110_mode"]:
            policy_settings[k] = val
            
    try:
        update_bitcoin_conf(bitcoin_conf_path, bitcoin_settings)
        update_policy_toml(policy_toml_path, policy_settings)
        return {"success": True}
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
    
    _, policy_toml_path = get_config_paths(datadir, network)
    net_dir = os.path.dirname(policy_toml_path)
    log_path = os.path.join(net_dir, "debug.log")
    
    if not os.path.exists(log_path):
        return {"success": False, "error": f"debug.log not found at {log_path}"}
        
    try:
        num_lines = 200
        lines = []
        with open(log_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            
            block_size = 4096
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
        return {"success": True, "logs": "\n".join(last_lines)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ----------------------------------------------------
# Main Program Launch & Threading
# ----------------------------------------------------
def start_bottle_server(port):
    run(host='127.0.0.1', port=port, quiet=True)

def main():
    dashboard_port = find_available_port(8080)
    
    # Start Bottle server in background thread
    server_thread = threading.Thread(target=start_bottle_server, args=(dashboard_port,), daemon=True)
    server_thread.start()
    
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
