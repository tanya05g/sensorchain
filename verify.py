from . import merkle


def verify_window(store, ledger, window_id):
    """Recompute this window's hash from raw data, apply a Merkle proof built from
    the batch's stored leaf hashes, and compare with the root held on the ledger."""
    w = store.get_window(window_id)
    if w is None:
        return {"ok": False, "reason": "window missing"}
    onchain = ledger.get_root(w["batch_id"])
    leaf = merkle.leaf_hash(w["sensor_id"], w["ts"], w["data_json"])
    stored = [r["leaf_hash"] for r in store.batch_rows(w["batch_id"])]
    proof = merkle.build_proof(stored, w["leaf_index"])
    computed = merkle.apply_proof(leaf, proof)
    return {"ok": computed == onchain, "leaf": leaf, "proof": proof,
            "computed_root": computed, "onchain_root": onchain, "batch_id": w["batch_id"]}


def verify_batch(store, ledger, batch_id):
    """Recompute every leaf from raw data. Catches edits, deletions and reordering."""
    rows = store.batch_rows(batch_id)
    if not rows:
        return {"ok": False, "reason": "batch empty"}
    leaves = [merkle.leaf_hash(r["sensor_id"], r["ts"], r["data_json"]) for r in rows]
    computed = merkle.build_root(leaves)
    onchain = ledger.get_root(batch_id)
    return {"ok": computed == onchain, "computed_root": computed, "onchain_root": onchain}
