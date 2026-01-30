import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    95: "Thunderstorm",
}

cache = requests_cache.CachedSession(".cache", expire_after=3600)
session = retry(cache, retries=5, backoff_factor=0.2)
client = openmeteo_requests.Client(session=session)  # type: ignore

params = {
    "latitude": 34.17,
    "longitude": 82.02,
    "daily": [
        "weather_code",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "precipitation_probability_max",
        "precipitation_sum",
    ],
    "temperature_unit": "fahrenheit",
    "precipitation_unit": "inch",
    "timeformat": "unixtime",
}

response = client.weather_api("https://api.open-meteo.com/v1/forecast", params)[0]
daily = response.Daily()

# Build DataFrame
daily_df = pd.DataFrame(
    {
        "conditions": pd.Series(daily.Variables(0).ValuesAsNumpy().astype(int)).map(
            WEATHER_CODE_MAP
        ),
        "high_f": daily.Variables(1).ValuesAsNumpy(),
        "low_f": daily.Variables(2).ValuesAsNumpy(),
        "precip_prob_pct": daily.Variables(3).ValuesAsNumpy(),
        "precip_total_in": daily.Variables(4).ValuesAsNumpy(),
    }
).round(
    {
        "high_f": 1,
        "low_f": 1,
        "precip_prob_pct": 0,
        "precip_total_in": 2,
    }
)

# Convert DataFrame to Python-native types to avoid excessive precision
daily_records = daily_df.head(3).to_dict(orient="records")
for day in daily_records:
    day["high_f"] = float(day["high_f"])
    day["low_f"] = float(day["low_f"])
    day["precip_total_in"] = float(day["precip_total_in"])
    day["precip_prob_pct"] = int(day["precip_prob_pct"])

tooltip_lines = []
for i, day in enumerate(daily_records, start=1):
    line = (
        f"Day {i}: {day['conditions']}, "
        f"High {day['high_f']:.1f}°F, Low {day['low_f']:.1f}°F, "
        f"Precip {day['precip_prob_pct']}% ({day['precip_total_in']:.2f} in)"
    )
    tooltip_lines.append(line)
tooltip_text = "\n".join(tooltip_lines)

print(tooltip_text)

