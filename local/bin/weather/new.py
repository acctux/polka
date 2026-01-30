#!/usr/bin/env python3
import requests
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime
import json

# --- Localization ---
localization = {
    "en": {
        "feels_like": "Feels like",
        "wind": "Wind",
        "humidity": "Humidity",
        "today": "Today",
        "tomorrow": "Tomorrow",
        "day_after_tomorrow": "Day after tomorrow",
        "weatherDesc": "weatherDesc",
        "chanceoffog": "Fog",
        "chanceoffrost": "Frost",
        "chanceofovercast": "Overcast",
        "chanceofrain": "Rain",
        "chanceofsnow": "Snow",
        "chanceofsunshine": "Sunshine",
        "chanceofthunder": "Thunder",
        "chanceofwindy": "Wind",
    },
}

# --- Weather codes ---
WEATHER_CODES = {
    "113": "☀️",
    "116": "⛅️",
    "119": "☁️",
    "122": "☁️",
    "143": "🌫",
    "176": "🌦",
    "179": "🌧",
    "182": "🌧",
    "185": "🌧",
    "200": "⛈",
    "227": "🌨",
    "230": "❄️",
    "248": "🌫",
    "260": "🌫",
    "263": "🌦",
    "266": "🌦",
    "281": "🌧",
    "284": "🌧",
    "293": "🌦",
    "296": "🌦",
    "299": "🌧",
    "302": "🌧",
    "305": "🌧",
    "308": "🌧",
    "311": "🌧",
    "314": "🌧",
    "317": "🌧",
    "320": "🌨",
    "323": "🌨",
    "326": "🌨",
    "329": "❄️",
    "332": "❄️",
    "335": "❄️",
    "338": "❄️",
    "350": "🌧",
    "353": "🌦",
    "356": "🌧",
    "359": "🌧",
    "362": "🌧",
    "365": "🌧",
    "368": "🌨",
    "371": "❄️",
    "374": "🌧",
    "377": "🌧",
    "386": "⛈",
    "389": "🌩",
    "392": "⛈",
    "395": "❄️",
}


# --- Formatting helpers ---
def format_time(time_str: str) -> str:
    """Convert '0', '600', '1200' → '00', '06', '12'"""
    hour = int(time_str) // 100 if int(time_str) >= 100 else int(time_str)
    return str(hour).zfill(2)


def format_temp(temp: str) -> str:
    return f"{temp}°".ljust(3)


def format_chances(hour: dict, text: dict) -> str:
    chances_keys = [
        "chanceoffog",
        "chanceoffrost",
        "chanceofovercast",
        "chanceofrain",
        "chanceofsnow",
        "chanceofsunshine",
        "chanceofthunder",
        "chanceofwindy",
    ]
    probs = {
        text[key]: int(hour[key])
        for key in chances_keys
        if key in hour and hour[key].isdigit() and int(hour[key]) > 0
    }
    sorted_probs = dict(sorted(probs.items(), key=lambda item: item[1], reverse=True))
    return ", ".join(f"{event} {prob}%" for event, prob in sorted_probs.items())


# --- Fetch weather ---
def fetch_wttr_weather(location="Atlanta", lang="en"):
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {"User-Agent": "curl/7.68.0"}
    try:
        url = f"https://{lang}.wttr.in/{location}?format=j1"
        response = session.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch weather: {e}")
        return None


# --- Main function ---
def main():
    lang = "en"
    text = localization[lang]
    location = "Atlanta"
    weather = fetch_wttr_weather(location, lang)
    if weather is None:
        data = {"text": "❌", "tooltip": "Failed to fetch weather data"}
    else:
        current = weather["current_condition"][0]
        weather_desc_key = text["weatherDesc"]
        data = {
            "text": f"{WEATHER_CODES.get(current['weatherCode'], '')} {current['FeelsLikeC']}°C",
            "tooltip": "",
        }
        tooltip_lines = [
            f"<b>{current[weather_desc_key][0]['value']} {current['temp_C']}°</b>",
            f"{text['feels_like']}: {current['FeelsLikeC']}°",
            f"{text['wind']}: {current['windspeedKmph']} Km/h",
            f"{text['humidity']}: {current['humidity']}%",
        ]
        for i, day in enumerate(weather["weather"]):
            day_name = (
                text.get("today")
                if i == 0
                else text.get("tomorrow")
                if i == 1
                else text.get("day_after_tomorrow", "")
            )
            tooltip_lines.append(f"\n<b>{day_name}, {day['date']}</b>")
            tooltip_lines.append(
                f"⬆️ {day['maxtempC']}° ⬇️ {day['mintempC']}° 🌅 {day['astronomy'][0]['sunrise']} 🌇 {day['astronomy'][0]['sunset']}"
            )
            for hour in day["hourly"]:
                hour_int = int(format_time(hour["time"]))
                if i == 0 and hour_int < datetime.now().hour - 2:
                    continue
                tooltip_lines.append(
                    f"{format_time(hour['time'])} {WEATHER_CODES.get(hour['weatherCode'], '')} "
                    f"{format_temp(hour['FeelsLikeC'])} {hour[weather_desc_key][0]['value']}, "
                    f"{format_chances(hour, text)}"
                )
        data["tooltip"] = "\n".join(tooltip_lines)
    print(json.dumps(data, ensure_ascii=False))


# --- Run main ---
if __name__ == "__main__":
    main()
