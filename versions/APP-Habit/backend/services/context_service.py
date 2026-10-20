from __future__ import annotations

from datetime import date
import requests


# ============================================================
# SAISON — DATE
# ============================================================

def get_season(current_date: date | None = None) -> str:

    if current_date is None:
        current_date = date.today()

    month = current_date.month

    if month in (3, 4, 5):
        return "printemps"

    if month in (6, 7, 8):
        return "été"

    if month in (9, 10, 11):
        return "automne"

    return "hiver"


# ============================================================
# METEO — LOCALISATION
# ============================================================

def get_weather(
    latitude: float,
    longitude: float,
) -> dict:

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "weather_code",
            "wind_speed_10m",
        ]),

        "timezone": "auto",
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()
    current = data["current"]

    return {
        "temperature": current["temperature_2m"],
        "temperature_ressentie": current["apparent_temperature"],

        "precipitations": current["precipitation"],
        "pluie": current["rain"],

        "vent": current["wind_speed_10m"],

        "weather_code": current["weather_code"],

        "timezone": data.get("timezone"),
    }


# ============================================================
# CONTEXTE COMPLET
# ============================================================

def get_context(
    latitude: float,
    longitude: float,
    current_date: date | None = None,
) -> dict:

    if current_date is None:
        current_date = date.today()

    weather = get_weather(
        latitude,
        longitude,
    )

    return {
        "date": current_date.isoformat(),

        # La saison dépend uniquement de la date.
        "saison": get_season(
            current_date
        ),

        # La météo dépend uniquement de la localisation.
        "meteo": weather,

        "localisation": {
            "latitude": latitude,
            "longitude": longitude,
        },
    }
