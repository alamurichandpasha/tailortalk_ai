# Frontend/app.py (Streamlit UI)
import streamlit as st
import requests

# 🔄 USE your deployed Render backend URL here
BACKEND_URL = "https://tailortalk-backend.onrender.com"  # ✅ Change this line

st.title("✂️ TailorTalk Appointment Bot")

# Function to send input to backend
def send_to_backend(user_input):
    try:
        res = requests.post(f"{BACKEND_URL}/agent", json={"message": user_input})
        print("Status:", res.status_code, "Raw:", res.text)
        data = res.json()
        return data.get("response", "No response")
    except Exception as e:
        print("❌ Frontend error:", e)
        return "Server error. Please try again later."

# Input from user
user_input = st.text_input("You:")

# Handle interaction on button click
if st.button("Send") and user_input:
    with st.spinner("Thinking..."):
        reply = send_to_backend(user_input)
        st.markdown(f"**Bot:** {reply}")
