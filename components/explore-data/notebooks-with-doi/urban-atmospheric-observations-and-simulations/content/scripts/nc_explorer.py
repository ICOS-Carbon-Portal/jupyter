"""Viewers for WRF-style output.

WRFExplorer  clickable leaflet map + Plotly time series at the selected cell
MapPanels       2x2 pcolormesh maps: total and background, then biogenic and anthropogenic

Both take an xarray Dataset with 2-D lat/lon, a time coordinate, an eta vertical
dimension, and tracer1/tracer2/tracer3. Call .show() to display.
"""

# AI assistance:
# Portions of this code were developed and refined with assistance from OpenAI's ChatGPT (GPT-6).

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
TOTAL = "total"
LABELS = {"tracer1": "Background CO<sub>2</sub>", "tracer2": "Biogenic CO<sub>2</sub>",
          "tracer3": "Anthropogenic CO<sub>2</sub>", TOTAL: "Total CO<sub>2</sub> concentration"}
OFFSET = 400  # Added to tracer2 and tracer3 in the source data
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


def label(ds, var, matplotlib=False, plain=False):
    """CO2 labels for HTML-based widgets/Plotly or Matplotlib mathtext."""
    value = LABELS[TOTAL] if var == TOTAL else ds[var].attrs.get(
        "standard_name", LABELS.get(var, var))
    value = value.replace("CO₂", "CO<sub>2</sub>").replace("CO2", "CO<sub>2</sub>")
    if matplotlib:
        return value.replace("CO<sub>2</sub>", r"CO$_2$")
    if plain:  # ipywidgets.Dropdown options display plain text, not HTML
        return value.replace("CO<sub>2</sub>", "CO₂")
    return value


def units(ds, var):
    if var == TOTAL:
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
    """Color limits, guarding against a zero-width scale."""
    values = np.asarray(values)
    if robust:
        vmin, vmax = np.nanpercentile(values, [2, 98])
    else:
        vmin, vmax = np.nanmin(values), np.nanmax(values)
    if np.isclose(vmin, vmax):
        pad = abs(vmin) * 0.01 if vmin != 0 else 1.0
        vmin, vmax = vmin - pad, vmax + pad
    return float(vmin), float(vmax)


def eta_options(ds):
    """Use the dimensionless eta values for vertical-level selection."""
    if "eta" in ds.coords:
        return [(f"{float(v):.5f}", i) for i, v in enumerate(ds["eta"].values)]
    return [(f"eta {i}", i) for i in range(ds.sizes["eta"])]


# --------------------------------------------------- four-panel map view

class MapPanels:

    CMAPS = ["viridis", "plasma", "inferno", "magma", "turbo", "RdYlBu_r"]

    def __init__(self, ds, offset=OFFSET, figsize=(11, 9)):
        check(ds)
        self.ds, self.offset, self.figsize = ds, offset, figsize
        if "eta" not in ds["tracer1"].dims:
            raise KeyError("Tracer fields must contain an eta dimension.")
        style = {"description_width": "initial"}
        self.time = W.Dropdown(
            options=[(pd.Timestamp(t).strftime("%Y-%m-%d %H:%M"), i)
                     for i, t in enumerate(ds["time"].values)],
            value=0, description="Time:", layout=col(3), style=style)
        self.eta = W.Dropdown(
            options=eta_options(ds), value=0,
            description="eta:", layout=col(3), style=style)
        self.cmap = W.Dropdown(options=self.CMAPS, value="viridis",
                               description="Color map:", style=style, layout=col(2))
        self.robust = W.Checkbox(value=True, description="Use 2–98% percentile color limits",
                                 indent=False, layout=col(3))

        self.out = W.interactive_output(self._plot, {
            "ti": self.time, "ei": self.eta, "cmap": self.cmap, "robust": self.robust})
        self.out.layout = W.Layout(width="100%", overflow="hidden")

        self.widget = W.VBox([
            W.HBox([self.time, self.eta],
                   layout=W.Layout(width="100%", column_gap="10px", flex_flow="row wrap",
                                   overflow="hidden")),
            W.HBox([self.cmap, self.robust],
                   layout=W.Layout(width="100%", column_gap="10px", flex_flow="row wrap",
                                   overflow="hidden")),
            self.out,
        ], layout=W.Layout(width="100%", overflow="hidden"))

    def _plot(self, ti, ei, cmap, robust):
        fields = {v: slab(self.ds, v, self.offset, time=ti,
                          eta=ei) for v in TRACERS.values()}
        fields[TOTAL] = sum(fields.values())

        fig, axes = plt.subplots(2, 2, figsize=self.figsize, constrained_layout=True)
        for ax, var in zip(axes.flat, (TOTAL, *TRACERS.values())):
            field = fields[var]
            vmin, vmax = limits(field.values, robust)
            mesh = ax.pcolormesh(self.ds["lon"], self.ds["lat"], field, shading="auto",
                                 cmap=cmap, vmin=vmin, vmax=vmax)
            fig.colorbar(mesh, ax=ax, shrink=0.85).set_label(units(self.ds, var))
            ax.set(title=label(self.ds, var, matplotlib=True), xlabel="Longitude", ylabel="Latitude")
            ax.set_aspect("equal", adjustable="box")

        timestamp = pd.Timestamp(self.ds["time"].isel(time=ti).item())
        eta_label = eta_options(self.ds)[ei][0]
        fig.suptitle(f"{timestamp:%Y-%m-%d %H:%M} UTC  |  eta = {eta_label}", fontsize=14)
        plt.show()

    def show(self):
        display(HTML(CSS))
        display(self.widget)
        return self


# ------------------------------------------------- map + time series view

class WRFExplorer:

    def __init__(self, ds, offset=OFFSET, height=400, map_share=1, plot_share=2, zoom=8):
        check(ds)
        self.ds, self.offset, self.height = ds, offset, height
        if "eta" not in ds["tracer1"].dims:
            raise KeyError("Tracer fields must contain an eta dimension.")
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
        levels = eta_options(self.ds)

        self.time = W.Dropdown(options=times, value=0, description="Time:", style=style, layout=col(3))
        self.eta = W.Dropdown(options=levels, value=0, description="eta:", style=style, layout=col(2))
        self.tracer = W.Dropdown(options=[(label(self.ds, v, plain=True), v) for v in (*TRACERS.values(), TOTAL)],
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
            W.HBox([W.VBox([self._title("CO<sub>2</sub> concentration"), spacer], layout=col(map_share)),
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
                            eta=self.eta.value, time=self.time.value).values, float)
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
        for layer in (self.overlay, self.outline, self.marker):
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
            ("Background", bck, "blue", 1.5),
            ("Background + biogenic", bck + bio, "green", 1.5),
            ("Background + anthropogenic", bck + ant, "orange", 1.5),
            ("Total", bck + bio + ant, "black", 2.0),
        ]:
            fig.add_trace(go.Scatter(
                x=self.times, y=values, mode="lines", name=name,
                line=dict(color=color, width=w),
                hovertemplate=f"<b>{name}</b><br>CO<sub>2</sub>: %{{y:.2f}} {unit}<extra></extra>"))
        fig.add_vline(x=self.times[self.time.value], line_width=1.5,
                      line_dash="dash", line_color="red")
        fig.update_layout(
            autosize=True, height=self.height, margin=dict(l=70, r=20, t=45, b=50),
            xaxis=dict(title="Time", showgrid=True, automargin=True),
            yaxis=dict(title=f"CO<sub>2</sub> concentration ({unit})", showgrid=True, automargin=True),
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


