# ✂️ TailorTalk – AI Appointment Booking Assistant

**TailorTalk** is a conversational AI bot that helps users check availability or book appointments using natural language. It features a `FastAPI` backend, a `Streamlit` frontend, and a custom NLP parser. It’s structured using LangGraph to manage dialogue flow, and is designed to be lightweight, testable, and extendable.

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **NLP Parsing**: Custom logic (can be swapped with LLMs)
- **LangGraph**: For managing stateful conversational flows
- **CalendarService**: Dummy calendar (can integrate with Google Calendar)
- **Environment**: Python 3.10+

---

## 📦 Features

✅ Understands intents: `check` or `book`  
✅ Extracts natural language time, date, and title  
✅ Responds with free slots or confirms a booking  
✅ Handles edge cases like missing time or unclear intent  
✅ Fully modular and customizable for real-world integrations  

---

## 📁 Project Structure

