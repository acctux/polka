import json
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from pathlib import Path


def fetch_weather_response():
    _cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    _retry_session = retry(_cache_session, retries=5, backoff_factor=0.2)
    _client = openmeteo_requests.Client(session=_retry_session)

    def load_config(filename="coordinates.json"):
        script_dir = Path.home() / ".local" / "bin" / "weather"
        config_path = script_dir / filename
        with open(config_path, "r") as f:
            return json.load(f)

    config = {
        "latitude": 48.29,
        "longitude": 25.94,
        "timezone": "Europe/Kyiv",
    }
    conf = load_config()
    if not conf:
        conf = config
    LAT = conf["latitude"]
    LON = conf["longitude"]
    TZ = conf["timezone"]
    params = {
        "latitude": LAT,
        "longitude": LON,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "sunrise",
            "sunset",
            "precipitation_sum",
            "precipitation_probability_max",
        ],
        "hourly": [
            "temperature_2m",
            "dew_point_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "cloud_cover",
            "wind_speed_10m",
            "wind_direction_10m",
            "soil_temperature_0cm",
            "soil_moisture_3_to_9cm",
            "soil_moisture_9_to_27cm",
            "is_day",
        ],
        "past_days": 3,
        "timezone": TZ,
        "forecast_days": 14,
    }
    return _client.weather_api("https://api.open-meteo.com/v1/forecast", params=params)[
        0
    ]


def build_hourly_dataframe(response) -> pd.DataFrame:
    hourly = response.Hourly()
    date_index = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left",
    ).tz_convert(response.Timezone().decode())
    data = {
        "date": date_index,
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "dew_point_2m": hourly.Variables(1).ValuesAsNumpy(),
        "relative_humidity_2m": hourly.Variables(2).ValuesAsNumpy(),
        "precipitation_probability": hourly.Variables(3).ValuesAsNumpy(),
        "precipitation": hourly.Variables(4).ValuesAsNumpy(),
        "weather_code": hourly.Variables(5).ValuesAsNumpy(),
        "cloud_cover": hourly.Variables(6).ValuesAsNumpy(),
        "wind_speed_10m": hourly.Variables(7).ValuesAsNumpy(),
        "wind_direction_10m": hourly.Variables(8).ValuesAsNumpy(),
        "soil_temperature_0cm": hourly.Variables(9).ValuesAsNumpy(),
        "soil_moisture_3_to_9cm": hourly.Variables(10).ValuesAsNumpy(),
        "soil_moisture_9_to_27cm": hourly.Variables(11).ValuesAsNumpy(),
        "is_day": hourly.Variables(12).ValuesAsNumpy(),
    }
    return pd.DataFrame(data)


def build_daily_dataframe(response) -> pd.DataFrame:
    daily = response.Daily()
    date_index = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left",
    ).tz_convert(response.Timezone().decode())
    data = {
        "date": date_index,
        "weather_code": daily.Variables(0).ValuesAsNumpy(),
        "temperature_2m_max": daily.Variables(1).ValuesAsNumpy(),
        "temperature_2m_min": daily.Variables(2).ValuesAsNumpy(),
        "sunrise": daily.Variables(3).ValuesInt64AsNumpy(),
        "sunset": daily.Variables(4).ValuesInt64AsNumpy(),
        "precipitation_sum": daily.Variables(5).ValuesAsNumpy(),
        "precipitation_probability_max": daily.Variables(6).ValuesAsNumpy(),
    }
    return pd.DataFrame(data)


def load_weather_dataframes():
    response = fetch_weather_response()
    hourly_df = build_hourly_dataframe(response)
    daily_df = build_daily_dataframe(response)
    return hourly_df, daily_df
