# Oracle Knots (SovereignKnots)
============================

Oracle Knots is a professional, high-quality fork of **Bitcoin Knots** designed specifically for sovereign individuals, node operators, and low-resource mining operations (such as BitAxe + Mac Mini or single-board setups). 

Our philosophy centers on **"Don't Trust, Verify"**, reclaiming Bitcoin as **sound money first**, and keeping node verification lightweight by aggressively filtering non-financial data spam (e.g., Runes, BRC-20, Ordinals, and bloated OP_RETURN outputs).

---

## Key Features & Differences vs. Bitcoin Knots

1. **Full BIP-110 Support (Temporary Soft Fork)**
   - Implements strict consensus-level restrictions designed to temporarily cap arbitrary data storage on the blockchain.
   - Restricts `scriptPubKey` sizes to 34 bytes (except `OP_RETURN` which is capped at 83 bytes).
   - Restricts witness pushdata elements to 256 bytes.
   - Restricts Taproot control blocks to 257 bytes.
   - Disallows `OP_SUCCESS` opcodes and Tapscript conditionally.
   - Exposes a new CLI / config option `-bip110=auto|always|never` to configure the activation mode (fully compatible with UASF nodes).

2. **Declarative Policy Engine**
   - Configure mempool and relay policies at runtime without compiling. 
   - Managed via a simple human-readable `policy.toml` configuration file in the node's data directory.
   - Includes predefined profiles for different network alignment strategies:
     - `maximalist`: Zero tolerance for data carrier spam. OP_RETURN is blocked entirely (datacarrier size set to 0), and all inscriptions/token protocols are actively filtered.
     - `bip110-strict`: Enforces standard BIP-110 consensus bounds locally.
     - `monetary-only`: Similar to maximalist, targeting monetary usage exclusively.
     - `default-knots`: Standard Knots policy profile.

3. **Sovereign Mining Template Filtering**
   - The Block Template Assembler (`BlockAssembler`) dynamically inspects transactions and packages from the mempool and filters out any transaction violating your active `policy.toml` rules.
   - Ensures that blocks mined by your node contain zero non-compliant transactions.

4. **Native Prometheus Metrics Exporter**
   - Built-in lightweight HTTP server serving standard Prometheus format metrics on a configurable port (`-prometheusport`, default `9332`).
   - Tracks block height, mempool size/bytes/usage, peer count (inbound/outbound), active policy profile, and detailed rejection statistics since startup (rejections by type: inscriptions, runes, dust, etc.).

5. **Sovereign UX & Resource-Aware Defaults**
   - **RAM Preservation:** Lowers the default `-maxmempool` from 300MB to 100MB, preventing memory exhaustion on modest hardware (like BitAxe mining hosts, Raspberry Pis, or older Mac Minis).
   - **Tor / I2P Friendly Startup:** Automatically warns the operator at startup if running a public mainnet node without Tor/Onion/I2P proxy configured to discourage exposing physical IPs.
   - **Branded User Agent:** Shows up as `OracleKnots` on the P2P network.

6. **Sovereign Oracle Desktop Dashboard GUI**
   - **Modern GUI App**: Mobile-first responsive dashboard powered by `pywebview` + Bottle, branded with the Oracle Owl identity.
   - **Wallet (Sparrow-style)**: Multi-wallet, receive+QR, send with fee rate, UTXO manager, coin control, PSBT tools, sign/verify messages, encrypt/backup/import, watch-only & descriptors.
   - **Oracle CLI Terminal**: Interactive `bitcoin-cli` shell with history and quick commands.
   - **Interactive Config Editor**: Visual tabs for storage, P2P, spam filters, optimization, and RPC settings.
   - **Live Dashboard**: Mempool sparkline, policy rejection panel, Prometheus metrics, debug.log streamer.
   - **Desktop Launcher**: `./install-desktop.sh` installs a `.desktop` entry with the Oracle Owl icon.


---

## How to Build

### Dependencies
Install the required build dependencies for your distribution. On **Arch Linux**:
```bash
sudo pacman -S base-devel boost openssl libevent sqlite
```

### Compile
Oracle Knots utilizes **CMake** for build configuration:
```bash
# Configure the build directory
cmake -B build -DCMAKE_BUILD_TYPE=Release

# Build the binaries (bitcoind, bitcoin-cli, bitcoin-util)
cmake --build build -j$(nproc)
```
Binaries are in `build/bin/` (or `build/src/` on some CMake configs).

Alternatively use the project build script:

```bash
./build.sh
```

### Control Center GUI

```bash
# One-time setup
./setup-gui.sh

# Launch dashboard
./launch.sh

# Optional: install desktop launcher
./install-desktop.sh
```

**GUI dependencies** (Arch Linux): `python`, `qt6-webengine` (for pywebview). Python packages are in `requirements.txt`.

**Wallet note:** `server=1` in `bitcoin.conf` is required for wallet and CLI features.

---

## Configuring the Declarative Policy Engine

At startup, a default configuration file named `policy.toml` is generated in your Bitcoin data directory. You can edit this file to select a profile or define custom rules:

```toml
# policy.toml
profile = "maximalist"
bip110_mode = "auto" # Options: auto, always, never

[custom_rules]
datacarrier_size = 0          # Capping OP_RETURN payload size
reject_tokens = true          # Reject BRC-20 / Runes
reject_inscriptions = true    # Reject Taproot/Witness Ordinals inscriptions
dust_relay_fee = 3000         # Custom dust fee in sat/kvb
permit_bare_multisig = false
permit_bare_pubkey = false
reject_parasites = true
max_op_return_outputs = 0
```

### Dynamic Policy Modification (RPC)
You can set and toggle policy values on the fly without restarting the node:
```bash
bitcoin-cli setsovereignpolicy monetary-only
```
Check compliance status and transaction rejection statistics:
```bash
bitcoin-cli checkbip110status
```

---

## Recommended Configuration for Sovereign Operators

Below is a recommended configuration (`bitcoin.conf`) for a resource-constrained, high-privacy mining operator setup:

```ini
# bitcoin.conf
txindex=0
blocksonly=0
maxconnections=40
maxmempool=100
dbcache=150

# Privacy
proxy=127.0.0.1:9050
onion=127.0.0.1:9050
listenonion=1
discover=0

# Oracle Knots Custom Policy
policyprofile=maximalist
bip110=auto
prometheus=1
prometheusport=9332
```

---

## Publicar en GitHub

Para subir el repo **sin compilar ni ejecutar el nodo** (útil si esa máquina ya tiene otro nodo activo), ver **[GITHUB_PUSH.md](GITHUB_PUSH.md)**.

Resumen rápido en la otra PC:

```bash
cd ~/oracle-knots
git restore depends/          # si el tarball no trajo depends/
./scripts/push-to-github.sh   # push no interactivo
```

---

## License

Oracle Knots is released under the terms of the MIT license. See [COPYING](COPYING) for more information.
