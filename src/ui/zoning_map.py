"""
Industrial / land-use zoning map (Folium) for pilot cities.

Shapefiles are shipped as .zip per city under data/Zoning_Spatial_Data/.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import folium
import geopandas as gpd
import streamlit as st
import streamlit.components.v1 as st_components

from src.ui.charts import city_color

# zip stem inside data/Zoning_Spatial_Data/<stem>.zip (matches .shp name)
ZONING_ZIP_STEM: Dict[str, str] = {
    "Oklahoma City": "Zoning_Oklahoma_City_Industrial",
    "Boston": "Boston_Zoning_Industrial",
    "Denver": "Denver_Metro_Zoning_Industrial",
    "Houston": "Houston_LandUse_Industrial",
    "Gainesville": "City_of_Gainesville_Zoning_Industrial",
}

_ZONING_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "Zoning_Spatial_Data"

# Simplification in Web Mercator metres before mapping.
_SIMPLIFY_M = 45.0
# If a city has more than this many polygon rows, we random-sample for the web map
# (keeps the browser responsive; full metro parcel counts can be 10^4+).
_MAX_FEATURES = 3000
_SAMPLE_SIZE = 500
_RNG_SEED = 7


@st.cache_data(show_spinner="Loading industrial zoning layers …", ttl=None)
def _load_industrial_gdf(
    city: str,
) -> Tuple[Optional[gpd.GeoDataFrame], Dict[str, Any]]:
    """Load and prepare industrial zoning for one city. Cached per city name."""
    stem = ZONING_ZIP_STEM.get(city)
    if not stem:
        return None, {"missing_city": city}

    zip_path = _ZONING_DIR / f"{stem}.zip"
    if not zip_path.is_file():
        return None, {"zip_missing": str(zip_path.name)}

    path = f"zip://{zip_path.resolve().as_posix()}!{stem}.shp"
    gdf = gpd.read_file(path, on_invalid="ignore")
    gdf = gdf[gdf.geometry.notna()].copy()
    n_total = len(gdf)
    if n_total == 0:
        return None, {"empty": city}

    sampled = False
    gdf = gdf.reset_index(drop=True)
    if n_total > _MAX_FEATURES:
        gdf = gdf.sample(n=_SAMPLE_SIZE, random_state=_RNG_SEED)
        sampled = True

    gdf = gdf.to_crs(3857)
    gdf["geometry"] = gdf.geometry.simplify(_SIMPLIFY_M, preserve_topology=True)
    gdf = gdf.to_crs(4326)
    gdf = gdf[(~gdf.geometry.is_empty) & gdf.geometry.notna()]
    # Folium serialises the GeoDataFrame; drop attribute columns (some DBF types
    # e.g. dates are not JSON-friendly).
    gdf = gdf[["geometry"]].copy()

    info: Dict[str, Any] = {
        "n_total": n_total,
        "n_shown": int(len(gdf)),
        "sampled": sampled,
    }
    return gdf, info


def _fit_map_bounds(
    m: folium.Map,
    gdfs: List[gpd.GeoDataFrame],
) -> None:
    if not gdfs:
        m.location = [37.0, -98.0]
        m.options["zoom"] = 4
        return
    minx = min(g.total_bounds[0] for g in gdfs)
    miny = min(g.total_bounds[1] for g in gdfs)
    maxx = max(g.total_bounds[2] for g in gdfs)
    maxy = max(g.total_bounds[3] for g in gdfs)
    m.fit_bounds([[miny, minx], [maxy, maxx]])


def build_industrial_zoning_map(
    selected_cities: List[str],
) -> Tuple[Optional[folium.Map], List[Dict[str, Any]]]:
    """
    Return a folium map with industrial / industrial-use polygons for the given cities.
    If nothing could be shown, (None, meta list with errors) is returned.
    """
    if not selected_cities:
        return None, []

    m = folium.Map(
        location=[37.0, -98.0],
        zoom_start=4,
        tiles="CartoDB Positron",
    )
    meta: List[Dict[str, Any]] = []
    gdfs: List[gpd.GeoDataFrame] = []

    for city in selected_cities:
        gdf, info = _load_industrial_gdf(city)
        if gdf is None or gdf.empty:
            meta.append({"city": city, **(info or {}), "ok": False})
            continue

        gdfs.append(gdf)
        c = city_color(city)
        fg = folium.FeatureGroup(name=city, show=True)
        style = lambda _f, _c=c: {
            "fillColor": _c,
            "color": _c,
            "weight": 1.0,
            "fillOpacity": 0.32,
        }
        hstyle = lambda _f, _c=c: {
            "fillColor": _c,
            "color": _c,
            "weight": 2.0,
            "fillOpacity": 0.5,
        }
        layer = folium.GeoJson(
            gdf,
            name=city,
            style_function=style,
            highlight_function=hstyle,
            tooltip=folium.Tooltip(f"{city} — industrial / industrial-use zoning"),
        )
        layer.add_to(fg)
        fg.add_to(m)
        meta.append(
            {
                "city": city,
                "ok": True,
                "n_total": info.get("n_total"),
                "n_shown": info.get("n_shown"),
                "sampled": info.get("sampled", False),
            }
        )

    if not gdfs:
        return None, meta

    _fit_map_bounds(m, gdfs)
    folium.LayerControl(collapsed=False).add_to(m)
    return m, meta


def render_industrial_zoning_map(selected_cities: List[str]) -> None:
    """Streamlit: render the industrial-zoning map for selected cities."""
    if not selected_cities:
        st.info("Select at least one city to show on the map.")
        return

    m, meta = build_industrial_zoning_map(selected_cities)
    if m is None:
        parts: List[str] = []
        for row in meta:
            city = row.get("city", "?")
            if row.get("zip_missing"):
                parts.append(f"- **{city}**: missing file `{row['zip_missing']}` in `data/Zoning_Spatial_Data/`.")
            elif row.get("missing_city"):
                parts.append(f"- **{city}**: no zoning archive is mapped for this city.")
            else:
                parts.append(f"- **{city}**: {row!r}.")
        st.warning("No industrial zoning could be shown.\n\n" + "\n".join(parts))
        return

    st_components.html(m._repr_html_(), height=520)

    ok_rows = [row for row in meta if row.get("ok")]
    for row in ok_rows:
        if row.get("sampled"):
            st.caption(
                f"**{row['city']}**: showing **{row['n_shown']:,}** of **{row['n_total']:,}** "
                f"industrial parcel polygons (random sample for map performance)."
            )

    err_rows = [row for row in meta if not row.get("ok")]
    for row in err_rows:
        if row.get("zip_missing"):
            st.caption(f"**{row['city']}**: missing archive `{row['zip_missing']}`.")
        elif row.get("missing_city"):
            st.caption(
                f"**{row['city']}**: no industrial zoning file is defined for this pilot."
            )
        else:
            st.caption(f"**{row['city']}**: could not load layer ({row!r}).")
