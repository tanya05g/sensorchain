import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS windows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sensor_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  data_json TEXT NOT NULL,
  score REAL,
  anomaly INTEGER,
  label INTEGER,
  batch_id TEXT,
  leaf_index INTEGER,
  leaf_hash TEXT
);
CREATE TABLE IF NOT EXISTS tamper_backup (
  window_id INTEGER PRIMARY KEY,
  data_json TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def insert_windows(self, rows):
        self.db.executemany(
            "INSERT INTO windows (sensor_id, ts, data_json, score, anomaly, label,"
            " batch_id, leaf_index, leaf_hash) VALUES (:sensor_id, :ts, :data_json,"
            " :score, :anomaly, :label, :batch_id, :leaf_index, :leaf_hash)", rows)
        self.db.commit()

    def get_window(self, window_id):
        return self.db.execute("SELECT * FROM windows WHERE id=?", (window_id,)).fetchone()

    def batch_rows(self, batch_id):
        return self.db.execute(
            "SELECT * FROM windows WHERE batch_id=? ORDER BY leaf_index", (batch_id,)).fetchall()

    def list_windows(self, sensor_id):
        return self.db.execute(
            "SELECT id, ts, score, anomaly, label, batch_id, leaf_index FROM windows"
            " WHERE sensor_id=? ORDER BY id", (sensor_id,)).fetchall()

    def sensors(self):
        return [r[0] for r in self.db.execute("SELECT DISTINCT sensor_id FROM windows")]

    def tamper_window(self, window_id):
        row = self.get_window(window_id)
        if not self.db.execute("SELECT 1 FROM tamper_backup WHERE window_id=?", (window_id,)).fetchone():
            self.db.execute("INSERT INTO tamper_backup VALUES (?,?)", (window_id, row["data_json"]))
        vals = row["data_json"].strip("[]").split(",")
        vals[len(vals) // 2] = str(round(float(vals[len(vals) // 2]) + 0.01, 5))
        self.db.execute("UPDATE windows SET data_json=? WHERE id=?", ("[" + ",".join(vals) + "]", window_id))
        self.db.commit()

    def restore_window(self, window_id):
        b = self.db.execute("SELECT data_json FROM tamper_backup WHERE window_id=?", (window_id,)).fetchone()
        if b:
            self.db.execute("UPDATE windows SET data_json=? WHERE id=?", (b[0], window_id))
            self.db.execute("DELETE FROM tamper_backup WHERE window_id=?", (window_id,))
            self.db.commit()

    def delete_window(self, window_id):
        self.db.execute("DELETE FROM windows WHERE id=?", (window_id,))
        self.db.commit()
