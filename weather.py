from flask import Flask, render_template, request

from weather_service import DEMO_MODE, WeatherApiError, get_locations
from weather_processing import build_weather_info

app = Flask(__name__)

CITY_SUGGESTIONS = (
    "北京",
    "上海",
    "广州",
    "深圳市南山区",
    "佛山市禅城区",
    "揭阳市揭东区",
)


@app.route("/", methods=["GET", "POST"])
def index():
    weather_info = None
    city_name = ""
    geo_list = None
    error_message = None

    if request.method == "POST":
        city_name = (request.form.get("city") or "").strip()
        if not city_name:
            error_message = "请输入要查询的城市或地区"
        else:
            try:
                geo_list = get_locations(city_name)
                if not geo_list:
                    error_message = "没有找到匹配的城市或地区"
                    geo_list = None
                else:
                    selected_idx = request.form.get("selected_idx")
                    selected_location = None
                    if selected_idx not in (None, ""):
                        try:
                            index_value = int(selected_idx)
                        except ValueError:
                            index_value = -1
                        if 0 <= index_value < len(geo_list):
                            selected_location = geo_list[index_value]
                        else:
                            error_message = "所选地点无效，请重新选择"
                    elif len(geo_list) == 1:
                        selected_location = geo_list[0]

                    if selected_location is not None:
                        weather_info = build_weather_info(selected_location)
                        geo_list = None
            except WeatherApiError as exc:
                error_message = str(exc)
                geo_list = None
            except (KeyError, TypeError, ValueError):
                error_message = "地点或天气数据解析失败，请重新查询"
                geo_list = None

    return render_template(
        "index.html",
        weather=weather_info,
        city=city_name,
        geo_list=geo_list,
        error_message=error_message,
        city_suggestions=CITY_SUGGESTIONS,
        demo_mode=DEMO_MODE,
    )


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5020)
