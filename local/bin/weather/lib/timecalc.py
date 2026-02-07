#!/usr/bin/env python3
import pandas as pd
from zoneinfo import ZoneInfo


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
