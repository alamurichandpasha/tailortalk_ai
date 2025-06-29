# backend/nlp_parser.py

import re
import json
import dateparser
import spacy
from datetime import datetime
from typing import Optional, Dict

# Load spaCy English model once
nlp = spacy.load("en_core_web_sm")

def extract_intent(text: str) -> str:
    t = text.lower()
    if re.search(r"\b(book|schedule)\b", t):
        return "book"
    if re.search(r"\b(free|available|open)\b", t):
        return "check"
    return "check"

def extract_date_time(text: str) -> Dict[str, Optional[str]]:
    """
    Returns:
      - date: "YYYY-MM-DD"
      - time_start: "HH:MM" or None
      - time_end:   "HH:MM" or None
    """
    settings = {
        "PREFER_DATES_FROM": "future",
        "RETURN_AS_TIMEZONE_AWARE": False
    }
    # 1) Try to parse a date + time
    dt = dateparser.parse(text, settings=settings)
    if not dt:
        dt = datetime.now()

    date_str = dt.date().isoformat()

    # 2) Look for explicit time range "3-5 PM" or "3 to 5pm"
    range_match = re.search(
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:-|to)\s*"
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
        text, re.IGNORECASE
    )
    if range_match:
        t1, t2 = range_match.groups()
        dt1 = dateparser.parse(t1, settings=settings)
        dt2 = dateparser.parse(t2, settings=settings)
        return {
            "date": date_str,
            "time_start": dt1.strftime("%H:%M"),
            "time_end":   dt2.strftime("%H:%M")
        }

    # 3) Single time "3PM" or "15:00"
    time_match = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", text, re.IGNORECASE)
    if time_match:
        dt_time = dateparser.parse(time_match.group(1), settings=settings)
        time_str = dt_time.strftime("%H:%M")
        return {"date": date_str, "time_start": time_str, "time_end": None}

    # 4) Fallback by keywords: morning/afternoon/evening
    t = text.lower()
    if "morning" in t:
        return {"date": date_str, "time_start": "09:00", "time_end": "12:00"}
    if "afternoon" in t:
        return {"date": date_str, "time_start": "12:00", "time_end": "17:00"}
    if "evening" in t:
        return {"date": date_str, "time_start": "17:00", "time_end": "20:00"}

    # 5) No time specified
    return {"date": date_str, "time_start": None, "time_end": None}

def extract_title(text: str) -> Optional[str]:
    """
    Tries to extract a meeting title:
      - phrases like "with Alice"
      - "called X" / "titled X"
      - fallback: first spaCy noun chunk acting as object
    """
    # 1) Explicit "with X" / "about X"
    m = re.search(r"(?:with|about)\s+(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip().title()

    # 2) "called X" / "titled X"
    m2 = re.search(r"(?:called|titled)\s+(.+)", text, re.IGNORECASE)
    if m2:
        return m2.group(1).strip().title()

    # 3) spaCy noun-chunk fallback
    doc = nlp(text)
    for chunk in doc.noun_chunks:
        if chunk.root.dep_ in ("dobj", "pobj", "nsubj"):
            return chunk.text.title()

    return None

def parse_user_input(text: str) -> Dict[str, Optional[str]]:
    """
    Main parser entrypoint.
    Returns a dictionary:
      {
        "intent": "check" or "book",
        "date": "YYYY-MM-DD",
        "time_start": "HH:MM" or None,
        "time_end": "HH:MM" or None,
        "title": string or None
      }
    """
    intent = extract_intent(text)
    dt     = extract_date_time(text)
    title  = extract_title(text) if intent == "book" else None

    # Log for debugging
    print("📝 Parsed Input:", {"intent": intent, **dt, "title": title})

    return {
        "intent":     intent,
        "date":       dt["date"],
        "time_start": dt["time_start"],
        "time_end":   dt["time_end"],
        "title":      title,
    }
