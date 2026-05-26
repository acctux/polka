from dataclasses import dataclass


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


codes = {
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
groups = [
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
            WeatherUnit(icon="", codes=[6, 7, 8, 9]),
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
