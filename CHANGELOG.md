# Changelog

## v2.0.0 — All-in-one BLAKE2b stack

The headline release: Oracle Knots moves from a SHA-256d Knots fork to the
**BLAKE2b proof-of-work chain (XBT)** and becomes an all-in-one node + wallet +
mining stack managed from one Control Center.

### Node
- **Unified the BLAKE2b proof-of-work fork** into the Oracle Knots tree (header
  v2, `DEPLOYMENT_BLAKE2B` at mainnet height 961640, consensus-critical
  `blake2b_headline`). BIP-110/RDTS enforcement preserved with the
  `-bip110=auto|always|never` override.
- **Branded P2P user agent**: `UA_NAME = OracleKnots`.

### All-in-one
- **DATUM Gateway (CONVOY)** vendored as a submodule (`mining/datum-convoy`) and
  built by `build.sh`; **Sovereign Mining** tab with in-app configuration
  (auto-injects node RPC), start/stop guarded against externally-managed miners.
- **All-in-one launcher** `./oracle-knots` (idempotent; `status`/`--help`).
- **Oracle Wallet (Shrike)** integration: one-click connection bundle from
  `bitcoin.conf`, launch, and OS-level rebrand (`contrib/wallet`).

### Control Center
- **Live XBT price** from Neoxa (`/api/price`) with a high-risk disclaimer;
  wallet balances now valued in **XBT** (previously mis-valued at the BTC price).
- **Mempool Explorer** rebuilt on standard RPC (fee-rate histogram + top txs).
- **Recent Blocks** now works via a standard-RPC fallback.
- Footer shows the **real node version** (dynamic, not hardcoded).
- UI amounts relabeled **BTC → XBT**.

### Security
- No credentials committed; real DATUM/wallet configs gitignored, sanitized
  examples only. Secrets are never sent to the browser.

### Known follow-ups
- Compile on a machine with Boost (`sudo pacman -S boost`); see docs/BUILD.md.
- Pull `src/common/sighash_rules.cpp` (opt-in unified sighash) from the 29.4.1
  tree for full parity — standard-signature spending works without it.
- Deep JavaFX rebrand of Oracle Wallet (title bar still reads "Shrike").
