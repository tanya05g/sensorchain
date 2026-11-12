# SensorChain

Sensor anomaly detection with tamper-evident, Merkle-anchored evidence.

## Run (GitHub Codespaces)

    python -m sensorchain.run --reset --windows 500
    streamlit run dashboard/app.py

Open the forwarded port 8501. Pick a sensor, click "Simulate tampering", then "Verify".

## Test

    pytest -q

## Layout

    sensors.yaml            one entry per sensor (type, rate, window, detector, source)
    src/sensorchain/
      sources.py            simulator and CSV replay (add MQTT here)
      detectors.py          zscore baseline (add LSTM autoencoder here)
      merkle.py             leaf hashing, root, proofs
      chain.py              LocalLedger, same methods as the contract
      store.py              SQLite store for raw windows
      pipeline.py           detect, hash, batch, anchor
      verify.py             window and batch verification
    dashboard/app.py        Streamlit UI
    contracts/              Hardhat project goes here (next step)
