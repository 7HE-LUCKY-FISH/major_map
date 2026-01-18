from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

SEM_ORDER = {"Spring": 0, "Fall": 1}

@dataclass(frozen=True)
class SemesterIndexConfig:
    base: int  # min(year*2 + sem_order) from training data

def compute_semester_index(year: int, semester: str, cfg: SemesterIndexConfig) -> int:
    return (int(year) * 2 + SEM_ORDER.get(semester, 0)) - cfg.base

def parse_time_range(s: str) -> tuple[int, int, int]:
    s = str(s).strip()
    if s == "TBA" or "-" not in s:
        return -1, -1, -1
    start_str, end_str = s.split("-")

    start_dt = pd.to_datetime(start_str, format="%I:%M%p", errors="coerce")
    end_dt = pd.to_datetime(end_str, format="%I:%M%p", errors="coerce")
    if pd.isna(start_dt) or pd.isna(end_dt):
        return -1, -1, -1

    start_min = start_dt.hour * 60 + start_dt.minute
    end_min = end_dt.hour * 60 + end_dt.minute
    return start_min, end_min, end_min - start_min

def get_building(location: str) -> str:
    location = str(location).strip()
    if location in {"ONLINE", "Unknown"}:
        return location
    prefix = ""
    for ch in location:
        if ch.isalpha():
            prefix += ch
        else:
            break
    return prefix or "Unknown"

def section_to_course_code(section: str) -> tuple[str, str]:
    section = str(section).strip()
    extracted = pd.Series(section).str.extract(r"^(\w+)\s+([^\s]+)").iloc[0]
    dept = extracted[0] if pd.notna(extracted[0]) else "Unknown"
    num = extracted[1] if pd.notna(extracted[1]) else "Unknown"
    return dept, f"{dept} {num}"

def make_slot(days: str, start_minutes: int) -> str:
    days = str(days).strip()
    if start_minutes == -1:
        return f"{days}_TBA"
    return f"{days}_{int(start_minutes)}"

def has_ge(satifies: str) -> int:
    return int(str(satifies).startswith("GE:"))

