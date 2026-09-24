import html

import folium
import streamlit as st
from folium.plugins import HeatMap

from geocoleta.core.model import Dataset
from geocoleta.ui.compat import html_frame

POINT_COLOR = "#2a78d6"


def location_field(dataset: Dataset, config_map: dict):
    key = (config_map or {}).get("campo")
    if key:
        return dataset.find(key)
    found = dataset.of_kind("location")
    return found[0] if found else None


def render_map(dataset: Dataset, df, config_map: dict, key="map", height=460):
    f = location_field(dataset, config_map)
    if f is None or f.lat not in df.columns:
        return False

    points = df.dropna(subset=[f.lat, f.lon])
    missing = len(df) - len(points)
    if points.empty:
        st.info("Nenhuma resposta com localização no filtro atual.")
        return True

    popup_fields = [p for p in (dataset.find(k) for k in (config_map or {}).get("popup", [])) if p]
    mode = st.radio("Visualização", ["Pontos", "Calor"], horizontal=True, key=f"{key}_mode",
                    label_visibility="collapsed")

    center = [points[f.lat].mean(), points[f.lon].mean()]
    fmap = folium.Map(location=center, zoom_start=13, tiles="OpenStreetMap", height=height)
    if mode == "Calor":
        HeatMap(points[[f.lat, f.lon]].values.tolist(), radius=18).add_to(fmap)
    else:
        for _, row in points.iterrows():
            lines = [f"<b>{html.escape(p.label)}</b>: {html.escape(str(row[p.column]))}"
                     for p in popup_fields if p.column in row and str(row[p.column]) != "nan"]
            folium.CircleMarker(
                [row[f.lat], row[f.lon]], radius=6, weight=2, color="white",
                fill=True, fill_color=POINT_COLOR, fill_opacity=0.9,
                popup=folium.Popup("<br>".join(lines), max_width=260) if lines else None,
            ).add_to(fmap)
    fmap.fit_bounds([[points[f.lat].min(), points[f.lon].min()], [points[f.lat].max(), points[f.lon].max()]],
                   max_zoom=15)  # com um só ponto, evita zoom no nível de quadra

    # HTML estático: altura exata e sem rerun do Streamlit a cada movimento do mapa
    html_frame(fmap.get_root().render(), height)
    if missing:
        st.caption(f"{missing} respostas sem coordenadas não aparecem no mapa.")
    return True
