import os
import json
from datetime import datetime, timezone  # <-- Add timezone
from typing import TypedDict, List, Dict, Optional

from langgraph.graph import StateGraph
from backend.calendar_service import CalendarService
from backend.nlp_parser import parse_user_input
  # local NLP parser

# Define the agent state used across LangGraph nodes
class AgentState(TypedDict):
    user_text: str
    parsed: Optional[str]
    slots: Optional[List[Dict[str, str]]]
    event: Optional[Dict[str, str]]
    response: Optional[str]

# Initialize the calendar interface
cal = CalendarService()

# Step 1: Parse the user query using local NLP logic
def parse_fn(state: AgentState) -> AgentState:
    try:
        parsed = parse_user_input(state["user_text"])
        print("Parsed locally:", parsed)
        return {
            "user_text": state["user_text"],
            "parsed": json.dumps(parsed)
        }
    except Exception as e:
        print("❌ Parsing error:", e)
        return {
            "user_text": state["user_text"],
            "response": "Sorry, I couldn't understand your request."
        }

# Step 2: Check available slots in the user's time range
def avail_fn(state: AgentState) -> AgentState:
    parsed = json.loads(state["parsed"])
    date = parsed["date"]
    start = datetime.fromisoformat(f"{date}T{parsed.get('time_start') or '00:00'}").replace(tzinfo=timezone.utc)
    end   = datetime.fromisoformat(f"{date}T{parsed.get('time_end') or '23:59'}").replace(tzinfo=timezone.utc)
    slots = cal.list_free_slots(start, end)
    return {"slots": slots}

# Step 3: Book an event based on user input
def book_fn(state: AgentState) -> AgentState:
    parsed = json.loads(state["parsed"])

    if not parsed.get("time_start") or not parsed.get("time_end"):
        return {"response": "Time details missing. Please specify both start and end times."}

    date = parsed["date"]
    start = datetime.fromisoformat(f"{date}T{parsed['time_start']}").replace(tzinfo=timezone.utc)
    end   = datetime.fromisoformat(f"{date}T{parsed['time_end']}").replace(tzinfo=timezone.utc)
    title = parsed.get("title") or "Meeting"
    event = cal.create_event(start, end, title)

    print("📆 Event booked:", event)
    return {"event": event}

# Step 4: Format a human-friendly reply based on the outcome
def format_fn(state: AgentState) -> AgentState:
    parsed = json.loads(state["parsed"])
    intent = parsed.get("intent")

    if intent == "check":
        slots = state.get("slots", [])
        if not slots:
            return {"response": "Sorry, no free slots found."}
        lines = [f"- {s['start']} to {s['end']}" for s in slots]
        return {"response": "Here are your free slots:\n" + "\n".join(lines)}

    elif intent == "book":
        event = state.get("event")
        if not event:
            return {"response": "Booking failed due to incomplete information."}
        return {
            "response": f"Your meeting “{event['summary']}” is booked from {event['start']} to {event['end']}."
        }

    return {"response": "I’m not sure how to help with that."}

# Step 5: Route the flow depending on detected intent
def route_fn(state: AgentState) -> str:
    try:
        parsed = json.loads(state["parsed"])
        intent = parsed.get("intent")

        if intent == "check":
            return "check_availability"
        elif intent == "book":
            if parsed.get("time_start") and parsed.get("time_end"):
                return "book_slot"
            else:
                print("❌ Missing time info for booking. Falling back to formatter.")
    except Exception as e:
        print("❌ Route error:", e)

    return "format_response"

# Step 6: Build and wire the LangGraph
graph = StateGraph(AgentState)

graph.add_node("parse_request", parse_fn)
graph.add_node("check_availability", avail_fn)
graph.add_node("book_slot", book_fn)
graph.add_node("format_response", format_fn)

graph.set_entry_point("parse_request")

graph.add_conditional_edges("parse_request", route_fn, {
    "check_availability": "check_availability",
    "book_slot": "book_slot"
})
graph.add_edge("check_availability", "format_response")
graph.add_edge("book_slot", "format_response")

executor = graph.compile()

# Entry point callable from FastAPI
def run_agent(user_text: str) -> str:
    state = executor.invoke({"user_text": user_text})
    print("Final state:", state)
    return state.get("response", "Something went wrong.")
