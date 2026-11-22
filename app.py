
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import threading
import time

st.set_page_config(
    page_title="Smart Noise Detector",
    page_icon="🔊",
    layout="wide"
)

st.title("🔊 Smart Noise Detection System")
st.caption("Real-Time Microphone Noise Monitoring")

# -----------------------------
# AUDIO STATE
# -----------------------------

class AudioState:
    def __init__(self):
        self.lock = threading.Lock()
        self.level = 0.0
        self.history = []
        self.last_update = 0

audio = AudioState()

# -----------------------------
# AUDIO CALLBACK
# -----------------------------

def audio_callback(frame: av.AudioFrame):

    samples = frame.to_ndarray().astype(np.float32)

    if samples.size == 0:
        return frame

    # Convert audio samples to mono if required
    samples = samples.flatten()

    # Calculate RMS audio level
    rms = float(np.sqrt(np.mean(samples ** 2)))

    # Normalize display level
    if np.issubdtype(frame.to_ndarray().dtype, np.integer):
        scale = float(max(abs(np.iinfo(frame.to_ndarray().dtype).min),
                          np.iinfo(frame.to_ndarray().dtype).max))
        display_level = (rms / scale) * 1000
    else:
        display_level = rms * 1000

    with audio.lock:
        audio.level = display_level
        audio.history.append(display_level)
        audio.history = audio.history[-100:]
        audio.last_update = time.time()

    return frame

# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.header("⚙️ Monitoring Settings")

threshold = st.sidebar.slider(
    "Noise Threshold",
    min_value=1,
    max_value=1000,
    value=100,
    step=10
)

st.sidebar.caption(
    "Threshold is a relative audio level, not calibrated dB."
)

# -----------------------------
# MICROPHONE CONNECTION
# -----------------------------

st.subheader("🎙️ Microphone Monitoring")

ctx = webrtc_streamer(
    key="noise-monitor",
    mode=WebRtcMode.SENDONLY,
    audio_frame_callback=audio_callback,

    media_stream_constraints={
        "audio": True,
        "video": False
    },

    rtc_configuration={
        "iceServers": [
            {
                "urls": ["stun:stun.l.google.com:19302"]
            }
        ]
    },

    async_processing=True
)

# -----------------------------
# LIVE DASHBOARD
# -----------------------------

st.subheader("📊 Live Monitoring Dashboard")

with audio.lock:
    current_level = audio.level
    history = audio.history.copy()
    last_update = audio.last_update

audio_received = (
    last_update > 0 and
    time.time() - last_update < 5
)

if audio_received:

    if current_level > threshold:
        status = "NOISE DETECTED"
    else:
        status = "NORMAL"

else:
    status = "WAITING FOR AUDIO"

# -----------------------------
# METRICS
# -----------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Audio Level",
    round(current_level, 2)
)

col2.metric(
    "Monitoring Status",
    status
)

col3.metric(
    "Monitoring Range",
    "50 Feet Target"
)

# -----------------------------
# ALERT
# -----------------------------

if status == "NOISE DETECTED":

    st.error("🚨 LOUD NOISE DETECTED!")

elif status == "NORMAL":

    st.success("✅ Environment Normal")

else:

    st.warning("🎙️ Waiting for microphone audio...")

# -----------------------------
# CONNECTION STATUS
# -----------------------------

if ctx.state.playing:

    st.success("Microphone stream is connected.")

else:

    st.info("Click START to activate microphone.")

# -----------------------------
# GRAPH
# -----------------------------

st.subheader("📈 Live Noise Graph")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        y=history,
        mode="lines",
        name="Audio Level",
        line=dict(
            color="blue",
            width=2
        )
    )
)

fig.add_hline(
    y=threshold,
    line_dash="dash",
    line_color="red",
    annotation_text="Noise Threshold"
)

fig.update_layout(
    xaxis_title="Recent Audio Samples",
    yaxis_title="Relative Audio Level",
    height=400,
    yaxis=dict(
        rangemode="tozero"
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# -----------------------------
# AUTO REFRESH
# -----------------------------

if ctx.state.playing:
    time.sleep(0.5)
    st.rerun()

# -----------------------------
# PROJECT INFORMATION
# -----------------------------

st.divider()

st.info(
    "Current version supports microphone audio monitoring. "
    "50-foot detection, calibrated decibel measurement, "
    "direction detection and automatic bell alerts "
    "are not yet implemented."
)
