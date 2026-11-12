import json
from datetime import datetime, timedelta, timezone

from . import merkle
from .detectors import make_detector
from .sources import make_source


def _flush(sensor_id, batch_no, rows, store, ledger):
    batch_id = f"{sensor_id}-B{batch_no:03d}"
    for i, r in enumerate(rows):
        r["batch_id"], r["leaf_index"] = batch_id, i
        r["leaf_hash"] = merkle.leaf_hash(sensor_id, r["ts"], r["data_json"])
    root = merkle.build_root([r["leaf_hash"] for r in rows])
    store.insert_windows(rows)
    ledger.anchor_batch(batch_id, root, rows[0]["ts"], rows[-1]["ts"])
    for r in rows:
        if r["anomaly"]:
            ledger.log_anomaly(batch_id, r["leaf_index"], r["score"], r["ts"])
    return batch_id


def process_sensor(sensor_id, cfg, store, ledger, n_windows=500, batch_size=100, seed=0):
    source = make_source(cfg, seed)
    detector = make_detector(cfg).fit(source.normal_windows(50))
    t = datetime.now(timezone.utc)
    step = timedelta(seconds=cfg["window"] / cfg["rate"])
    rows, batch_no = [], 1
    for window, label in source.stream(n_windows):
        score = detector.score(window)
        rows.append({
            "sensor_id": sensor_id,
            "ts": t.isoformat(timespec="milliseconds"),
            "data_json": json.dumps([round(float(x), 5) for x in window], separators=(",", ":")),
            "score": round(score, 4),
            "anomaly": int(score > detector.threshold),
            "label": label,
            "batch_id": None, "leaf_index": None, "leaf_hash": None})
        t += step
        if len(rows) == batch_size:
            _flush(sensor_id, batch_no, rows, store, ledger)
            rows, batch_no = [], batch_no + 1
    if rows:
        _flush(sensor_id, batch_no, rows, store, ledger)
