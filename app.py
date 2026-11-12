import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sensorchain.chain import LocalLedger
from sensorchain.config import data_dir, load_sensors
from sensorchain.store import Store
from sensorchain.verify import verify_window

st.set_page_config(page_title="SensorChain", layout="wide")
d = data_dir()
if not (d / "sensorchain.db").exists():
    st.error("No data yet. Run: python -m sensorchain.run --reset")
    st.stop()

store, ledger = Store(d / "sensorchain.db"), LocalLedger(d / "ledger.json")
sensors = load_sensors()

st.sidebar.title("SensorChain")
sid = st.sidebar.selectbox("Sensor", list(sensors))
cfg = sensors[sid]
st.sidebar.caption(f"{cfg['type']} / {cfg['rate']} Hz / window {cfg['window']}")

df = pd.DataFrame([dict(r) for r in store.list_windows(sid)])
batches = {k: v for k, v in ledger.batches().items() if k.startswith(sid + "-")}
anoms = [a for a in ledger.anomalies() if a["batch_id"].startswith(sid + "-")]

st.title(f"{sid}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Windows", len(df))
c2.metric("Anomalies flagged", int(df["anomaly"].sum()))
c3.metric("Batches anchored", len(batches))
c4.metric("On-chain writes", len(batches) + len(anoms), help="vs one write per window")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df["id"], y=df["score"], mode="lines", name="score", line=dict(width=2)))
a = df[df["anomaly"] == 1]
fig.add_trace(go.Scatter(x=a["id"], y=a["score"], mode="markers", name="anomaly",
                         marker=dict(color="red", size=9, symbol="triangle-up")))
fig.add_hline(y=4.0, line_dash="dash", line_color="orange", annotation_text="threshold")
fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="window id", yaxis_title="anomaly score")
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Anomaly log")
    st.dataframe(pd.DataFrame(anoms)[["batch_id", "leaf_index", "score", "ts"]] if anoms else pd.DataFrame(),
                 use_container_width=True, hide_index=True)
with right:
    st.subheader("Anchored batches")
    st.dataframe(pd.DataFrame([{"batch": k, "root": v["root"][:10] + "..." + v["root"][-6:], "tx": v["tx"][:12] + "..."}
                               for k, v in batches.items()]), use_container_width=True, hide_index=True)

st.subheader("Verify evidence")
default = int(a["id"].iloc[0]) if len(a) else int(df["id"].iloc[0])
wid = st.number_input("Window id", min_value=int(df["id"].min()), max_value=int(df["id"].max()), value=default)
b1, b2, b3 = st.columns(3)
if b1.button("Simulate tampering"):
    store.tamper_window(int(wid))
    st.toast(f"Edited one value in window {int(wid)}")
if b2.button("Restore original"):
    store.restore_window(int(wid))
if b3.button("Verify", type="primary"):
    res = verify_window(store, ledger, int(wid))
    if res.get("ok"):
        st.success("VERIFIED: data matches the on-chain root")
    else:
        st.error("TAMPERED: recomputed root does not match the on-chain root")
    if "computed_root" in res:
        st.code(f"on-chain  {res['onchain_root']}\ncomputed  {res['computed_root']}\nproof length  {len(res['proof'])} hashes")
