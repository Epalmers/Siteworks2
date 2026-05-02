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

# Per-parcel simplification in Web Mercator metres (before merge).
_SIMPLIFY_M = 45.0
# After dissolving all parcels into one industrial extent, simplify again (metres) so
# the merged outline is lighter in the browser (huge MSAs can still be multi-MB).
_SIMPLIFY_MERGED_M = 100.0


@st.cache_data(show_spinner="Loading industrial zoning layers …", ttl=None)
def _load_industrial_gdf(
    city: str,
) -> Tuple[Optional[gpd.GeoDataFrame], Dict[str, Any]]:
    """
    Load all industrial parcels, merge to one dissolved extent, and return GeoDataFrame
    with a single feature (geometry only) for Folium.
    """
    stem = ZONING_ZIP_STEM.get(city)
    if not stem:
        return None, {"missing_city": city}

    zip_path = _ZONING_DIR / f"{stem}.zip"
    if not zip_path.is_file():
        return None, {"zip_missing": str(zip_path.name)}

    path = f"zip://{zip_path.resolve().as_posix()}!{stem}.shp"
    gdf = gpd.read_file(path, on_invalid="ignore")
    gdf = gdf[gdf.geometry.notna()].copy()
    n_parcels = len(gdf)
    if n_parcels == 0:
        return None, {"empty": city}

    gdf = gdf.reset_index(drop=True)
    gdf = gdf.to_crs(3857)
    gdf["geometry"] = gdf.geometry.simplify(_SIMPLIFY_M, preserve_topology=True)
    gdf = gdf[(~gdf.geometry.is_empty) & gdf.geometry.notna()]
    gdf = gdf[["geometry"]].copy()
    gdf = gdf.assign(_sw_dissolve=1)
    gdf = gdf.dissolve(by="_sw_dissolve", as_index=False)
    gdf = gdf.drop(columns=["_sw_dissolve"], errors="ignore")
    gdf["geometry"] = gdf.geometry.simplify(
        _SIMPLIFY_MERGED_M, preserve_topology=True
    )
    gdf = gdf.to_crs(4326)
    gdf = gdf[(~gdf.geometry.is_empty) & gdf.geometry.notna()]

    info: Dict[str, Any] = {
        "n_parcels": n_parcels,
        "n_map_features": int(len(gdf)),
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
            tooltip=folium.Tooltip(
                f"{city} — industrial extent (all parcels merged; boundaries simplified)"
            ),
        )
        layer.add_to(fg)
        fg.add_to(m)
        meta.append(
            {
                "city": city,
                "ok": True,
                "n_parcels": info.get("n_parcels"),
            }
        )

    if not gdfs:
        return None, meta

    _fit_map_bounds(m, gdfs)
    if len(gdfs) > 1:
        folium.LayerControl(collapsed=False).add_to(m)
    return m, meta


def render_industrial_zoning_map(selected_city: str) -> None:
    """Streamlit: render the industrial-zoning map for a single city (map zooms to that extent)."""
    if not (selected_city or "").strip():
        st.info("Select a city to show on the map.")
        return

    m, meta = build_industrial_zoning_map([selected_city])
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
        n_p = row.get("n_parcels")
        if n_p is not None:
            cap = (
                f"**{row['city']}**: map shows the **full industrial extent** from **{n_p:,}** "
                f"source parcels, merged into one area (boundaries simplified for display)."
            )
            if row.get("city") == "Houston":
                cap += (
                    " Houston does not have a proper zone ordinance; the parcels shown are "
                    "industrial land-use parcels and are meant to serve as a guide."
                )
            st.caption(cap)

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
