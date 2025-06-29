# backend/nlp_parser.py

import re
import dateparser
from datetime import datetime, timedelta

def parse_user_input(text: str) -> dict:
    text = text.lower().strip()

    # 1) Intent detection
    intent = "book" if re.search(r"\b(book|schedule)\b", text) else "check"

    # 2) Title extraction (with X, about X)
    title = None
    m = re.search(r"(?:with|about)\s+([a-z\s]+)$", text)
    if m:
        title = m.group(1).strip().title()

    # 3) Use dateparser for date + time
    settings = {
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": datetime.now(),
    }
    dt = dateparser.parse(text, settings=settings)
    if not dt:
        # fallback to today
        dt = datetime.now()

    date_str = dt.date().isoformat()
    time_start_str = dt.strftime("%H:%M") if dt.time().hour or dt.time().minute else None

    # 4) Range detection: “3-5 pm”
    range_match = re.search(r"(\d{1,2}(?::\d{2})?)\s*[-–to]+\s*(\d{1,2}(?::\d{2})?)\s*(am|pm)?", text)
    if range_match:
        t1, t2, ampm = range_match.groups()
        t1_dt = dateparser.parse(f"{t1} {ampm or ''}", settings=settings)
        t2_dt = dateparser.parse(f"{t2} {ampm or ''}", settings=settings)
        time_start_str = t1_dt.strftime("%H:%M")
        time_end_str   = t2_dt.strftime("%H:%M")
    else:
        time_end_str = None

    # 5) If only a single time is found (and intent is book), assume 1h duration
    if intent == "book" and time_start_str and not time_end_str:
        h, m = map(int, time_start_str.split(":"))
        end_dt = dt.replace(hour=h, minute=m) + timedelta(hours=1)
        time_end_str = end_dt.strftime("%H:%M")

    return {
        "intent": intent,
        "date": date_str,
        "time_start": time_start_str,
        "time_end": time_end_str,
        "title": title
    }
