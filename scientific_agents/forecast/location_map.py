"""Offline China location figure for HTML/PDF reports; never changes source coordinates."""
from functools import lru_cache
import json
from math import atan2, cos, pi, sin, sqrt
from pathlib import Path

from .config import Location


def gcj02(location: Location):
    """Display conversion adapted from MIT coordtransform; see assets license/README."""
    lon, lat = location.longitude, location.latitude
    if lon is None or lat is None:
        return None
    if location.coordinate_system == "BD09":
        x, y = lon - .0065, lat - .006
        z = sqrt(x*x + y*y) - .00002*sin(y*pi*3000/180)
        theta = atan2(y, x) - .000003*cos(x*pi*3000/180)
        return z*cos(theta), z*sin(theta)
    if location.coordinate_system == "GCJ02" or not (72.004 <= lon <= 137.8347 and .8293 <= lat <= 55.8271):
        return lon, lat
    x, y = lon - 105, lat - 35
    dlat = -100 + 2*x + 3*y + .2*y*y + .1*x*y + .2*sqrt(abs(x))
    dlon = 300 + x + 2*y + .1*x*x + .1*x*y + .1*sqrt(abs(x))
    shared = (20*sin(6*x*pi) + 20*sin(2*x*pi))*2/3
    dlat += shared + (20*sin(y*pi) + 40*sin(y*pi/3))*2/3 + (160*sin(y*pi/12) + 320*sin(y*pi/30))*2/3
    dlon += shared + (20*sin(x*pi) + 40*sin(x*pi/3))*2/3 + (150*sin(x*pi/12) + 300*sin(x*pi/30))*2/3
    rad = lat*pi/180
    magic = 1 - .00669342162296594323*sin(rad)**2
    dlat = dlat*180 / ((6378245*(1-.00669342162296594323))/(magic*sqrt(magic))*pi)
    dlon = dlon*180 / (6378245/sqrt(magic)*cos(rad)*pi)
    return lon + dlon, lat + dlat


@lru_cache(maxsize=1)
def boundaries():
    data = json.loads((Path(__file__).parent / "assets/china.geojson").read_text(encoding="utf-8"))
    rings = []
    for feature in data["features"]:
        geometry = feature["geometry"]
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        rings.extend(polygon[0] for polygon in polygons)
    return rings


def render_location(raw, path: Path):
    """Return a readable reason if unplottable; otherwise save a PNG and return None."""
    try:
        location = Location.model_validate(raw)
    except ValueError:
        return "位置信息不完整或坐标无效，暂不标点。"
    point = gcj02(location)
    if point is None:
        return "尚未提供经纬度，暂不标点。"
    lon, lat = point
    in_main = 73 <= lon <= 136 and 18 <= lat <= 54
    in_inset = 105 <= lon <= 125 and 3 <= lat <= 25
    if not (in_main or in_inset):
        return "坐标超出本报告中国地图图幅，保留原始位置说明。"

    from matplotlib.figure import Figure
    from matplotlib.patches import Polygon
    from matplotlib import font_manager
    fonts = {font.name for font in font_manager.fontManager.ttflist}
    font = next((name for name in ["Microsoft YaHei", "Noto Sans CJK SC", "Noto Sans CJK JP", "Source Han Sans SC", "SimHei", "SimSun",
                                 "WenQuanYi Micro Hei", "WenQuanYi Zen Hei", "Droid Sans Fallback"] if name in fonts), "DejaVu Sans")
    chinese = font != "DejaVu Sans"
    figure = Figure(figsize=(7, 4.4), facecolor="#f6f9fc")
    main = figure.add_axes([.02, .04, .96, .87])
    inset = figure.add_axes([.78, .08, .19, .30])
    for axis, limits in [(main, (73,136,18,54)), (inset, (105,125,3,25))]:
        axis.set_facecolor("#f6f9fc")
        for ring in boundaries():
            axis.add_patch(Polygon(ring, facecolor="#e4edf3", edgecolor="#91a9b9", linewidth=.4))
        axis.set_xlim(limits[:2]); axis.set_ylim(limits[2:])
        axis.set_aspect(1/cos(35*pi/180))
        axis.set_xticks([]); axis.set_yticks([])
        for spine in axis.spines.values():
            spine.set_visible(axis is inset)
            spine.set_color("#b8c8d2")
        if limits[0] <= lon <= limits[1] and limits[2] <= lat <= limits[3]:
            axis.scatter([lon], [lat], s=64, color="#d36d38", edgecolors="white", linewidths=1.2, zorder=5)
            label = location.name or location.address or "数据位置"
            # Put eastern labels to the left; wrap long names to keep them inside the map.
            label = "\n".join(label[i:i + 12] for i in range(0, len(label), 12))
            left = lon > (limits[0] + limits[1]) / 2
            axis.annotate(label, (lon,lat), xytext=(-7 if left else 7, 9), textcoords="offset points",
                          ha="right" if left else "left", va="bottom", color="#a7451c", fontsize=10,
                          fontfamily=font, zorder=6,
                          bbox=dict(boxstyle="round,pad=.25", facecolor="#f6f9fc", edgecolor="none", alpha=.9))
    figure.text(.04,.95,"中国 · 数据位置" if chinese else "China - data location",fontfamily=font,fontsize=12,color="#20384b")
    inset.set_title("南海诸岛" if chinese else "South China Sea",fontfamily=font,fontsize=7,color="#627e90")
    temporary = path.with_suffix(".png.tmp")
    figure.savefig(temporary, format="png", dpi=180, facecolor=figure.get_facecolor())
    temporary.replace(path)
    return None
