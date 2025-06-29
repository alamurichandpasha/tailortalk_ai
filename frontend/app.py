# Frontend/app.py (Streamlit UI)

import streamlit as st
import requests

# ✅ Update with your deployed backend URL
BACKEND_URL = "https://tailortalk-ai-1.onrender.com"

st.set_page_config(page_title="TailorTalk Bot", page_icon="🧵")
st.title("✂️ TailorTalk Appointment Bot")

st.markdown("Ask something like:\n- *Book an appointment for tomorrow 3PM*\n- *Schedule a meeting next Tuesday with Alice*")

# Function to send input to backend
def send_to_backend(user_input):
    try:
        res = requests.post(f"{BACKEND_URL}/agent", json={"message": user_input})
        st.session_state['last_status'] = res.status_code
        print("📡 Status:", res.status_code, "| 📦 Raw:", res.text)
        data = res.json()
        return data.get("response", "⚠️ No response from bot.")
    except Exception as e:
        print("❌ Frontend error:", e)
        return "⚠️ Server error. Please try again later."

# Input from user
user_input = st.text_input("🗣️ You:", placeholder="E.g. Book a slot for 5PM tomorrow")

# Handle interaction on button click
if st.button("📨 Send") and user_input:
    with st.spinner("🤖 Thinking..."):
        reply = send_to_backend(user_input)
        st.markdown(f"**🤖 Bot:** {reply}")

# Optionally show backend status at bottom
if 'last_status' in st.session_state:
    st.caption(f"Backend status: {st.session_state['last_status']}")
