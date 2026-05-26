#!/usr/bin/env python3

from pathlib import Path
import pickle
import time
from typing import Any
import pandas as pd
import json
from tzlocal import get_localzone
from weather_dataframes import load_weather_dataframes
from dataclasses import dataclass

# =========================================================
# CACHE
# =========================================================
CACHE_TTL = 60 * 15  # 15 min


@dataclass(slots=True)
class WeatherUnit:
    codes: list[int]
    icon: tuple[str, str]

    def __init__(self, codes: list[int], icon: str | tuple[str, str]):
        self.codes = codes
        self.icon = icon if isinstance(icon, tuple) else (icon, icon)


@dataclass(slots=True)
class WeatherGroup:
    name: str
    color: str
    units: list[WeatherUnit]


CODES = {
    0: "Cloud development not observed or not observable",
    1: "Clouds generally dissolving or becoming less developed ",
    2: "State of sky on the whole unchanged",
    3: "Clouds generally forming or developing",
    4: "Visibility reduced by smoke",
    5: "Haze",
    6: "Widespread dust in suspension in the air, not raised by wind",
    7: "Dust or sand raised by wind, but no well developed dust whirl(s) or sand whirl(s), and no duststorm or sandstorm",
    8: "Well developed dust whirl(s) or sand whirl(s), but no duststorm or sandstorm",
    9: "Duststorm or sandstorm within sight",
    10: "Mist",
    11: "Patches shallow fog or ice fog",
    12: "More or less continuous shallow fog or ice fog",
    13: "Lightning visible, no thunder heard",
    14: "Precipitation within sight, not reaching the ground",
    15: "Precipitation within sight, reaching the ground or the surface of the sea, distant",
    16: "Precipitation within sight, reaching the ground or the surface of the sea, near to",
    17: "Thunderstorm, but no precipitation at the time of observation ",
    18: "Squalls",
    19: "Funnel cloud (Tornado or water-spout)",
    20: "not falling as shower, Drizzle (not freezing) or snow grains",
    21: "not falling as shower, Rain (not freezing)",
    22: "not falling as shower, Snow",
    23: "not falling as shower, Rain and snow or ice pellets",
    24: "not falling as shower, Freezing drizzle or freezing rain",
    25: "Shower(s) of rain",
    26: "Shower(s) of snow, or of rain and snow",
    27: "Shower(s) of hail, or of rain and hail",
    28: "Fog or ice fog",
    29: "Thunderstorm (with or without precipitation)",
    30: "Slight or moderate duststorm or sandstorm, has decreased during preceding hour",
    31: "Slight or moderate duststorm or sandstorm, no appreciable change during the preceding hour",
    32: "Slight or moderate duststorm or sandstorm, has begun or has increased during the preceding hour",
    33: "Severe duststorm or sandstorm, has decreased during preceding hour",
    34: "Severe duststorm or sandstorm, no appreciable change during the preceding hour",
    35: "Severe duststorm or sandstorm, has begun or has increased during the preceding hour",
    36: "Slight or moderate blowing snow, generally low (below eye level)",
    37: "Heavy drifting snow, generally low (below eye level)",
    38: "Slight or moderate blowing snow generally high (above eye level)",
    39: "Heavy drifting snow generally high (above eye level)",
    40: "Fog or ice fog at a distance",
    41: "Fog or ice fog in patches",
    42: "Fog or ice fog, sky visible, has become thinner during the preceding hour",
    43: "Fog or ice fog, sky invisible, has become thinner during the preceding hour",
    44: "Fog or ice fog, sky visible, no appreciable change during the preceding hour",
    45: "Fog or ice fog, sky invisible, no appreciable change during the preceding hour",
    46: "Fog or ice fog, sky visible, has begun or has become thicker during the preceding hour",
    47: "Fog or ice fog, sky invisible, has begun or has become thicker during the preceding hour",
    48: "Fog, depositing rime, sky visible",
    49: "Fog, depositing rime, sky invisible",
    50: "Drizzle, not freezing, intermittent, slight",
    51: "Drizzle, not freezing, continuous, slight",
    52: "Drizzle, not freezing, intermittent, moderate",
    53: "Drizzle, not freezing, continuous, moderate",
    54: "Drizzle not freezing intermittent, heavy (dense)",
    55: "Drizzle not freezing continuous, heavy (dense)",
    56: "Drizzle, freezing, slight",
    57: "Drizzle, freezing, moderate or heavy (dence)",
    58: "Drizzle and rain, slight",
    59: "Drizzle and rain, moderate or heavy",
    60: "Rain, not freezing, intermittent, slight",
    61: "Rain, not freezing, continuous, slight",
    62: "Rain, not freezing, intermittent, moderate",
    63: "Rain, not freezing, continuous, moderate",
    64: "Rain, not freezing, intermittent, heavy",
    65: "Rain, not freezing, continuous, heavy",
    66: "Rain, freezing, slight",
    67: "Rain, freezing, moderate or heavy (dence)",
    68: "Rain or drizzle and snow, slight",
    69: "Rain or drizzle and snow, moderate or heavy",
    70: "Intermittent fall of snowflakes, slight",
    71: "Continuous fall of snowflakes, slight",
    72: "Intermittent fall of snowflakes, moderate",
    73: "Continuous fall of snowflakes, moderate",
    74: "Intermittent fall of snowflakes, heavy",
    75: "Continuous fall of snowflakes, heavy",
    76: "Diamond dust (with or without fog)",
    77: "Snow grains (with or without fog)",
    78: "Isolated star-like snow crystals (with or without fog)",
    79: "Ice pellets",
    80: "Rain shower(s), slight",
    81: "Rain shower(s), moderate or heavy",
    82: "Rain shower(s), violent",
    83: "Shower(s) of rain and snow mixed, slight",
    84: "Shower(s) of rain and snow mixed, moderate or heavy",
    85: "Snow shower(s), slight",
    86: "Snow shower(s), moderate or heavy",
    87: "Shower(s) of snow pellets or small hail, slight",
    88: "Shower(s) of snow pellets or small hail, moderate or heavy",
    89: "Shower(s) of hail slight",
    90: "Shower(s) of hail moderate or heavy",
    91: "Slight rain at time of observation, Thunderstorm during the preceding hour but not at time of observation",
    92: "Moderate or heavy rain at time of observation, Thunderstorm during the preceding hour but not at time of observation",
    93: "Slight snow or rain and snow mixed or hail, Thunderstorm during the preceding hour but not at time of observation",
    94: "Moderate or heavy snow or rain and snow mixed or hail, Thunderstorm during the preceding hour but not at time of observation",
    95: "Thunderstorm, slight or moderate, without hail, with rain and/or snow, Thunderstorm at time of observation",
    96: "Thunderstorm, slight or moderate, with hail, Thunderstorm at time of observation",
    97: "Thunderstorm, heavy, without hail, with rain/snow, Thunderstorm at time of observation",
    98: "Thunderstorm combined with duststorm or sandstorm, Thunderstorm at time of observation",
    99: "Thunderstorm, heavy, with hail",
}
GROUPS = [
    WeatherGroup(
        name="fog",
        color="grey",
        units=[
            WeatherUnit(icon="", codes=[12, 43, 45, 47, 49]),
            WeatherUnit(icon=("", ""), codes=[11, 28, 40, 41, 42, 44, 46, 48]),
        ],
    ),
    WeatherGroup(
        name="hail",
        color="cyan",
        units=[
            WeatherUnit(icon="", codes=[88, 90]),
            WeatherUnit(icon=("", ""), codes=[79, 87, 89]),
        ],
    ),
    WeatherGroup(
        name="snow_wind",
        color="white",
        units=[
            WeatherUnit(icon="", codes=[37, 39]),
            WeatherUnit(icon=("", ""), codes=[36, 38]),
        ],
    ),
    WeatherGroup(
        name="thunderstorm_showers",
        color="red",
        units=[
            WeatherUnit(icon="", codes=[92]),
            WeatherUnit(icon=("", ""), codes=[29, 91, 95]),
        ],
    ),
    WeatherGroup(
        name="rain_mix",
        color="blue",
        units=[
            WeatherUnit(icon="", codes=[84]),
            WeatherUnit(icon=("", ""), codes=[57, 83]),
        ],
    ),
    WeatherGroup(
        name="rain_wind",
        color="blue",
        units=[
            WeatherUnit(icon="", codes=[]),
            WeatherUnit(icon=("", ""), codes=[62, 63, 64, 65]),
        ],
    ),
    WeatherGroup(
        name="sleet",
        color="blue",
        units=[
            WeatherUnit(icon="", codes=[23, 24, 67, 69]),
            WeatherUnit(icon=("", ""), codes=[56, 66, 68]),
        ],
    ),
    WeatherGroup(
        name="snow",
        color="white",
        units=[
            WeatherUnit(icon="", codes=[22, 73, 74, 75, 86]),
            WeatherUnit(icon=("", ""), codes=[70, 71, 72, 76, 77, 78, 85]),
        ],
    ),
    WeatherGroup(
        name="rain",
        color="blue",
        units=[
            WeatherUnit(icon="", codes=[21]),
            WeatherUnit(icon=("", ""), codes=[]),
        ],
    ),
    WeatherGroup(
        name="showers",
        color="blue",
        units=[
            WeatherUnit(icon="", codes=[59, 60, 61, 81, 82]),
            WeatherUnit(icon=("", ""), codes=[25, 26, 27, 58, 80]),
        ],
    ),
    WeatherGroup(
        name="cloudy",
        color="white",
        units=[
            WeatherUnit(icon="", codes=[]),
            WeatherUnit(icon=("", ""), codes=[3, 14, 15, 16]),
        ],
    ),
    WeatherGroup(
        name="sprinkle",
        color="blue",
        units=[
            WeatherUnit(icon="", codes=[20, 54, 55]),
            WeatherUnit(icon=("", ""), codes=[10, 50, 51, 52, 53]),
        ],
    ),
    WeatherGroup(
        name="cloudy_gusts",
        color="grey",
        units=[
            WeatherUnit(icon="", codes=[]),
            WeatherUnit(icon=("", ""), codes=[]),
        ],
    ),
    WeatherGroup(
        name="cloudy_windy",
        color="grey",
        units=[
            WeatherUnit(icon="", codes=[]),
            WeatherUnit(icon=("", ""), codes=[]),
        ],
    ),
    WeatherGroup(
        name="lightning",
        color="red",
        units=[
            WeatherUnit(icon="", codes=[17, 97, 99]),
            WeatherUnit(icon=("", ""), codes=[13, 98]),
        ],
    ),
    WeatherGroup(
        name="clear",
        color="yellow",
        units=[
            WeatherUnit(icon=("", ""), codes=[0, 1, 2]),
        ],
    ),
    WeatherGroup(
        name="cloudy_high",
        color="yellow",
        units=[
            WeatherUnit(icon=("", ""), codes=[]),
        ],
    ),
    WeatherGroup(
        name="sleet_thunderstorm",
        color="red",
        units=[
            WeatherUnit(icon=("", ""), codes=[93, 96]),
        ],
    ),
    WeatherGroup(
        name="snow_thunderstorm",
        color="red",
        units=[
            WeatherUnit(icon=("", ""), codes=[94]),
        ],
    ),
    WeatherGroup(
        name="partly_cloudy",
        color="yellow",
        units=[
            WeatherUnit(icon=("", ""), codes=[]),
        ],
    ),
    WeatherGroup(
        name="day_hazy",
        color="grey",
        units=[
            WeatherUnit(icon="", codes=[5]),
        ],
    ),
    WeatherGroup(
        name="dust",
        color="brown",
        units=[
            WeatherUnit(icon="", codes=list(range(6, 10))),
        ],
    ),
    WeatherGroup(
        name="tornado",
        color="red",
        units=[
            WeatherUnit(icon="", codes=[18, 19]),
        ],
    ),
    WeatherGroup(
        name="sandstorm",
        color="brown",
        units=[
            WeatherUnit(icon="", codes=list(range(30, 36))),
        ],
    ),
    WeatherGroup(
        name="smoke",
        color="red",
        units=[
            WeatherUnit(icon="", codes=[4]),
        ],
    ),
]


class WeatherProcessor:
    def __init__(
        self,
        imperial: bool,
        groups: list[WeatherGroup],
        codes: dict[int, str],
    ):
        self.imperial = imperial
        self.codes = codes
        self.temp_unit = "" if imperial else ""
        self.size_unit = "in" if imperial else "mm"
        self.icon_map: dict[int, tuple[str, str]] = {}
        self.color_map: dict[int, str] = {}
        for group in groups:
            for unit in group.units:
                for code in unit.codes:
                    self.icon_map[code] = unit.icon
                    self.color_map[code] = group.color

    # =========================================================
    # FORMATTING UTILITIES (Internal)
    # =========================================================
    def _fmt_temp(
        self,
        series: pd.Series,
        show_unit: bool = True,
    ) -> pd.Series:
        def fmt(x):
            value = f"{x:.0f}"
            return f"{value}{self.temp_unit}" if show_unit else value

        series = pd.to_numeric(series, errors="coerce")
        if self.imperial:
            series = series * 9 / 5 + 32
        return series.map(fmt)

    def _fmt_probability(
        self,
        series: pd.Series,
    ) -> pd.Series:
        def fmt(x):
            if pd.isna(x):
                return ""
            if x < 15:
                return ""
            return f"{int(round(x))}% 󰖌"

        series = pd.to_numeric(series, errors="coerce")
        return series.map(fmt)

    def _fmt_size(
        self,
        series: pd.Series,
    ) -> pd.Series:
        def fmt(x):
            if self.imperial:
                x = x / 25.4
            if abs(x) < 0.01:
                return ""
            if abs(x) < 1:
                value = f"{x:.2f}".lstrip("0")
            elif abs(x) < 10:
                value = f"{x:.1f}"
            else:
                value = f"{x:.0f}"
            return f"{value}({self.size_unit})"

        series = pd.to_numeric(series, errors="coerce")
        return series.map(fmt)

    # =========================================================
    # DATA ENRICHMENT (Internal)
    # =========================================================
    def enrich(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        df = df.copy()
        df["description"] = df["weather_code"].map(self.codes)
        df["color"] = df["weather_code"].map(self.color_map)
        icons = df["weather_code"].map(self.icon_map)
        is_day = pd.Series(1, index=df.index)
        if "is_day" in df.columns:
            is_day = df["is_day"]
        rendered_icons: list[str] = []
        for icon_pair, day_value in zip(icons, is_day):
            if not isinstance(icon_pair, tuple):
                icon_pair = (icon_pair, icon_pair)
            day_icon, night_icon = icon_pair
            icon = day_icon if day_value == 1 else night_icon
            rendered_icons.append(icon)
        df["icon"] = rendered_icons
        return df

    # =========================================================
    # PUBLIC PROCESSING METHODS
    # =========================================================
    def map_sunrise_sunset(
        self,
        hourly_df: pd.DataFrame,
        daily_df: pd.DataFrame,
        tz: str,
    ) -> pd.DataFrame:
        hourly_df = hourly_df.copy()
        hourly_df["day_date"] = hourly_df["date"].dt.normalize()
        daily = daily_df.copy()
        daily["day_date"] = daily["date"].dt.normalize()
        sun = daily[["day_date", "sunrise", "sunset"]].copy()
        sun["sunrise_dt"] = pd.to_datetime(
            sun["sunrise"], unit="s", utc=True
        ).dt.tz_convert(tz)
        sun["sunset_dt"] = pd.to_datetime(
            sun["sunset"], unit="s", utc=True
        ).dt.tz_convert(tz)
        hourly = hourly_df.merge(sun, on="day_date", how="left")
        return hourly

    def process_hourly(
        self,
        hourly_df: pd.DataFrame,
        now: pd.Timestamp,
    ) -> pd.DataFrame:
        start = now.floor("h")
        if now.minute >= 30:
            start = now.ceil("h")
        end = start + pd.Timedelta(hours=23)
        mask = hourly_df["date"].between(start, end)
        hourly_filtered = hourly_df.loc[mask]
        hourly = hourly_filtered.copy()
        # 1. Apply Formats
        hourly["temperature_2m"] = self._fmt_temp(hourly["temperature_2m"])
        hourly["soil_temperature_0cm"] = self._fmt_temp(hourly["soil_temperature_0cm"])
        hourly["precipitation"] = self._fmt_size(hourly["precipitation"])
        hourly["precipitation_probability"] = self._fmt_probability(
            hourly["precipitation_probability"]
        )
        # 2. Extract Sun Events
        hourly["sun_event"] = ""
        h_end = hourly["date"] + pd.Timedelta(hours=1)
        sunrise_hit = (hourly["sunrise_dt"] >= hourly["date"]) & (
            hourly["sunrise_dt"] < h_end
        )
        sunset_hit = (hourly["sunset_dt"] >= hourly["date"]) & (
            hourly["sunset_dt"] < h_end
        )
        sunrise_str = "<span size='15pt'>󰖜</span> " + hourly["sunrise_dt"].dt.strftime(
            "%H:%M"
        )
        sunset_str = "<span size='15pt'>󰖛</span> " + hourly["sunset_dt"].dt.strftime(
            "%H:%M"
        )
        hourly.loc[sunrise_hit, "sun_event"] = sunrise_str
        hourly.loc[sunset_hit, "sun_event"] = sunset_str
        # 1. Identify sun events sitting on odd indices
        odd_events = hourly["sun_event"].where(hourly.index % 2 == 1, "")
        # 2. Shift them backward by 1 row to line up with even indices
        shifted_events = odd_events.shift(-1, fill_value="")
        # 3. Fill empty even slots with the shifted events
        hourly["sun_event"] = hourly["sun_event"].where(
            hourly["sun_event"] != "", shifted_events
        )
        hourly = hourly.iloc[::2].reset_index(drop=True)
        return hourly

    def process_daily(
        self,
        daily_df: pd.DataFrame,
    ) -> pd.DataFrame:
        daily_df["temperature_2m"] = (
            self._fmt_temp(daily_df["temperature_2m_max"], show_unit=False)
            + "/"
            + self._fmt_temp(daily_df["temperature_2m_min"])
        )
        daily_df["temperature_2m_max"] = self._fmt_temp(daily_df["temperature_2m_max"])
        daily_df["temperature_2m_min"] = self._fmt_temp(daily_df["temperature_2m_min"])
        daily_df["precipitation_sum"] = self._fmt_size(daily_df["precipitation_sum"])
        daily_df["precipitation_probability"] = self._fmt_probability(
            daily_df["precipitation_probability_max"]
        )
        return daily_df.head(7).reset_index(drop=True)


# =========================================================
# WAYBAR RENDERER
# =========================================================
class WaybarRenderer:
    @staticmethod
    def today_label(now: pd.Timestamp) -> str:
        int_day = now.day
        if 10 <= int_day <= 20:
            suffix = "th"
        else:
            last_digit = int_day % 10
            if last_digit == 1:
                suffix = "st"
            elif last_digit == 2:
                suffix = "nd"
            elif last_digit == 3:
                suffix = "rd"
            else:
                suffix = "th"
        weekday = now.strftime("%a")
        month = now.strftime("%b")
        year = now.year
        return f"{weekday}, {month} {weekday}{suffix}, {year}"

    def row(
        self,
        row: dict[str, Any],
        hourly_mode: bool,
    ) -> str:
        icon = row.get("icon", "")
        size = 22 if hourly_mode else 24
        if hourly_mode:
            return (
                f"{row['date']:%H:%M}"
                f"<span size='{size}pt'>{icon:^3}</span>"
                f"{row.get('temperature_2m'):^8}"
                f"{row.get('precipitation_probability'):^6}"
                f"{row.get('precipitation'):^8}"
                # f"{row.get('soil_temperature_0cm'):^7}"
                f"{row.get('sun_event'):^9}"
            )
        return (
            f"{row['date']:%a}"
            f"<span size='{size}pt'>{icon:^5}</span>"
            f"{row.get('temperature_2m'):^9}"
            f"{row.get('precipitation_probability'):^10}"
            f"{row.get('precipitation_sum'):^8}"
        )

    def render(
        self,
        now: pd.Timestamp,
        hourly_df: pd.DataFrame,
        daily_df: pd.DataFrame,
    ) -> dict[str, str]:
        hourly_rows = [self.row(row, True) for row in hourly_df.to_dict("records")]
        daily_rows = [self.row(row, False) for row in daily_df.to_dict("records")]
        tooltip = (
            [
                f"<span size='20pt'>󰨳</span><span size='13pt'>  {self.today_label(now)}</span>",
                "──────────────────────────────────────────",
            ]
            + hourly_rows
            + [
                "",
                f"<span size='20pt'></span><span size='13pt'>  {now.strftime('%H:%M')}</span>",
                "──────────────────────────────────────────",
            ]
            + daily_rows
        )
        return {
            "text": now.strftime("%H:%M"),
            "tooltip": "\n".join(tooltip),
            "class": hourly_df["color"].iloc[0],
        }


# =========================================================
# MAIN
# =========================================================
class WeatherApp:
    def __init__(
        self,
        imperial: bool,
        pkl_cache: Path,
        groups: list,
        codes: dict[int, str],
    ) -> None:
        self.processor = WeatherProcessor(imperial=imperial, groups=groups, codes=codes)
        self.renderer = WaybarRenderer()
        self.pkl_cache = pkl_cache

    def save_pkl(
        self,
        pkl_cache: Path,
        hourly_df: pd.DataFrame,
        daily_df: pd.DataFrame,
    ):
        pkl_cache.parent.mkdir(parents=True, exist_ok=True)
        with open(pkl_cache, "wb") as pkl_txt:
            pickle.dump((hourly_df, daily_df), pkl_txt)

    def run(
        self,
        ttl: int,
    ) -> None:
        tz = str(get_localzone())
        now = pd.Timestamp.now(tz)
        if self.pkl_cache.exists():
            if (time.time() - self.pkl_cache.stat().st_mtime) < ttl:
                with open(self.pkl_cache, "rb") as pkl_txt:
                    hourly_df, daily_df = pickle.load(pkl_txt)
                    daily_df = self.processor.process_daily(daily_df)
                    hourly_df = self.processor.process_hourly(hourly_df, now)
                    output = self.renderer.render(now, hourly_df, daily_df)
                    print(json.dumps(output, ensure_ascii=False))
            else:
                hourly_df, daily_df = load_weather_dataframes()
                hourly_df = self.processor.map_sunrise_sunset(hourly_df, daily_df, tz)
                hourly_df = self.processor.enrich(hourly_df)
                daily_df = self.processor.enrich(daily_df)
                self.save_pkl(self.pkl_cache, hourly_df, daily_df)
                daily_df = self.processor.process_daily(daily_df)
                hourly_df = self.processor.process_hourly(hourly_df, now)
                output = self.renderer.render(now, hourly_df, daily_df)
                print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    WeatherApp(
        imperial=True,
        pkl_cache=Path.home() / ".cache/weather_cache" / "weather.pkl",
        groups=GROUPS,
        codes=CODES,
    ).run(
        ttl=CACHE_TTL,
    )

