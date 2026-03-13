import streamlit as st
import requests
import base64

# --- PAGE CONFIG ---
st.set_page_config(page_title="SMT Expert System", page_icon="🔧", layout="wide")
st.title("🔧 SMT & Wave Expert")

# --- 1. DYNAMIC CONFIGURATION ---
with st.sidebar:
    st.header("🔗 Backend Connection")
    ngrok_url = st.text_input(
        "Enter Active ngrok URL:", 
        placeholder="https://xxxx-xxx.ngrok-free.app",
        value=st.session_state.get("last_url", ""),
        help="Paste the forwarding URL from the ngrok terminal here."
    )
    if ngrok_url:
        st.session_state["last_url"] = ngrok_url

    st.divider()
    st.header("🎙️ Voice Input")
    audio_value = st.audio_input("Describe the defect")
    
    st.divider()
    st.header("📸 Visual Inspection")
    uploaded_file = st.file_uploader("Upload defect photo", type=["jpg", "jpeg", "png"])

# --- 2. VALIDATION ---
if not ngrok_url:
    st.info("👋 Welcome! Please paste your **ngrok URL** in the sidebar to start.")
    st.stop()

base_url = ngrok_url.strip().rstrip("/")
STREAM_URL = f"{base_url}/stream"
VOICE_URL = f"{base_url}/transcribe"
headers = {"ngrok-skip-browser-warning": "true"}

# --- 3. INITIALIZE STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

# --- 4. PROCESS VOICE INPUT (LOGIC) ---
# We check if there is new audio that we haven't processed yet
if audio_value and audio_value != st.session_state.last_processed_audio:
    with st.spinner("Transcribing..."):
        try:
            files = {"file": ("audio.wav", audio_value.getvalue(), "audio/wav")}
            v_resp = requests.post(VOICE_URL, files=files, headers=headers)
            v_resp.raise_for_status()
            transcript = v_resp.json().get("text", "")
            
            # Store the transcript so the user can see/edit it in the chat input
            st.session_state["voice_draft"] = transcript
            st.session_state.last_processed_audio = audio_value
            st.rerun() # Refresh to put the text in the chat box
        except Exception as e:
            st.sidebar.error(f"Voice Error: {e}")

# --- 5. DISPLAY CHAT HISTORY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. CHAT INPUT ---
# If we have a voice transcript, we pre-fill the chat input
placeholder_text = st.session_state.get("voice_draft", "Ask about a defect...")
prompt = st.chat_input(placeholder_text)

# If the user hits enter (or voice was captured)
if prompt or ("voice_draft" in st.session_state and st.session_state.voice_draft):
    # Priority: If user typed something, use that. Otherwise use the voice draft.
    final_prompt = prompt if prompt else st.session_state.voice_draft
    
    # Clear the draft so it doesn't repeat
    if "voice_draft" in st.session_state:
        del st.session_state["voice_draft"]

    # Add to UI
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user"):
        st.markdown(final_prompt)

    # Prepare payload
    payload = {"input": final_prompt}
    
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
