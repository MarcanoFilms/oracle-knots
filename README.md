# Oracle Knots — the sovereign BLAKE2b stack

<img width="420" height="142" alt="Oracle Knots" src="https://github.com/user-attachments/assets/d227f2b0-7f68-4629-a2a9-cae9ea38604e" />

Oracle Knots is an **all-in-one node, wallet, and mining stack for the BLAKE2b
proof-of-work fork of Bitcoin** (community ticker **XBT**, listed as **BTCB2** on
Neoxa). Install one thing and get a fully verifying node, a wallet that can spend
on the fork, and sovereign solo/pool mining — managed from a single Control
Center. No compiling five separate programs.

Philosophy: **"Don't Trust, Verify"**, sound money first, and keeping node
verification lightweight by aggressively filtering non-financial data spam.

> Follows the BLAKE2b chain: PoW is BLAKE2b, block headers are v2, mainnet
> activation is at height **961640**. See **[docs/BLAKE2B.md](docs/BLAKE2B.md)**.

---

## Why you need *this* stack

Standard wallets (Electrum, online Sparrow, BlueWallet) **cannot connect to the
BLAKE2b chain** — they validate 80-byte SHA-256d headers client-side and reject
the fork's v2 headers. So the only way to see and spend XBT is software that
understands the fork: **your Oracle Knots node + Oracle Wallet**.

| You want to… | Use |
|---|---|
| Verify the BLAKE2b chain | Oracle Knots **node** |
| See balance / spend / sign XBT | **Oracle Wallet** (Shrike + BLAKE2b) → [docs/WALLET.md](docs/WALLET.md) |
| Mine your own templates | **DATUM Gateway (CONVOY)**, bundled → [docs/MINING.md](docs/MINING.md) |
| Watch it all | **Control Center** GUI |

---

## The all-in-one Control Center

A mobile-first desktop dashboard (`pywebview` + Bottle) branded with the Oracle
Owl:

- **Dashboard** — sync, block template stats, fork consensus (BLAKE2b/RDTS),
  mempool, recent blocks, **live XBT price from Neoxa** (with a high-risk
  disclaimer), and policy-rejection summary.
- **Wallet** — the built-in wallet plus an **Oracle Wallet** card that
  configures Shrike's connection to your node in one click and launches it.
  Balances are valued in **XBT** (not BTC).
- **Sovereign Mining** — start/stop and **fully configure the DATUM Gateway
  in-app** (auto-injects node RPC), with live hashrate, shares, and pool status.
- **Mempool Explorer** — fee-rate distribution and top transactions (standard
  RPC, pruned-safe).
- **Policy Engine**, **Fork Status**, **Config editor**, **Oracle CLI**,
  **Console Logs**.

Launch everything:

```bash
./oracle-knots            # ensure the node is up + open the Control Center
./oracle-knots --with-datum --wallet   # also start mining + open Oracle Wallet
./oracle-knots status     # component status, starts nothing
```

---

## Node features vs. Bitcoin Knots

1. **BLAKE2b proof-of-work fork** — header v2, `DEPLOYMENT_BLAKE2B` (mainnet
   961640), consensus-critical `blake2b_headline`, opt-in unified sighash.
2. **Full BIP-110 / RDTS support** — `-bip110=auto|always|never` to configure
   the reduced-data soft-fork enforcement.
3. **Declarative Policy Engine** — runtime `policy.toml` with profiles
   (`maximalist`, `bip110-strict`, `monetary-only`, `default-knots`).
4. **Sovereign mining template filtering** — the block assembler drops mempool
   txs that violate *your* policy.
5. **Native Prometheus exporter** (`-prometheusport`, default 9332).
6. **Resource-aware defaults** and a **branded `OracleKnots` P2P user agent**.

See **[OPERATOR_TOOLS.md](OPERATOR_TOOLS.md)** for the operator RPCs.

---

## Build & run

Full instructions (deps, submodule, verification): **[docs/BUILD.md](docs/BUILD.md)**.

```bash
git clone https://github.com/MarcanoFilms/oracle-knots.git
cd oracle-knots
git submodule update --init --recursive   # DATUM Gateway (CONVOY)
./build.sh                                 # node + DATUM
./setup-gui.sh                             # one-time GUI venv
./oracle-knots                             # launch the stack
```

**GUI deps** (Arch): `python`, `qt6-webengine`. Python packages in
`requirements.txt`. `server=1` in `bitcoin.conf` is required for wallet/CLI.

---

## Recommended `bitcoin.conf`

```ini
# BLAKE2b consensus
consensusrules=rdts
blake2b_headline=<exact canonical headline>

# Sovereign / resource-aware
policyprofile=maximalist
bip110=auto
maxmempool=100
prometheus=1
prometheusport=9332

# Privacy
proxy=127.0.0.1:9050
onion=127.0.0.1:9050
listenonion=1
```

---

## Repository layout

```
gui.py, gui/            Control Center (backend + frontend)
oracle-knots            all-in-one launcher
build.sh                builds node + DATUM
src/                    Oracle Knots node (Knots + BLAKE2b + policy engine)
mining/datum-convoy/    DATUM Gateway (CONVOY) submodule
contrib/datum/          sanitized DATUM example config
contrib/wallet/         Oracle Wallet launcher + desktop entry
docs/                   BLAKE2B, WALLET, MINING, BUILD
```

---

## Security

- No credentials are committed. Real DATUM/wallet configs are gitignored; only
  sanitized examples are tracked.
- The Control Center never sends `rpcpassword`/`admin_password` to the browser.

## License

MIT. See [COPYING](COPYING).
