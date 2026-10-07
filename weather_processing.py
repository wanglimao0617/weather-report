from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from weather_service import WeatherApiError, get_air_quality, get_forecast

WEATHER_META = {
    0: {"text": "晴空万里", "icon": "sun", "theme": "clear"},
    1: {"text": "云淡风清（晴间多云）", "icon": "cloud-sun", "theme": "clear"},
    2: {"text": "层云蔽日（多云）", "icon": "cloud-sun", "theme": "cloud"},
    3: {"text": "阴云密布（阴天）", "icon": "cloud", "theme": "cloud"},
    45: {"text": "雾气弥漫", "icon": "cloud-fog", "theme": "mist"},
    48: {"text": "雾凇", "icon": "cloud-fog", "theme": "mist"},
    51: {"text": "细雨濛濛", "icon": "cloud-drizzle", "theme": "rain"},
    53: {"text": "毛雨霏霏", "icon": "cloud-drizzle", "theme": "rain"},
    55: {"text": "密雨沾衣", "icon": "cloud-drizzle", "theme": "rain"},
    56: {"text": "微雨沾裳", "icon": "cloud-drizzle", "theme": "rain"},
    57: {"text": "冻雨淅沥", "icon": "cloud-drizzle", "theme": "rain"},
    61: {"text": "细雨如丝", "icon": "cloud-rain", "theme": "rain"},
    63: {"text": "雨声淅沥（中雨）", "icon": "cloud-rain", "theme": "rain"},
    65: {"text": "大雨滂沱", "icon": "cloud-rain", "theme": "rain"},
    66: {"text": "冻雨淅沥（轻微冻雨）", "icon": "cloud-rain", "theme": "rain"},
    67: {"text": "冻雨如注（强冻雨）", "icon": "cloud-rain", "theme": "rain"},
    71: {"text": "飞雪轻扬（小雪）", "icon": "cloud-snow", "theme": "snow"},
    73: {"text": "雪落纷纷（中雪）", "icon": "cloud-snow", "theme": "snow"},
    75: {"text": "鹅毛大雪（大雪）", "icon": "cloud-snow", "theme": "snow"},
    77: {"text": "碎雪扑面（米雪）", "icon": "cloud-snow", "theme": "snow"},
    80: {"text": "阵雨忽来（小阵雨）", "icon": "cloud-sun-rain", "theme": "rain"},
    81: {"text": "骤雨阵阵（中阵雨）", "icon": "cloud-sun-rain", "theme": "rain"},
    82: {"text": "骤雨倾盆（强阵雨）", "icon": "cloud-sun-rain", "theme": "rain"},
    85: {"text": "飞雪零星（小阵雪）", "icon": "cloud-snow", "theme": "snow"},
    86: {"text": "风雪扑面（强阵雪）", "icon": "cloud-snow", "theme": "snow"},
    95: {"text": "雷雨交加（雷阵雨）", "icon": "cloud-lightning", "theme": "storm"},
    96: {"text": "雷雨夹雹（小冰雹）", "icon": "cloud-lightning", "theme": "storm"},
    99: {"text": "雷雨冰雹齐下（强冰雹）", "icon": "cloud-lightning", "theme": "storm"},
}

WIND_DIRECTIONS = ("北", "东北", "东", "东南", "南", "西南", "西", "西北")


def round_number(value: Any, digits: int = 0) -> Any:
    if isinstance(value, (int, float)):
        return round(value, digits)
    return value


def weather_meta(code: Any, is_day: bool = True) -> dict[str, str]:
    try:
        normalized_code = int(code)
    except (TypeError, ValueError):
        normalized_code = -1

    meta = WEATHER_META.get(
        normalized_code,
        {"text": "天气未知", "icon": "cloud", "theme": "cloud"},
    ).copy()
    if not is_day and normalized_code == 0:
        meta.update({"text": "晴朗夜空", "icon": "moon", "theme": "night"})
    elif not is_day and normalized_code in (1, 2):
        meta.update({"text": "夜间多云", "icon": "moon", "theme": "night"})
    elif not is_day:
        meta["theme"] = "night"
    return meta


def wind_direction_text(degrees: Any) -> str:
    try:
        index = int(round(float(degrees) / 45)) % len(WIND_DIRECTIONS)
    except (TypeError, ValueError):
        return "未知"
    return WIND_DIRECTIONS[index]


def uv_level(value: Any) -> str:
    try:
        uv = float(value)
    except (TypeError, ValueError):
        return "暂无数据"
    if uv < 3:
        return "较弱"
    if uv < 6:
        return "中等"
    if uv < 8:
        return "较强"
    if uv < 11:
        return "很强"
    return "极强"


def air_quality_level(value: Any) -> tuple[str, str]:
    try:
        aqi = float(value)
    except (TypeError, ValueError):
        return "unknown", "暂无数据"
    if aqi <= 20:
        return "good", "优"
    if aqi <= 40:
        return "fair", "良"
    if aqi <= 60:
        return "moderate", "中等"
    if aqi <= 80:
        return "poor", "较差"
    if aqi <= 100:
        return "very-poor", "很差"
    return "extreme", "极差"


def build_hourly_forecast(forecast: dict[str, Any]) -> list[dict[str, Any]]:
    hourly = forecast.get("hourly") or {}
    current = forecast.get("current") or {}
    times = hourly.get("time") or []
    if not times:
        return []

    try:
        current_time = datetime.fromisoformat(current["time"]).replace(
            minute=0, second=0, microsecond=0
        )
    except (KeyError, TypeError, ValueError):
        current_time = datetime.fromisoformat(times[0]).replace(
            minute=0, second=0, microsecond=0
        )

    start_index = 0
    for index, time_value in enumerate(times):
        try:
            if datetime.fromisoformat(time_value) >= current_time:
                start_index = index
                break
        except (TypeError, ValueError):
            continue

    result = []
    for offset, index in enumerate(range(start_index, min(start_index + 24, len(times)))):
        try:
            forecast_time = datetime.fromisoformat(times[index])
        except (TypeError, ValueError):
            continue

        code = (hourly.get("weather_code") or [None] * len(times))[index]
        meta = weather_meta(code, True)
        precip_probability = (
            hourly.get("precipitation_probability") or [0] * len(times)
        )[index]
        result.append(
            {
                "label": "现在" if offset == 0 else forecast_time.strftime("%H:%M"),
                "date": forecast_time.strftime("%m/%d"),
                "temp": round_number(
                    (hourly.get("temperature_2m") or [None] * len(times))[index]
                ),
                "precip_probability": round_number(precip_probability or 0),
                "text": meta["text"],
                "icon": meta["icon"],
            }
        )
    return result


def build_daily_forecast(forecast: dict[str, Any]) -> list[dict[str, Any]]:
    daily = forecast.get("daily") or {}
    dates = daily.get("time") or []
    if not dates:
        return []

    weekdays = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
    items = []
    for index, date_value in enumerate(dates):
        try:
            date = datetime.fromisoformat(date_value)
        except (TypeError, ValueError):
            continue

        code = (daily.get("weather_code") or [None] * len(dates))[index]
        meta = weather_meta(code, True)
        items.append(
            {
                "date": date.strftime("%m/%d"),
                "weekday": "今天" if index == 0 else weekdays[date.weekday()],
                "text": meta["text"],
                "icon": meta["icon"],
                "temp_min": round_number(
                    (daily.get("temperature_2m_min") or [None] * len(dates))[index]
                ),
                "temp_max": round_number(
                    (daily.get("temperature_2m_max") or [None] * len(dates))[index]
                ),
                "precip_probability": round_number(
                    (daily.get("precipitation_probability_max") or [0] * len(dates))[
                        index
                    ]
                    or 0
                ),
                "uv_index": round_number(
                    (daily.get("uv_index_max") or [None] * len(dates))[index], 1
                ),
                "sunrise": (daily.get("sunrise") or [None] * len(dates))[index],
                "sunset": (daily.get("sunset") or [None] * len(dates))[index],
            }
        )

    numeric_items = [
        item
        for item in items
        if isinstance(item["temp_min"], (int, float))
        and isinstance(item["temp_max"], (int, float))
    ]
    if numeric_items:
        week_min = min(item["temp_min"] for item in numeric_items)
        week_max = max(item["temp_max"] for item in numeric_items)
        span = max(week_max - week_min, 1)
        for item in numeric_items:
            item["range_left"] = round(
                (item["temp_min"] - week_min) / span * 100, 1
            )
            item["range_width"] = round(
                max((item["temp_max"] - item["temp_min"]) / span * 100, 4), 1
            )
    return items


def build_air_quality(air_data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not air_data:
        return None
    current = air_data.get("current") or {}
    aqi = current.get("european_aqi")
    level, label = air_quality_level(aqi)
    return {
        "value": round_number(aqi),
        "level": level,
        "label": label,
        "pm2_5": round_number(current.get("pm2_5")),
        "pm10": round_number(current.get("pm10")),
        "no2": round_number(current.get("nitrogen_dioxide")),
    }


def build_travel_advice(
    current: dict[str, Any],
    today: dict[str, Any],
    air_quality: dict[str, Any] | None,
) -> list[dict[str, str]]:
    advice: list[dict[str, str]] = []
    code = current.get("code")
    temp = current.get("temp")
    wind_gust = current.get("wind_gust")
    precip_probability = today.get("precip_probability") or 0
    uv_index = today.get("uv_index") or 0

    if isinstance(code, int) and code >= 95:
        advice.append(
            {
                "level": "warning",
                "title": "雷暴天气",
                "detail": "请尽量避免户外活动，远离高处、水域和孤立树木。",
            }
        )
    elif isinstance(code, int) and code in {
        51,
        53,
        55,
        56,
        57,
        61,
        63,
        65,
        66,
        67,
        80,
        81,
        82,
    }:
        advice.append(
            {
                "level": "notice",
                "title": "携带雨具",
                "detail": "当前有降水，路面可能湿滑，通勤请预留更多时间。",
            }
        )
    elif isinstance(code, int) and code in {71, 73, 75, 77, 85, 86}:
        advice.append(
            {
                "level": "warning",
                "title": "雪天慢行",
                "detail": "注意道路结冰，驾车和步行都应降低速度。",
            }
        )

    if precip_probability >= 60 and not any(
        item["title"] == "携带雨具" for item in advice
    ):
        advice.append(
            {
                "level": "notice",
                "title": "降水概率较高",
                "detail": f"今日降水概率约 {precip_probability}%，建议随身携带雨具。",
            }
        )

    if isinstance(wind_gust, (int, float)) and wind_gust >= 35:
        advice.append(
            {
                "level": "warning",
                "title": "阵风较强",
                "detail": (
                    f"阵风可达 {round_number(wind_gust)} km/h，"
                    "注意高空坠物并减少骑行。"
                ),
            }
        )

    if isinstance(temp, (int, float)) and temp >= 32:
        advice.append(
            {
                "level": "warning",
                "title": "高温防护",
                "detail": "注意补水，减少午后长时间户外活动。",
            }
        )
    elif isinstance(temp, (int, float)) and temp <= 5:
        advice.append(
            {
                "level": "notice",
                "title": "注意保暖",
                "detail": "气温偏低，外出请增添衣物并注意早晚温差。",
            }
        )

    if isinstance(uv_index, (int, float)) and uv_index >= 7:
        advice.append(
            {
                "level": "notice",
                "title": "紫外线较强",
                "detail": f"今日紫外线指数 {uv_index}，建议做好防晒。",
            }
        )

    if air_quality and air_quality["level"] in {"poor", "very-poor", "extreme"}:
        advice.append(
            {
                "level": "warning",
                "title": "空气质量欠佳",
                "detail": (
                    f"空气质量等级为“{air_quality['label']}”，"
                    "敏感人群应减少户外活动。"
                ),
            }
        )

    if not advice:
        advice.append(
            {
                "level": "good",
                "title": "适宜出行",
                "detail": "当前气象条件较平稳，适合日常通勤与户外活动。",
            }
        )
    return advice


def build_weather_info(location: dict[str, Any]) -> dict[str, Any]:
    try:
        lon_text, lat_text = location["location"].split(",")
        lat = float(lat_text)
        lon = float(lon_text)
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherApiError("地点坐标无效，请重新查询") from exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        forecast_future = executor.submit(get_forecast, lat, lon)
        air_quality_future = executor.submit(get_air_quality, lat, lon)
        forecast = forecast_future.result()
        try:
            air_data = air_quality_future.result()
        except WeatherApiError:
            air_data = None

    current_raw = forecast.get("current") or {}
    current_code = current_raw.get("weather_code", current_raw.get("weathercode"))
    is_day = bool(current_raw.get("is_day", 1))
    meta = weather_meta(current_code, is_day)
    hourly = build_hourly_forecast(forecast)
    daily = build_daily_forecast(forecast)
    if not daily:
        raise WeatherApiError("暂时无法获取未来天气数据")

    today = daily[0].copy()
    for key in ("sunrise", "sunset"):
        try:
            today[key] = datetime.fromisoformat(today[key]).strftime("%H:%M")
        except (TypeError, ValueError):
            today[key] = "--:--"

    current = {
        "temp": round_number(current_raw.get("temperature_2m")),
        "feel": round_number(current_raw.get("apparent_temperature")),
        "humidity": round_number(current_raw.get("relative_humidity_2m")),
        "precip": round_number(current_raw.get("precipitation"), 1),
        "wind_speed": round_number(current_raw.get("wind_speed_10m")),
        "wind_dir": round_number(current_raw.get("wind_direction_10m")),
        "wind_dir_text": wind_direction_text(current_raw.get("wind_direction_10m")),
        "wind_gust": round_number(current_raw.get("wind_gusts_10m")),
        "pressure": round_number(current_raw.get("pressure_msl")),
        "cloud_cover": round_number(current_raw.get("cloud_cover")),
        "dew_point": round_number(current_raw.get("dew_point_2m")),
        "code": current_code,
        "text": meta["text"],
        "icon": meta["icon"],
        "is_day": is_day,
    }
    today["uv_level"] = uv_level(today.get("uv_index"))
    air_quality = build_air_quality(air_data)

    try:
        updated_at = datetime.fromisoformat(current_raw["time"]).strftime(
            "%m月%d日 %H:%M"
        )
    except (KeyError, TypeError, ValueError):
        updated_at = "刚刚"

    return {
        "addr": location.get("formatted_address")
        or location.get("address")
        or "未知地点",
        "updated_at": updated_at,
        "coordinates": f"{lat:.3f}, {lon:.3f}",
        "theme": meta["theme"],
        "current": current,
        "today": today,
        "hourly": hourly,
        "daily": daily,
        "air_quality": air_quality,
        "advice": build_travel_advice(current, today, air_quality),
    }


