from __future__ import annotations

from typing import Any

from demo_data import demo_air_quality, demo_forecast, demo_locations

DEMO_MODE = True


class WeatherApiError(RuntimeError):
    """Raised when weather data cannot be constructed."""


def get_locations(city_name: str) -> list[dict[str, Any]]:
    return demo_locations(city_name)


def get_forecast(lat: float, lon: float) -> dict[str, Any]:
    return demo_forecast(lat, lon)


def get_air_quality(lat: float, lon: float) -> dict[str, Any]:
    return demo_air_quality(lat, lon)
