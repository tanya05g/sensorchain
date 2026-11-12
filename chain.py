import hashlib
import json
from pathlib import Path


class LocalLedger:
    """Stand-in for the smart contract. Same method names, so a Web3 version
    (web3.py + Hardhat) can replace it later without touching the pipeline."""

    def __init__(self, path):
        self.path = Path(path)
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
        else:
            self.state = {"batches": {}, "anomalies": [], "tx_count": 0}
            self._save()

    def _save(self):
        self.path.write_text(json.dumps(self.state, indent=2))

    def _tx(self, payload) -> str:
        self.state["tx_count"] += 1
        raw = json.dumps(payload, sort_keys=True) + str(self.state["tx_count"])
        return "0x" + hashlib.sha256(raw.encode()).hexdigest()[:40]

    def anchor_batch(self, batch_id, merkle_root, start_ts, end_ts):
        if batch_id in self.state["batches"]:
            raise ValueError("batch already anchored")
        tx = self._tx([batch_id, merkle_root, start_ts, end_ts])
        self.state["batches"][batch_id] = {
            "root": merkle_root, "start_ts": start_ts, "end_ts": end_ts, "tx": tx}
        self._save()
        return tx

    def log_anomaly(self, batch_id, leaf_index, score, ts):
        tx = self._tx([batch_id, leaf_index, score, ts])
        self.state["anomalies"].append({
            "batch_id": batch_id, "leaf_index": leaf_index,
            "score": round(float(score), 3), "ts": ts, "tx": tx})
        self._save()
        return tx

    def get_root(self, batch_id):
        b = self.state["batches"].get(batch_id)
        return b["root"] if b else None

    def batches(self):
        return self.state["batches"]

    def anomalies(self):
        return self.state["anomalies"]
