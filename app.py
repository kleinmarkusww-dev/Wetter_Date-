from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from flask import Flask, render_template, request

app = Flask(__name__)


@dataclass
class WeatherResult:
    location: str
    temperature: float | None
    wind_speed: float | None
    weather_code: int | None
    is_day: int | None
    error: str | None = None


WEATHER_CODE_MAP = {
    0: "Klarer Himmel",
    1: "Überwiegend klar",
    2: "Teilweise bewölkt",
    3: "Bedeckt",
    45: "Nebel",
    48: "Reif-Nebel",
    51: "Leichter Nieselregen",
    53: "Mäßiger Nieselregen",
    55: "Starker Nieselregen",
    61: "Leichter Regen",
    63: "Mäßiger Regen",
    65: "Starker Regen",
    71: "Leichter Schneefall",
    73: "Mäßiger Schneefall",
    75: "Starker Schneefall",
    80: "Leichte Regenschauer",
    81: "Mäßige Regenschauer",
    82: "Starke Regenschauer",
    95: "Gewitter",
}


def fetch_coordinates(city: str) -> dict[str, Any]:
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "de", "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("results"):
        raise ValueError("Kein Ergebnis für den Ort gefunden.")
    return data["results"][0]


def fetch_weather(lat: float, lon: float) -> dict[str, Any]:
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "timezone": "auto",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("current_weather", {})


def get_weather(city: str) -> WeatherResult:
    try:
        place = fetch_coordinates(city)
        current = fetch_weather(place["latitude"], place["longitude"])
    except (requests.RequestException, ValueError) as error:
        return WeatherResult(
            location=city,
            temperature=None,
            wind_speed=None,
            weather_code=None,
            is_day=None,
            error=str(error),
        )

    return WeatherResult(
        location=f"{place['name']}, {place.get('country', '')}".strip(", "),
        temperature=current.get("temperature"),
        wind_speed=current.get("windspeed"),
        weather_code=current.get("weathercode"),
        is_day=current.get("is_day"),
    )


@app.get("/")
def index() -> str:
    city = request.args.get("city", "Berlin")
    result = get_weather(city)
    weather_description = WEATHER_CODE_MAP.get(result.weather_code, "Unbekannt")
    greeting = "Guten Tag" if result.is_day == 1 else "Guten Abend"

    return render_template(
        "index.html",
        result=result,
        description=weather_description,
        greeting=greeting,
        timestamp=datetime.now().strftime("%d.%m.%Y %H:%M"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
