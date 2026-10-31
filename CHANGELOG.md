# Changelog

## v2.1.0 — Knots 29.4.3, data-carrier filter, UA privacy

Upstream refresh plus operator protections. Consensus for the BLAKE2b chain is
unchanged throughout: the upstream merges bring Knots' own policy and maturity
work, and everything else is policy, privacy, mining and GUI product.

### Upstream
- Rebased onto **Bitcoin Knots v29.4.2 final** and then **v29.4.3** (merges of
  tags `v29.4.2.knots20260508` and `v29.4.3.knots20260508`), which ship the
  rolling 180-day coinbase maturity (Knots #468) and the 29.4.x maintenance
  fixes.

### Privacy
- **New `-uaprivacy` option, on by default.** Peers on public networks
  (IPv4/IPv6/CJDNS) are sent a generic upstream user agent
  (`/Satoshi:29.4.3/Knots:20260508/`); the real `/OracleKnots:…/` user agent
  is only sent to peers reached over Tor or I2P. A user-agent scan of clearnet
  listeners can no longer produce a list of Oracle Knots operators — on
  2026-10-30 exactly that kind of scan was used to post a node operator's home
  IP in public. `-uaprivacy=0` restores full advertising, `-uaspoof` still
  overrides everything, and `getnetworkinfo` keeps reporting the real
  subversion locally. Covered by the new `p2p_ua_privacy.py` functional test,
  which Build CI runs.

### Policy
- **Fake 1-of-N bare-multisig data carriers are rejected by standardness.**
  The `bpub`/bitfiles pattern hides arbitrary data in the keys of a 1-of-N
  multisig output; those outputs are now recognized as data carriers and kept
  out of the mempool like any other datacarrier violation.

### Mining
- CONVOY submodule updated to fix BLAKE2b coinbase sizing (DATUM templates no
  longer overrun the coinbase budget).
- The DATUM vardiff floor is configurable from the Control Center's Sovereign
  Mining tab.

### Control Center
- The wallet view auto-refreshes and raises Sparrow-style desktop
  notifications when a new transaction touches the wallet.

### Security hardening

Security fixes across the node and the Control Center. No consensus code is
touched: the node's validation rules are unchanged.

#### Node
- **The Prometheus exporter no longer listens on every interface.** It bound
  `INADDR_ANY` while `-prometheus` defaults to on, so every node published its
  height, peer counts, mempool and uptime to anyone who could reach the host,
  unauthenticated. It now binds loopback, with `-prometheusbind=<addr>` to widen
  it deliberately, and warns in the log when that address is not loopback.
- The exporter serves one client at a time, so it now sets a send/receive timeout
  per connection: a client that connected and stayed quiet used to stall every
  later scrape.

#### Control Center
- **The API requires a per-run token.** Loopback alone was no boundary: any other
  user on the machine could reach wallet send, dump and unlock, plus the
  `bitcoin-cli` passthrough. The token is written to `~/.oracle-knots/gui.token`
  (0600) and injected into the page the launcher opens.
- **Requests must be addressed to a loopback `Host`**, and cross-site `Origin`s are
  refused. This is what stops DNS rebinding, where a website resolves its own
  hostname to `127.0.0.1` and so looks same-origin to the browser.
- **Wallet passphrases are no longer passed as command-line arguments.** Unlock,
  encrypt and change-passphrase now use `bitcoin-cli -stdinwalletpassphrase`/
  `-stdin`, so secrets cannot be read from `ps` or `/proc/<pid>/cmdline`.
  Imported descriptors, which can carry an xprv, go the same way.
- **Price lookups follow the node's proxy.** The Neoxa ticker and the CoinGecko and
  Kraken reference prices went out in the clear, exposing the IP of a node meant to
  be reachable only over Tor. They now use `proxy=`/`onion=` from `bitcoin.conf`
  with DNS resolved by the proxy, and fail closed when that is impossible.
  `ORACLE_PRICE_FETCH=off`/`=direct` are the operator overrides.
- The dashboard no longer fetches webfonts from a CDN, and the BTC reference price
  is fetched by the backend instead of directly by the window.
- `requests` and `PySocks` are now declared in `requirements.txt`. `requests` was
  always imported by `api/bitcoin_price.py`, so without it the price routes were
  silently skipped.

#### Tests and CI
- New `test/gui/` suite (38 tests) covering the API guard, the Host/Origin checks,
  the token file's permissions, secret routing for every affected endpoint, and the
  outbound proxy policy. It needs no node build.
- Build CI now runs those tests in a separate fast job, and runs the fork's own
  functional tests (`p2p_blake2b_*`) after the regtest smoke test.

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
- Deep JavaFX rebrand of Oracle Wallet (title bar still reads "Shrike").
