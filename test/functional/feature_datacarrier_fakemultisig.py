#!/usr/bin/env python3
# Copyright (c) 2026 The Bitcoin Knots developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test rejection of fake 1-of-N multisig data carriers (bpub/bitfiles).

Data-embedding services such as bitfiles (via the bpub library) hide payload
bytes inside the "public keys" of a 1-of-N CHECKMULTISIG script, wrapped in
P2WSH (or P2SH-P2WSH) so the script only appears on-chain, in the witness/redeem,
when the dust funding output is spent (the "reveal" tx). Only one of the N keys
is ever a real signer; the rest are pure data.

When bare multisig is not permitted (-permitbaremultisig=0), a revealed 1-of-N
multisig with N >= MULTISIG_DATACARRIER_MIN_KEYS (3) is rejected as a data
carrier. Threshold multisig (m >= 2) and small 1-of-2 multisig are unaffected.

The policy check runs in PreChecks (AreInputsStandard), before script/signature
verification, so these tests fund a real P2WSH/P2SH output and then submit a
reveal transaction with a dummy signature: the data-carrier rejection fires
first, which is exactly what we assert.
"""
from hashlib import sha256

from test_framework.messages import (
    COutPoint,
    CTransaction,
    CTxIn,
    CTxInWitness,
    CTxOut,
)
from test_framework.script import CScript, OP_0
from test_framework.script_util import (
    keys_to_multisig_script,
    key_to_p2wpkh_script,
    script_to_p2wsh_script,
    script_to_p2sh_p2wsh_script,
)
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal
from test_framework.wallet import MiniWallet

from random import randbytes

REJECT = "datacarrier-fakemultisig"


def fake_pubkey():
    """A 33-byte compressed-looking pubkey full of payload bytes."""
    return bytes([0x02 + (randbytes(1)[0] & 1)]) + randbytes(32)


class DatacarrierFakeMultisigTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        # Reject wrapped bare-multisig data carriers. Upstream this is gated by
        # -permitbaremultisig; on Oracle Knots the active policy profile pins it.
        self.extra_args = [["-permitbaremultisig=0"]]

    def build_reveal(self, funding, witness_script, *, p2sh_p2wsh=False):
        """Build a reveal tx spending `funding` with a dummy single-sig witness."""
        tx = CTransaction()
        tx.vin = [CTxIn(COutPoint(int(funding["txid"], 16), funding["sent_vout"]))]
        tx.vout = [CTxOut(funding["value"] - 1000, key_to_p2wpkh_script(fake_pubkey()))]
        tx.wit.vtxinwit = [CTxInWitness()]
        # CHECKMULTISIG dummy element, one (dummy) signature, then the script.
        tx.wit.vtxinwit[0].scriptWitness.stack = [b"", b"\x00" * 72, bytes(witness_script)]
        if p2sh_p2wsh:
            # scriptSig pushes the P2WSH program (the P2SH redeemScript).
            program = CScript([OP_0, sha256(bytes(witness_script)).digest()])
            tx.vin[0].scriptSig = CScript([bytes(program)])
        return tx

    def fund(self, m, n, *, p2sh_p2wsh=False):
        """Create and confirm a P2WSH / P2SH-P2WSH output over a fake m-of-n multisig."""
        ws = keys_to_multisig_script([fake_pubkey() for _ in range(n)], k=m)
        spk = script_to_p2sh_p2wsh_script(ws) if p2sh_p2wsh else script_to_p2wsh_script(ws)
        funding = self.wallet.send_to(from_node=self.nodes[0], scriptPubKey=spk, amount=100_000)
        funding["value"] = 100_000
        self.generate(self.nodes[0], 1)  # confirm + sync to node1
        return funding, ws

    def check(self, node, m, n, *, p2sh_p2wsh=False):
        funding, ws = self.fund(m, n, p2sh_p2wsh=p2sh_p2wsh)
        reveal = self.build_reveal(funding, ws, p2sh_p2wsh=p2sh_p2wsh)
        return node.testmempoolaccept([reveal.serialize().hex()])[0]

    def run_test(self):
        self.wallet = MiniWallet(self.nodes[0])
        node = self.nodes[0]

        self.log.info("1-of-15 P2WSH reveal (the real bpub shape) is rejected")
        res = self.check(node, 1, 15)
        assert_equal(res["allowed"], False)
        assert res["reject-reason"].endswith(REJECT), res["reject-reason"]

        self.log.info("1-of-3 P2WSH reveal (threshold boundary) is rejected")
        res = self.check(node, 1, 3)
        assert_equal(res["allowed"], False)
        assert res["reject-reason"].endswith(REJECT), res["reject-reason"]

        self.log.info("1-of-15 P2SH-P2WSH reveal is also rejected")
        res = self.check(node, 1, 15, p2sh_p2wsh=True)
        assert_equal(res["allowed"], False)
        assert res["reject-reason"].endswith(REJECT), res["reject-reason"]

        self.log.info("1-of-2 P2WSH is below threshold -> not a data-carrier rejection")
        res = self.check(node, 1, 2)
        assert not res["reject-reason"].endswith(REJECT), res["reject-reason"]

        self.log.info("2-of-3 threshold multisig -> not a data-carrier rejection")
        res = self.check(node, 2, 3)
        assert not res["reject-reason"].endswith(REJECT), res["reject-reason"]

        self.log.info("3-of-5 threshold multisig -> not a data-carrier rejection")
        res = self.check(node, 3, 5)
        assert not res["reject-reason"].endswith(REJECT), res["reject-reason"]


if __name__ == "__main__":
    DatacarrierFakeMultisigTest(__file__).main()
