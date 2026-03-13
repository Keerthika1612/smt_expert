import streamlit as st
import requests
import base64

# --- PAGE CONFIG ---
st.set_page_config(page_title="SMT Expert System", page_icon="🔧")
st.title("🔧 SMT & Wave Expert")

# --- 1. DYNAMIC CONFIGURATION ---
with st.sidebar:
    st.header("🔗 Backend Connection")
    ngrok_url = st.text_input(
        "Enter Active ngrok URL:", 
        placeholder="https://xxxx-xxx.ngrok-free.app",
        help="Paste the forwarding URL from the ngrok terminal here."
    )
    
    st.divider()
    st.header("🎙️ Voice Input")
    # This widget handles the microphone recording
    audio_value = st.audio_input("Describe the defect verbally")
    
    st.divider()
    st.header("📸 Visual Inspection")
    uploaded_file = st.file_uploader("Upload defect photo", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Defect to analyze")

# --- 2. VALIDATION ---
if not ngrok_url:
    st.info("👋 Welcome! To begin, please paste the active **ngrok URL** provided by the technician in the sidebar.")
    st.stop()

base_url = ngrok_url.strip().rstrip("/")
STREAM_URL = f"{base_url}/stream"
VOICE_URL = f"{base_url}/transcribe"

# --- SETUP HEADERS ---
headers = {
    "ngrok-skip-browser-warning": "true" 
}

# --- INITIALIZE CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- DISPLAY CHAT HISTORY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- PROCESS VOICE INPUT ---
voice_text = None
if audio_value:
    with st.spinner("Transcribing your voice..."):
        try:
            # Send the audio bytes to the backend /transcribe endpoint
            files = {"file": ("audio.wav", audio_value.getvalue(), "audio/wav")}
            v_resp = requests.post(VOICE_URL, files=files, headers=headers)
            v_resp.raise_for_status()
            voice_text = v_resp.json().get("text")
            st.sidebar.success(f"Recognized: {voice_text}")
        except Exception as e:
            st.sidebar.error(f"Voice Error: {e}")

# --- CHAT LOGIC ---
# Use the transcribed voice text if available, otherwise use text input
prompt = st.chat_input("Ask about a defect...")
if voice_text:
    prompt = voice_text

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare payload for the main RAG chain
    payload = {"input": prompt}
    if uploaded_file:
        uploaded_file.seek(0)
        encoded_image = base64.b64encode(uploaded_file.read()).decode('utf-8')
        payload["image"] = encoded_image

    # --- API CALL TO BACKEND ---
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            with requests.post(
                STREAM_URL, 
                json=payload, 
                headers={"Content-Type": "application/json", **headers}, 
                stream=True,
                timeout=120 
            ) as r:
                r.raise_for_status() 
                for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"❌ Connection Error: {e}")
            st.warning("Check if ngrok is active and your backend is running.")
