
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import threading

st.set_page_config(
    page_title="Smart Noise Detector",
    page_icon="🔊",
    layout="wide"
)

st.title("🔊 Smart Noise Detection System")
st.write("Live Noise Monitoring Dashboard")

class AudioState:
    def __init__(self):
        self.lock = threading.Lock()
        self.level = 0.0
        self.history = []

audio = AudioState()

def audio_callback(frame):
    samples = frame.to_ndarray().astype(np.float32)

    level = float(np.sqrt(np.mean(samples ** 2)))

    with audio.lock:
        audio.level = level
        audio.history.append(level)
        audio.history = audio.history[-100:]

    return frame

st.sidebar.header("Settings")

threshold = st.sidebar.slider(
    "Noise Threshold",
    100,
    15000,
    3000
)

st.subheader("Microphone Monitoring")

webrtc_streamer(
    key="noise-monitor",
    mode=WebRtcMode.SENDONLY,
    audio_frame_callback=audio_callback,
    media_stream_constraints={
        "audio": True,
        "video": False
    },
    async_processing=True
)

with audio.lock:
    current_level = audio.level
    history = audio.history.copy()

col1, col2, col3 = st.columns(3)

col1.metric("Audio Level", round(current_level, 2))

status = (
    "NOISE DETECTED"
    if current_level > threshold
    else "NORMAL"
)

col2.metric("Status", status)
col3.metric("Target Range", "50 Feet")

if current_level > threshold:
    st.error("🚨 Loud Noise Detected!")
else:
    st.success("Environment Normal")

fig = go.Figure()

fig.add_trace(go.Scatter(
    y=history,
    mode="lines",
    name="Audio Level"
))

fig.add_hline(
    y=threshold,
    line_dash="dash",
    line_color="red"
)

fig.update_layout(
    title="Live Noise Monitoring",
    xaxis_title="Audio Samples",
    yaxis_title="Audio Amplitude"
)

st.plotly_chart(fig, use_container_width=True)

st.info(
    "Directional detection and calibrated "
    "50-feet monitoring will be added in the next version."
)
