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
    **{
        k: (v[0], "yellow", v[1], v[2])
        for k, v in {
            0: ("clear", "", ""),
            1: ("Clouds dissolving", "", "󰼱"),
        }.items()
    },
    **{
        k: (v[0], "lightblue", v[1], v[2])
        for k, v in {
            2: ("Sky unchanged", "󰖕", "󰼱"),
            3: ("Clouds forming", "󰖐", "󰖐"),
            14: ("Precipitation in sight", "", ""),
            23: ("Rain, or snow, or ice pellets", "󰙿", "󰙿"),
            26: ("Shower(s) of snow, or of rain and snow", "󰙿", "󰙿"),
            20: ("Drizzel", "", ""),
            21: ("Rain not freezing", "", ""),
            25: ("Showers of rain", "󰖗", "󰖗"),
            50: ("Drizzle", "", ""),
            51: ("Drizzle", "", ""),
            52: ("Drizzle", "", ""),
            53: ("Drizzle", "", ""),
            54: ("Heavy drizzle", "", ""),
            55: ("Drizzle", "", ""),
            80: ("rain_showers", "󰖖", ""),
            81: ("rain_showers", "󰖖", ""),
            82: ("rain_showers", "󰖖", ""),
            85: ("snow_showers", "󰖘", ""),
            86: ("snow_showers", "󰖘", ""),
            87: ("rain_showers", "󰖖", ""),
            60: ("Rain", "󰖗", ""),
            61: ("Rain", "󰖗", ""),
            62: ("Rain", "󰖗", ""),
            63: ("Rain", "󰖗", ""),
            64: ("Heavy rain", "󰖗", ""),
            65: ("Heavy rain", "󰖗", ""),
        }.items()
    },
    **{
        k: (v[0], "grey", v[1], v[2])
        for k, v in {
            4: ("Smoke", "", ""),
            5: ("Haze", "", ""),
            6: ("Dust", "", ""),
            10: ("Mist", "", ""),
            11: ("Patches", "", ""),
            28: ("fog", "󰖑", "󰖑"),
            40: ("fog", "", ""),
            41: ("Fog or ice fog in patches", "", ""),
            42: ("Fog or ice fog, sky visible", "", ""),
            43: ("Fog or ice fog, sky invisible", "", ""),
            44: ("Fog or ice fog, sky visible", "", ""),
            45: ("Fog or ice fog, sky invisible", "", ""),
            46: ("Fog or ice fog, sky visible", "", ""),
            47: ("Fog or ice fog, sky invisible", "", ""),
        }.items()
    },
    **{
        k: (v[0], "red", v[1], v[2])
        for k, v in {
            13: ("Lightning, no thunder", "󰼲", ""),
            29: ("Thunderstorm", "", ""),
            30: ("Dust/sandstorms", "", ""),
            33: ("Severe dust/sandstorms", "", ""),
            95: ("thunderstorm", "󰖓", ""),
            96: ("thunderstorm_hail", "", ""),
            99: ("thunderstorm_hail", "󰖒", ""),
        }.items()
    },
    **{
        k: (v[0], "darkblue", v[1], v[2])
        for k, v in {
            22: ("Snow", "󰼶", ""),
            36: ("Slight or moderate blowing snow", "", ""),
            37: ("Heavy drifting snow", "", ""),
            38: ("Blowing snow (above eye level)", "", ""),
            39: ("Heavy drifting snow (above eye level)", "", ""),
            56: ("Freezing drizzle", "", ""),
            57: ("Freezing drizzle (heavy)", "", ""),
            58: ("Drizzle and rain", "", ""),
            59: ("Drizzle and rain (heavy)", "", ""),
            66: ("Freezing rain", "󰖗", ""),
            67: ("Freezing rain (heavy)", "󰖗", ""),
            68: ("Rain/snow mix", "󰖗", ""),
            69: ("Rain/snow mix (heavy)", "󰖗", ""),
            70: ("Snow", "󰖗", ""),
            71: ("Snow", "󰖗", ""),
            72: ("Snow", "󰖗", ""),
            73: ("Snow", "󰖗", ""),
            74: ("Heavy snow", "󰖗", ""),
            75: ("Heavy snow", "󰖗", ""),
            76: ("Diamond dust", "󰖗", ""),
            77: ("Snow grains", "󰖗", ""),
            78: ("Snow crystals", "󰖗", ""),
            79: ("Ice pellets", "󰖗", ""),
        }.items()
    },
}
FALLBACK_ICON = ("unknown", "grey", "", "")
LATITUDE = 34.1751
LONGITUDE = -82.024
HOURLY_STEP = 2
TIMEZONE = "America/New_York"
CACHE_FILE = Path(".metric_cache")


def open_meteo(lat, lon):
    def create_retry_session():
        return retry(
            requests_cache.CachedSession(".cache", expire_after=1800),
            retries=5,
            backoff_factor=0.2,
        )

    def df_daily(response):
        daily = response.Daily()
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
            ),
            "weather_code": daily.Variables(0).ValuesAsNumpy(),
            "precipitation_sum": daily.Variables(1).ValuesAsNumpy(),
            "sunrise": daily.Variables(2).ValuesInt64AsNumpy(),
            "sunset": daily.Variables(3).ValuesInt64AsNumpy(),
            "temperature_2m_max": daily.Variables(4).ValuesAsNumpy(),
            "temperature_2m_min": daily.Variables(5).ValuesAsNumpy(),
            "precipitation_probability_max": daily.Variables(6).ValuesAsNumpy(),
        }
        return pd.DataFrame(data=daily_data)

    def df_hourly(response):
        hourly = response.Hourly()
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
            ),
            "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
            "precipitation_probability": hourly.Variables(1).ValuesAsNumpy(),
            "precipitation": hourly.Variables(2).ValuesAsNumpy(),
            "weather_code": hourly.Variables(3).ValuesAsNumpy(),
        }
        return pd.DataFrame(data=hourly_data)

    session = create_retry_session()
    client = openmeteo_requests.Client(session)
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
        "timezone": TIMEZONE,
        "wind_speed_unit": "mph",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
    }
    response = client.weather_api(
        "https://api.open-meteo.com/v1/forecast", params=params
    )[0]
    return df_daily(response), df_hourly(response)


def add_daytime_flag(
    hourly_df: pd.DataFrame, daily_df: pd.DataFrame, tz: str, step: int, metric
) -> pd.DataFrame:
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
    hourly_df["is_day"] = (hourly_df["sunrise"] <= hourly_df["date"]) & (
        hourly_df["date"] < hourly_df["sunset"]
    )
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
    fallback_icon=("unknown", "grey", "?", "?"),
) -> pd.DataFrame:

    def pick_icon_description_color(row):
        weather_code = int(row["weather_code"])
        description, color, night_icon, day_icon = weather_icons.get(
            weather_code, fallback_icon
        )
        icon = night_icon if (is_hourly and not row.get("is_day", True)) else day_icon
        return icon, description, color

    df[["icon", "description", "color"]] = df.apply(
        pick_icon_description_color,
        axis=1,
        result_type="expand",
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

    def format(self, now: pd.Timestamp) -> str:
        today = now.strftime("%a")
        label = self.label
        if self.label == today:
            label = "Today"
        precip_prob = f"{self.precip_prob}%" if self.precip_prob > 0 else ""
        precip_sum = ""
        if self.precipitation >= 0.01:
            if self.precipitation < 0.1:
                precip = f"{round(self.precipitation, 2)}".lstrip("0")
            else:
                precip = f"{round(self.precipitation, 1)}"
            precip_sum = f"({precip}{self.units_in_cm})"
        temp_low = round(self.temp_low) if self.temp_low is not None else ""
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
            return (
                f"{label:<5}"
                f"<span size='23pt'>{self.icon.rjust(2)}</span>"
                f"{daily_temp.rjust(9)}<span size='17pt'></span>{self.units}"
                f"<span size='14pt'>{rain_icon.rjust(5)}</span>{precip_prob.rjust(4)}{precip_sum.rjust(10)}"
            )


def today_formatted(now: pd.Timestamp) -> str:
    day_suffix = {1: "st", 2: "nd", 3: "rd"}.get(now.day % 10, "th")
    if 10 <= now.day % 100 <= 20:
        day_suffix = "th"
    return now.strftime(f"%a, %b {now.day}{day_suffix}, %Y")


def build_tooltip(
    daily_df, hourly_df, my_zone: str, celsius, now: pd.Timestamp, hourly_step=2
):
    def proc_entries(entries):
        return "\n".join([entry.format(now) for entry in entries])

    unit_str = "C" if celsius else "F"
    current_time = now.replace(minute=0, second=0, microsecond=0)
    time_24h_later = current_time + pd.Timedelta(hours=24)  # 24 hours later
    current_time_str = now.strftime("%H:%M")
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
            precip_prob=int(row["precipitation_probability"]),
            precipitation=row["precipitation"],
        )
        for _, row in hourly_df.iterrows()
        if current_time <= row["date"] < time_24h_later
        and (row["date"].hour - current_time.hour) % hourly_step == 0
    ]
    daily_entries = [
        WeatherEntry(
            label=row["date"].strftime("%a"),
            icon=row["icon"],
            units_in_cm=row["units"],
            temp=row["temperature_2m_max"],
            temp_low=row["temperature_2m_min"],
            units=unit_str,
            precip_prob=int(row["precipitation_probability_max"]),
            precipitation=row["precipitation_sum"],
        )
        for _, row in daily_df.iterrows()
    ]
    formatted_date = today_formatted(now)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--metric", action="store_true")
    args = parser.parse_args()
    if args.metric:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
        else:
            CACHE_FILE.write_text("1")
    return CACHE_FILE.exists()


def main():
    METRIC = parse_args()
    daily_df, hourly_df = open_meteo(lat=LATITUDE, lon=LONGITUDE)
    now = pd.Timestamp.now(tz=TIMEZONE)
    hourly_df = add_daytime_flag(
        hourly_df, daily_df, tz=TIMEZONE, step=HOURLY_STEP, metric=METRIC
    )
    hourly_df = map_icons(hourly_df, is_hourly=True)
    daily_df = map_icons(daily_df, is_hourly=False)
    tooltip = build_tooltip(
        daily_df,
        hourly_df,
        my_zone=TIMEZONE,
        celsius=METRIC,
        hourly_step=HOURLY_STEP,
        now=now,
    )
    idx = (hourly_df["date"] - now).abs().idxmin()
    current = hourly_df.loc[idx]
    output = {
        "text": now.strftime("%H:%M"),
        "tooltip": tooltip,
        "class": current.color,
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
