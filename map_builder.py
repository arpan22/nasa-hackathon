import folium
from folium.plugins import HeatMap

def get_aqi_color(aqi):
    if aqi <= 50: return "green"
    elif aqi <= 100: return "yellow"
    elif aqi <= 150: return "orange"
    elif aqi <= 200: return "red"
    elif aqi <= 300: return "purple"
    return "maroon"

def make_map(df_aqi=None, df_aod=None, df_pred=None, show_pred='both'):
    print("🗺️ Building map...")
    m = folium.Map(location=[39.5, -98.35], zoom_start=5, tiles="cartodbpositron")

    # === Current AQI ===
    if df_aqi is not None and len(df_aqi) > 0 and show_pred in ['both', 'current']:
        aqi_layer = folium.FeatureGroup(name="Current AQI Levels")
        for _, row in df_aqi.iterrows():
            color = get_aqi_color(row.get("aqi", 0))
            city = row.get("city", f"({row.get('latitude', 0):.2f}, {row.get('longitude', 0):.2f})")
            param = row.get("parameter", "PM2.5")
            popup = f"<b>{city}</b><br>AQI: {row['aqi']}<br>Parameter: {param}"
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=4,
                color=color,
                fill=True,
                fill_opacity=0.85,
                popup=popup,
            ).add_to(aqi_layer)
        aqi_layer.add_to(m)

    # === AOD Heatmap ===
    if df_aod is not None and len(df_aod) > 0:
        aod_layer = folium.FeatureGroup(name="AOD (MERRA-2)")
        heat_data = [[r["latitude"], r["longitude"], r["aod"]] for _, r in df_aod.iterrows()]
        HeatMap(
            heat_data, name="Aerosol Optical Depth", min_opacity=0.3,
            radius=25, blur=18, max_zoom=6
        ).add_to(aod_layer)
        aod_layer.add_to(m)

    # === Predicted AQI ===
    if df_pred is not None and len(df_pred) > 0 and show_pred in ['both', 'predicted']:
        pred_layer = folium.FeatureGroup(name="Predicted AQI (Tomorrow)")
        for _, r in df_pred.iterrows():
            color = get_aqi_color(r.get("aqi_pred", 0))
            folium.CircleMarker(
                location=[r["latitude"], r["longitude"]],
                radius=4,
                color=color,
                fill=True,
                fill_opacity=0.75,
                popup=f"<b>Predicted AQI:</b> {r['aqi_pred']}",
            ).add_to(pred_layer)
        pred_layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    print("✅ Map built successfully.")
    return m
