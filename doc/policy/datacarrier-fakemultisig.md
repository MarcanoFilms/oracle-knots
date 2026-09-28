# Fake multisig data carriers

## Summary

Spends that reveal a **1-of-N `CHECKMULTISIG` script** (with N ≥ 3) wrapped in
P2SH or P2WSH are treated as data carriers and are non-standard when bare
multisig is not permitted (`-permitbaremultisig=0`, the default). Such a script
has no legitimate custody use, so the rule has no effect on real threshold
multisig (2-of-3, 3-of-5, …) or on 1-of-2 "either party" scripts.

## Background

Data-embedding services such as [bitfiles](https://bitfiles.io/) (via the
[`bpub`](https://github.com/bitfiles-io/bpub) library) store arbitrary files
on-chain by hiding the payload inside the "public keys" of a bare multisig
script:

* A **funding** transaction creates many small (dust) P2WSH outputs. At this
  point the outputs are ordinary P2WSH and are indistinguishable from a real
  wallet's — there is nothing to filter.
* A **reveal** transaction later spends those outputs. Each input's witness
  exposes a redeem script of the form

  ```
  OP_1 <pubkey_1> <pubkey_2> ... <pubkey_15> OP_15 OP_CHECKMULTISIG
  ```

  where 14 of the 15 "public keys" are 33-byte chunks of file data (≈31 payload
  bytes each) and only one is a real signer. Because the script is a 1-of-N,
  the other keys are never checked against a signature.

Each fake key includes a brute-forced trailing "ground nonce" byte so that its
x-coordinate lands on the secp256k1 curve. A naïve "reject keys that are not
valid curve points" filter therefore does **not** catch it.

The reveal transaction is otherwise perfectly standard: the witnessScript is
under `MAX_STANDARD_P2WSH_SCRIPT_SIZE`, every other witness item is under
`MAX_STANDARD_P2WSH_STACK_ITEM_SIZE`, and the wrapping P2WSH bypasses
`-permitbaremultisig`, which only inspects output scripts. This is why the
existing datacarrier, parasite and bare-multisig filters miss it.

## The rule

The reliable, false-positive-free signature is the **shape** of the revealed
script rather than the content of its keys. A 1-of-N multisig lets any single
one of its N keys spend the output, which is strictly weaker than a plain
single-key output — nobody constructs one for security. Once N is 3 or more,
the only plausible reason to pay for the extra keys is to carry data.

`AreInputsStandard` extracts the executed script for every P2SH, P2WSH and
P2SH-P2WSH input (via `GetScriptForTransactionInput`) and, when
`-permitbaremultisig=0`, rejects the transaction if that script solves to a
multisig with `m == 1` and `n >= MULTISIG_DATACARRIER_MIN_KEYS` (3). The
rejection reason is `datacarrier-fakemultisig`.

Because the check runs in `AreInputsStandard` (part of `PreChecks`), it fires
before signature validation and applies to relay and to block-template
construction, so a node running this policy neither relays nor mines these
reveals.

## What is *not* affected

* Threshold multisig (`m >= 2`): 2-of-3, 3-of-5, 4-of-7, m-of-15, etc.
* 1-of-2 multisig (below the N threshold).
* The funding transactions themselves (ordinary P2WSH outputs; not
  distinguishable until spent).

## Limitations

* This is **relay/mempool policy**, not consensus. It stops a node from
  relaying or mining these transactions, but a node still accepts a valid block
  that contains one. On a network where a filtering node produces the block
  templates, that is enough to keep the reveals out of blocks; where a
  non-filtering miner includes them, only a consensus rule would prevent
  confirmation.
* An embedder could migrate to `m >= 2` to dodge the `m == 1` test, at the cost
  of a second real key and signature per input. The threshold constants are
  kept in `src/policy/policy.h` so the heuristic can be tightened if that
  happens.
