#!/usr/bin/env python3
# Copyright (c) 2026 The Oracle Knots developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test the -uaprivacy option.

With -uaprivacy on (the mainnet default), peers reached over public
networks are sent a generic upstream user agent instead of the Oracle
Knots one, so user-agent scans of clearnet listeners cannot locate
Oracle Knots operators. Regtest connections run over IPv4 loopback,
which counts as a public network, so the camouflaged user agent is what
the peer must see. On test chains the option defaults to off.

The test framework's connect_nodes() identifies peers by matching their
wire subver against the other node's local subversion, which is exactly
what -uaprivacy breaks, so the first handshake is awaited by hand.
"""

import re

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

GENERIC_UA_RE = re.compile(r"^/Satoshi:\d+\.\d+\.\d+/Knots:\d+/$")


class UAPrivacyTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 2
        self.setup_clean_chain = True
        # node0 camouflages, node1 runs the regtest default (off)
        self.extra_args = [["-uaprivacy=1"], []]

    def setup_network(self):
        self.setup_nodes()
        # connect_nodes() would wait for a subver match that -uaprivacy
        # deliberately prevents, so wait for the handshake manually
        self.connect_nodes(0, 1, wait_for_connect=False)
        self.wait_until(lambda: all(
            len(n.getpeerinfo()) == 1 and n.getpeerinfo()[0]["version"] != 0
            for n in self.nodes))

    def seen_subversion(self, node):
        peers = node.getpeerinfo()
        assert_equal(len(peers), 1)
        return peers[0]["subver"]

    def run_test(self):
        self.log.info("the local subversion is never camouflaged")
        assert "OracleKnots" in self.nodes[0].getnetworkinfo()["subversion"]

        self.log.info("a public-network peer of a -uaprivacy node sees a generic user agent")
        ua = self.seen_subversion(self.nodes[1])
        assert GENERIC_UA_RE.match(ua), f"unexpected camouflaged UA: {ua}"
        assert "OracleKnots" not in ua
        # the default -uacomment=testnode0 must not leak into the generic UA
        assert "testnode0" not in ua

        self.log.info("without -uaprivacy the real user agent goes out (test-chain default)")
        ua = self.seen_subversion(self.nodes[0])
        assert "OracleKnots" in ua
        assert "(testnode1)" in ua

        self.log.info("-uaprivacy=0 restores the real user agent on the wire")
        self.restart_node(0, [])
        self.wait_until(lambda: len(self.nodes[1].getpeerinfo()) == 0)
        self.connect_nodes(0, 1)
        ua = self.seen_subversion(self.nodes[1])
        assert "OracleKnots" in ua
        assert "(testnode0)" in ua


if __name__ == "__main__":
    UAPrivacyTest(__file__).main()
