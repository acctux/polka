import pandas as pd

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
