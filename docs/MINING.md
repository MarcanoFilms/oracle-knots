# Sovereign mining with DATUM (CONVOY)

Oracle Knots bundles the **DATUM Gateway (CONVOY)** so you can mine your *own*
block templates to a DATUM pool without compiling a separate program. With DATUM,
**you are the miner** — the pool coordinates the reward split but never builds
your template. It is vendored at `mining/datum-convoy` and built by `build.sh`.

The Control Center's **Sovereign Mining** tab manages it end-to-end: status,
in-app configuration, and start/stop.

## How it fits together

```
mining hardware ──Stratum v1──▶ DATUM Gateway ──RPC (getblocktemplate)──▶ your node
                                      │
                                      └──DATUM protocol──▶ pool (PyBLØCK / CONVOY)
```

The gateway serves BLAKE2b (and BLAKE2b-Sia) work to your miners, fetches
templates from your node, and submits solved blocks directly to the network.

## Configure it in the GUI (no manual editing)

1. **Sovereign Mining** tab → **Auto-setup from node**. This copies
   `contrib/datum/oracle-datum.example.json` to
   `~/.oracle-knots-gui/oracle-datum.conf.json` and injects your node's
   `rpcuser`/`rpcpassword` automatically.
2. Fill in the fields and **Save Config**:
   - **Payout address** — your BLAKE2b (XBT) address.
   - **Stratum port** — where your miners connect (default `9735`).
   - **Pool host / port / pubkey** — pre-wired to PyBLØCK WAVICLES.
   - **Dashboard admin password** — for the gateway's own web UI.
3. **Start Mining**. The tab shows pool status, hashrate, shares, connected
   miners, and the current job (block height + value in XBT).

Secrets (`rpcpassword`, `admin_password`) are never sent to the browser; blank
fields keep their saved value.

## Node requirements

- Reserve block space for the pool's generation transaction.
- `blocknotify` to the gateway (the recommended `bitcoin.conf` sets this).
- Keep `consensusrules=rdts` and a correct `blake2b_headline` (see
  [BLAKE2B.md](BLAKE2B.md)).

## Safety

- The Control Center only **stops** a gateway **it started itself** (tracked by
  pidfile). A gateway launched outside Oracle Knots (e.g. a systemd/production
  miner) is shown as *externally managed* and is never touched.
- It will not start a second gateway if one is already running (avoids Stratum/API
  port collisions).

## Never commit secrets

Your real config (`oracle-datum.conf.json`) holds `rpcpassword`, `admin_password`,
and your payout address. It is gitignored. Only the sanitized
`contrib/datum/oracle-datum.example.json` is tracked.
