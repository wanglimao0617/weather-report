from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any


CITY_COORDINATES = {
    "北京": (39.904, 116.407, "北京市"),
    "上海": (31.230, 121.474, "上海市"),
    "广州": (23.129, 113.264, "广东省广州市"),
    "深圳": (22.543, 114.058, "广东省深圳市"),
    "深圳市南山区": (22.531, 113.930, "广东省深圳市南山区"),
    "佛山": (23.022, 113.122, "广东省佛山市"),
    "佛山市禅城区": (23.009, 113.123, "广东省佛山市禅城区"),
    "天津": (39.084, 117.201, "天津市"),
    "杭州": (30.274, 120.155, "浙江省杭州市"),
    "成都": (30.573, 104.067, "四川省成都市"),
    "揭阳": (23.550, 116.373, "广东省揭阳市"),
    "揭阳市揭东区": (23.567, 116.412, "广东省揭阳市揭东区"),
}


def demo_locations(city_name: str) -> list[dict[str, Any]]:
    city_name = city_name.strip()
    if city_name == "朝阳":
        return [
            {
                "formatted_address": "北京市朝阳区（演示地点）",
                "location": "116.486,39.921",
            },
            {
                "formatted_address": "吉林省长春市朝阳区（演示地点）",
                "location": "125.288,43.833",
            },
        ]

    if city_name in CITY_COORDINATES:
        lat, lon, address = CITY_COORDINATES[city_name]
    else:
        seed = sum(ord(char) for char in city_name) or 100
        lat = 22 + seed % 15
        lon = 102 + seed % 22
        address = f"{city_name}（演示地点）"
    return [{"formatted_address": address, "location": f"{lon},{lat}"}]


def demo_forecast(lat: float, lon: float) -> dict[str, Any]:
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    seed = int(abs(lat * 10 + lon * 10))
    base_temp = 18 + seed % 10
    hourly_times = [
        (now + timedelta(hours=offset)).strftime("%Y-%m-%dT%H:%M")
        for offset in range(30)
    ]
    hourly_temps = [
        round(
            base_temp
            + 4.5 * math.sin((hour - 8) / 24 * math.tau)
            + (hour % 3 - 1) * 0.3,
            1,
        )
        for hour in range(30)
    ]
    rain_probabilities = [
        max(5, min(92, int(42 + 40 * math.sin((hour - 3) / 8 * math.tau))))
        for hour in range(30)
    ]
    hourly_codes = [
        61 if probability >= 75 else 2 if probability >= 45 else 0
        for probability in rain_probabilities
    ]

    daily_times = [
        (now + timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(7)
    ]
    daily_codes = [0, 1, 2, 61, 80, 3, 0]
    daily_highs = [base_temp + value for value in (7, 6, 5, 2, 3, 4, 7)]
    daily_lows = [base_temp - value for value in (1, 1, 2, 3, 3, 2, 1)]
    daily_rain = [10, 20, 35, 80, 65, 25, 10]
    daily_uv = [6.2, 5.4, 4.8, 2.6, 3.1, 4.2, 6.5]

    return {
        "current": {
            "time": now.strftime("%Y-%m-%dT%H:%M"),
            "temperature_2m": hourly_temps[0],
            "relative_humidity_2m": 60 + seed % 18,
            "apparent_temperature": round(hourly_temps[0] + 1.4, 1),
            "is_day": 1 if 6 <= now.hour < 18 else 0,
            "precipitation": 0.0,
            "weather_code": hourly_codes[0],
            "cloud_cover": 35 + seed % 45,
            "pressure_msl": 1008 + seed % 9,
            "wind_speed_10m": 7 + seed % 9,
            "wind_direction_10m": (seed * 17) % 360,
            "wind_gusts_10m": 16 + seed % 14,
            "dew_point_2m": round(hourly_temps[0] - 7.5, 1),
        },
        "hourly": {
            "time": hourly_times,
            "temperature_2m": hourly_temps,
            "precipitation_probability": rain_probabilities,
            "weather_code": hourly_codes,
        },
        "daily": {
            "time": daily_times,
            "weather_code": daily_codes,
            "temperature_2m_max": daily_highs,
            "temperature_2m_min": daily_lows,
            "precipitation_probability_max": daily_rain,
            "uv_index_max": daily_uv,
            "sunrise": [f"{date}T06:12" for date in daily_times],
            "sunset": [f"{date}T18:08" for date in daily_times],
        },
    }


def demo_air_quality(lat: float, lon: float) -> dict[str, Any]:
    seed = int(abs(lat * 10 + lon * 10))
    aqi = 22 + seed % 48
    return {
        "current": {
            "european_aqi": aqi,
            "pm2_5": round(aqi * 0.72, 1),
            "pm10": round(aqi * 0.86, 1),
            "nitrogen_dioxide": round(aqi * 0.54, 1),
        }
    }
