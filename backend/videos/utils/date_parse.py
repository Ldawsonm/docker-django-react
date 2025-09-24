import re
from datetime import datetime
from django.utils import timezone


DATE_RE = re.compile(
    r"(?:[A-Za-z]+,\s*)?"           # optional weekday like "Tuesday, "
    r"([A-Za-z]+)\s+"               # month name or abbr (captured)
    r"(\d{1,2})(?:st|nd|rd|th)?\s*" # day number with optional suffix
    r",?\s*"                        # optional comma
    r"(\d{4})"                      # year
)

def parse_date_from_title(title: str) -> datetime | None:
    # Normalize any weird spaces (NBSP)
    title = title.replace("\xa0", " ")
    m = DATE_RE.search(title)
    if not m:
        return None

    month_raw, day, year = m.groups()
    # Strip trailing dot on abbreviations (e.g., "Sept.")
    month = month_raw.rstrip(".")

    # Try full month first (September), then abbreviated (Sep)
    for fmt in ("%B %d %Y", "%b %d %Y"):
        try:
            return timezone.make_aware(datetime.strptime(f"{month} {day} {year}", fmt))
        except ValueError:
            continue
    return None

def parse_date_with_suffix(text: str):
    # Remove weekday if present
    text = re.sub(r"^[A-Za-z]+,\s+", "", text)  # drop "Thursday, "
    # Remove suffixes like "st", "nd", "rd", "th"
    text = re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", text)
    try:
        return datetime.strptime(text.strip(), "%B %d, %Y")
    except ValueError:
        return None