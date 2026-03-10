import streamlit as st
import requests
import base64

# --- PAGE CONFIG ---
st.set_page_config(page_title="SMT Expert System", page_icon="🔧")
st.title("🔧 SMT & Wave Expert")

# --- 1. SET THE BACKEND URL ---
BACKEND_BASE = "https://ab0d-115-242-182-162.ngrok-free.app"
TARGET_URL = "https://ab0d-115-242-182-162.ngrok-free.app/stream"  # Ensure this matches your FastAPI endpoint

# --- 2. SETUP HEADERS ---
headers = {
    "Content-Type": "application/json",
    # CRITICAL: This header bypasses the ngrok "browser warning" page
    "ngrok-skip-browser-warning": "true" 
}

# --- SIDEBAR FOR IMAGE UPLOAD ---
with st.sidebar:
    st.header("Visual Inspection")
    uploaded_file = st.file_uploader("Upload defect photo", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Defect to analyze")

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
        # Reset file pointer to beginning before reading
        uploaded_file.seek(0)
        encoded_image = base64.b64encode(uploaded_file.read()).decode('utf-8')
        payload["image"] = encoded_image

    # --- API CALL TO BACKEND ---
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Use a timeout to prevent hanging indefinitely
            with requests.post(
                TARGET_URL, 
                json=payload, 
                headers=headers, 
                stream=True,
                timeout=60 
            ) as r:
                r.raise_for_status() 
                # iter_content with decode_unicode=True is perfect for text/plain
                for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"❌ Connection Error: {e}")
            st.info("Check if your ngrok URL is still active and your FastAPI backend is running.")
