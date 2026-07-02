"""Pure mempool projection helpers for the explorer (no GUI dependencies)."""

EXPLORER_BLOCK_WEIGHT = 4_000_000
EXPLORER_COINBASE_RESERVE_VB = 4_000
EXPLORER_PROJECTED_BLOCKS = 4
EXPLORER_SAMPLE_TXS_PER_BLOCK = 400
EXPLORER_MEMPOOL_SCAN_LIMIT = 50_000
EXPLORER_FEE_BUCKETS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 40, 50, 70, 100, 150, 200, 300]


def block_cap_vbytes():
    return (EXPLORER_BLOCK_WEIGHT // 4) - EXPLORER_COINBASE_RESERVE_VB


def fee_bucket_label(rate):
    prev = 0
    for b in EXPLORER_FEE_BUCKETS:
        if rate < b:
            return f"{prev}-{b}"
        prev = b
    return f"{EXPLORER_FEE_BUCKETS[-1]}+"


def _new_projected_block():
    return {"txs": [], "total_vsize": 0, "total_fees": 0, "rates": [], "tx_count": 0}


def pack_mempool_blocks(entries, block_cap_vb, num_blocks, sample_per_block, scan_limit=None):
    """Pack feerate-sorted mempool entries into projected blocks by vsize capacity."""
    scan_entries = entries[:scan_limit] if scan_limit else entries
    projected = []
    cur = _new_projected_block()
    consumed = 0

    for idx, (txid, vsize, rate, fee_sat, anc) in enumerate(scan_entries):
        if cur["tx_count"] > 0 and cur["total_vsize"] + vsize > block_cap_vb:
            projected.append(cur)
            if len(projected) >= num_blocks:
                consumed = idx
                cur = None
                break
            cur = _new_projected_block()

        cur["tx_count"] += 1
        cur["total_vsize"] += vsize
        cur["total_fees"] += fee_sat
        cur["rates"].append(rate)
        if len(cur["txs"]) < sample_per_block:
            cur["txs"].append([txid, vsize, round(rate, 1), anc])
        consumed = idx + 1
    else:
        if cur is not None and cur["tx_count"] > 0:
            projected.append(cur)

    blocks_out = []
    for b in projected:
        rates = sorted(b["rates"])
        median = rates[len(rates) // 2] if rates else 0
        blocks_out.append({
            "txs": b["txs"],
            "tx_count": b["tx_count"],
            "total_vsize": b["total_vsize"],
            "total_fees_sat": b["total_fees"],
            "median_feerate": round(median, 1),
            "min_feerate": round(rates[0], 1) if rates else 0,
            "max_feerate": round(rates[-1], 1) if rates else 0,
            "fill_pct": round(min(100.0, b["total_vsize"] / block_cap_vb * 100), 1),
        })

    return blocks_out, entries[consumed:]