import re
import dateparser
import spacy
from datetime import datetime
from typing import Optional, Dict

nlp = spacy.load("en_core_web_sm")

def extract_intent(text: str) -> str:
    t = text.lower()
    if "book" in t or "schedule" in t:
        return "book"
    if "free" in t or "available" in t:
        return "check"
    return "check"

def extract_date_time(text: str) -> Dict[str, Optional[str]]:
    # parse a date
    dp = dateparser.parse(text, settings={"PREFER_DATES_FROM": "future"})
    date = dp.date().isoformat() if dp else datetime.now().date().isoformat()

    # parse explicit time range “3-5 PM”
    times = re.findall(
        r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:-|to)\s*'
        r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
        text, re.IGNORECASE
    )
    if times:
        start = dateparser.parse(times[0][0]).strftime("%H:%M")
        end   = dateparser.parse(times[0][1]).strftime("%H:%M")
    else:
        # fallback by keyword
        t = text.lower()
        if "morning" in t:   start, end = "09:00", "12:00"
        elif "afternoon" in t:start, end = "12:00", "17:00"
        elif "evening" in t:  start, end = "17:00", "20:00"
        else:                 start, end = None, None

    return {"date": date, "time_start": start, "time_end": end}

def extract_title(text: str) -> Optional[str]:
    # look for “called X” or fallback to first noun chunk
    m = re.search(r'(?:called|titled)\s+(.+)', text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    doc = nlp(text)
    for chunk in doc.noun_chunks:
        if chunk.root.dep_ in ("dobj", "pobj"):
            return chunk.text
    return None

def parse_user_input(text: str) -> Dict[str, Optional[str]]:
    intent = extract_intent(text)
    dt     = extract_date_time(text)
    title  = extract_title(text) if intent == "book" else None
    return {
        "intent":    intent,
        "date":      dt["date"],
        "time_start":dt["time_start"],
        "time_end":  dt["time_end"],
        "title":     title,
    }
