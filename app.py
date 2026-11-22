
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
st.write("Live Noise Monitoring Dashboard")

# Shared audio state
class AudioState:
    def __init__(self):
        self.lock = threading.Lock()
        self.level = 0.0
        self.history = []
        self.last_update = 0

audio = AudioState()

# Audio processing
def audio_callback(frame: av.AudioFrame):

    samples = frame.to_ndarray().astype(np.float32)

    if samples.size == 0:
        return frame

    level = float(np.sqrt(np.mean(samples ** 2)))

    with audio.lock:
        audio.level = level
        audio.history.append(level)
        audio.history = audio.history[-100:]
        audio.last_update = time.time()

    return frame


# Sidebar settings
st.sidebar.header("⚙️ Settings")

threshold = st.sidebar.slider(
    "Noise Threshold",
    min_value=100,
    max_value=15000,
    value=3000,
    step=100
)

st.sidebar.caption(
    "Threshold uses raw audio amplitude, not calibrated dB."
)

# Microphone section
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

# Dashboard
st.subheader("📊 Live Monitoring")

with audio.lock:
    current_level = audio.level
    history = audio.history.copy()
    last_update = audio.last_update

col1, col2, col3 = st.columns(3)

col1.metric(
    "Audio Level",
    round(current_level, 2)
)

if last_update and time.time() - last_update < 3:
    status = (
        "NOISE DETECTED"
        if current_level > threshold
        else "NORMAL"
    )
else:
    status = "WAITING FOR AUDIO"

col2.metric("Monitoring Status", status)

col3.metric("Target Range", "50 Feet")

# Alerts
if status == "NOISE DETECTED":
    st.error("🚨 LOUD NOISE DETECTED!")
elif status == "NORMAL":
    st.success("✅ Environment Normal")
else:
    st.warning("🎙️ Waiting for microphone audio...")

# Graph
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        y=history,
        mode="lines",
        name="Audio Level",
        line=dict(color="blue", width=2)
    )
)

fig.add_hline(
    y=threshold,
    line_dash="dash",
    line_color="red",
    annotation_text="Noise Threshold"
)

fig.update_layout(
    title="Live Noise Monitoring Graph",
    xaxis_title="Recent Audio Samples",
    yaxis_title="Raw Audio Amplitude",
    height=400
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# Connection status
if ctx.state.playing:
    st.success("Microphone streaming is active.")
else:
    st.info("Click START above to activate your microphone.")

st.info(
    "Note: 50-foot detection and sound direction "
    "are not yet implemented. They require real-world "
    "testing and suitable microphone hardware."
)
