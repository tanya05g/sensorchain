import csv

import numpy as np


class SimulatorSource:
    """Fake sensor with injected faults. Replace with ReplaySource or MQTT later."""

    def __init__(self, kind="vibration", rate=1000, window=256, fault_rate=0.05, seed=0):
        self.kind, self.rate, self.window = kind, rate, window
        self.fault_rate = fault_rate
        self.rng = np.random.default_rng(seed)

    def _window(self, fault):
        n, r = self.window, self.rng
        t = np.arange(n) / self.rate
        if self.kind == "vibration":
            x = 0.5 * np.sin(2 * np.pi * 50 * t + r.uniform(0, 6.28)) + 0.1 * r.standard_normal(n)
            if fault:
                x = x * 1.8 + (r.random(n) < 0.04) * r.choice([-1, 1], n) * 1.5
        elif self.kind == "temperature":
            x = 4.0 + 0.1 * r.standard_normal(n) + 0.02 * np.arange(n) * 0
            if fault:
                x = x + np.linspace(0, 3.0, n)
        else:
            x = 5.0 + 0.05 * r.standard_normal(n)
            if fault:
                x[r.integers(0, n, 4)] += r.choice([-1, 1]) * 0.6
        return x

    def normal_windows(self, n):
        return [self._window(False) for _ in range(n)]

    def stream(self, n):
        for _ in range(n):
            fault = bool(self.rng.random() < self.fault_rate)
            yield self._window(fault), int(fault)


class ReplaySource:
    """Replays a numeric CSV column (e.g. CWRU) as a stream of windows."""

    def __init__(self, path, column=0, window=256):
        with open(path) as f:
            rows = list(csv.reader(f))
        start = 1 if not _is_num(rows[0][column]) else 0
        self.data = np.array([float(r[column]) for r in rows[start:]])
        self.window = window

    def normal_windows(self, n):
        w = self.window
        return [self.data[i * w:(i + 1) * w] for i in range(n)]

    def stream(self, n):
        w = self.window
        for i in range(n):
            chunk = self.data[i * w:(i + 1) * w]
            if len(chunk) < w:
                return
            yield chunk, None


def _is_num(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def make_source(cfg, seed=0):
    if cfg["source"] == "simulator":
        return SimulatorSource(cfg["type"], cfg["rate"], cfg["window"], cfg.get("fault_rate", 0.05), seed)
    if cfg["source"] == "replay":
        return ReplaySource(cfg["file"], cfg.get("column", 0), cfg["window"])
    raise ValueError(f"unknown source {cfg['source']}")
