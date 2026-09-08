# Building Oracle Knots (all-in-one BLAKE2b stack)

Oracle Knots unifies the **BLAKE2b proof-of-work fork** with the Oracle policy
engine, sovereign-mining tooling, and the Control Center GUI in a single tree.
This guide builds the node (and, optionally, the bundled DATUM Gateway).

## 1. Dependencies

**Arch Linux**
```bash
sudo pacman -S base-devel cmake boost libevent sqlite openssl \
               curl jansson libmicrohttpd libsodium
```

**Debian / Ubuntu**
```bash
sudo apt install build-essential cmake libboost-dev libevent-dev \
                 libsqlite3-dev libssl-dev pkg-config \
                 libcurl4-openssl-dev libjansson-dev libmicrohttpd-dev libsodium-dev
```

(The last four packages on each line are only needed for the DATUM Gateway.)

## 2. Get the source (with the DATUM submodule)

```bash
git clone https://github.com/MarcanoFilms/oracle-knots.git
cd oracle-knots
git submodule update --init --recursive     # pulls mining/datum-convoy (CONVOY)
```

## 3. Build

```bash
./build.sh                 # builds the node, then the DATUM Gateway if vendored
./build.sh --node-only     # node only
```

`build.sh` passes `-DRDTS_CONSENT=IMPLICIT` (the Knots BIP-110/RDTS consent
gate). To build the node manually with the wallet enabled:

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_WALLET=ON -DRDTS_CONSENT=IMPLICIT
cmake --build build -j"$(nproc)"
```

Binaries land in `build/bin/` (`bitcoind`, `bitcoin-cli`). The DATUM Gateway
lands in `mining/datum-convoy/build/datum_gateway`.

## 4. Verify the BLAKE2b build

```bash
build/bin/bitcoind -version | head -1          # should report OracleKnots
grep -n 'Blake2bHeight' src/kernel/chainparams.cpp   # mainnet activation 961640
```

Once running against your datadir, the P2P subversion should read
`/OracleKnots:29.4.x/OracleKnots:.../` (see `bitcoin-cli getnetworkinfo`).

## 5. Launch the all-in-one stack

```bash
./oracle-knots            # ensures the node is up and opens the Control Center
./oracle-knots status     # component status without starting anything
./oracle-knots --help
```

## Notes

- **Deploying to a running node:** don't hot-swap a production binary. Build in a
  separate directory, verify, then point your service's `ExecStart` at the new
  `bitcoind` (see `~/blake2b-mainnet-prep/` for the switch/rollback pattern).
- **Unified sighash:** `src/common/sighash_rules.cpp` (opt-in unified sighash) is
  a follow-up delta from the 29.4.1 tree; standard-signature spending works
  without it.
