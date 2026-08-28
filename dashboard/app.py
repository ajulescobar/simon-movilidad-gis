import json, math, base64, os, psycopg2, folium
import streamlit as st
import pandas as pd
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

st.set_page_config(page_title="Simon Movilidad: Dashboard BI", layout="wide")

ROUTE_PALETTE = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"]

ZONE_STYLES = {
    "urban_perimeter": ("#3b82f6", "Perímetro urbano"),
    "high_risk_zone":  ("#f59e0b", "Zona de alto riesgo"),
    "restricted_area": ("#ef4444", "Área restringida"),
}

_SPEED_GRADIENT = {0.3: "#f97316", 0.6: "#ef4444", 1.0: "#7f1d1d"}
_FUEL_GRADIENT  = {0.3: "#60a5fa", 0.6: "#2563eb", 1.0: "#1e3a8a"}


def _zone_style(zone_type):
    return ZONE_STYLES.get(zone_type, ("#9ca3af", zone_type))

_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_simon.png")
with open(_LOGO_PATH, "rb") as _f:
    _LOGO_B64 = base64.b64encode(_f.read()).decode()

st.markdown("""
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
.metric-card {
    background-color: #1e2530;
    border: 1px solid #2d3748;
    border-radius: 0;
    padding: 0 24px;
    text-align: center;
    height: 120px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 3px;
}
.metric-icon  { font-size: 18px; line-height: 1; }
.metric-label { font-size: 10px; color: #9ca3af; text-transform: uppercase; letter-spacing: 1px; }
.metric-value { font-size: 26px; font-weight: 700; color: #f3f4f6; line-height: 1; }
.metric-sub   { font-size: 10px; color: #6b7280; }

div[data-testid="stToggle"] {
    background: #1a2332;
    border: 1px solid #2d3748;
    border-radius: 4px;
    padding: 8px 14px;
    transition: border-color 0.15s;
    cursor: pointer;
}
div[data-testid="stToggle"]:hover {
    border-color: #4b5563;
}
div[data-testid="stToggle"] label > div {
    display: flex;
    align-items: center;
    gap: 10px;
}
div[data-testid="stToggle"] label p {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #d1d5db !important;
    letter-spacing: 0.4px;
    margin: 0 !important;
}


</style>
""", unsafe_allow_html=True)


_now   = datetime.now()
_TODAY = _now.strftime("%d %b %Y")
_NOW   = _now.strftime("%H:%M")

st.markdown(f"""
<div style="
    background:#ffffff;
    border-bottom: 3px solid #111827;
    padding: 10px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
">
    <div style="display:flex;align-items:center;gap:18px;">
        <img src="data:image/png;base64,{_LOGO_B64}"
             style="height:44px;object-fit:contain;">
        <div>
            <div style="font-size:20px;font-weight:700;color:#111827;
                        font-family:sans-serif;line-height:1.1;">
                Simon Movilidad
            </div>
            <div style="font-size:12px;color:#6b7280;font-family:sans-serif;
                        letter-spacing:0.3px;margin-top:3px;">
                Dashboard de Telemetria GIS
            </div>
        </div>
    </div>
    <div style="text-align:right;font-family:sans-serif;line-height:1.6;">
        <div style="font-size:12px;font-weight:600;color:#374151;">v 1.0</div>
        <div style="font-size:11px;color:#9ca3af;">{_TODAY} &nbsp;{_NOW}</div>
    </div>
</div>
""", unsafe_allow_html=True)


def metric_card(icon, label, value, sub=None):
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="metric-card">
        <span class="metric-icon">{icon}</span>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


@st.cache_data(ttl=30)
def load_vehicle_list():
    conn = get_connection()
    df = pd.read_sql("SELECT DISTINCT vehicle_id FROM raw_telemetry ORDER BY vehicle_id;", conn)
    conn.close()
    return df["vehicle_id"].tolist()


@st.cache_data(ttl=30)
def load_route(vehicle_id):
    conn = get_connection()
    df = pd.read_sql(
        """
        SELECT ST_Y(geom) AS lat, ST_X(geom) AS lon, speed_kmh, fuel_level, reported_at
        FROM raw_telemetry
        WHERE vehicle_id = %(vehicle_id)s
        ORDER BY reported_at;
        """,
        conn,
        params={"vehicle_id": vehicle_id},
    )
    conn.close()
    return df


@st.cache_data(ttl=30)
def load_all_telemetry():
    conn = get_connection()
    df = pd.read_sql("SELECT speed_kmh FROM raw_telemetry;", conn)
    conn.close()
    return df


@st.cache_data(ttl=30)
def load_avg_min_fuel():
    conn = get_connection()
    df = pd.read_sql(
        """
        SELECT AVG(min_fuel) AS avg_min_fuel
        FROM (
            SELECT vehicle_id, MIN(fuel_level) AS min_fuel
            FROM raw_telemetry
            GROUP BY vehicle_id
        ) AS por_vehiculo;
        """,
        conn,
    )
    conn.close()
    return df["avg_min_fuel"].iloc[0]


@st.cache_data(ttl=30)
def load_alerts_heatmap():
    conn = get_connection()
    df = pd.read_sql(
        """
        SELECT ST_Y(rt.geom) AS lat, ST_X(rt.geom) AS lon,
               rt.vehicle_id, 'velocidad' AS tipo
        FROM speed_alerts sa
        JOIN raw_telemetry rt ON rt.id = sa.telemetry_id
        UNION ALL
        SELECT ST_Y(rt.geom) AS lat, ST_X(rt.geom) AS lon,
               rt.vehicle_id, 'combustible' AS tipo
        FROM fuel_alerts fa
        JOIN raw_telemetry rt ON rt.id = fa.telemetry_id;
        """,
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=300)
def load_geofences():
    conn = get_connection()
    df = pd.read_sql(
        """
        SELECT name, zone_type, max_speed_kmh, ST_AsGeoJSON(geom) AS geojson
        FROM geofences
        ORDER BY id;
        """,
        conn,
    )
    conn.close()
    return df


vehicles = load_vehicle_list()

if not vehicles:
    st.warning("No hay datos de telemetria todavia. Corre el simulador primero.")
    st.stop()

# Fila 1: filtro de vehiculos
selected_vehicles = st.multiselect(
    "Seleccionar vehículos",
    vehicles,
    placeholder="Todos los vehículos",
)

is_all = len(selected_vehicles) == 0


all_alerts_df = load_alerts_heatmap()

if is_all:
    telemetry_df = load_all_telemetry()
    avg_speed = telemetry_df["speed_kmh"].mean()
    avg_min_fuel = load_avg_min_fuel()
    fuel_value = f"{avg_min_fuel:.1f}%"
    fuel_sub = "FINAL PROMEDIO RECORRIDO"
    alerts_df = all_alerts_df
else:
    route_dfs = {v: load_route(v) for v in selected_vehicles}
    avg_speed = pd.concat([df["speed_kmh"] for df in route_dfs.values()]).mean()
    last_fuels = [df["fuel_level"].iloc[-1] for df in route_dfs.values()]
    fuel_value = f"{sum(last_fuels) / len(last_fuels):.1f}%"
    fuel_sub = "FINAL PROMEDIO RECORRIDO" if len(selected_vehicles) > 1 else "FINAL RECORRIDO"
    alerts_df = all_alerts_df[all_alerts_df["vehicle_id"].isin(selected_vehicles)]

speed_alerts = alerts_df[alerts_df["tipo"] == "velocidad"]
fuel_alerts  = alerts_df[alerts_df["tipo"] == "combustible"]

m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_card(
        '<i class="fas fa-triangle-exclamation" style="color:#f87171;"></i>',
        "Exceso de velocidad",
        len(speed_alerts),
        sub="EN GEOCERCAS",
    )
with m2:
    metric_card(
        '<i class="fas fa-gauge-high" style="color:#60a5fa;"></i>',
        "Velocidad promedio",
        f"{avg_speed:.1f} km/h",
        sub="EN LA RUTA",
    )
with m3:
    metric_card(
        '<i class="fas fa-battery-quarter" style="color:#fb923c;"></i>',
        "Alertas combustible",
        len(fuel_alerts),
        sub="AUTONOMÍA MENOR A 100 km",
    )
with m4:
    metric_card(
        '<i class="fas fa-gas-pump" style="color:#fbbf24;"></i>',
        "Nivel Combustible",
        fuel_value,
        sub=fuel_sub,
    )

st.write("")


st.markdown(
    '<p style="font-size:10px;color:#6b7280;text-transform:uppercase;'
    'letter-spacing:1px;margin:8px 0 4px;">Capas del mapa</p>',
    unsafe_allow_html=True,
)
_lc1, _lc2, _ = st.columns([2, 2, 5])
with _lc1:
    show_heatmap = st.toggle("Mapa de calor", value=True, key="show_heatmap")
with _lc2:
    show_geofences = st.toggle("Geocercas", value=True, key="show_geofences")


if not is_all:
    all_lats = pd.concat([df["lat"] for df in route_dfs.values()])
    all_lons = pd.concat([df["lon"] for df in route_dfs.values()])
    center_lat, center_lon = all_lats.mean(), all_lons.mean()
else:
    center_lat, center_lon = 3.43, -76.52

geofences_df = load_geofences() if show_geofences else pd.DataFrame()

main_map = folium.Map(location=[center_lat, center_lon], zoom_start=12)

# Bounds combinados: rutas + geocercas para que nada quede cortado
bound_lats = list(all_lats) if not is_all else []
bound_lons = list(all_lons) if not is_all else []

if is_all and show_geofences and not geofences_df.empty:
    for _, gf in geofences_df.iterrows():
        gj = json.loads(gf["geojson"])
        for lon, lat in gj["coordinates"][0]:
            bound_lats.append(lat)
            bound_lons.append(lon)

if bound_lats:
    main_map.fit_bounds(
        [[min(bound_lats), min(bound_lons)], [max(bound_lats), max(bound_lons)]],
        padding=[40, 40],
    )


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _route_km(df):
    total = 0.0
    for i in range(1, len(df)):
        total += _haversine_km(
            df.iloc[i - 1]["lat"], df.iloc[i - 1]["lon"],
            df.iloc[i]["lat"], df.iloc[i]["lon"],
        )
    return total


def _marker_tooltip(label, lat, lon, v_id, dist_km):
    lat_s = f"{abs(lat):.6f}° {'N' if lat >= 0 else 'S'}"
    lon_s = f"{abs(lon):.6f}° {'E' if lon >= 0 else 'W'}"
    html = f"""
    <div style="font-family:sans-serif;padding:4px 2px;min-width:220px;">
      <div style="font-weight:700;font-size:13px;color:#111827;
                  border-bottom:1px solid #e5e7eb;padding-bottom:5px;margin-bottom:7px;">
        {label}
      </div>
      <table style="font-size:12px;color:#374151;border-collapse:collapse;width:100%;">
        <tr>
          <td style="color:#6b7280;padding:2px 10px 2px 0;white-space:nowrap;">Vehículo</td>
          <td style="font-weight:600;">{v_id}</td>
        </tr>
        <tr>
          <td style="color:#6b7280;padding:2px 10px 2px 0;">Latitud</td>
          <td style="font-family:monospace;font-weight:600;">{lat_s}</td>
        </tr>
        <tr>
          <td style="color:#6b7280;padding:2px 10px 2px 0;">Longitud</td>
          <td style="font-family:monospace;font-weight:600;">{lon_s}</td>
        </tr>
        <tr>
          <td style="color:#6b7280;padding:2px 10px 2px 0;">Distancia ruta</td>
          <td style="font-weight:600;">{dist_km:.2f} km</td>
        </tr>
      </table>
    </div>
    """
    return folium.Tooltip(html, sticky=False)


def _pin(letter):
    return folium.DivIcon(
        html=f"""
        <div style="
            background:white; color:#111827; border-radius:50%;
            width:28px; height:28px; display:flex; align-items:center;
            justify-content:center; font-weight:700; font-size:13px;
            border:2px solid #374151;
            box-shadow:0 2px 8px rgba(0,0,0,0.45);
            font-family:sans-serif;">{letter}</div>""",
        icon_size=(28, 28),
        icon_anchor=(14, 14),
    )


# Capas de ruta
if not is_all:
    for i, (v_id, route_df) in enumerate(route_dfs.items()):
        color = ROUTE_PALETTE[i % len(ROUTE_PALETTE)]
        layer = folium.FeatureGroup(name=f"Ruta: {v_id}", show=True)
        points = list(zip(route_df["lat"], route_df["lon"]))
        dist_km = _route_km(route_df)

        folium.PolyLine(points, color=color, weight=8, opacity=0.15).add_to(layer)
        folium.PolyLine(points, color=color, weight=3, opacity=0.95, tooltip=v_id).add_to(layer)

        folium.Marker(
            location=points[0],
            tooltip=_marker_tooltip("Punto A. Inicio de ruta", points[0][0], points[0][1], v_id, dist_km),
            icon=_pin("A"),
        ).add_to(layer)

        folium.Marker(
            location=points[-1],
            tooltip=_marker_tooltip("Punto B. Fin de ruta", points[-1][0], points[-1][1], v_id, dist_km),
            icon=_pin("B"),
        ).add_to(layer)

        layer.add_to(main_map)

# Capas de infracciones
if show_heatmap:
    if not speed_alerts.empty:
        s_layer = folium.FeatureGroup(name="Exceso de velocidad", show=True)
        HeatMap(
            speed_alerts[["lat", "lon"]].values.tolist(),
            radius=15, blur=20,
            gradient=_SPEED_GRADIENT,
        ).add_to(s_layer)
        s_layer.add_to(main_map)

    if not fuel_alerts.empty:
        f_layer = folium.FeatureGroup(name="Bajo combustible", show=True)
        HeatMap(
            fuel_alerts[["lat", "lon"]].values.tolist(),
            radius=15, blur=20,
            gradient=_FUEL_GRADIENT,
        ).add_to(f_layer)
        f_layer.add_to(main_map)

# Capa de geocercas
if show_geofences:
    if not geofences_df.empty:
        geo_layer = folium.FeatureGroup(name="Geocercas", show=True)
        for _, gf in geofences_df.iterrows():
            geojson = json.loads(gf["geojson"])
            coords = [[lat, lon] for lon, lat in geojson["coordinates"][0]]
            color, zone_label = _zone_style(gf["zone_type"])

            popup_html = f"""
            <div style="font-family:sans-serif;min-width:210px;padding:2px;">
              <div style="font-weight:700;font-size:13px;color:#111827;
                          border-left:3px solid {color};padding-left:8px;margin-bottom:10px;">
                {gf['name']}
              </div>
              <table style="width:100%;font-size:12px;color:#374151;border-collapse:collapse;">
                <tr>
                  <td style="color:#6b7280;padding:4px 12px 4px 0;white-space:nowrap;">Tipo de zona</td>
                  <td style="font-weight:600;">{zone_label}</td>
                </tr>
                <tr>
                  <td style="color:#6b7280;padding:4px 12px 4px 0;">Velocidad máxima</td>
                  <td style="font-weight:600;">{int(gf['max_speed_kmh'])} km/h</td>
                </tr>
              </table>
            </div>
            """

            folium.Polygon(
                locations=coords,
                color=color,
                weight=2,
                opacity=0.85,
                fill=True,
                fill_color=color,
                fill_opacity=0.06,
                dash_array="8 5",
                popup=folium.Popup(popup_html, max_width=280),
            ).add_to(geo_layer)
        geo_layer.add_to(main_map)


def _legend_row(sym, label):
    return (
        f'<tr style="height:26px;">'
        f'<td style="width:30px;text-align:center;vertical-align:middle;">{sym}</td>'
        f'<td style="vertical-align:middle;padding-left:6px;line-height:1;">{label}</td>'
        f'</tr>'
    )


# Leyenda dinamica
_PIN_STYLE = (
    "background:white;color:#111827;border-radius:50%;width:18px;height:18px;"
    "display:flex;align-items:center;justify-content:center;font-weight:700;"
    "font-size:10px;border:1.5px solid #374151;margin:auto;font-family:sans-serif;"
)

legend_rows = ""

if not is_all:
    for label, letter in [("Inicio de ruta", "A"), ("Fin de ruta", "B")]:
        legend_rows += _legend_row(f'<div style="{_PIN_STYLE}">{letter}</div>', label)
    for i, v_id in enumerate(selected_vehicles):
        color = ROUTE_PALETTE[i % len(ROUTE_PALETTE)]
        legend_rows += _legend_row(
            f'<span style="width:22px;height:3px;background:{color};display:inline-block;border-radius:2px;"></span>',
            v_id,
        )

if show_heatmap and not speed_alerts.empty:
    legend_rows += _legend_row(
        '<div style="width:22px;height:10px;border-radius:2px;margin:auto;'
        'background:linear-gradient(to right,#f97316,#ef4444,#7f1d1d);"></div>',
        "Exceso de velocidad",
    )

if show_heatmap and not fuel_alerts.empty:
    legend_rows += _legend_row(
        '<div style="width:22px;height:10px;border-radius:2px;margin:auto;'
        'background:linear-gradient(to right,#60a5fa,#2563eb,#1e3a8a);"></div>',
        "Bajo combustible",
    )

if show_geofences and not geofences_df.empty:
    seen_types = set()
    for _, gf in geofences_df.iterrows():
        zt = gf["zone_type"]
        if zt not in seen_types:
            seen_types.add(zt)
            color, zone_label = _zone_style(zt)
            legend_rows += _legend_row(
                f'<div style="width:20px;height:14px;margin:auto;border:2px dashed {color};'
                f'background:transparent;border-radius:1px;"></div>',
                zone_label,
            )

if legend_rows:
    main_map.get_root().html.add_child(folium.Element(f"""
<div style="
    position:fixed; bottom:24px; right:16px; z-index:9999;
    background:#1e2530; border:1px solid #374151;
    font-family:sans-serif; font-size:11px; color:#e5e7eb;
    box-shadow:0 2px 10px rgba(0,0,0,.5); min-width:170px; pointer-events:none;">
  <div style="padding:7px 12px 6px; font-weight:700; font-size:10px;
              color:#f9fafb; text-transform:uppercase; letter-spacing:1px;
              border-bottom:1px solid #374151;">Leyenda</div>
  <div style="padding:4px 12px 10px;">
    <table style="border-collapse:collapse; width:100%;">
      {legend_rows}
    </table>
  </div>
</div>
"""))


st_folium(main_map, use_container_width=True, height=580, returned_objects=[])