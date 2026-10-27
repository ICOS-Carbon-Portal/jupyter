"""Viewers for WRF-style output.


MapPanels       clickable leaflet map: total and background, then biogenic and anthropogenic

Validate clickable leaflet map;Interactive observation-vs-WRFChem validation
MAPS Combined CO2 map + selected-grid time series with bounded caching
Both take an xarray Dataset with 2-D lat/lon, a time coordinate, an eta
dimension, and tracer1/tracer2/tracer3. Call .show() to display.
"""

import base64
from io import BytesIO

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, to_hex
from matplotlib.path import Path
import plotly.graph_objects as go
from IPython.display import HTML, clear_output, display
import ipywidgets as W
import ipyleaflet as L
from shapely.geometry import mapping
import geopandas as gpd
import dask

CSS = """
<style>
.jupyter-widgets-output-area, .jupyter-widgets-output-area .output,
.jp-OutputArea-child .jp-OutputArea-output {
    height: auto !important; max-height: unset !important; overflow: hidden !important;
}
.jupyter-widgets-output-area .output_scroll {
    height: unset !important; max-height: unset !important; box-shadow: unset !important;
}
.widget-html, .widget-html-content { overflow: visible !important; }
.js-plotly-plot, .plot-container, .svg-container, .leaflet-container {
    width: 100% !important; max-width: 100% !important;
}
/* Scale inline matplotlib PNGs down instead of scrolling sideways */
.jupyter-widgets-output-area img, .jp-OutputArea-output img {
    max-width: 100% !important; height: auto !important;
}
</style>
"""

TRACERS = {"bck": "tracer1", "bio": "tracer2", "ant": "tracer3"}
TOTAL = "total"                           # pseudo-variable: sum of the three tracers
LABELS = {"tracer1": "Background CO₂", "tracer2": "Biogenic CO₂",
          "tracer3": "Anthropogenic CO₂", TOTAL: "Total CO₂"}
FIELDS = list(TRACERS.values()) + [TOTAL]
PANELS = [TOTAL, TRACERS["bck"], TRACERS["bio"], TRACERS["ant"]]   # 2x2 reading order
OFFSET = 400                              # tracer2/tracer3 are stored with this added
OFFSET_VARS = ("tracer2", "tracer3")
TITLE_H, INFO_H = 25, 34


# ---------------------------------------------------------------- helpers

def col(share, **kw):
    """Flexible column. min_width 0 lets it shrink instead of overflowing."""
    return W.Layout(width="auto", flex=f"{share} 1 0%", min_width="0", overflow="hidden", **kw)


def div(text, h, **css):
    style = ";".join(f"{k.replace('_', '-')}:{v}" for k, v in css.items())
    return (f"<div style='width:100%;height:{h}px;line-height:{h}px;white-space:nowrap;"
            f"overflow:hidden;text-overflow:ellipsis;{style}'>{text}</div>")


def check(ds):
    """Raise if a tracer is missing; warn if their units disagree."""
    missing = [v for v in TRACERS.values() if v not in ds.data_vars]
    if missing:
        raise KeyError(f"Variables not found in dataset: {missing}")
    found = {v: units(ds, v) for v in TRACERS.values()}
    if len(set(found.values())) > 1:
        print("Warning: tracer units are different:")
        for var, unit in found.items():
            print(f"  {var}: {unit}")


def label(ds, var):
    """standard_name if the file provides one, else a readable default."""
    if var == TOTAL:
        return LABELS[TOTAL]
    return ds[var].attrs.get("standard_name", LABELS.get(var, var))


def units(ds, var):
    if var == TOTAL:                      # the sum inherits the tracers' units
        var = TRACERS["bck"]
    return ds[var].attrs.get("units", "unit not specified")


def strip_offset(values, var, offset=OFFSET):
    """Remove the constant offset that tracer2/tracer3 carry in the model output."""
    return values - offset if var in OFFSET_VARS else values


def slab(ds, var, offset=OFFSET, **isel):
    """One field with the offset removed. var may be TOTAL for the tracer sum."""
    if var == TOTAL:
        return sum(slab(ds, v, offset, **isel) for v in TRACERS.values())
    return strip_offset(ds[var].isel(**isel).squeeze(drop=True).compute(), var, offset)


def limits(values, robust=True):
    """Colour limits, guarding against a zero-width scale."""
    values = np.asarray(values)
    if robust:
        vmin, vmax = np.nanpercentile(values, [2, 98])
    else:
        vmin, vmax = np.nanmin(values), np.nanmax(values)
    if np.isclose(vmin, vmax):
        pad = abs(vmin) * 0.01 if vmin != 0 else 1.0
        vmin, vmax = vmin - pad, vmax + pad
    return float(vmin), float(vmax)


# ------------------------------------------------- map + time series view

class WRFExplorer:

    def __init__(self, ds, offset=400, height=400, map_share=1, plot_share=2, zoom=8):
        check(ds)
        self.ds, self.offset, self.height = ds, offset, height
        self.lat = ds["lat"].values.squeeze()
        self.lon = ds["lon"].values.squeeze()
        self.times = pd.to_datetime(ds["time"].values)
        self.overlay = self.marker = self.i = self.j = None

        edge = np.concatenate([
            np.c_[self.lat[0, :], self.lon[0, :]],
            np.c_[self.lat[:, -1], self.lon[:, -1]],
            np.c_[self.lat[-1, ::-1], self.lon[-1, ::-1]],
            np.c_[self.lat[::-1, 0], self.lon[::-1, 0]],
        ])
        self.domain_path = Path(np.c_[edge[:, 1], edge[:, 0]])
        self.bounds = ((float(np.nanmin(self.lat)), float(np.nanmin(self.lon))),
                       (float(np.nanmax(self.lat)), float(np.nanmax(self.lon))))

        self._build(edge, zoom, map_share, plot_share)
        self._draw_map()

    def _build(self, edge, zoom, map_share, plot_share):
        style = {"description_width": "50px"}
        times = [(t.strftime("%Y-%m-%d %H:%M"), i) for i, t in enumerate(self.times)]
        etas = ([(f"{float(v):g}", i) for i, v in enumerate(self.ds["eta"].values)]
                if "eta" in self.ds.coords else
                [(f"eta {i}", i) for i in range(self.ds.sizes["eta"])])

        self.time = W.Dropdown(options=times, value=0, description="Time:", style=style, layout=col(3))
        self.eta = W.Dropdown(options=etas, value=0, description="Eta:", style=style, layout=col(2))
        self.tracer = W.Dropdown(options=[(label(self.ds, v), v) for v in FIELDS],
                                 value="tracer1", description="Map:", style=style, layout=col(2))

        self.map = L.Map(center=(float(np.nanmean(self.lat)), float(np.nanmean(self.lon))),
                         zoom=zoom, basemap=L.basemaps.OpenStreetMap.Mapnik,
                         layout=col(map_share, height=f"{self.height}px"))
        self.outline = L.Polygon(locations=edge.tolist(), color="red", weight=2,
                                 fill_color="red", fill_opacity=0.01)
        self.map.add_layer(self.outline)

        self.legend = W.HTML(layout=W.Layout(width="100px", margin="0", overflow="visible"))
        self.map.add_control(L.WidgetControl(widget=self.legend, position="bottomright",
                                            transparent_bg=True))

        self.info = W.HTML(self._info("<b>Click inside the model domain</b> to display the time series."),
                           layout=W.Layout(width="100%", height=f"{INFO_H}px", flex="0 0 auto"))
        self.out = W.Output(layout=col(plot_share, height="auto", margin="0", padding="0"))
        with self.out:
            display(W.HTML(
                f"<div style='width:100%;height:{self.height}px;display:flex;align-items:center;"
                f"justify-content:center;color:#666;font-size:12px;'>"
                f"Click a location inside the model domain.</div>"))

        spacer = W.HTML("", layout=W.Layout(width="100%", height=f"{INFO_H}px", flex="0 0 auto"))
        self.widget = W.VBox([
            W.HBox([self.time, self.eta, self.tracer],
                   layout=W.Layout(width="100%", column_gap="10px", margin="0 0 8px 0",
                                   flex_flow="row wrap", overflow="hidden")),
            W.HBox([W.VBox([self._title("CO₂ concentration"), spacer], layout=col(map_share)),
                    W.VBox([self._title("Time series at selected location"), self.info],
                           layout=col(plot_share))],
                   layout=W.Layout(width="100%", column_gap="25px", align_items="flex-end",
                                   overflow="hidden")),
            W.HBox([self.map, self.out],
                   layout=W.Layout(width="100%", column_gap="25px", align_items="flex-start",
                                   overflow="hidden")),
        ], layout=W.Layout(width="100%", overflow="hidden"))

        for w in (self.time, self.eta):
            w.observe(lambda c: (self._draw_map(), self._draw_plot()), names="value")
        self.tracer.observe(lambda c: self._draw_map(), names="value")
        self.map.on_interaction(self._click)

    @staticmethod
    def _title(text):
        return W.HTML(div(text, TITLE_H, text_align="center", font_weight="600", font_size="14px"),
                      layout=W.Layout(width="100%", height=f"{TITLE_H}px", flex="0 0 auto"))

    @staticmethod
    def _info(text, color="#000"):
        return div(text, INFO_H, font_size="11px", color=color)

    def _image(self, name):
        f = np.asarray(slab(self.ds, name, self.offset,
                            time=self.time.value, eta=self.eta.value).values, float)
        if f.shape != self.lat.shape:
            f = f.T
        finite = f[np.isfinite(f)]
        if not finite.size:
            return None
        lo, hi = limits(finite)
        if np.nanmean(self.lat[0]) < np.nanmean(self.lat[-1]):
            f = np.flipud(f)
        if np.nanmean(self.lon[:, 0]) > np.nanmean(self.lon[:, -1]):
            f = np.fliplr(f)
        rgba = plt.get_cmap("viridis")(Normalize(lo, hi, clip=True)(f))
        rgba[..., 3] = np.where(np.isfinite(f), 0.8, 0)
        buf = BytesIO()
        plt.imsave(buf, rgba, format="png")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), lo, hi

    def _draw_map(self):
        name = self.tracer.value
        image = self._image(name)
        if image is None:
            return
        uri, lo, hi = image

        for layer in (self.overlay, self.outline, self.marker):
            if layer is not None:
                try:
                    self.map.remove_layer(layer)
                except Exception:
                    pass
        self.overlay = L.ImageOverlay(url=uri, bounds=self.bounds, opacity=0.75)
        for layer in (self.overlay, self.outline, self.marker):  # raster first, markers on top
            if layer is not None:
                self.map.add_layer(layer)

        unit = units(self.ds, name)
        ramp = ",".join(to_hex(plt.get_cmap("viridis")(x)) for x in np.linspace(0, 1, 7))
        self.legend.value = f"""
        <div style="width:94px;padding:2px;background:rgba(255,255,255,0.2);font-size:8px;line-height:1.05;">
            <b>{label(self.ds, name)}</b>
            <div style="width:90px;height:6px;margin:1px 0;background:linear-gradient(to right,{ramp});"></div>
            <div style="width:90px;display:flex;justify-content:space-between;font-size:7px;">
                <span>{lo:.2f}</span><span>{hi:.2f} {unit}</span>
            </div>
        </div>"""

    def _series(self, name):
        values = np.asarray(self.ds[name].isel(eta=self.eta.value, south_north=self.i,
                                               west_east=self.j).squeeze(drop=True).values, float)
        return strip_offset(values, name, self.offset)

    def _draw_plot(self):
        if self.i is None:
            return
        bck, bio, ant = (self._series(v) for v in TRACERS.values())
        unit = units(self.ds, "tracer1")

        fig = go.Figure()
        for name, values, color, w in [
            ("Total", bck + bio + ant, "red", 2.0),
            ("Background", bck, "blue", 1.5),
            ("Background + biogenic", bck + bio, "green", 1.5),
            ("Background + anthropogenic", bck + ant, "orange", 1.5),
        ]:
            fig.add_trace(go.Scatter(
                x=self.times, y=values, mode="lines", name=name,
                line=dict(color=color, width=w),
                hovertemplate=f"<b>{name}</b><br>CO₂: %{{y:.2f}} {unit}<extra></extra>"))
        fig.add_vline(x=self.times[self.time.value], line_width=1.5,
                      line_dash="dash", line_color="red")
        fig.update_layout(  # no width: the flex column decides
            autosize=True, height=self.height, margin=dict(l=70, r=20, t=45, b=50),
            xaxis=dict(title="Time", showgrid=True, automargin=True),
            yaxis=dict(title=f"CO₂ concentration ({unit})", showgrid=True, automargin=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                        font=dict(size=10)),
            hovermode="x unified", template="plotly_white")

        with self.out:
            clear_output(wait=True)
            fig.show(config={"responsive": True, "displaylogo": False})

    def _click(self, **kw):
        if kw.get("type") != "click" or kw.get("coordinates") is None:
            return
        lat, lon = map(float, kw["coordinates"])
        if not self.domain_path.contains_point((lon, lat)):
            self.info.value = self._info("<b>Selected location is outside the model domain.</b>",
                                         color="#b00020")
            return

        dx = (self.lon - lon) * np.cos(np.deg2rad(lat))
        d2 = np.where(np.isfinite(self.lat) & np.isfinite(self.lon),
                      dx**2 + (self.lat - lat)**2, np.inf)
        self.i, self.j = np.unravel_index(np.argmin(d2), self.lat.shape)
        plat, plon = float(self.lat[self.i, self.j]), float(self.lon[self.i, self.j])

        if self.marker is not None:
            try:
                self.map.remove_layer(self.marker)
            except Exception:
                pass
        self.marker = L.CircleMarker(location=(plat, plon), radius=5, color="black",
                                     fill_color="white", fill_opacity=1, weight=2)
        self.map.add_layer(self.marker)

        self.info.value = self._info(
            f"<b>Selected grid:</b> ({self.i}, {self.j}) &nbsp;|&nbsp; "
            f"<b>Lat:</b> {plat:.4f} &nbsp; <b>Lon:</b> {plon:.4f}")
        self._draw_plot()

    def show(self):
        display(HTML(CSS))
        display(self.widget)
        return self


# ============================================================
# MapPanels
# Interactive single-map explorer with:
#   1. Background / Biogenic / Anthropogenic / Total
#   2. Hourly / Daily mean / Monthly mean
#   3. Eta + Geopotential height (Z_e)
# ============================================================

# --------------------------------------------------- interactive single-map view
# ---------------------------------------------------

class MapPanels:

    CMAPS = [
        "viridis",
        "plasma",
        "inferno",
        "magma",
        "turbo",
        "RdYlBu_r",
    ]

    COMPONENTS = {
        "Background CO₂": "tracer1",
        "Biogenic CO₂": "tracer2",
        "Anthropogenic CO₂": "tracer3",
        "Total CO₂": TOTAL,
    }

    def __init__(
        self,
        ds,
        offset=OFFSET,
        height=600,
        zoom=8,
        amb_path="./data/AMB_BCN_limit_P.shp",
        bcn_path="./data/BCN_WGS84_4.shp",
    ):

        check(ds)

        self.ds = ds
        self.offset = offset
        self.height = height
        self.zoom = zoom

        # ------------------------------------------------
        # Coordinates
        # ------------------------------------------------

        self.lat = ds["lat"].values.squeeze()
        self.lon = ds["lon"].values.squeeze()

        self.times = pd.to_datetime(
            ds["time"].values
        )

        # ------------------------------------------------
        # Check Z_e
        # ------------------------------------------------

        if "Z_e" not in ds.data_vars:

            raise KeyError(
                "Z_e was not found in the dataset. "
                "MapPanels2 requires Z_e."
            )

        # ------------------------------------------------
        # Read shapefiles
        # ------------------------------------------------

        self.amb_path = amb_path
        self.bcn_path = bcn_path

        self.amb_gdf = self._read_boundary(
            amb_path,
            "AMB"
        )

        self.bcn_gdf = self._read_boundary(
            bcn_path,
            "Barcelona"
        )

        # ------------------------------------------------
        # Model domain boundary
        # ------------------------------------------------

        edge = np.concatenate([
            np.c_[
                self.lat[0, :],
                self.lon[0, :]
            ],

            np.c_[
                self.lat[:, -1],
                self.lon[:, -1]
            ],

            np.c_[
                self.lat[-1, ::-1],
                self.lon[-1, ::-1]
            ],

            np.c_[
                self.lat[::-1, 0],
                self.lon[::-1, 0]
            ],
        ])

        self.domain_path = Path(
            np.c_[edge[:, 1], edge[:, 0]]
        )

        self.bounds = (
            (
                float(np.nanmin(self.lat)),
                float(np.nanmin(self.lon))
            ),
            (
                float(np.nanmax(self.lat)),
                float(np.nanmax(self.lon))
            ),
        )

        # ------------------------------------------------
        # State
        # ------------------------------------------------

        self.overlay = None
        self.marker = None

        self.amb_layer = None
        self.bcn_layer = None
        self.domain_layer = None

        # ------------------------------------------------
        # Build widgets
        # ------------------------------------------------

        self._build_widgets(edge)

        # ------------------------------------------------
        # Initial map
        # ------------------------------------------------

        self._draw_map()

    # ====================================================
    # Read shapefile
    # ====================================================

    def _read_boundary(self, path, name):

        if path is None:
            return None

        try:

            gdf = gpd.read_file(path)

        except Exception as e:

            print(
                f"Warning: could not read {name} "
                f"shapefile:\n{e}"
            )

            return None

        if gdf.empty:
            print(
                f"Warning: {name} shapefile is empty."
            )
            return None

        if gdf.crs is None:

            print(
                f"Warning: {name} shapefile has "
                f"no CRS."
            )

        elif gdf.crs.to_epsg() != 4326:

            gdf = gdf.to_crs(
                epsg=4326
            )

        return gdf

    # ====================================================
    # Widgets
    # ====================================================

    def _build_widgets(self, edge):

        style = {
            "description_width": "initial"
        }

        wide = W.Layout(
            width="100%"
        )
     
        # ------------------------------------------------
        # Row 1: time scale + time
        # ------------------------------------------------

        self.time_scale = W.Dropdown(
            options=[
                ("Hourly", "hourly"),
                ("Daily mean", "daily"),
                ("Monthly mean", "monthly"),
            ],
            value="hourly",
            description="Time scale:",
            style=style,
            layout=col(2),
        )

        self.time = W.SelectionSlider(
            options=self._make_time_options(
                "hourly"
            ),
            value=0,
            description="Time:",
            continuous_update=False,
            style=style,
            layout=col(6),
        )

        # ------------------------------------------------
        # Row 2: vertical level
        # ------------------------------------------------

        self.eta = W.SelectionSlider(
            options=self._make_eta_options(),
            value=0,
            description="Vertical level:",
            continuous_update=False,
            style=style,
            layout=wide,
        )

        # ------------------------------------------------
        # Row 3: component
        # ------------------------------------------------

        self.component = W.ToggleButtons(
            options=list(
                self.COMPONENTS.keys()
            ),
            value="Background CO₂",
            description="Component:",
            style=style,
            layout=wide,
        )

        # ------------------------------------------------
        # Row 4: map options
        # ------------------------------------------------

        self.cmap = W.Dropdown(
            options=self.CMAPS,
            value="viridis",
            description="Colour map:",
            style=style,
            layout=col(2),
        )

        self.robust = W.Checkbox(
            value=True,
            description="2–98% colour limits",
            indent=False,
            layout=col(2),
        )

        self.show_amb = W.Checkbox(
            value=True,
            description="AMB boundary",
            indent=False,
            layout=col(2),
        )

        self.show_bcn = W.Checkbox(
            value=True,
            description="Barcelona boundary",
            indent=False,
            layout=col(2),
        )

        # ------------------------------------------------
        # Z_e information
        # ------------------------------------------------

        self.level_info = W.HTML(
            self._level_info(),
            layout=W.Layout(
                width="100%",
                min_height="30px",
            ),
        )

        # ------------------------------------------------
        # Map
        # ------------------------------------------------

        self.map = L.Map(

            center=(
                float(np.nanmean(self.lat)),
                float(np.nanmean(self.lon))
            ),

            zoom=self.zoom,

            basemap=L.basemaps.OpenStreetMap.Mapnik,

            layout=W.Layout(
                width="100%",
                height=f"{self.height}px"
            ),
        )

        # ------------------------------------------------
        # Model domain outline
        # ------------------------------------------------

        self.domain_layer = L.Polygon(

            locations=edge.tolist(),

            color="black",

            weight=2,

            fill_opacity=0.0,
        )

        self.map.add_layer(
            self.domain_layer
        )

        # ------------------------------------------------
        # Boundary layers
        # ------------------------------------------------

        self._add_boundary_layers()

        # ------------------------------------------------
        # Legend
        # ------------------------------------------------

        self.legend = W.HTML(
            layout=W.Layout(
                width="130px",
                margin="0",
                overflow="visible",
            )
        )

        self.map.add_control(
            L.WidgetControl(
                widget=self.legend,
                position="bottomright",
                transparent_bg=True,
            )
        )
        
        self.map_title = W.HTML(
            value=self._map_title(),
            layout=W.Layout(
                width="100%",
                text_align="center",
                margin="5px 0px",
            )
        )   
        # ------------------------------------------------
        # Information below map
        # ------------------------------------------------

        self.info = W.HTML(
            self._info(
                "<b>Click on the map</b> "
                "to inspect a grid cell."
            ),
            layout=W.Layout(
                width="100%",
                min_height="30px",
            ),
        )

        # ------------------------------------------------
        # Widget layout
        # ------------------------------------------------

        self.widget = W.VBox(

            [

                # Row 1
                W.HBox(
                    [
                        self.time_scale,
                        self.time,
                    ],

                    layout=W.Layout(
                        width="100%",
                        column_gap="10px",
                        flex_flow="row wrap",
                    ),
                ),

                # Row 2
                self.eta,

                # Row 3
                self.component,

                # Row 4
                W.HBox(
                    [
                        self.cmap,
                        self.robust,
                        self.show_amb,
                        self.show_bcn,
                    ],

                    layout=W.Layout(
                        width="100%",
                        column_gap="10px",
                        flex_flow="row wrap",
                    ),
                ),

                # Z_e information
                self.level_info,
                # Map title
                self.map_title,
                # Map
                self.map,

                # Click information
                self.info,

            ],

            layout=W.Layout(
                width="100%",
                overflow="hidden",
            )
        )

        # ------------------------------------------------
        # Observers
        # ------------------------------------------------

        self.time_scale.observe(
            self._time_scale_changed,
            names="value"
        )

        self.time.observe(
            self._selection_changed,
            names="value"
        )

        self.eta.observe(
            self._selection_changed,
            names="value"
        )

        self.component.observe(
            self._selection_changed,
            names="value"
        )

        self.cmap.observe(
            self._selection_changed,
            names="value"
        )

        self.robust.observe(
            self._selection_changed,
            names="value"
        )

        self.show_amb.observe(
            self._boundary_changed,
            names="value"
        )

        self.show_bcn.observe(
            self._boundary_changed,
            names="value"
        )

        self.map.on_interaction(
            self._click
        )

    # ====================================================
    # Boundary layers
    # ====================================================

    def _add_boundary_layers(self):

        # ------------------------------------------------
        # AMB
        # ------------------------------------------------

        if self.amb_gdf is not None:

            geojson = L.GeoJSON(
                data=self.amb_gdf.__geo_interface__,

                style={
                    "color": "black",
                    "weight": 3,
                    "fillOpacity": 0,
                },
            )

            self.amb_layer = geojson

            if self.show_amb.value:
                self.map.add_layer(
                    self.amb_layer
                )

        # ------------------------------------------------
        # Barcelona municipality
        # ------------------------------------------------

        if self.bcn_gdf is not None:

            geojson = L.GeoJSON(
                data=self.bcn_gdf.__geo_interface__,

                style={
                    "color": "blue",
                    "weight": 2,
                    "fillOpacity": 0,
                },
            )

            self.bcn_layer = geojson

            if self.show_bcn.value:
                self.map.add_layer(
                    self.bcn_layer
                )

    # ====================================================
    # Boundary visibility
    # ====================================================

    def _boundary_changed(self, change):

        if self.amb_layer is not None:

            try:
                self.map.remove_layer(
                    self.amb_layer
                )
            except Exception:
                pass

            if self.show_amb.value:

                self.map.add_layer(
                    self.amb_layer
                )

        if self.bcn_layer is not None:

            try:
                self.map.remove_layer(
                    self.bcn_layer
                )
            except Exception:
                pass

            if self.show_bcn.value:

                self.map.add_layer(
                    self.bcn_layer
                )

        # Keep raster below boundaries
        self._draw_map()

    # ====================================================
    # Time options
    # ====================================================

    def _make_time_options(self, scale):

        if scale == "hourly":

            return [
                (
                    t.strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    i
                )

                for i, t
                in enumerate(self.times)
            ]

        elif scale == "daily":

            days = (
                pd.Series(
                    self.times.normalize()
                )
                .drop_duplicates()
                .tolist()
            )

            return [
                (
                    pd.Timestamp(t).strftime(
                        "%Y-%m-%d"
                    ),
                    i
                )

                for i, t
                in enumerate(days)
            ]

        # elif scale == "monthly":

        #     months = (
        #         pd.Series(
        #             self.times.to_period("M")
        #         )
        #         .drop_duplicates()
        #         .tolist()
        #     )

        #     return [
        #         (
        #             str(p),
        #             i
        #         )

        #         for i, p
        #         in enumerate(months)
        #     ]

    # ====================================================
    # Eta options
    # ====================================================

    def _make_eta_options(self):

        options = []

        for i, eta_value in enumerate(
            self.ds["eta"].values
        ):

            options.append(
                (
                    f"Level {i}: "
                    f"η = {float(eta_value):.5f}",

                    i
                )
            )

        return options

    # ====================================================
    # Time-scale changed
    # ====================================================

    def _time_scale_changed(self, change):

        scale = change["new"]

        options = self._make_time_options(
            scale
        )

        self.time.options = options

        if options:

            self.time.value = (
                options[0][1]
            )

        self._update_level_info()

        self._draw_map()

    # ====================================================
    # Selection changed
    # ====================================================

    def _selection_changed(self, change):

        self._update_level_info()

        self._draw_map()

    # ====================================================
    # Representative time
    # ====================================================

    def _representative_time_index(self):

        scale = self.time_scale.value

        selected = self.time.value

        # Hourly
        if scale == "hourly":

            return selected

        # Daily
        elif scale == "daily":

            selected_day = (

                pd.Series(
                    self.times.normalize()
                )
                .drop_duplicates()
                .iloc[selected]
            )

            indices = np.where(
                self.times.normalize()
                == selected_day
            )[0]

            return int(
                indices[len(indices) // 2]
            )

        # Monthly
        elif scale == "monthly":

            selected_month = (

                pd.Series(
                    self.times.to_period("M")
                )
                .drop_duplicates()
                .iloc[selected]
            )

            indices = np.where(
                self.times.to_period("M")
                == selected_month
            )[0]

            return int(
                indices[len(indices) // 2]
            )

    # ====================================================
    # Get Z_e
    # ====================================================

    def _get_ze_field(self):

        ti = (
            self._representative_time_index()
        )

        ei = self.eta.value

        ze = self.ds["Z_e"].isel(
            time=ti,
            eta=ei,
        )

        return np.asarray(
            ze.compute().values,
            dtype=float
        ).squeeze()

    # ====================================================
    # Z_e information
    # ====================================================

    def _level_info(self):

        ei = self.eta.value

        eta_value = float(
            self.ds["eta"]
            .isel(eta=ei)
            .item()
        )

        ze = self._get_ze_field()

        finite = ze[
            np.isfinite(ze)
        ]

        if finite.size:

            ze_mean = np.nanmean(
                finite
            )

            ze_min = np.nanmin(
                finite
            )

            ze_max = np.nanmax(
                finite
            )

            return (

                f"<b>Vertical level {ei}</b> "
                f"&nbsp; | &nbsp; "
                f"η = {eta_value:.5f} "
                f"&nbsp; | &nbsp; "
                f"Zₑ mean = {ze_mean:.1f} m "
                f"&nbsp; | &nbsp; "
                f"range = "
                f"{ze_min:.1f}–{ze_max:.1f} m"
            )

        return (

            f"<b>Vertical level {ei}</b> "
            f"&nbsp; | &nbsp; "
            f"η = {eta_value:.5f}"
        )

    # ====================================================
    # Update Z_e
    # ====================================================

    def _update_level_info(self):

        self.level_info.value = (
            self._level_info()
        )

    # ====================================================
    # Get map field
    # ====================================================

    def _get_map_field(self):

        name = self.COMPONENTS[
            self.component.value
        ]

        scale = self.time_scale.value

        selected = self.time.value

        ei = self.eta.value

        # ------------------------------------------------
        # Hourly
        # ------------------------------------------------

        if scale == "hourly":

            return slab(
                self.ds,
                name,
                self.offset,
                time=selected,
                eta=ei,
            )

        # ------------------------------------------------
        # Daily
        # ------------------------------------------------

        if scale == "daily":

            selected_day = (

                pd.Series(
                    self.times.normalize()
                )
                .drop_duplicates()
                .iloc[selected]
            )

            mask = (
                self.times.normalize()
                == selected_day
            )

        # ------------------------------------------------
        # Monthly
        # ------------------------------------------------

        elif scale == "monthly":

            selected_month = (

                pd.Series(
                    self.times.to_period("M")
                )
                .drop_duplicates()
                .iloc[selected]
            )

            mask = (
                self.times.to_period("M")
                == selected_month
            )

        indices = np.where(mask)[0]

        data = self.ds[name].isel(
            time=indices,
            eta=ei,
        )

        data = (
            data
            .mean(dim="time")
            .compute()
        )

        if name in OFFSET_VARS:

            data = data - self.offset

        return data.squeeze(
            drop=True
        )

    # ====================================================
    # Title
    # ====================================================

    def _map_title(self):

        scale = self.time_scale.value

        selected = self.time.value

        if scale == "hourly":

            timestamp = self.times[
                selected
            ]

            return (
                f"Hourly CO₂ concentrations "
                f"at "
                f"{timestamp:%Y-%m-%d %H:%M} UTC"
            )

        elif scale == "daily":

            day = (

                pd.Series(
                    self.times.normalize()
                )
                .drop_duplicates()
                .iloc[selected]
            )

            return (
                f"Daily mean CO₂ concentrations "
                f"on "
                f"{pd.Timestamp(day):%Y-%m-%d}"
            )

        elif scale == "monthly":

            month = (

                pd.Series(
                    self.times.to_period("M")
                )
                .drop_duplicates()
                .iloc[selected]
            )

            return (
                f"Monthly mean CO₂ concentrations "
                f"in "
                f"{month}"
            )

    # ====================================================
    # Draw map
    # ====================================================

    def _draw_map(self):

        field = self._get_map_field()

        f = np.asarray(
            field.values,
            dtype=float
        )

        if f.shape != self.lat.shape:

            f = f.T

        finite = f[
            np.isfinite(f)
        ]

        if not finite.size:
            return

        vmin, vmax = limits(
            f,
            self.robust.value
        )

        # ------------------------------------------------
        # Orientation
        # ------------------------------------------------

        if (
            np.nanmean(self.lat[0])
            <
            np.nanmean(self.lat[-1])
        ):

            f = np.flipud(f)

        if (
            np.nanmean(self.lon[:, 0])
            >
            np.nanmean(self.lon[:, -1])
        ):

            f = np.fliplr(f)

        # ------------------------------------------------
        # Colormap
        # ------------------------------------------------

        cmap = plt.get_cmap(
            self.cmap.value
        )

        rgba = cmap(
            Normalize(
                vmin,
                vmax,
                clip=True
            )(f)
        )

        rgba[..., 3] = np.where(
            np.isfinite(f),
            0.80,
            0
        )

        # ------------------------------------------------
        # Convert to PNG
        # ------------------------------------------------

        buf = BytesIO()

        plt.imsave(
            buf,
            rgba,
            format="png"
        )

        uri = (
            "data:image/png;base64,"
            +
            base64.b64encode(
                buf.getvalue()
            ).decode()
        )

        # ------------------------------------------------
        # Remove old raster
        # ------------------------------------------------

        if self.overlay is not None:

            try:

                self.map.remove_layer(
                    self.overlay
                )

            except Exception:
                pass

        # ------------------------------------------------
        # Add new raster
        # ------------------------------------------------

        self.overlay = L.ImageOverlay(

            url=uri,

            bounds=self.bounds,

            opacity=0.75,
        )

        self.map.add_layer(
            self.overlay
        )

        # ------------------------------------------------
        # Restore boundary order
        # ------------------------------------------------

        self._restore_boundary_order()

        # ------------------------------------------------
        # Legend
        # ------------------------------------------------

        name = self.COMPONENTS[
            self.component.value
        ]

        unit = units(
            self.ds,
            name
        )

        ramp = ",".join(

            to_hex(
                cmap(x)
            )

            for x in np.linspace(
                0,
                1,
                9
            )
        )

        self.legend.value = f"""

        <div style="
            width:120px;
            padding:5px;
            background:rgba(
                255,255,255,0.90
            );
            font-size:10px;
            line-height:1.2;
        ">

            <b>
                {self.component.value}
            </b>

            <div style="
                width:115px;
                height:10px;
                margin:4px 0;
                background:
                linear-gradient(
                    to right,
                    {ramp}
                );
            "></div>

            <div style="
                width:115px;
                display:flex;
                justify-content:
                space-between;
            ">

                <span>
                    {vmin:.2f}
                </span>

                <span>
                    {vmax:.2f}
                </span>

            </div>

            <div>
                {unit}
            </div>

        </div>
        """

        # ------------------------------------------------
        # Update map title
        # ------------------------------------------------

        self._update_map_title()

    # ====================================================
    # Restore layer order
    # ====================================================

    def _restore_boundary_order(self):

        layers = [

            self.domain_layer,

            self.amb_layer
            if self.show_amb.value
            else None,

            self.bcn_layer
            if self.show_bcn.value
            else None,

            self.marker,
        ]

        for layer in layers:

            if layer is None:
                continue

            try:

                self.map.remove_layer(
                    layer
                )

            except Exception:
                pass

            self.map.add_layer(
                layer
            )

    # ====================================================
    # Map title
    # ====================================================

    def _update_map_title(self):

        self.map_title.value = (
            f"<h3 style='margin:5px 0px;'>"
            f"{self._map_title()}"
            f"</h3>"
        )

    # ====================================================
    # Map click
    # ====================================================

    def _click(self, **kw):

        if (
            kw.get("type") != "click"
            or kw.get("coordinates") is None
        ):
            return

        lat, lon = map(
            float,
            kw["coordinates"]
        )

        # ------------------------------------------------
        # Check domain
        # ------------------------------------------------

        if not self.domain_path.contains_point(
            (lon, lat)
        ):

            self.info.value = self._info(

                "<b>Selected location is "
                "outside the model domain.</b>",

                color="#b00020",
            )

            return

        # ------------------------------------------------
        # Find nearest grid cell
        # ------------------------------------------------

        dx = (

            self.lon - lon

        ) * np.cos(
            np.deg2rad(lat)
        )

        d2 = np.where(

            np.isfinite(self.lat)
            &
            np.isfinite(self.lon),

            dx**2
            +
            (self.lat - lat)**2,

            np.inf,
        )

        i, j = np.unravel_index(
            np.argmin(d2),
            self.lat.shape
        )

        self.i = i
        self.j = j

        plat = float(
            self.lat[i, j]
        )

        plon = float(
            self.lon[i, j]
        )

        # ------------------------------------------------
        # Z_e
        # ------------------------------------------------

        ze = self._get_ze_field()

        ze_value = float(
            ze[i, j]
        )

        eta_value = float(

            self.ds["eta"]
            .isel(
                eta=self.eta.value
            )
            .item()
        )

        # ------------------------------------------------
        # Marker
        # ------------------------------------------------

        if self.marker is not None:

            try:

                self.map.remove_layer(
                    self.marker
                )

            except Exception:
                pass

        self.marker = L.CircleMarker(

            location=(
                plat,
                plon
            ),

            radius=6,

            color="black",

            fill_color="white",

            fill_opacity=1,

            weight=2,
        )

        self.map.add_layer(
            self.marker
        )

        # ------------------------------------------------
        # Information
        # ------------------------------------------------

        self.info.value = self._info(

            f"<b>Selected grid:</b> "
            f"({i}, {j}) "
            f"&nbsp; | &nbsp; "

            f"<b>Lat:</b> "
            f"{plat:.4f} "

            f"&nbsp; | &nbsp; "

            f"<b>Lon:</b> "
            f"{plon:.4f} "

            f"&nbsp; | &nbsp; "

            f"<b>η:</b> "
            f"{eta_value:.5f} "

            f"&nbsp; | &nbsp; "

            f"<b>Zₑ:</b> "
            f"{ze_value:.1f} m"
        )

    # ====================================================
    # Helper
    # ====================================================

    @staticmethod
    def _info(
        text,
        color="#000"
    ):

        return div(
            text,
            INFO_H,
            font_size="12px",
            color=color,
        )

    # ====================================================
    # Show
    # ====================================================

    def show(self):

        display(
            HTML(CSS)
        )

        display(
            self.widget
        )

        return self

# ============================================================
# Validate
#
# Interactive observation-vs-WRF validation
#
# Left:
#     observation stations on an interactive map
#
# Right:
#     Plotly time series
#
# Supports:
#     Hourly
#     Daily mean
#     Monthly mean
#
# Model:
#     Background
#     Background + Biogenic
#     Background + Anthropogenic
#     Total
#
# Vertical interpolation:
#     WRF Z_e -> observation inlet height ASL
#
# Observation timestamp:
#     ICOS 12:30 represents the average over 12:00-13:00
#     Therefore 12:30 is assigned to 12:00
#
# Statistics:
#     R
#     RMSE
#     MB
#     N
# ============================================================

class Validate:

    MODEL_COMPONENTS = {
        "Background": "bck",
        "Background + Biogenic": "bck_bio",
        "Background + Anthropogenic": "bck_ant",
        "Total": "total",
    }

    def __init__(
        self,
        ds,
        station_data,
        station_meta,
        offset=OFFSET,
        height=600,
        zoom=8,
    ):

        check(ds)

        self.ds = ds
        self.station_data = station_data
        self.station_meta = station_meta

        self.offset = offset
        self.height = height
        self.zoom = zoom

        # ----------------------------------------------------
        # Model coordinates
        # ----------------------------------------------------

        self.lat = np.asarray(
            ds["lat"].values.squeeze(),
            dtype=float
        )

        self.lon = np.asarray(
            ds["lon"].values.squeeze(),
            dtype=float
        )

        self.times = pd.DatetimeIndex(
            pd.to_datetime(ds["time"].values)
        )

        # ----------------------------------------------------
        # Basic checks
        # ----------------------------------------------------

        if self.lat.ndim != 2 or self.lon.ndim != 2:
            raise ValueError(
                "lat and lon must be 2-D model coordinates."
            )

        if "Z_e" not in ds.data_vars:
            raise KeyError(
                "Z_e was not found in the dataset. "
                "Validation requires Z_e for vertical interpolation."
            )

        self.station_names = list(
            station_data.keys()
        )

        if not self.station_names:
            raise ValueError(
                "No observational stations were provided."
            )

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        self.selected_station = None

        self.station_markers = {}

        self.selected_marker = None

        # Cache vertically interpolated model data
        self.model_cache = {}

        # ----------------------------------------------------
        # Model domain boundary
        # ----------------------------------------------------

        edge = np.concatenate([
            np.c_[
                self.lat[0, :],
                self.lon[0, :]
            ],

            np.c_[
                self.lat[:, -1],
                self.lon[:, -1]
            ],

            np.c_[
                self.lat[-1, ::-1],
                self.lon[-1, ::-1]
            ],

            np.c_[
                self.lat[::-1, 0],
                self.lon[::-1, 0]
            ],
        ])

        self.domain_path = Path(
            np.c_[
                edge[:, 1],
                edge[:, 0]
            ]
        )

        # ----------------------------------------------------
        # Build interface
        # ----------------------------------------------------

        self._build_widgets(edge)

        # No _draw_map() here.
        # The map is constructed in _build_widgets().


    # ========================================================
    # Station metadata
    #
    # station_meta contains the ORIGINAL ICOS DataObject.
    #
    # We extract:
    #     latitude
    #     longitude
    #     station elevation ASL
    #     sampling height AGL
    # ========================================================

    def _station_metadata(self, station):

        meta = self.station_meta[station]

        try:

            acquisition = (
                meta.specificInfo.acquisition
            )

            station_obj = (
                acquisition.station
            )

            location = (
                station_obj.location
            )

            lat = float(
                location.lat
            )

            lon = float(
                location.lon
            )

            elevation = float(
                location.alt
            )

            sampling_height = float(
                acquisition.samplingHeight
            )

            return {
                "lat": lat,
                "lon": lon,
                "elevation": elevation,
                "sampling_height": sampling_height,
            }

        except Exception as e:

            raise ValueError(
                f"Could not extract ICOS metadata "
                f"for station '{station}': {e}"
            )


    # ========================================================
    # Observation inlet height
    #
    # station elevation = ground height ASL
    # sampling height   = inlet height AGL
    #
    # Therefore:
    #
    # target Z_e = elevation + sampling height
    # ========================================================

    def _observation_height(self, station):

        meta = self._station_metadata(
            station
        )

        return (
            meta["elevation"]
            +
            meta["sampling_height"]
        )


    # ========================================================
    # Nearest WRF grid
    # ========================================================

    def _nearest_grid(self, lat, lon):

        dx = (
            self.lon - lon
        ) * np.cos(
            np.deg2rad(lat)
        )

        d2 = np.where(
            np.isfinite(self.lat)
            &
            np.isfinite(self.lon),

            dx**2
            +
            (self.lat - lat)**2,

            np.inf
        )

        i, j = np.unravel_index(
            np.argmin(d2),
            self.lat.shape
        )

        return int(i), int(j)


    # ========================================================
    # Time options
    # ========================================================

    def _make_time_options(self, scale):

        if scale == "hourly":

            return [
                (
                    t.strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    i
                )
                for i, t
                in enumerate(self.times)
            ]

        if scale == "daily":

            days = (
                pd.DatetimeIndex(
                    self.times.normalize()
                )
                .drop_duplicates()
            )

            return [
                (
                    t.strftime(
                        "%Y-%m-%d"
                    ),
                    i
                )
                for i, t
                in enumerate(days)
            ]

        raise ValueError(
            f"Unknown time scale: {scale}"
        )


    # # ========================================================
    # # Eta options
    # # ========================================================

    # def _make_eta_options(self):

    #     return [
    #         (
    #             f"Level {i}: "
    #             f"η = {float(v):.5f}",
    #             i
    #         )
    #         for i, v
    #         in enumerate(
    #             self.ds["eta"].values
    #         )
    #     ]


    # ========================================================
    # Widgets / interface
    # ========================================================

    def _build_widgets(self, edge):

        style = {
            "description_width": "initial"
        }

        # ----------------------------------------------------
        # Time scale
        # ----------------------------------------------------

        self.time_scale = W.Dropdown(
            options=[
                ("Hourly", "hourly"),
                ("Daily mean", "daily"),
            ],

            value="hourly",

            description="Time scale:",

            style=style,

            layout=col(2),
        )

        # ----------------------------------------------------
        # Time
        # ----------------------------------------------------

        self.time = W.SelectionSlider(
            options=self._make_time_options(
                "hourly"
            ),

            value=0,

            description="Time:",

            continuous_update=False,

            style=style,

            layout=col(6),
        )

        # # ----------------------------------------------------
        # # Vertical level
        # #
        # # Kept because the model dataset uses eta levels.
        # # For validation itself, however, Z_e is used.
        # # ----------------------------------------------------

        # self.eta = W.SelectionSlider(
        #     options=self._make_eta_options(),

        #     value=0,

        #     description="Vertical level:",

        #     continuous_update=False,

        #     style=style,

        #     layout=W.Layout(
        #         width="100%"
        #     ),
        # )

        # ----------------------------------------------------
        # Map
        # ----------------------------------------------------

        self.map = L.Map(

            center=(
                float(
                    np.nanmean(self.lat)
                ),

                float(
                    np.nanmean(self.lon)
                )
            ),

            zoom=self.zoom,

            basemap=L.basemaps.OpenStreetMap.Mapnik,

            layout=W.Layout(
                width="100%",
                height=f"{self.height}px"
            ),
        )

        # ----------------------------------------------------
        # Model domain
        # ----------------------------------------------------

        self.domain_layer = L.Polygon(

            locations=edge.tolist(),

            color="black",

            weight=2,

            fill_opacity=0,
        )

        self.map.add_layer(
            self.domain_layer
        )

        # ----------------------------------------------------
        # Station markers
        # ----------------------------------------------------

        self._add_station_markers()

        # ----------------------------------------------------
        # Station information
        # ----------------------------------------------------

        self.station_info = W.HTML(

            self._station_info_text(
                None
            ),

            layout=W.Layout(
                width="100%",
                min_height="60px",
                overflow="hidden"
            ),
        )

        # ----------------------------------------------------
        # Plot output
        # ----------------------------------------------------

        self.out = W.Output(

            layout=W.Layout(
                width="100%",
                height=f"{self.height}px",
                overflow="hidden"
            )
        )

        self.diagnostic_out = W.Output(
            layout=W.Layout(
                width="100%",
                height="360px",
                overflow="hidden"
            )
        )

        # ----------------------------------------------------
        # Layout
        # ----------------------------------------------------

        self.widget = W.VBox(

            [

                # Row 1
                W.HBox(
                    [
                        self.time_scale,
                        self.time,
                    ],

                    layout=W.Layout(
                        width="100%",
                        column_gap="10px",
                        flex_flow="row wrap",
                        overflow="hidden"
                    ),
                ),

                # # Row 2
                # self.eta,

                # Main panel
                W.HBox(
                    [

                        W.VBox(
                            [
                                W.HTML(
                                    div(
                                        "Observation stations",
                                        25,
                                        text_align="center",
                                        font_weight="600",
                                        font_size="14px"
                                    )
                                ),

                                self.map,
                            ],

                            layout=col(1)
                        ),

                        W.VBox(
                            [
                                self.station_info,
                                self.out,
                                self.diagnostic_out,
                            ],

                            layout=col(2)
                        ),
                    ],

                    layout=W.Layout(
                        width="100%",
                        column_gap="25px",
                        align_items="flex-start",
                        overflow="hidden"
                    ),
                ),
            ],

            layout=W.Layout(
                width="100%",
                overflow="hidden"
            )
        )

        # ----------------------------------------------------
        # Observers
        # ----------------------------------------------------

        self.time_scale.observe(
            self._time_scale_changed,
            names="value"
        )

        self.time.observe(
            self._selection_changed,
            names="value"
        )

        # self.eta.observe(
        #     self._selection_changed,
        #     names="value"
        # )


    # ========================================================
    # Station markers
    # ========================================================

    def _add_station_markers(self):

        for station in self.station_names:

            meta = self._station_metadata(
                station
            )

            marker = L.CircleMarker(

                location=(
                    meta["lat"],
                    meta["lon"]
                ),

                radius=7,

                color="black",

                fill_color="white",

                fill_opacity=1,

                weight=2,
            )

            # Store station name on marker
            marker.station_name = station

            # ipyleaflet CircleMarker supports on_click
            marker.on_click(
                self._station_click
            )

            self.map.add_layer(
                marker
            )

            self.station_markers[
                station
            ] = marker


    # ========================================================
    # Station click
    # ========================================================

    def _station_click(self, **kwargs):

        station = kwargs.get(
            "station_name"
        )

        if station is None:

            # Some ipyleaflet versions do not return
            # custom Python attributes in callback kwargs.
            #
            # In that case, determine the nearest station
            # from the click coordinates.

            coordinates = kwargs.get(
                "coordinates"
            )

            if coordinates is None:
                return

            lat, lon = map(
                float,
                coordinates
            )

            station = self._nearest_station(
                lat,
                lon
            )

        if station is None:
            return

        self._select_station(
            station
        )


    # ========================================================
    # Find nearest observation station
    # ========================================================

    def _nearest_station(
        self,
        lat,
        lon
    ):

        distances = []

        for station in self.station_names:

            meta = self._station_metadata(
                station
            )

            dx = (
                meta["lon"] - lon
            ) * np.cos(
                np.deg2rad(lat)
            )

            d2 = (
                dx**2
                +
                (
                    meta["lat"] - lat
                )**2
            )

            distances.append(
                (
                    d2,
                    station
                )
            )

        if not distances:
            return None

        return min(
            distances,
            key=lambda x: x[0]
        )[1]


    # ========================================================
    # Select station
    # ========================================================

    def _select_station(self, station):

        self.selected_station = station

        # ----------------------------------------------------
        # Highlight selected station
        # ----------------------------------------------------

        if self.selected_marker is not None:

            try:
                self.map.remove_layer(
                    self.selected_marker
                )
            except Exception:
                pass

        meta = self._station_metadata(
            station
        )

        self.selected_marker = L.CircleMarker(

            location=(
                meta["lat"],
                meta["lon"]
            ),

            radius=10,

            color="black",

            fill_color="yellow",

            fill_opacity=0.9,

            weight=2,
        )

        self.map.add_layer(
            self.selected_marker
        )

        # ----------------------------------------------------
        # Information
        # ----------------------------------------------------

        self._update_station_info()

        # ----------------------------------------------------
        # Plot
        # ----------------------------------------------------

        self._draw_plot()


    # ========================================================
    # Observation series
    #
    # ICOS timestamps:
    #
    #     12:30 = average from 12:00–13:00
    #
    # Therefore:
    #
    #     12:30 -> 12:00
    # ========================================================

    def _get_observation_series(self, station):

        df = self.station_data[
            station
        ].copy()

        if "co2" not in df.columns:

            raise KeyError(
                f"'co2' not found for station "
                f"{station}. Available columns: "
                f"{list(df.columns)}"
            )

        obs = pd.to_numeric(
            df["co2"],
            errors="coerce"
        )

        obs.index = pd.to_datetime(
            obs.index
        )

        # ----------------------------------------------------
        # Assign period-average timestamp to period start
        #
        # 12:30 -> 12:00
        # 13:30 -> 13:00
        # ----------------------------------------------------

        obs.index = (
            obs.index
            - pd.Timedelta(
                minutes=30
            )
        )

        # Remove duplicate timestamps
        obs = obs[
            ~obs.index.duplicated(
                keep="first"
            )
        ]

        return obs.sort_index()


    # ========================================================
    # Vertical interpolation
    #
    # Z_e dimensions:
    #
    #     time × eta × south_north × west_east
    #
    # At the nearest model grid:
    #
    #     Z_e(eta) -> observation inlet height ASL
    #
    # The tracer is then interpolated onto that height.
    # ========================================================
# # old function ========================================================
#     def _interpolate_vertical(self, station):

#         meta = self._station_metadata(
#             station
#         )

#         slat = meta["lat"]
#         slon = meta["lon"]

#         i, j = self._nearest_grid(
#             slat,
#             slon
#         )

#         target_z = self._observation_height(
#             station
#         )

#         # ----------------------------------------------------
#         # Z_e
#         # ----------------------------------------------------

#         ze = np.asarray(

#             self.ds["Z_e"]
#             .isel(
#                 south_north=i,
#                 west_east=j
#             )
#             .compute()
#             .values,

#             dtype=float
#         )

#         # Expected:
#         #
#         # time × eta

#         if ze.ndim != 2:

#             raise ValueError(
#                 "Expected Z_e at a single grid cell to have "
#                 "dimensions (time, eta), but got "
#                 f"shape {ze.shape}."
#             )

#         # ----------------------------------------------------
#         # Model tracer values
#         # ----------------------------------------------------

#         model = {}

#         for tracer in TRACERS.values():

#             values = np.asarray(

#                 self.ds[tracer]
#                 .isel(
#                     south_north=i,
#                     west_east=j
#                 )
#                 .compute()
#                 .values,

#                 dtype=float
#             )

#             if values.ndim != 2:

#                 raise ValueError(
#                     f"{tracer} at a single grid cell should "
#                     f"have shape (time, eta), but got "
#                     f"{values.shape}."
#                 )

#             values = strip_offset(
#                 values,
#                 tracer,
#                 self.offset
#             )

#             model[tracer] = values

#         # ----------------------------------------------------
#         # Result
#         # ----------------------------------------------------

#         nt = ze.shape[0]

#         result = {
#             "bck": np.full(
#                 nt,
#                 np.nan
#             ),

#             "bio": np.full(
#                 nt,
#                 np.nan
#             ),

#             "ant": np.full(
#                 nt,
#                 np.nan
#             ),
#         }

#         # ----------------------------------------------------
#         # Interpolate each model time
#         # ----------------------------------------------------

#         for t in range(nt):

#             z = ze[t]

#             valid_z = np.isfinite(
#                 z
#             )

#             if valid_z.sum() < 2:
#                 continue

#             z = z[
#                 valid_z
#             ]

#             order = np.argsort(
#                 z
#             )

#             z = z[
#                 order
#             ]

#             for key in result:

#                 values = (
#                     model[
#                         TRACERS[key]
#                     ][t][
#                         valid_z
#                     ][
#                         order
#                     ]
#                 )

#                 good = np.isfinite(
#                     values
#                 )

#                 if good.sum() < 2:
#                     continue

#                 z_good = z[
#                     good
#                 ]

#                 v_good = values[
#                     good
#                 ]

#                 # Remove duplicate heights if present
#                 unique_z, unique_idx = np.unique(
#                     z_good,
#                     return_index=True
#                 )

#                 z_good = unique_z
#                 v_good = v_good[
#                     unique_idx
#                 ]

#                 if len(z_good) < 2:
#                     continue

#                 # Observation inlet outside model vertical range
#                 if (
#                     target_z < z_good[0]
#                     or
#                     target_z > z_good[-1]
#                 ):
#                     continue

#                 result[key][t] = np.interp(
#                     target_z,
#                     z_good,
#                     v_good
#                 )

#         return (
#             result,
#             i,
#             j,
#             target_z
#         )
# ===new to use dask
    def _interpolate_vertical(self, station):
    
        meta = self._station_metadata(station)
    
        slat = meta["lat"]
        slon = meta["lon"]
    
        i, j = self._nearest_grid(slat, slon)
    
        target_z = self._observation_height(station)
    
        # ----------------------------------------------------
        # Extract all variables at the nearest model grid cell
        # ----------------------------------------------------
        variable_names = ["Z_e", *TRACERS.values()]
    
        selected = {
            name: self.ds[name]
            .isel(
                south_north=i,
                west_east=j
            )
            .data
            for name in variable_names
        }
    
        # ----------------------------------------------------
        # Compute all variables together using Dask
        # ----------------------------------------------------
        computed = dask.compute(
            *(selected[name] for name in variable_names)
        )
    
        # Convert the computed arrays to NumPy arrays
        ze = np.asarray(
            computed[0],
            dtype=float
        )
    
        # Expected shape: time × eta
        if ze.ndim != 2:
            raise ValueError(
                "Expected Z_e at a single grid cell to have "
                "dimensions (time, eta), but got "
                f"shape {ze.shape}."
            )
    
        # ----------------------------------------------------
        # Model tracer values
        # ----------------------------------------------------
        model = {}
    
        for idx, tracer in enumerate(TRACERS.values(), start=1):
    
            values = np.asarray(
                computed[idx],
                dtype=float
            )
    
            if values.ndim != 2:
                raise ValueError(
                    f"{tracer} at a single grid cell should "
                    f"have shape (time, eta), but got "
                    f"{values.shape}."
                )
    
            values = strip_offset(
                values,
                tracer,
                self.offset
            )
    
            model[tracer] = values
    
        # ----------------------------------------------------
        # Result arrays
        # ----------------------------------------------------
        nt = ze.shape[0]
    
        result = {
            "bck": np.full(nt, np.nan),
            "bio": np.full(nt, np.nan),
            "ant": np.full(nt, np.nan),
        }
    
        # ----------------------------------------------------
        # Interpolate each model time to the observation height
        # ----------------------------------------------------
        for t in range(nt):
    
            z = ze[t]
    
            valid_z = np.isfinite(z)
    
            if valid_z.sum() < 2:
                continue
    
            z = z[valid_z]
    
            order = np.argsort(z)
    
            z = z[order]
    
            for key in result:
    
                values = (
                    model[TRACERS[key]][t][valid_z][order]
                )
    
                good = np.isfinite(values)
    
                if good.sum() < 2:
                    continue
    
                z_good = z[good]
                v_good = values[good]
    
                # Remove duplicate heights if present
                unique_z, unique_idx = np.unique(
                    z_good,
                    return_index=True
                )
    
                z_good = unique_z
                v_good = v_good[unique_idx]
    
                if len(z_good) < 2:
                    continue
    
                # Observation inlet outside model vertical range
                if (
                    target_z < z_good[0]
                    or target_z > z_good[-1]
                ):
                    continue
    
                result[key][t] = np.interp(
                    target_z,
                    z_good,
                    v_good
                )
    
        return (
            result,
            i,
            j,
            target_z
        )

    # ========================================================
    # Model series
    # ========================================================

    def _get_model_series(self, station):

        if station in self.model_cache:

            return self.model_cache[
                station
            ]

        (
            result,
            i,
            j,
            target_z
        ) = self._interpolate_vertical(
            station
        )

        bck = result["bck"]
        bio = result["bio"]
        ant = result["ant"]

        model = {

            "Background":
                bck,

            "Background + Biogenic":
                bck + bio,

            "Background + Anthropogenic":
                bck + ant,

            "Total":
                bck + bio + ant,
        }

        contributions = {
            "Biogenic": bio,
            "Anthropogenic": ant,
        }

        output = {
            "model": model,
            "contributions": contributions,
            "i": i,
            "j": j,
            "target_z": target_z,
        }

        self.model_cache[
            station
        ] = output

        return output


    # ========================================================
    # Aggregate
    # ========================================================

    def _aggregate(
        self,
        series,
        scale
    ):

        if scale == "hourly":

            return series

        if scale == "daily":

            return series.resample(
                "1D"
            ).mean()

        raise ValueError(
            f"Unknown time scale: {scale}"
        )


    # ========================================================
    # Validation dataframe
    # ========================================================

    def _validation_dataframe(
        self,
        station
    ):

        model_data = self._get_model_series(
            station
        )

        obs = self._get_observation_series(
            station
        )

        # ----------------------------------------------------
        # Model dataframe
        # ----------------------------------------------------

        model_df = pd.DataFrame(

            model_data["model"],

            index=self.times
        )

        # ----------------------------------------------------
        # Aggregate according to selected time scale
        # ----------------------------------------------------

        scale = self.time_scale.value

        obs_agg = self._aggregate(
            obs,
            scale
        )

        model_agg = model_df.apply(
            lambda s:
                self._aggregate(
                    s,
                    scale
                )
        )

        # ----------------------------------------------------
        # Align
        # ----------------------------------------------------

        df = pd.concat(
            [
                obs_agg.rename(
                    "Observation"
                ),

                model_agg,
            ],

            axis=1
        )

        # IMPORTANT:
        #
        # Statistics must use only simultaneous
        # observation/model pairs.
        #    # Keep ONLY periods where both observation
    # and model are available.
        # Do not simply drop rows based on Observation.
        df = df.dropna(
            subset=[
                "Observation",
                "Total"
            ]
        )
    
        return df


    # ========================================================
    # Statistics
    # ========================================================

    @staticmethod
    def _statistics(
        obs,
        model
    ):

        df = pd.concat(
            [
                obs.rename("obs"),
                model.rename("model")
            ],
            axis=1
        ).dropna()

        N = len(df)

        if N == 0:

            return (
                np.nan,
                np.nan,
                np.nan,
                0
            )

        error = (
            df["model"]
            -
            df["obs"]
        )

        # ----------------------------------------------------
        # Correlation
        # ----------------------------------------------------

        if (
            N >= 2
            and
            df["obs"].nunique() > 1
            and
            df["model"].nunique() > 1
        ):

            R = df[
                "obs"
            ].corr(
                df["model"]
            )

        else:

            R = np.nan

        # ----------------------------------------------------
        # RMSE
        # ----------------------------------------------------

        RMSE = np.sqrt(
            np.mean(
                error**2
            )
        )

        # ----------------------------------------------------
        # Mean bias
        #
        # Positive:
        #     model > observation
        #
        # Negative:
        #     model < observation
        # ----------------------------------------------------

        MB = np.mean(
            error
        )

        return (
            R,
            RMSE,
            MB,
            N
        )


    # ========================================================
    # Selected timestamp
    # ========================================================

    def _selected_timestamp(self):

        scale = (
            self.time_scale.value
        )

        selected = (
            self.time.value
        )

        if scale == "hourly":

            return self.times[
                selected
            ]

        if scale == "daily":

            days = (
                pd.DatetimeIndex(
                    self.times.normalize()
                )
                .drop_duplicates()
            )

            return days[
                selected
            ]

        return None


    # ========================================================
    # Monthly-averaged diurnal cycle
    #
    # The currently loaded WRF file represents one month, so
    # this is the mean diurnal cycle over that loaded month.
    # The x-axis is always 00:00-23:00.
    # ========================================================

    def _monthly_diurnal_cycle(self, station):

        model_data = self._get_model_series(station)

        model_df = pd.DataFrame(
            model_data["model"],
            index=self.times
        )

        obs = self._get_observation_series(station)

        # Keep the same model/observation overlap used elsewhere.
        obs = obs.loc[
            (obs.index >= self.times.min())
            &
            (obs.index <= self.times.max())
        ]

        df = pd.concat(
            [obs.rename("Observation"), model_df],
            axis=1
        )

        return (
            df.groupby(df.index.hour)
            .mean()
            .reindex(range(24))
        )


    # ========================================================
    # Daily source contributions
    # ========================================================

    def _daily_contributions(self, station):

        model_data = self._get_model_series(station)

        df = pd.DataFrame(
            model_data["contributions"],
            index=self.times
        )

        return df.resample("1D").mean()


    # ========================================================
    # Diurnal cycle figure
    # ========================================================

    def _draw_diurnal_plot(self, station):

        diurnal = self._monthly_diurnal_cycle(station)
        unit = units(self.ds, "tracer1")

        fig = go.Figure()
        x = list(range(24))

        styles = [
            ("Observation", "black", 2.5),
            ("Total", "red", 2.2),
            ("Background", "blue", 1.5),
            ("Background + Biogenic", "green", 1.7),
            ("Background + Anthropogenic", "orange", 1.7),
        ]

        for name, color, width in styles:
            if name not in diurnal.columns:
                continue

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=diurnal[name],
                    mode="lines+markers",
                    name=name,
                    line=dict(color=color, width=width),
                    marker=dict(size=5),
                    connectgaps=False,
                    hovertemplate=(
                        f"<b>{name}</b><br>"
                        "Hour: %{x:02d}:00<br>"
                        "CO₂: %{y:.2f} "
                        f"{unit}<extra></extra>"
                    )
                )
            )

        month_label = (
            f"{self.times.min():%Y-%m-%d}"
            f" to {self.times.max():%Y-%m-%d}"
        )

        fig.update_layout(
            title=f"Month-averaged diurnal cycle at {station} ({month_label})",
            autosize=True,
            height=330,
            margin=dict(l=75, r=30, t=85, b=60),
            xaxis=dict(
                title="Hour of day",
                tickmode="array",
                tickvals=x,
                ticktext=[f"{h:02d}:00" for h in x],
                showgrid=True,
                automargin=True,
            ),
            yaxis=dict(
                title=f"CO₂ concentration ({unit})",
                showgrid=True,
                automargin=True,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=9),
            ),
            hovermode="x unified",
            template="plotly_white",
            showlegend=True,
        )

        return fig


    # ========================================================
    # Daily source contribution figure
    # ========================================================

    def _draw_daily_contribution_plot(self, station):

        daily = self._daily_contributions(station)
        unit = units(self.ds, "tracer1")

        fig = go.Figure()

        for name, color in [
            ("Biogenic", "green"),
            ("Anthropogenic", "orange"),
        ]:

            if name not in daily.columns:
                continue

            fig.add_trace(
                go.Scatter(
                    x=daily.index,
                    y=daily[name],
                    mode="lines+markers",
                    name=name,
                    line=dict(color=color, width=2),
                    marker=dict(size=6),
                    connectgaps=False,
                    hovertemplate=(
                        f"<b>{name}</b><br>"
                        "Date: %{x|%Y-%m-%d}<br>"
                        "Daily mean: %{y:.2f} "
                        f"{unit}<extra></extra>"
                    )
                )
            )

        fig.update_layout(
            title=f"Daily mean CO₂ source contributions at {station}",
            autosize=True,
            height=330,
            margin=dict(l=75, r=30, t=75, b=60),
            xaxis=dict(
                title="Date",
                showgrid=True,
                automargin=True,
            ),
            yaxis=dict(
                title=f"CO₂ contribution ({unit})",
                showgrid=True,
                automargin=True,
                zeroline=True,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=10),
            ),
            hovermode="x unified",
            template="plotly_white",
            showlegend=True,
        )

        return fig


    # ========================================================
    # Draw plot
    # ========================================================

    def _draw_plot(self):

        if self.selected_station is None:

            with self.out:

                clear_output(
                    wait=True
                )

                display(
                    HTML(
                        f"""
                        <div style="
                            height:{self.height}px;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            color:#666;
                            font-size:13px;
                        ">
                        Click an observation station
                        on the map.
                        </div>
                        """
                    )
                )


            with self.diagnostic_out:
                clear_output(wait=True)
            return

        station = (
            self.selected_station
        )

        try:

            df = self._validation_dataframe(
                station
            )

        except Exception as e:

            with self.out:

                clear_output(
                    wait=True
                )

                display(
                    HTML(
                        f"""
                        <div style="
                            height:{self.height}px;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            color:#b00020;
                        ">
                        Error while processing
                        {station}:<br>{e}
                        </div>
                        """
                    )
                )


            with self.diagnostic_out:
                clear_output(wait=True)
            return

        if df.empty:

            with self.out:

                clear_output(
                    wait=True
                )

                display(
                    HTML(
                        f"""
                        <div style="
                            height:{self.height}px;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            color:#b00020;
                        ">
                        No overlapping observation/model
                        data available for {station}.
                        </div>
                        """
                    )
                )


            with self.diagnostic_out:
                clear_output(wait=True)
            return

        # ----------------------------------------------------
        # Units
        # ----------------------------------------------------

        unit = units(
            self.ds,
            "tracer1"
        )

        # ----------------------------------------------------
        # Plotly figure
        # ----------------------------------------------------

        fig = go.Figure()

        # ----------------------------------------------------
        # Observation
        # ----------------------------------------------------

        fig.add_trace(
            go.Scatter(

                x=df.index,

                y=df["Observation"],

                mode="lines",

                name="Observation",

                line=dict(color="black",
                    width=2.5
                ),

                connectgaps=False,

                hovertemplate=(
                    "<b>Observation</b><br>"
                    "Time: %{x|%Y-%m-%d %H:%M}<br>"
                    "CO₂: %{y:.2f} "
                    f"{unit}"
                    "<extra></extra>"
                )
            )
        )

        # ----------------------------------------------------
        # Model curves
        # ----------------------------------------------------

        model_styles = [
            (
                "Total",
                "red",
                2.2
            ), 
            
            (
                "Background",
                "blue",
                1.5
            ),

            (
                "Background + Biogenic",
                "green",
                1.7
            ),

            (
                "Background + Anthropogenic",
                "orange",
                1.7
            ),


        ]

        for name, color, width in model_styles:

            if name not in df.columns:
                continue

            fig.add_trace(
                go.Scatter(

                    x=df.index,

                    y=df[name],

                    mode="lines",

                    name=name,

                    line=dict(color=color,
                        width=width
                    ),

                    connectgaps=False,

                    hovertemplate=(
                        f"<b>{name}</b><br>"
                        "Time: %{x|%Y-%m-%d %H:%M}<br>"
                        "CO₂: %{y:.2f} "
                        f"{unit}"
                        "<extra></extra>"
                    )
                )
            )

        # ----------------------------------------------------
        # Statistics: hourly view only
        # ----------------------------------------------------

        stats = None

        if self.time_scale.value == "hourly":
            stats = self._statistics(
                df["Observation"],
                df["Total"]
            )

        # ----------------------------------------------------
        # Selected time
        # ----------------------------------------------------

        timestamp = (
            self._selected_timestamp()
        )

        if timestamp is not None:

            # Only add marker if it is inside
            # the plotted time range.

            if (
                timestamp >= df.index.min()
                and
                timestamp <= df.index.max()
            ):

                fig.add_vline(
                    x=timestamp,
                    line_width=1.2,
                    line_dash="dash"
                )

        # ----------------------------------------------------
        # Scale label
        # ----------------------------------------------------

        scale_label = {

            "hourly":
                "Hourly",

            "daily":
                "Daily mean",

        }[
            self.time_scale.value
        ]

        # ----------------------------------------------------
        # Figure
        # ----------------------------------------------------

        fig.update_layout(

            title=(
                f"{scale_label} CO₂ "
                f"time series at {station}"
            ),

            autosize=True,

            height=self.height,

            margin=dict(
                l=75,
                r=30,
                t=100,
                b=60
            ),

            xaxis=dict(
                title="Time",
                showgrid=True,
                automargin=True
            ),

            yaxis=dict(
                title=(
                    f"CO₂ concentration "
                    f"({unit})"
                ),

                showgrid=True,

                automargin=True
            ),

            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(
                    size=10
                )
            ),

            hovermode="x unified",

            template="plotly_white",

            # Native Plotly legend interaction:
            #
            # click:
            #     hide/show one trace
            #
            # double click:
            #     isolate one trace
            #
            # This is Plotly's default behaviour.
            showlegend=True,
        )

        # ----------------------------------------------------
        # Statistics annotation -- hourly view only
        # ----------------------------------------------------

        if stats is not None:

            R, RMSE, MB, N = stats

            def fmt(value, digits=2):

                if pd.isna(value):
                    return "N/A"

                return f"{value:.{digits}f}"

            stats_text = (
                "<b>Simulated Total vs Observation</b><br>"
                f"R = {fmt(R, 3)}<br>"
                f"RMSE = {fmt(RMSE, 2)}<br>"
                f"MB = {fmt(MB, 2)}<br>"
                f"N = {N}"
            )

            fig.add_annotation(
                text=stats_text,
                xref="paper",
                yref="paper",
                x=0.01,
                y=0.99,
                xanchor="left",
                yanchor="top",
                showarrow=False,
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="gray",
                borderwidth=1,
                font=dict(size=11)
            )

        # ----------------------------------------------------
        # Display main plot
        # ----------------------------------------------------

        with self.out:

            clear_output(wait=True)

            fig.show(
                config={
                    "responsive": True,
                    "displaylogo": False,
                }
            )

        # ----------------------------------------------------
        # Display secondary diagnostic plot
        # ----------------------------------------------------

        try:

            if self.time_scale.value == "hourly":
                diagnostic_fig = self._draw_diurnal_plot(station)
            else:
                diagnostic_fig = self._draw_daily_contribution_plot(station)

            with self.diagnostic_out:

                clear_output(wait=True)

                diagnostic_fig.show(
                    config={
                        "responsive": True,
                        "displaylogo": False,
                    }
                )

        except Exception as e:

            with self.diagnostic_out:

                clear_output(wait=True)

                display(
                    HTML(
                        f"""
                        <div style="height:300px;display:flex;align-items:center;
                        justify-content:center;color:#b00020;">
                        Error while creating diagnostic plot:<br>{e}
                        </div>
                        """
                    )
                )


    # ========================================================
    # Station information
    # ========================================================

    def _station_info_text(
        self,
        station
    ):

        if station is None:

            return (
                "<b>Observation station:</b> "
                "Click a station on the map."
            )

        meta = self._station_metadata(
            station
        )

        model = self._get_model_series(
            station
        )

        i = model["i"]
        j = model["j"]

        target_z = model[
            "target_z"
        ]

        eta_values = np.asarray(
            self.ds["eta"].values
        ).ravel()

        eta0 = (
            float(eta_values[0])
            if len(eta_values)
            else np.nan
        )

        observation_z = (
            meta["elevation"]
            +
            meta["sampling_height"]
        )

        return (

            f"<b>Station:</b> "
            f"{station}"

            f" &nbsp; | &nbsp; "

            f"<b>Lat:</b> "
            f"{meta['lat']:.4f}"
            f" &nbsp; | &nbsp; "

            f"<b>Lon:</b> "
            f"{meta['lon']:.4f}"
            f" &nbsp; | &nbsp; "
            
            f"<b>Elevation:</b> "
            f"{meta['elevation']:.1f} m ASL"
            f" &nbsp; | &nbsp; "
            
            f"<b>Sampling:</b> "
            f"{meta['sampling_height']:.1f} m AGL"
            f" &nbsp; | &nbsp; "

            f"<b>Target height:</b> "
            f"{observation_z:.1f} m ASL"

            f"<br>"
            
            f"<b>WRF grid:</b> "
            f"({i}, {j})"
            f" &nbsp; | &nbsp; "

            f"<b>Vertical level:</b> 0"
            f" &nbsp; | &nbsp; "

            f"<b>η:</b> {eta0:.5f}"
            f" &nbsp; | &nbsp; "

            f"<b>Zₑ interpolation:</b> "
            f"{target_z:.1f} m ASL"
        )


    # ========================================================
    # Update station information
    # ========================================================

    def _update_station_info(self):

        self.station_info.value = (

            self._station_info_text(
                self.selected_station
            )
        )


    # ========================================================
    # Selection changed
    # ========================================================

    def _selection_changed(
        self,
        change
    ):

        if self.selected_station is not None:

            self._draw_plot()


    # ========================================================
    # Time scale changed
    # ========================================================

    def _time_scale_changed(
        self,
        change
    ):

        scale = change[
            "new"
        ]

        options = self._make_time_options(
            scale
        )

        self.time.options = options

        if options:

            self.time.value = (
                options[0][1]
            )

        if self.selected_station is not None:

            self._draw_plot()


    # ========================================================
    # Show
    # ========================================================

    def show(self):

        display(
            HTML(CSS)
        )

        display(
            self.widget
        )

        return self

from collections import OrderedDict


class MAPTS(MapPanels):
    """Combined CO2 map + selected-grid time series with bounded caching."""

    SERIES = [
        ("Total", "total", "red", 2.4),
        ("Background", "bck", "blue", 1.7),
        ("Background + biogenic", "bck_bio", "green", 1.7),
        ("Background + anthropogenic", "bck_ant", "orange", 1.7),
    ]

    def __init__(
        self, ds, offset=OFFSET, height=600, zoom=8,
        amb_path="./data/AMB_BCN_limit_P.shp",
        bcn_path="./data/BCN_WGS84_4.shp",
        plot_share=1.25,
        cache_cells=3,
    ):
        # Store the cache before parent initialization.
        self._series_cache = OrderedDict()
        self._cache_cells = max(1, int(cache_cells))
        self._loading_series = False
        self.plot_share = plot_share
        self.i = self.j = None
        self.out = None

        super().__init__(ds, offset, height, zoom, amb_path, bcn_path)

        self.out = W.Output(layout=W.Layout(
            width="100%", height=f"{self.height}px",
            min_width="0", overflow="hidden"))
        with self.out:
            display(W.HTML(
                f"<div style='height:{self.height}px;display:flex;"
                "align-items:center;justify-content:center;color:#666;"
                "text-align:center;padding:12px;'>"
                "Click a grid cell on the map to display its CO₂ time series."
                "</div>"))

        controls = [
            W.HBox([self.time_scale, self.time],
                   layout=W.Layout(width="100%", column_gap="10px",
                                   flex_flow="row wrap")),
            self.eta,
            self.component,
            W.HBox([self.cmap, self.robust, self.show_amb, self.show_bcn],
                   layout=W.Layout(width="100%", column_gap="10px",
                                   flex_flow="row wrap")),
            self.level_info,
        ]

        panels = W.HBox([
            W.VBox([self.map_title, self.map],
                   layout=W.Layout(width="auto", flex="1 1 0%",
                                   min_width="0", overflow="hidden")),
            W.VBox([
                W.HTML("<h3 style='text-align:center;margin:5px 0;'>"
                       "CO₂ time series at selected grid</h3>"),
                self.out,
            ], layout=W.Layout(width="auto", flex=f"{self.plot_share} 1 0%",
                               min_width="0", overflow="hidden")),
        ], layout=W.Layout(width="100%", column_gap="16px",
                          align_items="flex-start", overflow="hidden"))

        self.widget = W.VBox(controls + [panels, self.info],
                             layout=W.Layout(width="100%", overflow="hidden"))

        self.time_scale.observe(self._plot_selection_changed, names="value")
        self.time.observe(self._plot_selection_changed, names="value")
        self.eta.observe(self._plot_selection_changed, names="value")

    def _make_time_options(self, scale):
        # Retain hourly/daily/monthly selection.
        if scale == "monthly":
            months = self.times.to_period("M").drop_duplicates()
            return [(str(month), i) for i, month in enumerate(months)]
        if scale == "daily":
            days = pd.DatetimeIndex(self.times.normalize()).drop_duplicates()
            return [(day.strftime("%Y-%m-%d"), i) for i, day in enumerate(days)]
        return [(t.strftime("%Y-%m-%d %H:%M"), i)
                for i, t in enumerate(self.times)]

    def _selected_day(self):
        days = pd.DatetimeIndex(self.times.normalize()).drop_duplicates()
        return days[int(self.time.value)]

    def _selected_month(self):
        months = self.times.to_period("M").drop_duplicates()
        return months[int(self.time.value)]

    def _grid_cache_key(self):
        return (int(self.i), int(self.j), int(self.eta.value))

    def _load_selected_grid_series(self):
        """Load all three tracer time series together; cache only small 1-D arrays."""
        key = self._grid_cache_key()

        if key in self._series_cache:
            self._series_cache.move_to_end(key)
            return self._series_cache[key]

        # Get the actual spatial dimension names from the lat coordinate,
        # instead of assuming they are always named south_north/west_east.
        spatial_dims = tuple(self.ds["lat"].dims)
        if len(spatial_dims) != 2:
            raise ValueError(
                f"Expected 2-D lat coordinate; found dims {spatial_dims!r}"
            )
        y_dim, x_dim = spatial_dims

        indexers = {y_dim: int(self.i), x_dim: int(self.j)}
        if "eta" in self.ds["tracer1"].dims:
            indexers["eta"] = int(self.eta.value)

        tracer_names = [TRACERS["bck"], TRACERS["bio"], TRACERS["ant"]]

        # IMPORTANT: one compute for all three selected point series. This
        # shares the Dask task graph and avoids three separate reads/schedules.
        selected = self.ds[tracer_names].isel(indexers).compute()

        bck = np.asarray(selected[TRACERS["bck"]].values, dtype=np.float32).reshape(-1)
        bio = np.asarray(selected[TRACERS["bio"]].values, dtype=np.float32).reshape(-1)
        ant = np.asarray(selected[TRACERS["ant"]].values, dtype=np.float32).reshape(-1)

        # Correct the stored constant offset before deriving combined series.
        bio = bio - np.float32(self.offset)
        ant = ant - np.float32(self.offset)

        result = {
            "total": bck + bio + ant,
            "bck": bck,
            "bck_bio": bck + bio,
            "bck_ant": bck + ant,
        }

        # Keep a bounded number of cells; arrays are 1-D time series only.
        self._series_cache[key] = result
        self._series_cache.move_to_end(key)
        while len(self._series_cache) > self._cache_cells:
            self._series_cache.popitem(last=False)

        return result

    def _daily_means(self, values):
        frame = pd.DataFrame({"time": self.times, "value": values})
        means = frame.groupby(frame["time"].dt.normalize())["value"].mean()
        return means.index, means.to_numpy(dtype=np.float32)

    def _monthly_diurnal(self, values, month):
        mask = np.asarray(self.times.to_period("M") == month)
        frame = pd.DataFrame({
            "hour": self.times[mask].hour,
            "value": np.asarray(values, dtype=np.float32)[mask]
        })
        means = frame.groupby("hour")["value"].mean().reindex(range(24))
        return np.arange(24), means.to_numpy(dtype=np.float32)

    def _plot_selection_changed(self, change=None):
        # Do not touch the large dataset here: use cached 1-D arrays.
        if self.i is not None and self.j is not None and self.out is not None:
            self._draw_timeseries()

    def _click(self, **kw):
        # Parent handles the click, nearest grid, marker and map information.
        super()._click(**kw)
        if self.i is not None and self.j is not None and self.out is not None:
            self._draw_timeseries()

    def _draw_timeseries(self):
        if self.i is None or self.j is None:
            return

        # Only the first click for a given grid/eta reads model data.
        # Scale/time changes reuse these cached series.
        series = self._load_selected_grid_series()
        scale = self.time_scale.value
        unit = units(self.ds, TRACERS["bck"])
        fig = go.Figure()

        for name, key, color, width in self.SERIES:
            values = series[key]
            if scale == "hourly":
                x, y, x_title = self.times, values, "Time"
            elif scale == "daily":
                x, y = self._daily_means(values)
                x_title = "Date"
            else:
                x, y = self._monthly_diurnal(values, self._selected_month())
                x_title = "Hour of day (UTC)"

            fig.add_trace(go.Scatter(
                x=x, y=y, mode="lines", name=name,
                line=dict(color=color, width=width),
                connectgaps=False,
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    f"CO₂: %{{y:.2f}} {unit}<extra></extra>"
                )
            ))

        if scale == "hourly":
            fig.add_vline(x=self.times[int(self.time.value)],
                          line_width=1.3, line_dash="dash", line_color="black")
            plot_title = "Hourly CO₂ time series"
        elif scale == "daily":
            fig.add_vline(x=self._selected_day(),
                          line_width=1.3, line_dash="dash", line_color="black")
            plot_title = "Daily-mean CO₂ time series"
        else:
            plot_title = f"Mean diurnal CO₂ cycle — {self._selected_month()}"

        lat = float(self.lat[self.i, self.j])
        lon = float(self.lon[self.i, self.j])

        fig.update_layout(
            autosize=True,
            height=self.height,
        
            # Give the title and bottom legend enough space
            margin=dict(l=65, r=20, t=85, b=55),
        
            # Title and grid information
            title=dict(
                text=plot_title,
                x=0.5,
                xanchor="center",
                y=0.98,
                yanchor="top",
                font=dict(size=13),
            ),
        
            xaxis=dict(
                title=x_title,
                showgrid=True,
                automargin=True,
                title_standoff=12,
            ),
        
            yaxis=dict(
                title=f"CO₂ concentration ({unit})",
                showgrid=True,
                automargin=True,
                title_standoff=12,
            ),

            
            # Put the legend below the plotting area
            legend=dict(
                orientation="h",
                yanchor="top",
                y=1.03,
                xanchor="center",
                x=0.5,
                font=dict(size=9),
                bgcolor="rgba(255,255,255,0.8)",
            ),
        
            hovermode="x unified",
            template="plotly_white",
        )

        with self.out:
            clear_output(wait=True)
            fig.show(config={"responsive": True, "displaylogo": False})

    def clear_series_cache(self):
        """Optional: release cached point series from memory."""
        self._series_cache.clear()

    def show(self):
        display(HTML(CSS))
        display(self.widget)
        return self


def _make_annual_hourly_dataset(
    ds,
    year=2023,
    time_chunk=24,
    keep_variables=None,
):
    """
    Build a lightweight annual Dataset with NaN gaps.

    The result stays Dask-lazy. No .compute() or .persist() is called here.
    """
    if "time" not in ds.coords:
        raise KeyError("The dataset must have a 'time' coordinate.")

    # Retain only fields actually used by Validate2/MapPanels/MAPTS.
    # Coordinates lat/lon/eta are retained automatically by xarray.
    if keep_variables is None:
        candidates = [
            "tracer1", "tracer2", "tracer3",
            "Z_e", "Z_sfc",
        ]
        keep_variables = [v for v in candidates if v in ds.data_vars]

    missing_tracers = [
        v for v in ("tracer1", "tracer2", "tracer3")
        if v not in ds.data_vars
    ]
    if missing_tracers:
        raise KeyError(f"Missing required tracer variables: {missing_tracers}")

    slim = ds[keep_variables]

    # Smaller time chunks are important: input files commonly have chunks of
    # 720 hours, which makes even a single selected timestamp expensive.
    if time_chunk and "time" in slim.dims:
        try:
            slim = slim.chunk({"time": int(time_chunk)})
        except (ValueError, TypeError):
            # If Dask is unavailable or arrays are not chunkable, continue
            # without forcing data into memory.
            pass

    slim = slim.sortby("time")
    times = pd.DatetimeIndex(pd.to_datetime(slim["time"].values))

    if times.has_duplicates:
        keep = ~times.duplicated(keep="first")
        slim = slim.isel(time=np.flatnonzero(keep)).sortby("time")

    annual_time = pd.date_range(
        f"{int(year)}-01-01 00:00:00",
        f"{int(year) + 1}-01-01 00:00:00",
        inclusive="left",
        freq="h",
    )

    # Missing timestamps become NaN. This is lazy; do not call persist().
    return slim.reindex(time=annual_time)


