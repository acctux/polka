#!/usr/bin/env python3
import argparse
import json
import pandas as pd
from pathlib import Path
from zoneinfo import ZoneInfo
from dataclasses import dataclass
import openmeteo_requests
import requests_cache
from retry_requests import retry

WEATHER_ICONS = {
    0: ("clear", "", ""),
    1: ("Clouds dissolving", "", "󰼱"),
    2: ("Sky unchanged", "󰖕", "󰼱"),
    3: ("Clouds forming", "󰖐", "󰖐"),
    4: ("Smoke", "", ""),
    5: ("Haze", "", ""),
    6: ("Dust", "", ""),
    10: ("Mist", "", ""),
    11: ("Patches", "", ""),
    13: ("Lightning, no thunder", "󰼲", ""),
    14: ("Precipitation in sight", "", ""),
    20: ("Drizzel", "", ""),
    21: ("Rain not freezing", "", ""),
    22: ("Snow", "󰼶", ""),
    23: ("Rain, or snow, or ice pellets", "󰙿", "󰙿"),
    25: ("Showers of rain", "󰖗", "󰖗"),
    26: ("Shower(s) of snow, or of rain and snow", "󰙿", "󰙿"),
    28: ("fog", "󰖑", "󰖑"),
    29: ("Thunderstorm", "", ""),
    30: ("Dust/sandstorms", "", ""),
    33: ("Severe dust/sandstorms", "", ""),
    36: ("Slight or moderate blowing snow", "", ""),
    37: ("Heavy drifting snow", "", ""),
    38: ("Slight or moderate blowing snow(above eye level)", "", ""),
    39: ("Heavy drifting snow(above eye level)", "", ""),
    40: ("fog", "", ""),
    41: ("Fog or ice fog in patches", "", ""),
    42: ("Fog or ice fog, sky visible", "", ""),
    43: ("Fog or ice fog, sky invisible", "", ""),
    44: ("Fog or ice fog, sky visible", "", ""),
    45: ("Fog or ice fog, sky invisible", "", ""),
    46: ("Fog or ice fog, sky visible", "", ""),
    47: ("Fog or ice fog, sky invisible", "", ""),
    50: ("Drizzle, not freezing, intermittent)", "", ""),
    51: ("Drizzle, not freezing, continuous", "", ""),
    52: ("Drizzle, not freezing, intermittent)", "", ""),
    53: ("Drizzle, not freezing, continuous", "", ""),
    54: ("Drizzle, not freezing, intermittent (heavy)", "", ""),
    55: ("Drizzle, not freezing, continuous", "", ""),
    56: ("Drizzle, freezing, slight", "", ""),
    57: ("Drizzle, freezing, moderate or heavy (dense)", "", ""),
    58: ("Drizzle and rain, slight", "", ""),
    59: ("Drizzle and rain, moderate or heavy", "", ""),
    60: ("Rain, not freezing, intermittent (slight)", "󰖗", ""),
    61: ("Rain, not freezing, continuous", "󰖗", ""),
    62: ("Rain, not freezing, intermittent (moderate)", "󰖗", ""),
    63: ("Rain, not freezing, continuous", "󰖗", ""),
    64: ("Rain, not freezing, intermittent (heavy)", "󰖗", ""),
    65: ("Rain, not freezing, continuous", "󰖗", ""),
    66: ("Rain, freezing, slight", "󰖗", ""),
    67: ("Rain, freezing, moderate or heavy (dense)", "󰖗", ""),
    68: ("Rain or drizzle and snow, slight", "󰖗", ""),
    69: ("Rain or drizzle and snow, moderate or heavy", "󰖗", ""),
    70: ("Intermittent fall of snowflakes (slight)", "󰖗", ""),
    71: ("Continuous fall of snowflakes", "󰖗", ""),
    72: ("Intermittent fall of snowflakes (moderate)", "󰖗", ""),
    73: ("Continuous fall of snowflakes", "󰖗", ""),
    74: ("Intermittent fall of snowflakes (heavy)", "󰖗", ""),
    75: ("Continuous fall of snowflakes", "󰖗", ""),
    76: ("Diamond dust (with or without fog)", "󰖗", ""),
    77: ("Snow grains (with or without fog)", "󰖗", ""),
    78: ("Isolated snow crystals (with/without fog)", "󰖗", ""),
    79: ("Ice pellets", "󰖗", ""),
    80: ("rain_showers", "󰖖", ""),
    81: ("rain_showers", "󰖖", ""),
    82: ("rain_showers", "󰖖", ""),
    85: ("snow_showers", "󰖘", ""),
    86: ("snow_showers", "󰖘", ""),
    87: ("rain_showers", "󰖖", ""),
    95: ("thunderstorm", "󰖓", ""),
    96: ("thunderstorm_hail", "", ""),
    99: ("thunderstorm_hail", "󰖒", ""),
}
FALLBACK_ICON = ("unknown", "", "")
LATITUDE = 34.1751
LONGITUDE = -82.024
HOURLY_STEP = 2
TIMEZONE = "America/New_York"
# METRIC = True
CACHE_FILE = Path(".metric_cache")


def open_meteo(lat, lon):
    def create_retry_session():
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        return retry_session

    def df_daily(response):
        daily = response.Daily()
        daily_weather_code = daily.Variables(0).ValuesAsNumpy()
        daily_precipitation_sum = daily.Variables(1).ValuesAsNumpy()
        daily_sunrise = daily.Variables(2).ValuesInt64AsNumpy()
        daily_sunset = daily.Variables(3).ValuesInt64AsNumpy()
        daily_temperature_2m_max = daily.Variables(4).ValuesAsNumpy()
        daily_temperature_2m_min = daily.Variables(5).ValuesAsNumpy()
        daily_precipitation_probability_max = daily.Variables(6).ValuesAsNumpy()
        daily_data = {
            "date": pd.date_range(
                start=pd.to_datetime(
                    daily.Time() + response.UtcOffsetSeconds(), unit="s", utc=True
                ),
                end=pd.to_datetime(
                    daily.TimeEnd() + response.UtcOffsetSeconds(), unit="s", utc=True
                ),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left",
            )
        }
        daily_data["weather_code"] = daily_weather_code
        daily_data["precipitation_sum"] = daily_precipitation_sum
        daily_data["sunrise"] = daily_sunrise
        daily_data["sunset"] = daily_sunset
        daily_data["temperature_2m_max"] = daily_temperature_2m_max
        daily_data["temperature_2m_min"] = daily_temperature_2m_min
        daily_data["precipitation_probability_max"] = (
            daily_precipitation_probability_max
        )
        return pd.DataFrame(data=daily_data)

    def df_hourly(response):
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
        hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
        hourly_weather_code = hourly.Variables(3).ValuesAsNumpy()
        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(
                    hourly.Time() + response.UtcOffsetSeconds(), unit="s", utc=True
                ),
                end=pd.to_datetime(
                    hourly.TimeEnd() + response.UtcOffsetSeconds(), unit="s", utc=True
                ),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )
        }
        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["precipitation_probability"] = hourly_precipitation_probability
        hourly_data["precipitation"] = hourly_precipitation
        hourly_data["weather_code"] = hourly_weather_code
        return pd.DataFrame(data=hourly_data)

    session = create_retry_session()
    openmeteo = openmeteo_requests.Client(session)
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "weather_code",
            "precipitation_sum",
            "sunrise",
            "sunset",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
        ],
        "hourly": [
            "temperature_2m",
            "precipitation_probability",
            "precipitation",
            "weather_code",
        ],
        "timezone": "America/New_York",
        "wind_speed_unit": "mph",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
    }

    def fetch_weather(lat, lon):
        responses = openmeteo.weather_api(
            "https://api.open-meteo.com/v1/forecast", params=params
        )
        response = responses[0]
        daily_df = df_daily(response)
        hourly_df = df_hourly(response)
        return daily_df, hourly_df

    daily_df, hourly_df = fetch_weather(lat, lon)
    return daily_df, hourly_df


def add_daytime_flag(
    hourly_df: pd.DataFrame, daily_df: pd.DataFrame, tz: str, step: int, metric
) -> pd.DataFrame:
    def is_daytime(row):
        return row["sunrise"] <= row["date"] < row["sunset"]

    def get_sun_string(current_time, sun_time, window_hours):
        if pd.isna(sun_time):
            return ""
        window_end = current_time + pd.Timedelta(hours=window_hours)
        if current_time <= sun_time < window_end:
            return sun_time.strftime("%H:%M")
        return ""

    daily_df["sunrise"] = pd.to_datetime(
        daily_df["sunrise"], unit="s", utc=True
    ).dt.tz_convert(ZoneInfo(tz))
    daily_df["sunset"] = pd.to_datetime(
        daily_df["sunset"], unit="s", utc=True
    ).dt.tz_convert(ZoneInfo(tz))
    hourly_df["local_date"] = hourly_df["date"].dt.tz_convert(tz).dt.date
    sun_times = daily_df.set_index(daily_df["date"].dt.date)[["sunrise", "sunset"]]
    hourly_df = hourly_df.merge(
        sun_times, left_on="local_date", right_index=True, how="left"
    )
    hourly_df["is_day"] = hourly_df.apply(is_daytime, axis=1)
    hourly_df["sunrise_str"] = hourly_df.apply(
        lambda r: get_sun_string(r["date"], r["sunrise"], step), axis=1
    )
    hourly_df["sunset_str"] = hourly_df.apply(
        lambda r: get_sun_string(r["date"], r["sunset"], step), axis=1
    )
    units = "in"
    if metric:
        units = "cm"
        hourly_df["temperature_2m"] = (hourly_df["temperature_2m"] - 32) * 5 / 9
        daily_df["temperature_2m_max"] = (daily_df["temperature_2m_max"] - 32) * 5 / 9
        daily_df["temperature_2m_min"] = (daily_df["temperature_2m_min"] - 32) * 5 / 9
        hourly_df["precipitation"] = hourly_df["precipitation"] * 2.54
        daily_df["precipitation_sum"] = daily_df["precipitation_sum"] * 2.54
    hourly_df["units"] = units
    daily_df["units"] = units
    return hourly_df


def map_icons(
    df: pd.DataFrame,
    is_hourly: bool = False,
    weather_icons=WEATHER_ICONS,
    fallback_icon=FALLBACK_ICON,
) -> pd.DataFrame:
    def pick_icon_and_description(row):
        weather_code = int(row["weather_code"])
        _, night_icon, day_icon = weather_icons.get(weather_code, fallback_icon)
        description = weather_icons.get(weather_code, fallback_icon)[0]
        if is_hourly and not row.get("is_day", True):
            return day_icon, description
        return night_icon, description

    df[["icon", "description"]] = df.apply(
        pick_icon_and_description, axis=1, result_type="expand"
    )
    return df


@dataclass
class WeatherEntry:
    label: str
    icon: str
    temp: float
    units: str
    units_in_cm: str
    sunset_str: str | None = None
    sunrise_str: str | None = None
    temp_low: float | None = None
    precip_prob: int = 0
    precipitation: float = 0.0

    def format(self) -> str:
        today = pd.Timestamp.now().strftime("%m-%d")
        label = self.label
        if self.label == today:
            label = "Today"
        precip_prob = f"{self.precip_prob}%" if self.precip_prob > 0 else ""

        precip_sum = ""
        if 0.01 <= self.precipitation < 0.1:
            if round(self.precipitation, 2) == 0.1:
                precip = f"{round(self.precipitation, 1)}"
                precip_sum = f"({precip}{self.units_in_cm})"
            else:
                precip = f"{round(self.precipitation, 2)}".lstrip("0")
                precip_sum = f"({precip}{self.units_in_cm})"
        elif 0.1 < self.precipitation:
            precip = f"{round(self.precipitation, 1)}"
            precip_sum = f"({precip}{self.units_in_cm})"

        temp_low = ""
        if self.temp_low:
            temp_low = round(self.temp_low)
            if self.temp_low > 0.01:
                temp_low = round(self.temp_low)
        daily_temp = f"{round(self.temp)}/{temp_low}"

        sun_icon = ""
        sun_time = ""
        if self.sunrise_str:
            sun_icon = "󰖜"
            sun_time = f"{self.sunrise_str}"
        if self.sunset_str:
            sun_icon = "󰖛"
            sun_time = f"{self.sunset_str}".rjust(4)

        rain_icon = "󰖌" if self.precip_prob > 0 else ""

        is_hourly = ":" in self.label
        if is_hourly:
            return (
                f"{self.label:<5}"
                f"<span size='21pt'>{self.icon.rjust(2)}</span>"
                f"{str(round(self.temp)).rjust(5)}<span size='17pt'></span>{self.units}"
                f"<span size='14pt'>{rain_icon.rjust(3)}</span>{precip_prob.rjust(4)}{precip_sum.rjust(7)}"
                f"<span size='20pt'>{sun_icon.rjust(2)} </span>{sun_time.rjust(4)}"
            )
        else:
            rain_icon = rain_icon.rjust(4)
            return (
                f"{label:<5}"
                f"<span size='23pt'>{self.icon.rjust(2)}</span>"
                f"{daily_temp.rjust(8)}<span size='17pt'></span>{self.units}"
                f"<span size='14pt'>{rain_icon.rjust(6)}</span>{precip_prob.rjust(5)}{precip_sum.rjust(9)}"
            )


def today_formatted() -> str:
    t = pd.Timestamp.now()
    day_suffix = {1: "st", 2: "nd", 3: "rd"}.get(t.day % 10, "th")
    if 10 <= t.day % 100 <= 20:
        day_suffix = "th"
    return t.strftime(f"%a, %b {t.day}{day_suffix}, %Y")


def build_tooltip(daily_df, hourly_df, my_zone: str, celsius, hourly_step=2):
    def proc_entries(entries):
        return "\n".join([entry.format() for entry in entries])

    unit_str = "C" if celsius else "F"
    t = pd.Timestamp.now(ZoneInfo(my_zone))
    current_time = t.replace(minute=0, second=0, microsecond=0)
    time_24h_later = current_time + pd.Timedelta(hours=24)  # 24 hours later
    current_time_str = t.strftime("%H:%M")
    hourly_df["date"] = hourly_df["date"].dt.tz_convert(ZoneInfo(my_zone))
    hourly_entries = [
        WeatherEntry(
            label=row["date"].strftime("%H:%M"),
            icon=row["icon"],
            temp=row["temperature_2m"],
            sunrise_str=row["sunrise_str"],
            sunset_str=row["sunset_str"],
            units=unit_str,
            units_in_cm=row["units"],
            precip_prob=int(row.get("precipitation_probability", 0)),
            precipitation=row.get("precipitation", 0.0),
        )
        for i, (_, row) in enumerate(hourly_df.iterrows())
        if current_time <= row["date"] < time_24h_later
        and (row["date"].hour - current_time.hour) % hourly_step == 0
    ]
    daily_entries = [
        WeatherEntry(
            label=row["date"].strftime("%m-%d"),
            icon=row["icon"],
            units_in_cm=row["units"],
            temp=row["temperature_2m_max"],
            temp_low=row["temperature_2m_min"],
            units=unit_str,
            precip_prob=int(row.get("precipitation_probability_max", 0)),
            precipitation=row.get("precipitation_sum", 0.0),
        )
        for _, row in daily_df.iterrows()
    ]
    formatted_date = today_formatted()
    icon_size = 20
    return (
        f"<span size='{icon_size}pt'>󰨳</span><span size='13pt'>  {formatted_date}</span>\n"
        "─────────────────────────────────────────\n"
        + f"{proc_entries(daily_entries)}\n"
        + f"\n<span size='{icon_size}pt'></span><span size='13pt'>  {current_time_str}</span>\n"
        "─────────────────────────────────────────\n"
        + f"{proc_entries(hourly_entries)}"
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Weather script settings.")
    parser.add_argument(
        "--metric",
        action="store_true",
        help="Use metric units (Celsius, cm, etc.)",
    )
    args = parser.parse_args()
    if args.metric:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
            METRIC = False
        else:
            with CACHE_FILE.open("w") as file:
                file.write("True")
            METRIC = True
    else:
        if CACHE_FILE.exists():
            METRIC = True
        else:
            METRIC = False

    return METRIC


def main():
    METRIC = parse_args()
    daily_df, hourly_df = open_meteo(
        lat=LATITUDE,
        lon=LONGITUDE,
    )
    # print(f"{hourly_df.head(48)}")
    hourly_df = add_daytime_flag(
        hourly_df,
        daily_df,
        tz=TIMEZONE,
        step=HOURLY_STEP,
        metric=METRIC,
    )
    hourly_df = map_icons(hourly_df, is_hourly=True)
    daily_df = map_icons(daily_df, is_hourly=False)
    tooltip = build_tooltip(
        daily_df,
        hourly_df,
        my_zone=TIMEZONE,
        celsius=METRIC,
        hourly_step=HOURLY_STEP,
    )
    current = hourly_df.iloc[0]
    output = {
        "text": current.icon,
        "tooltip": tooltip,
        "class": current.description,
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
