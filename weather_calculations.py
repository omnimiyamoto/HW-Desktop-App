from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Rating:
    status: str
    reason: str


def celsius_to_fahrenheit(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Temperature must be finite.")
    return value * 9.0 / 5.0 + 32.0


def fahrenheit_to_celsius(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Temperature must be finite.")
    return (value - 32.0) * 5.0 / 9.0


def kmh_to_mph(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Wind speed must be finite.")
    return value / 1.60934


def mph_to_kmh(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Wind speed must be finite.")
    return value * 1.60934


def crane_rating(max_wind_mph: float, limit_mph: float) -> Rating:
    if not math.isfinite(max_wind_mph) or not math.isfinite(limit_mph):
        raise ValueError("Crane wind values must be finite.")
    if limit_mph <= 0:
        raise ValueError("Crane wind limit must be positive.")
    if max_wind_mph >= limit_mph:
        return Rating("No-Go", f"{max_wind_mph:.1f} mph meets or exceeds the {limit_mph:.1f} mph limit.")
    if max_wind_mph >= 0.8 * limit_mph:
        return Rating("Caution", f"{max_wind_mph:.1f} mph is at or above the 80% caution point.")
    return Rating("Go", f"{max_wind_mph:.1f} mph is below the {0.8 * limit_mph:.1f} mph caution point.")


def concrete_rating(min_temperature_f: float, project_minimum_f: float) -> Rating:
    if not math.isfinite(min_temperature_f) or not math.isfinite(project_minimum_f):
        raise ValueError("Concrete temperatures must be finite.")
    if min_temperature_f < project_minimum_f:
        return Rating(
            "No-Go",
            f"{min_temperature_f:.1f}°F is below the {project_minimum_f:.1f}°F project minimum.",
        )
    if min_temperature_f < 40.0:
        return Rating(
            "Caution",
            f"{min_temperature_f:.1f}°F is below the 40°F cold-weather planning screen.",
        )
    return Rating("Go", f"{min_temperature_f:.1f}°F meets both concrete thresholds.")


def roofing_rating(max_precipitation: float) -> Rating:
    if not math.isfinite(max_precipitation):
        raise ValueError("Precipitation probability must be finite.")
    if max_precipitation >= 60.0:
        return Rating("No-Go", f"{max_precipitation:.0f}% precipitation probability is 60% or higher.")
    if max_precipitation >= 30.0:
        return Rating(
            "Caution",
            f"{max_precipitation:.0f}% precipitation probability is from 30% to below 60%.",
        )
    return Rating("Go", f"{max_precipitation:.0f}% precipitation probability is below 30%.")


def parse_hour(time_text: str) -> datetime:
    return datetime.fromisoformat(time_text)


def interval_minutes(start_text: str, end_text: str) -> tuple[int, int] | None:
    def parse_clock(text: str) -> int:
        parts = text.strip().upper().replace(" ", "").split(":")
        if len(parts) != 2:
            raise ValueError("Use HH:MM for start and end times.")
        hour = int(parts[0])
        minute = int(parts[1])
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("Time is outside 00:00–23:59.")
        return hour * 60 + minute

    start = parse_clock(start_text)
    end = parse_clock(end_text)
    if start == end:
        raise ValueError("Start and end times cannot be equal.")
    return start, end


def date_intervals(start_text: str, end_text: str, date_text: str) -> list[tuple[datetime, datetime]]:
    start_minute, end_minute = interval_minutes(start_text, end_text)
    date = datetime.strptime(date_text, "%Y-%m-%d")
    start = date + timedelta(minutes=start_minute)
    end = date + timedelta(minutes=end_minute)
    if end <= start:
        end += timedelta(days=1)
    return [(start, end)]


def overlapping_hour_indexes(
    forecast_times: Sequence[str],
    intervals: Sequence[tuple[str, str]],
) -> list[int]:
    if not intervals:
        return []

    parsed_intervals: list[tuple[datetime, datetime]] = []
    for start_text, end_text in intervals:
        date_text = start_text[:10]
        start_minute, end_minute = interval_minutes(start_text[11:], end_text[11:])
        start = datetime.strptime(start_text, "%Y-%m-%d %H:%M")
        end = datetime.strptime(end_text, "%Y-%m-%d %H:%M")
        parsed_intervals.append((start, end))

    indexes: list[int] = []
    for index, time_text in enumerate(forecast_times):
        hour = parse_hour(time_text)
        hour_end = hour + timedelta(hours=1)
        if any(hour < interval_end and hour_end > interval_start for interval_start, interval_end in parsed_intervals):
            indexes.append(index)
    return indexes
