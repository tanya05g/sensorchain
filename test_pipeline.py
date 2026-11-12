from sensorchain.chain import LocalLedger
from sensorchain.pipeline import process_sensor
from sensorchain.store import Store
from sensorchain.verify import verify_batch, verify_window

CFG = {"type": "vibration", "rate": 2000, "window": 256, "detector": "zscore",
       "source": "simulator", "fault_rate": 0.1}


def setup(tmp_path):
    store, ledger = Store(tmp_path / "t.db"), LocalLedger(tmp_path / "l.json")
    process_sensor("m1", CFG, store, ledger, n_windows=250, batch_size=100, seed=1)
    return store, ledger


def test_untouched_data_verifies(tmp_path):
    store, ledger = setup(tmp_path)
    assert all(verify_window(store, ledger, i)["ok"] for i in (1, 50, 100, 101, 250))
    assert all(verify_batch(store, ledger, b)["ok"] for b in ledger.batches())


def test_edit_is_detected(tmp_path):
    store, ledger = setup(tmp_path)
    store.tamper_window(57)
    assert not verify_window(store, ledger, 57)["ok"]
    assert not verify_batch(store, ledger, "m1-B001")["ok"]
    store.restore_window(57)
    assert verify_window(store, ledger, 57)["ok"]


def test_deletion_is_detected(tmp_path):
    store, ledger = setup(tmp_path)
    store.delete_window(30)
    assert not verify_batch(store, ledger, "m1-B001")["ok"]
