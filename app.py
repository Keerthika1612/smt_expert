import streamlit as st
import requests
import base64

# --- PAGE CONFIG ---
st.set_page_config(page_title="SMT Expert System", page_icon="🔧")
st.title("🔧 SMT & Wave Expert")

# --- 1. DYNAMIC CONFIGURATION ---
with st.sidebar:
    st.header("🔗 Backend Connection")
    # This allows your friend to paste the new link you give them
    ngrok_url = st.text_input(
        "Enter Active ngrok URL:", 
        placeholder="https://87fb-106-208-32-20.ngrok-free.app",
        help="Paste the forwarding URL from the ngrok terminal here."
    )
    
    st.divider()
    st.header("📸 Visual Inspection")
    uploaded_file = st.file_uploader("Upload defect photo", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Defect to analyze")

# --- 2. VALIDATION ---
# If the URL is missing, stop the app and show a friendly message
if not ngrok_url:
    st.info("👋 Welcome! To begin, please paste the active **ngrok URL** provided by the technician in the sidebar.")
    st.stop()

# Ensure the URL doesn't end with a slash to prevent double slashes
base_url = ngrok_url.strip().rstrip("/")
TARGET_URL = f"{base_url}/stream"

# --- SETUP HEADERS ---
headers = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true" 
}

# --- INITIALIZE CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- DISPLAY CHAT HISTORY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- CHAT INPUT ---
if prompt := st.chat_input("Ask about a defect..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- PREPARE PAYLOAD ---
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
                TARGET_URL, 
                json=payload, 
                headers=headers, 
                stream=True,
                timeout=90 # Increased timeout for cloud-to-local latency
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
            st.warning("Ensure the ngrok URL is correct and the backend is running on the technician's laptop.")
