#!/home/nick/.local/bin/weather/.venv/bin/python

import json
import pandas as pd
import requests_cache
from retry_requests import retry
import openmeteo_requests

wmo_to_info = {
    0: ("", "Clear sky"),
    1: ("", "Mainly clear"),
    2: ("", "Partly cloudy"),
    3: ("", "Overcast"),
    4: ("", "Fog"),
    5: ("", "Depositing rime fog"),
    6: ("", "Drizzle: Light"),
    7: ("", "Drizzle: Moderate"),
    8: ("", "Drizzle: Dense"),
    10: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    11: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    12: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    13: ("", "Snow fall: Slight / Moderate / Heavy"),
    14: ("", "Snow fall: Slight / Moderate / Heavy"),
    15: ("", "Snow fall: Slight / Moderate / Heavy"),
    16: ("", "Snow fall: Slight / Moderate / Heavy"),
    17: ("", "Snow grains"),
    18: ("", "Snow grains"),
    19: ("", "Snow grains"),
    20: ("", "Rain showers: Slight / Moderate / Violent"),
    21: ("", "Thunderstorm: Slight or moderate"),
    22: ("", "Snow showers: Slight / Heavy"),
    23: ("", "Unknown / Other"),
    24: ("", "Unknown / Other"),
    25: ("", "Rain showers: Slight / Moderate / Violent"),
    26: ("", "Rain showers: Slight / Moderate / Violent"),
    27: ("", "Rain showers: Slight / Moderate / Violent"),
    28: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    29: ("", "Snow grains"),
    30: ("", "Fog"),
    31: ("", "Fog"),
    32: ("", "Fog"),
    33: ("", "Fog"),
    34: ("", "Fog"),
    35: ("", "Fog"),
    36: ("", "Snow showers: Slight / Heavy"),
    37: ("", "Snow showers: Slight / Heavy"),
    38: ("", "Snow showers: Slight / Heavy"),
    39: ("", "Snow showers: Slight / Heavy"),
    40: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    41: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    42: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    43: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    44: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    45: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    46: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    47: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    48: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
    49: ("", "Rain: Slight / Moderate / Heavy / Freezing Rain / Rain showers"),
}


def get_icon(code: float) -> str:
    return wmo_to_info.get(int(code), ("", "Unknown / Other"))[0]


cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)  # type: ignore
params = {
    "latitude": 34.1751,
    "longitude": -82.024,
    "daily": [
        "weather_code",
        "sunrise",
        "sunset",
        "precipitation_sum",
        "precipitation_probability_max",
        "apparent_temperature_max",
        "apparent_temperature_min",
    ],
    "hourly": [
        "temperature_2m",
        "precipitation_probability",
        "precipitation",
        "weather_code",
        "apparent_temperature",
    ],
    "current": ["temperature_2m", "precipitation", "weather_code"],
    "timezone": "America/New_York",
    "timeformat": "unixtime",
    "temperature_unit": "fahrenheit",
    "precipitation_unit": "inch",
}
response = openmeteo.weather_api(
    "https://api.open-meteo.com/v1/forecast", params=params
)[0]
daily = response.Daily()
daily_data = pd.DataFrame(
    {
        "date": pd.date_range(
            start=pd.to_datetime(
                daily.Time() + response.UtcOffsetSeconds(), unit="s", utc=True
            ),
            end=pd.to_datetime(
                daily.TimeEnd() + response.UtcOffsetSeconds(), unit="s", utc=True
            ),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left",
        ),
        "weather_code": daily.Variables(0).ValuesAsNumpy(),
        "sunrise": daily.Variables(1).ValuesInt64AsNumpy(),
        "sunset": daily.Variables(2).ValuesInt64AsNumpy(),
        "precipitation_sum": daily.Variables(3).ValuesAsNumpy(),
        "precipitation_probability_max": daily.Variables(4).ValuesAsNumpy(),
        "apparent_temperature_max": daily.Variables(5).ValuesAsNumpy(),
        "apparent_temperature_min": daily.Variables(6).ValuesAsNumpy(),
    }
)
daily_data["weather_icon"] = daily_data["weather_code"].apply(get_icon)
hourly = response.Hourly()
hourly_data = pd.DataFrame(
    {
        "date": pd.date_range(
            start=pd.to_datetime(
                hourly.Time() + response.UtcOffsetSeconds(), unit="s", utc=True
            ),
            end=pd.to_datetime(
                hourly.TimeEnd() + response.UtcOffsetSeconds(), unit="s", utc=True
            ),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        ),
        "weather_code": hourly.Variables(3).ValuesAsNumpy(),
    }
)
hourly_data["weather_icon"] = hourly_data["weather_code"].apply(get_icon)
tooltip_lines = [
    f"{row['weather_icon']} {row['apparent_temperature_max']:.0f}/{row['apparent_temperature_min']:.0f}°F, "
    f"{int(row['precipitation_probability_max'])}%, {row['precipitation_sum']:.2f} in\t"
    for _, row in daily_data.iterrows()
]


def get_class_grouped(code: float) -> str:
    code = int(code)

    if code in (0, 1):
        return "clear"

    if code in (2, 3):
        return "cloudy"

    if code in (45, 48) or (40 <= code <= 49):
        return "fog"

    if (51 <= code <= 55) or (61 <= code <= 65) or (80 <= code <= 82):
        return "rain"

    if (71 <= code <= 75) or (85 <= code <= 86):
        return "snow"

    if code >= 95:
        return "thunder"

    if code in (23, 24, 25, 26, 27):
        return "mixed"

    return "unknown"


tooltip_text = "\n".join(tooltip_lines)
waybar_output = {
    "text": hourly_data.at[0, "weather_icon"],  # icon
    "class": get_class_grouped(hourly_data.at[0, "weather_code"]),  # CSS class
    "tooltip": tooltip_text,
}
print(json.dumps(waybar_output, ensure_ascii=False))
