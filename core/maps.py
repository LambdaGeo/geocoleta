import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap

def render_map(df, profile):
    
    if not profile["geo"]:
        return

    col = profile["geo"][0]
    coords = df[col].dropna()

    if coords.empty:
        return

    points = [
        (float(p["latitude"]), float(p["longitude"]))
        for p in coords
    ]

    center = points[0]

    mapa = folium.Map(
        location=center,
        zoom_start=14,
        tiles="CartoDB positron"
    )

    HeatMap(points).add_to(mapa)
    folium_static(mapa)
