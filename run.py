import argparse

from .chain import LocalLedger
from .config import data_dir, load_sensors
from .pipeline import process_sensor
from .store import Store


def main():
    p = argparse.ArgumentParser(description="Run the sensor pipeline on all sensors in sensors.yaml")
    p.add_argument("--windows", type=int, default=500)
    p.add_argument("--batch-size", type=int, default=100)
    p.add_argument("--reset", action="store_true")
    a = p.parse_args()
    d = data_dir()
    if a.reset:
        for f in ("sensorchain.db", "ledger.json"):
            (d / f).unlink(missing_ok=True)
    store, ledger = Store(d / "sensorchain.db"), LocalLedger(d / "ledger.json")
    for i, (sid, cfg) in enumerate(load_sensors().items()):
        process_sensor(sid, cfg, store, ledger, a.windows, a.batch_size, seed=i)
        print(f"{sid}: {a.windows} windows processed")
    print(f"batches anchored: {len(ledger.batches())}, anomalies logged: {len(ledger.anomalies())}")


if __name__ == "__main__":
    main()
