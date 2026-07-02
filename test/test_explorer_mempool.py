"""Unit tests for mempool explorer block packing."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import api.explorer_mempool as em


BLOCK_CAP = em.block_cap_vbytes()


def _entry(txid, vsize, rate=10.0, fee_sat=None, anc=1):
    if fee_sat is None:
        fee_sat = int(rate * vsize)
    return (txid, vsize, rate, fee_sat, anc)


class TestPackMempoolBlocks(unittest.TestCase):
    def _pack(self, entries, num_blocks=4, sample=400, scan_limit=None):
        return em.pack_mempool_blocks(
            entries, BLOCK_CAP, num_blocks, sample, scan_limit
        )

    def test_single_block_not_full(self):
        entries = [_entry(f"{i:064x}", 500, rate=50 - i) for i in range(100)]
        blocks, tail = self._pack(entries)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["tx_count"], 100)
        self.assertEqual(len(blocks[0]["txs"]), 100)
        self.assertLess(blocks[0]["fill_pct"], 100)
        self.assertEqual(len(tail), 0)

    def test_spills_into_multiple_blocks(self):
        vsize = BLOCK_CAP // 2 + 1
        entries = [
            _entry("a" * 64, vsize, rate=100),
            _entry("b" * 64, vsize, rate=90),
            _entry("c" * 64, vsize, rate=80),
        ]
        blocks, tail = self._pack(entries)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0]["tx_count"], 1)
        self.assertEqual(blocks[1]["tx_count"], 1)
        self.assertEqual(blocks[2]["tx_count"], 1)
        self.assertEqual(len(tail), 0)

    def test_sample_capped_at_400(self):
        vsize = max(1, BLOCK_CAP // 500)
        entries = [_entry(f"{i:064x}", vsize, rate=200 - i) for i in range(900)]
        blocks, tail = self._pack(entries)
        self.assertGreaterEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["tx_count"], 500)
        self.assertEqual(len(blocks[0]["txs"]), 400)
        self.assertEqual(blocks[0]["tx_count"] - len(blocks[0]["txs"]), 100)

    def test_tail_after_four_full_blocks(self):
        vsize = BLOCK_CAP
        entries = [_entry(f"{i:064x}", vsize, rate=100 - i) for i in range(6)]
        blocks, tail = self._pack(entries, num_blocks=4)
        self.assertEqual(len(blocks), 4)
        self.assertEqual(len(tail), 2)
        self.assertEqual(tail[0][0], entries[4][0])

    def test_scan_limit_leaves_tail(self):
        entries = [_entry(f"{i:064x}", 100, rate=50) for i in range(20)]
        blocks, tail = self._pack(entries, scan_limit=10)
        self.assertEqual(sum(b["tx_count"] for b in blocks), 10)
        self.assertEqual(len(tail), 10)


if __name__ == "__main__":
    unittest.main()