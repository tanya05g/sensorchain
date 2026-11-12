import numpy as np


class ZScoreDetector:
    """Baseline detector. Interface: fit(windows), score(window) -> float.
    Add LSTMAutoencoder with the same interface later."""

    def __init__(self, threshold=4.0):
        self.threshold = threshold

    @staticmethod
    def _features(w):
        w = np.asarray(w)
        return np.array([np.sqrt(np.mean(w ** 2)), np.abs(w - w.mean()).max(), w[-len(w) // 4:].mean() - w[:len(w) // 4].mean()])

    def fit(self, windows):
        f = np.array([self._features(w) for w in windows])
        self.mu, self.sd = f.mean(0), f.std(0) + 1e-9
        return self

    def score(self, window) -> float:
        return float(np.max(np.abs((self._features(window) - self.mu) / self.sd)))


def make_detector(cfg):
    if cfg["detector"] == "zscore":
        return ZScoreDetector()
    raise ValueError(f"unknown detector {cfg['detector']}")
