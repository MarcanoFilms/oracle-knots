# Oracle Knots — Operator Tools (Phase 2)

Tools for sovereign node operators: clear rejection logging, sovereign mining visibility,
BIP-110 deployment status, mempool policy audit, and preflight diagnostics.

## Implementation order

1. **Rejection logging (C++)** — Human-readable `Oracle Policy:` lines in `debug.log` with wtxid and context (`relay`, `template`).
2. **Sovereign template stats (C++)** — `BlockAssembler` tracks policy-filtered txs; Prometheus + RPC expose them.
3. **Operator RPCs** — `getsovereigntemplatestats`, `getsovereigndiagnostics`, `getmempoolpolicyaudit`, `getrecentpolicyrejections`.
4. **GUI** — Dashboard mining panel, BIP-110 progress bar, mempool policy modal, preflight strip, filtered logs.
5. **Prometheus** — Template and BIP-110 gauges; fixed HELP/TYPE headers.

All mempool/template features work in **pruned mode** (no `txindex` required).

## RPC reference

### `getsovereigntemplatestats`

Last assembled block template: txs included, policy-filtered count, mempool size at build time, fees, weight, assembly time, active profile.

### `getsovereigndiagnostics`

Configuration and runtime checks with `severity` (`info`, `warning`, `critical`) and `recommendation` text.

### `getmempoolpolicyaudit [limit]`

Scans in-memory mempool (default 500 txs max): `would_pass`, `would_fail`, `pass_rate_pct`, `failures_by_reason`, sample failures.

### `getrecentpolicyrejections [limit]`

Recent policy rejections from the in-memory ring buffer (for dashboard / logs).

## Sovereign mining

When building a block template (`getblocktemplate` / internal miner), `BlockAssembler` re-applies your active `policy.toml` rules. Transactions that passed the network mempool but violate **your** policy are skipped — logged as:

```
Oracle Policy [template]: Rejected — Ordinals inscription detected (wtxid=...)
Oracle Sovereign Mining: template assembled — N txs included, M policy-filtered, ...
```

Use **Dashboard → Sovereign Mining** or `bitcoin-cli getsovereigntemplatestats` to monitor filtering.

## Log messages

| Context | Example |
|---------|---------|
| `relay` | Mempool / P2P rejection |
| `template` | Skipped during block template assembly |

Reason codes map to operator text (e.g. `inscription` → "Ordinals inscription detected").

## User Agent Comment (`uacomment`)

Append a custom tag to your node's P2P user agent (equivalent to `-uacomment=` in `bitcoin.conf`). This does **not** change the full user agent string — only adds a comment per BIP-14.

- **GUI**: Configuration → P2P Network → Node Identity
- **Config file**: `uacomment=sovereign-miner` in `bitcoin.conf`
- **Requires node restart** to take effect
- **Unsafe characters** (rejected): `/`, `:`, `(`, `)`, non-ASCII. Max 64 characters in the GUI.

## GUI

- **Dashboard**: Collapsible sidebar (icons only by default), prominent block height, Sovereign Mining card, RDTS progress bar
- **Oracle CLI**: Command reference panel with descriptions (click to insert)
- **Mempool Policy** button: modal with audit breakdown
- **Preflight** banner: Tor, policy conflicts, sync, prune notes
- **Logs tab**: "Policy only" filter for `Oracle Policy` lines