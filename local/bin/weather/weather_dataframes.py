import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 34.106,
    "longitude": -82.025,
    "daily": [
        "weather_code",
        "sunrise",
        "sunset",
        "uv_index_max",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "precipitation_probability_max",
        "cloud_cover_mean",
        "wind_speed_10m_max",
    ],
    "hourly": [
        "temperature_2m",
        "precipitation_probability",
        "precipitation",
        "weather_code",
        "is_day",
        "soil_moisture_3_to_9cm",
        "soil_moisture_9_to_27cm",
        "soil_temperature_0cm",
        "wind_speed_10m",
        "wind_direction_10m",
        "relative_humidity_2m",
        "apparent_temperature",
        "dew_point_2m",
    ],
    "timezone": "America/New_York",
    "forecast_days": 14,
}
responses = openmeteo.weather_api(url, params=params)
response = responses[0]
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
hourly_weather_code = hourly.Variables(3).ValuesAsNumpy()
hourly_is_day = hourly.Variables(4).ValuesAsNumpy()
hourly_soil_moisture_3_to_9cm = hourly.Variables(5).ValuesAsNumpy()
hourly_soil_moisture_9_to_27cm = hourly.Variables(6).ValuesAsNumpy()
hourly_soil_temperature_0cm = hourly.Variables(7).ValuesAsNumpy()
hourly_wind_speed_10m = hourly.Variables(8).ValuesAsNumpy()
hourly_wind_direction_10m = hourly.Variables(9).ValuesAsNumpy()
hourly_relative_humidity_2m = hourly.Variables(10).ValuesAsNumpy()
hourly_apparent_temperature = hourly.Variables(11).ValuesAsNumpy()
hourly_dew_point_2m = hourly.Variables(12).ValuesAsNumpy()
hourly_data = {
    "date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left",
    ).tz_convert(response.Timezone().decode())
}
hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["precipitation_probability"] = hourly_precipitation_probability
hourly_data["precipitation"] = hourly_precipitation
hourly_data["weather_code"] = hourly_weather_code
hourly_data["is_day"] = hourly_is_day
hourly_data["soil_moisture_3_to_9cm"] = hourly_soil_moisture_3_to_9cm
hourly_data["soil_moisture_9_to_27cm"] = hourly_soil_moisture_9_to_27cm
hourly_data["soil_temperature_0cm"] = hourly_soil_temperature_0cm
hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
hourly_data["wind_direction_10m"] = hourly_wind_direction_10m
hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
hourly_data["apparent_temperature"] = hourly_apparent_temperature
hourly_data["dew_point_2m"] = hourly_dew_point_2m
hourly_dataframe = pd.DataFrame(data=hourly_data)
daily = response.Daily()
daily_weather_code = daily.Variables(0).ValuesAsNumpy()
daily_sunrise = daily.Variables(1).ValuesInt64AsNumpy()
daily_sunset = daily.Variables(2).ValuesInt64AsNumpy()
daily_uv_index_max = daily.Variables(3).ValuesAsNumpy()
daily_temperature_2m_max = daily.Variables(4).ValuesAsNumpy()
daily_temperature_2m_min = daily.Variables(5).ValuesAsNumpy()
daily_precipitation_sum = daily.Variables(6).ValuesAsNumpy()
daily_precipitation_probability_max = daily.Variables(7).ValuesAsNumpy()
daily_cloud_cover_mean = daily.Variables(8).ValuesAsNumpy()
daily_wind_speed_10m_max = daily.Variables(9).ValuesAsNumpy()
daily_data = {
    "date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left",
    ).tz_convert(response.Timezone().decode())
}
daily_data["weather_code"] = daily_weather_code
daily_data["sunrise"] = daily_sunrise
daily_data["sunset"] = daily_sunset
daily_data["uv_index_max"] = daily_uv_index_max
daily_data["temperature_2m_max"] = daily_temperature_2m_max
daily_data["temperature_2m_min"] = daily_temperature_2m_min
daily_data["precipitation_sum"] = daily_precipitation_sum
daily_data["precipitation_probability_max"] = daily_precipitation_probability_max
daily_data["cloud_cover_mean"] = daily_cloud_cover_mean
daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
daily_dataframe = pd.DataFrame(data=daily_data)
