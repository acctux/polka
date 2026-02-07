#!/usr/bin/env python3
import json
import time
from zoneinfo import ZoneInfo
from lib.weatherdataframe import open_meteo
from lib.iconmapper import map_icons
from dataclasses import dataclass
from lib.timecalc import add_daytime_flag
import pandas as pd

LATITUDE = 34.1751
LONGITUDE = -82.024
HOURLY_STEP = 2
TIMEZONE = "America/New_York"
METRIC = False


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


def build_tooltip(daily_df, hourly_df, my_zone: str, celsius, hourly_step=2):
    def proc_entries(entries):
        return "\n".join([entry.format() for entry in entries])

    unit_str = "C" if celsius else "F"
    t = pd.Timestamp.now(ZoneInfo(my_zone))
    current_time = t.replace(minute=0, second=0, microsecond=0)
    time_24h_later = current_time + pd.Timedelta(hours=24)  # 24 hours later
    current_time_str = t.strftime("%H:%M")

    # Convert hourly_df to the desired timezone
    hourly_df["date"] = hourly_df["date"].dt.tz_convert(ZoneInfo(my_zone))
    # Filter hourly_df for the next 24 hours from the current time
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
        if current_time
        <= row["date"]
        < time_24h_later  # Only include rows within the next 24 hours
        and (row["date"].hour - current_time.hour) % hourly_step
        == 0  # Filter by step interval
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
    return formatted_date, (
        f"<span size='{icon_size}pt'>󰨳</span><span size='13pt'>  {formatted_date}</span>\n"
        "─────────────────────────────────────────\n"
        + f"{proc_entries(daily_entries)}\n"
        + f"\n<span size='{icon_size}pt'></span><span size='13pt'>  {current_time_str}</span>\n"
        "─────────────────────────────────────────\n"
        + f"{proc_entries(hourly_entries)}"
    )


def today_formatted() -> str:
    t = pd.Timestamp.now()
    day_suffix = {1: "st", 2: "nd", 3: "rd"}.get(t.day % 10, "th")
    if 10 <= t.day % 100 <= 20:
        day_suffix = "th"
    return t.strftime(f"%a, %b {t.day}{day_suffix}, %Y")


def main():
    def refresh_data():
        daily_df, hourly_df = open_meteo(lat=LATITUDE, lon=LONGITUDE)
        hourly_df = add_daytime_flag(
            hourly_df, daily_df, tz=TIMEZONE, step=HOURLY_STEP, metric=METRIC
        )
        hourly_df = map_icons(hourly_df, is_hourly=True)
        daily_df = map_icons(daily_df, is_hourly=False)
        return daily_df, hourly_df

    t = pd.Timestamp.now(ZoneInfo(TIMEZONE))
    current_time_str = t.strftime("%H:%M")
    place = 1
    daily_df, hourly_df = refresh_data()
    while True:
        if place == 60:
            daily_df, hourly_df = refresh_data()
            place = 1
        else:
            place += 1
        formatted_date, tooltip = build_tooltip(
            daily_df,
            hourly_df,
            my_zone=TIMEZONE,
            celsius=METRIC,
            hourly_step=HOURLY_STEP,
        )
        current = hourly_df.iloc[0]
        output = {
            "text": current_time_str,
            "tooltip": tooltip,
            "class": current.description,
        }
        print(json.dumps(output, ensure_ascii=False))
        time.sleep(60)


if __name__ == "__main__":
    main()
