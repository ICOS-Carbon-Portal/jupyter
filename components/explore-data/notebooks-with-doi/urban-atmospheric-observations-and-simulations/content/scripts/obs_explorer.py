## This function has the option of plotting time series, diurnal cycles, and pollutant roses
## The inputs are: 
## - Station data dictionary (required)
## site_names (default= None, should be a list e.g. ['ICTA', 'ICM']
## variable (default= "co2")
## plot_type (default= 'timeseries', options: "timeseries","diurnal", "excess","rose","excess_rose", 
##                                           "excessrose", "delta_rose")
# --- Excess / Background Options ---
## background_station (default="Fabra")
## urban_stations (default= None, should be a list e.g. ['ICTA', 'ICM']
##
# --- Wind Sector & Speed Filters ---
## sectors=None,
## min_speed (default= None, it is in m/s, should be a float e.g., 2.0 to remove calm winds) 
## max_speed (default= None, it is in m/s, should be a float e.g., 10.0 to limit the range of wind speed) 
##
# --- Time Filters ---
## seasons (default= None, which means the whole timeseries, for selecting a season choose one or more e.g., 
##         ['summer'] or  ['summer','spring','autumn'] or ['winter','autumn'], etc...
## months (default= None, which means the whole timeseries, the month should be an integer e.g. 8 for August
## years (default= None, which means the whole timeseries, the year should be an integer e.g. 2024
## hours (default= None, which means the whole timeseries, this option is for a range e.g., range(8, 18) or [8, 9, 10]
## start_hour (default= None, which means the whole timeseries, but you can use an integer to select a starting hour, e.g., 8 (inclusive)
## end_hour (default= None, which means the whole timeseries, but you can use an integer to select an ending hour, e.g., 17 (inclusive)
## start_date (default= None, which means the whole timeseries, but you can use a date format to select an specific perdiod, e.g. '2026-12-01'
## end_date (default= None, which means the whole timeseries, but you can use a date format to select an specific perdiod, e.g. '2026-12-01'
## day_type (default= None, which means the whole timeseries, options are: 'weekday' and 'weekend'
## 
# --- Formatting & Rose Options ---
## resample_freq (default="1h" , if any resample is needed you can choose the frequency)
## variability (default="sem", which stands for standard error, this option is for 'diurnal' plots,
                ## options are: 'std' for 1 standard deviation, 'iqr' for interquartile, or  'ci95' for 95% confidence interval
## n_sectors=16 (default=16, this is for windroses/pollutant roses options) 
## concentration_bins (default=5, this is for windroses/pollutant roses options) 
# --- Day/Night Options: valid for time series ---
## split_day_night (default=False, this is for visualization purposes, so  you can visually distinguish between day and night in the timeseries)##
## day_start (if split_day_night=True, the default time to start the day is 6am (this will be based on the index timezone!))
## day_end (if split_day_night=True, the default time to end the day is 18 (6pm) (this will be based on the index timezone!))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
from plotly.subplots import make_subplots
import re
import folium
from statsmodels.tsa.seasonal import STL


#=============================================================================================
#=============================================================================================

# Function to create stations map

def create_station_map(
    data, lat_col="lat", lon_col="lon", zoom_start=11, tiles="OpenStreetMap"
):
    """Generates an interactive Folium map with station markers from a DataFrame."""
    # Center map on the mean latitude and longitude
    map_center = [data[lat_col].mean(), data[lon_col].mean()]
    m = folium.Map(location=map_center, tiles=tiles, zoom_start=zoom_start)

    # Add markers for each station
    for _, row in data.iterrows():
        popup_text = f"""
        <div style="white-space: nowrap;">
            <b>Station:</b> <a href="{row['uri']}" target="_blank">{row['name']}</a><br>
            <b>Elevation:</b> {row['elevation']} m
        </div>
        """

        folium.Marker(
            location=[row[lat_col], row[lon_col]],
            popup=folium.Popup(popup_text),
            tooltip=row["name"],
        ).add_to(m)

    return m




#=============================================================================================    
#=============================================================================================
    

# DATA AVAILABILITY: Summary table (considers the data available for CO2)


def summarize_availability(station_dict, var_name="co2"):
    summary_list = []

    for name, df in station_dict.items():
        df_temp = df.copy()

        # Ensure datetime index
        if not isinstance(df_temp.index, pd.DatetimeIndex):
            df_temp.index = pd.to_datetime(df_temp.index)

        # Drop duplicate timestamps if present
        df_temp = df_temp[~df_temp.index.duplicated(keep="first")]

        # Filter: Must have valid value AND Flag == 'O'
        valid_mask = df_temp[var_name].notna() & (df_temp["Flag"] == "O")
        available_hours = valid_mask.sum()

        start_time = df_temp.index.min()
        end_time = df_temp.index.max()

        total_expected_hours = (
            int((end_time - start_time).total_seconds() / 3600) + 1
        )
        missing_hours = total_expected_hours - available_hours
        coverage_pct = (
            (available_hours / total_expected_hours) * 100
            if total_expected_hours > 0
            else 0
        )

        summary_list.append({
            "Station": name,
            "Start": start_time,
            "End": end_time,
            "Available Hours (Flag O)": available_hours,
            "Missing/Bad Hours": missing_hours,
            "Expected Hours": total_expected_hours,
            "Coverage (%)": round(coverage_pct, 2),
        })

    return pd.DataFrame(summary_list)




#=========================================================================================
#=========================================================================================

def calculate_noaa_growth_rate(
    sites_dict: dict[str, pd.DataFrame],
    col: str,
    flag_col: str = "flag",
    valid_flags: list = ["O"],
    n_bootstraps: int = 100,
) -> pd.DataFrame:
    """Calculates NOAA annual growth rates with 95% confidence intervals for ANY gas.

    Parameters:
    -----------
    sites_dict : dict
        Dictionary of site DataFrames (e.g., {'ICTA': df_icta, 'ICM': df_icm}).
    col : str
        Column name to analyze (e.g., 'co2', 'ch4', 'CO2', 'CH4').
    flag_col : str
        Column name containing quality flags.
    valid_flags : list
        Accepted unflagged/valid status values.
    n_bootstraps : int
        Number of Monte Carlo iterations for 95% CI estimation.

    Returns:
    --------
    pd.DataFrame
        Table of growth rates formatted as 'Value ± CI (unit)'.
    """
    formatted_results = {}

    # Detect gas type & automatically configure scaling + units
    is_ch4 = "ch4" in col.lower()
    scale_factor = 1000.0 if is_ch4 else 1.0
    unit = "ppb/yr" if is_ch4 else "ppm/yr"
    fmt = ".1f" if is_ch4 else ".2f"

    for site_name, df in sites_dict.items():
        if col not in df.columns:
            continue

        # 1. Filter quality flags
        clean_df = (
            df[df[flag_col].isin(valid_flags)] if flag_col in df.columns else df
        )

        # 2. Resample to monthly means & apply unit scaling
        monthly_series = (
            clean_df[col].resample("ME").mean().interpolate(method="linear")
            * scale_factor
        )

        # Require at least 2 full years of data
        if len(monthly_series.dropna()) < 24:
            continue

        # 3. Base STL Decomposition
        stl = STL(monthly_series, period=12, robust=True)
        res = stl.fit()
        base_trend = res.trend
        residuals = res.resid

        # Base NOAA Growth Rate (Dec_t - Dec_t-1)
        dec_base = base_trend[base_trend.index.month == 12]
        dec_base.index = dec_base.index.year
        base_rates = dec_base.diff()

        # 4. Monte Carlo Bootstrapping for Uncertainty
        boot_rates = {year: [] for year in base_rates.dropna().index}

        np.random.seed(42)  # For reproducibility
        for _ in range(n_bootstraps):
            resampled_resid = np.random.choice(
                residuals.dropna(), size=len(monthly_series)
            )
            synthetic_series = base_trend + resampled_resid

            stl_boot = STL(synthetic_series, period=12, robust=True)
            boot_trend = stl_boot.fit().trend

            dec_boot = boot_trend[boot_trend.index.month == 12]
            dec_boot.index = dec_boot.index.year
            rate_boot = dec_boot.diff()

            for year in boot_rates.keys():
                if year in rate_boot.index and not np.isnan(rate_boot[year]):
                    boot_rates[year].append(rate_boot[year])

        # 5. Format results into string: "Value ± 1.96*SE (unit)"
        site_formatted = {}
        for year, rate in base_rates.items():
            if np.isnan(rate):
                site_formatted[year] = "NaN"
            else:
                std_err = np.std(boot_rates[year])
                ci_95 = 1.96 * std_err
                site_formatted[year] = (
                    f"{rate:{fmt}} ± {ci_95:{fmt}} ({unit})"
                )

        formatted_results[site_name] = pd.Series(site_formatted)

    df_out = pd.DataFrame(formatted_results)
    df_out.index.name = "Year"
    return df_out



#=========================================================================================
#=========================================================================================




# Meta dictionary containing units and descriptions for variables
DEFAULT_DOBJ_META = {
    "co2": {"unit": "ppm", "label": "CO₂ mole fraction"},
    "ch4": {"unit": "ppm", "label": "CH₄ mole fraction"},
    "co2_std": {"unit": "ppm", "label": "CO₂ SD within the hour"},
    "ch4_std": {"unit": "ppm", "label": "CH₄ SD within the hour"},
    "co": {"unit": "ppb", "label": "CO mole fraction"},
    "wind_speed_ms": {"unit": "m/s", "label": "Wind Speed"},
    "drct": {"unit": "°", "label": "Wind Direction"},
}


def format_gas_html(var_name):
    """Formats gas variable string to HTML subscript format (e.g., 'co2' -> 'CO<sub>2</sub>')."""
    return re.sub(r"(\d+)", r"<sub>\1</sub>", str(var_name).upper())


def plot_station_data_advanced(
    station_data_dict,
    site_names=None,
    variable="co2",  # Accepts string or list/tuple of strings (e.g., ["co2", "ch4", "co"])
    plot_type="timeseries",
    # --- Excess / Background Options ---
    background_station="Fabra",
    urban_stations=None,
    # --- Wind Sector & Speed Filters ---
    sectors=None,
    min_speed=None,
    max_speed=None,
    # --- Time Filters ---
    seasons=None,
    months=None,
    years=None,
    hours=None,        # e.g., range(8, 18) or [8, 9, 10]
    start_hour=None,   # e.g., 8 (inclusive)
    end_hour=None,     # e.g., 17 (inclusive)
    start_date=None,
    end_date=None,
    day_type=None,
    # --- Formatting, Rose & Day/Night Options ---
    resample_freq="1h",
    variability="sem",
    n_sectors=16,
    concentration_bins=5,
    # --- Day/Night Options: valid for time series ---
    split_day_night=False,
    day_start=6,
    day_end=18,
    # --- Metadata Option ---
    dobj_meta=None,
):
    """Unified interactive Plotly plotting function for air quality & meteorological station data."""
    if dobj_meta is None:
        dobj_meta = DEFAULT_DOBJ_META

    colors = [
        "#636EFA",
        "#EF553B",
        "#00CC96",
        "#AB63FA",
        "#FFA15A",
        "#19D3F3",
        "#FF6692",
    ]

    dir_sectors_16 = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
    ]
    sector_group_map = {
        "N": ["N", "NNW", "NNE"],
        "NE": ["NE", "ENE", "NNE"],
        "E": ["E", "ENE", "ESE"],
        "SE": ["SE", "ESE", "SSE"],
        "S": ["S", "SSE", "SSW"],
        "SW": ["SW", "SSW", "WSW"],
        "W": ["W", "WSW", "WNW"],
        "NW": ["NW", "WNW", "NNW"],
    }

    def get_unit_str(var):
        """Helper to fetch formatted unit string from metadata if present."""
        meta = dobj_meta.get(str(var).lower(), {})
        unit = meta.get("unit", "")
        return f" ({unit})" if unit else ""


    # Standardize 'variable' input to a list
    if isinstance(variable, (list, tuple)):
        variables = list(variable)
    else:
        variables = [variable]

    selected_cardinals = []
    if sectors is not None:
        sector_list = [sectors] if isinstance(sectors, str) else list(sectors)
        for s in sector_list:
            s_upper = str(s).upper()
            if s_upper in sector_group_map:
                selected_cardinals.extend(sector_group_map[s_upper])
            elif s_upper in dir_sectors_16:
                selected_cardinals.append(s_upper)
        selected_cardinals = list(set(selected_cardinals))

    def apply_filters(df_input):
        if df_input is None or df_input.empty:
            return pd.DataFrame()

        df = df_input.copy()

        if "TIMESTAMP" in df.columns:
            df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])
            df = df.set_index("TIMESTAMP")
        elif not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        if "Flag" in df.columns:
            df = df[df["Flag"] == "O"]

        if "dir_sector" not in df.columns and "drct" in df.columns:
            shifted_deg = (df["drct"] + 11.25) % 360
            sector_idx = (shifted_deg // 22.5).astype("Int64")
            df["dir_sector"] = sector_idx.map(dict(enumerate(dir_sectors_16)))

        mask = pd.Series(True, index=df.index)

        if selected_cardinals and "dir_sector" in df.columns:
            mask &= df["dir_sector"].isin(selected_cardinals)
        if min_speed is not None and "wind_speed_ms" in df.columns:
            mask &= df["wind_speed_ms"] >= min_speed
        if max_speed is not None and "wind_speed_ms" in df.columns:
            mask &= df["wind_speed_ms"] <= max_speed

        if start_date is not None:
            mask &= df.index >= pd.to_datetime(start_date)
        if end_date is not None:
            mask &= df.index <= pd.to_datetime(end_date)
        if years is not None:
            year_list = [years] if isinstance(years, int) else list(years)
            mask &= df.index.year.isin(year_list)
        if months is not None:
            month_list = [months] if isinstance(months, int) else list(months)
            mask &= df.index.month.isin(month_list)

        if seasons is not None:
            season_list = (
                [seasons] if isinstance(seasons, str) else list(seasons)
            )
            season_month_map = {
                "DJF": [12, 1, 2], "WINTER": [12, 1, 2],
                "MAM": [3, 4, 5], "SPRING": [3, 4, 5],
                "JJA": [6, 7, 8], "SUMMER": [6, 7, 8],
                "SON": [9, 10, 11], "AUTUMN": [9, 10, 11], "FALL": [9, 10, 11],
            }
            matched_months = []
            for s in season_list:
                matched_months.extend(season_month_map.get(str(s).upper(), []))
            if matched_months:
                mask &= df.index.month.isin(matched_months)

        if day_type is not None:
            if str(day_type).lower() == "weekday":
                mask &= df.index.dayofweek < 5
            elif str(day_type).lower() == "weekend":
                mask &= df.index.dayofweek >= 5

        if hours is not None:
            hour_list = [hours] if isinstance(hours, (int, float)) else list(hours)
            mask &= df.index.hour.isin(hour_list)

        if start_hour is not None:
            mask &= df.index.hour >= start_hour
        if end_hour is not None:
            mask &= df.index.hour <= end_hour

        return df[mask]

    def compute_bounds(stats_df, var_setting):
        if not var_setting:
            return None, None, ""

        var_type = str(var_setting).lower().strip()
        ste = stats_df["std"] / np.sqrt(stats_df["count"])

        if var_type == "iqr":
            return stats_df["q25"], stats_df["q75"], "25th-75th Percentile"
        elif var_type in ["std", "sd"]:
            return (
                stats_df["mean"] - stats_df["std"],
                stats_df["mean"] + stats_df["std"],
                "±1 SD",
            )
        elif var_type in ["ste", "sem"]:
            return stats_df["mean"] - ste, stats_df["mean"] + ste, "±1 SEM"
        elif var_type == "ci95":
            return (
                stats_df["mean"] - (1.96 * ste),
                stats_df["mean"] + (1.96 * ste),
                "95% CI",
            )
        return None, None, ""

    # Check for multi-variable vs single-variable layout
    n_vars = len(variables)
    is_polar = plot_type.lower() in ["rose", "excess_rose", "excessrose", "delta_rose"]

    if n_vars > 1 and not is_polar:
        fig = make_subplots(
            rows=n_vars,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=max(0.04, 0.12 / n_vars),
            subplot_titles=[
                f"Variable: {format_gas_html(v)}{get_unit_str(v)}" for v in variables
            ],
        )
    else:
        fig = go.Figure()

    has_data_to_plot = False
    active_band_label = ""

    # =========================================================================
    # PLOT OPTION : URBAN EXCESS ROSE
    # =========================================================================
    if plot_type.lower() in ["excess_rose", "excessrose", "delta_rose"]:
        var = variables[0]
        site = site_names[0] if isinstance(site_names, list) else site_names
        if not site or site not in station_data_dict:
            print("Please specify a valid urban station in `site_names`.")
            return

        if background_station not in station_data_dict:
            print(f"Background station '{background_station}' not found.")
            return

        urban_df = apply_filters(station_data_dict[site])
        bg_df = apply_filters(station_data_dict[background_station])

        if urban_df.empty or bg_df.empty:
            print("Filtered dataset is empty.")
            return

        wd_col = None
        for col in ["drct", "wdir", "wind_dir", "WD", "direction"]:
            if col in urban_df.columns:
                wd_col = col
                break

        if wd_col is None:
            if "dir_sector" in urban_df.columns:
                cardinal_deg_map = {
                    "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5, "E": 90,
                    "ESE": 112.5, "SE": 135, "SSE": 157.5, "S": 180,
                    "SSW": 202.5, "SW": 225, "WSW": 247.5, "W": 270,
                    "WNW": 292.5, "NW": 315, "NNW": 337.5,
                }
                urban_df["drct"] = urban_df["dir_sector"].map(cardinal_deg_map)
                wd_col = "drct"
            else:
                print(f"Station '{site}' is missing a wind direction column.")
                return

        if var not in urban_df.columns or var not in bg_df.columns:
            print(f"Variable '{var}' missing from stations.")
            return

        urban_res = (
            urban_df[[var, wd_col]].dropna().resample("1h").first()
        )
        urban_res = urban_res.rename(columns={wd_col: "drct"})
        bg_res = bg_df[[var]].dropna().resample("1h").mean()

        aligned = pd.concat(
            [urban_res, bg_res], axis=1, keys=["urban", "bg"], sort=False
        ).dropna()
        if aligned.empty:
            print("No matching hourly timestamps between urban and background sites.")
            return

        has_data_to_plot = True

        aligned["excess"] = (
            aligned[("urban", var)] - aligned[("bg", var)]
        )
        aligned["drct"] = aligned[("urban", "drct")]

        bin_width = 360.0 / n_sectors
        half_width = bin_width / 2.0
        shifted_drct = (aligned["drct"] + half_width) % 360
        aligned["wdir_bin"] = (shifted_drct // bin_width) * bin_width

        excess_vals = aligned["excess"].values
        max_abs = np.nanpercentile(np.abs(excess_vals), 98)
        bin_edges = np.linspace(-max_abs, max_abs, concentration_bins + 1)
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf

        labels = [
            f"Δ {bin_edges[i]:.1f} to {bin_edges[i+1]:.1f}"
            for i in range(len(bin_edges) - 1)
        ]
        labels[0] = f"Δ < {bin_edges[1]:.1f} (Clean/BG)"
        labels[-1] = f"Δ > {bin_edges[-2]:.1f} (High Excess)"

        aligned["var_bin"] = pd.cut(
            aligned["excess"],
            bins=bin_edges,
            labels=labels,
            include_lowest=True,
        )

        total_obs = len(aligned)
        counts = (
            aligned.groupby(["wdir_bin", "var_bin"], observed=False)
            .size()
            .reset_index(name="count")
        )
        counts["frequency"] = (counts["count"] / total_obs) * 100.0

        palette = sample_colorscale(
            px.colors.diverging.RdBu_r, np.linspace(0, 1, concentration_bins)
        )
        all_angles = np.arange(0, 360, bin_width)

        for i, label in enumerate(labels):
            bin_data = counts[counts["var_bin"] == label]
            full_bin = pd.merge(
                pd.DataFrame({"wdir_bin": all_angles}),
                bin_data,
                on="wdir_bin",
                how="left",
            )
            full_bin["frequency"] = full_bin["frequency"].fillna(0)
            full_bin["count"] = full_bin["count"].fillna(0)
            full_bin["var_bin"] = full_bin["var_bin"].fillna(label)

            fig.add_trace(
                go.Barpolar(
                    r=full_bin["frequency"],
                    theta=full_bin["wdir_bin"],
                    width=bin_width,
                    name=f"{label}",
                    marker_color=palette[i],
                    marker_line_color="black",
                    marker_line_width=0.5,
                    hovertemplate=f"<b>Δ{site} ({site} − {background_station})</b><br>Dir: %{{theta:.0f}}°<br>Freq: %{{r:.1f}}%<br>Range: {label}<extra></extra>",
                )
            )

    # =========================================================================
    # PLOT OPTION : STANDARD POLLUTANT ROSE
    # =========================================================================
    elif plot_type.lower() == "rose":
        var = variables[0]
        site = site_names[0] if isinstance(site_names, list) else site_names
        if not site or site not in station_data_dict:
            print("Please specify `site_names` for rose plot mode.")
            return

        filtered_df = apply_filters(station_data_dict[site])
        if filtered_df.empty or var not in filtered_df.columns:
            print(f"Station '{site}' lacks required variable '{var}' or has no data.")
            return

        wd_col = None
        for col in ["drct", "wdir", "wind_dir", "WD", "direction"]:
            if col in filtered_df.columns:
                wd_col = col
                break

        if wd_col is None:
            print(f"Station '{site}' is missing wind direction column.")
            return

        clean_rose = filtered_df.dropna(subset=[wd_col, var]).copy()
        clean_rose["drct"] = clean_rose[wd_col]
        if clean_rose.empty:
            print("No valid wind direction and concentration pairs.")
            return

        has_data_to_plot = True

        bin_width = 360.0 / n_sectors
        half_width = bin_width / 2.0
        shifted_drct = (clean_rose["drct"] + half_width) % 360
        clean_rose["wdir_bin"] = (shifted_drct // bin_width) * bin_width

        quantiles = np.linspace(0, 1, concentration_bins + 1)
        bin_edges = np.quantile(clean_rose[var], quantiles)
        bin_edges = np.unique(bin_edges)

        labels = [
            f"{bin_edges[i]:.1f} – {bin_edges[i+1]:.1f}"
            for i in range(len(bin_edges) - 1)
        ]
        clean_rose["var_bin"] = pd.cut(
            clean_rose[var],
            bins=bin_edges,
            labels=labels,
            include_lowest=True,
        )

        total_obs = len(clean_rose)
        counts = (
            clean_rose.groupby(["wdir_bin", "var_bin"], observed=False)
            .size()
            .reset_index(name="count")
        )
        counts["frequency"] = (counts["count"] / total_obs) * 100.0

        palette = sample_colorscale(
            px.colors.sequential.Turbo, np.linspace(0, 1, len(labels))
        )
        all_angles = np.arange(0, 360, bin_width)

        for i, label in enumerate(labels):
            bin_data = counts[counts["var_bin"] == label]
            full_bin = pd.merge(
                pd.DataFrame({"wdir_bin": all_angles}),
                bin_data,
                on="wdir_bin",
                how="left",
            )
            full_bin["frequency"] = full_bin["frequency"].fillna(0)
            full_bin["count"] = full_bin["count"].fillna(0)
            full_bin["var_bin"] = full_bin["var_bin"].fillna(label)

            fig.add_trace(
                go.Barpolar(
                    r=full_bin["frequency"],
                    theta=full_bin["wdir_bin"],
                    width=bin_width,
                    name=f"{label}",
                    marker_color=palette[i],
                    marker_line_color="black",
                    marker_line_width=0.5,
                    hovertemplate=f"<b>{site}</b><br>Dir: %{{theta:.0f}}°<br>Freq: %{{r:.1f}}%<br>Range: {label}<extra></extra>",
                )
            )

    # =========================================================================
    # PLOT OPTION : URBAN EXCESS DIURNAL CYCLE
    # =========================================================================
    elif plot_type.lower() == "excess":
        if background_station not in station_data_dict:
            print(f"Background station '{background_station}' not found!")
            return

        bg_df = apply_filters(station_data_dict[background_station])
        if bg_df.empty:
            print(f"Background station '{background_station}' has no valid data after filtering.")
            return

        if urban_stations is None:
            urban_stations = ["ICTA", "ICM", "IDAEA", "UPC"]

        urb_sites = (
            [urban_stations]
            if isinstance(urban_stations, str)
            else list(urban_stations)
        )

        for v_idx, var in enumerate(variables, start=1):
            if var not in bg_df.columns:
                continue

            bg_series = bg_df[var].dropna().resample("1h").mean()

            for s_idx, site in enumerate(urb_sites):
                if site not in station_data_dict:
                    continue

                urban_df = apply_filters(station_data_dict[site])
                if urban_df.empty or var not in urban_df.columns:
                    continue

                urban_series = urban_df[var].dropna().resample("1h").mean()
                aligned = pd.concat(
                    [urban_series, bg_series], axis=1, keys=["urban", "bg"], sort=False
                ).dropna()

                if aligned.empty:
                    continue

                has_data_to_plot = True
                line_color = colors[s_idx % len(colors)]

                aligned["excess"] = aligned["urban"] - aligned["bg"]
                aligned["hour"] = aligned.index.hour

                stats = (
                    aligned.groupby("hour")["excess"]
                    .agg(
                        mean="mean",
                        std="std",
                        count="count",
                        q25=lambda x: x.quantile(0.25),
                        q75=lambda x: x.quantile(0.75),
                    )
                    .reset_index()
                )

                lower_bnd, upper_bnd, band_label = compute_bounds(stats, variability)
                if band_label:
                    active_band_label = band_label

                row_arg = v_idx if n_vars > 1 else None

                if lower_bnd is not None and upper_bnd is not None:
                    fig.add_trace(
                        go.Scatter(
                            x=pd.concat([stats["hour"], stats["hour"][::-1]]),
                            y=pd.concat([upper_bnd, lower_bnd[::-1]]),
                            fill="toself",
                            fillcolor=line_color,
                            opacity=0.18,
                            line=dict(color="rgba(255,255,255,0)"),
                            hoverinfo="skip",
                            showlegend=False,
                        ),
                        row=row_arg,
                        col=1 if row_arg else None,
                    )

                unit_str = get_unit_str(var)
                fig.add_trace(
                    go.Scatter(
                        x=stats["hour"],
                        y=stats["mean"],
                        mode="lines+markers",
                        name=f"Δ{site} ({site} − {background_station})" if v_idx == 1 else None,
                        legendgroup=site,
                        showlegend=(v_idx == 1),
                        line=dict(color=line_color, width=2.5),
                        marker=dict(size=6),
                        hovertemplate=f"<b>Δ{site}</b><br>Hour: %{{x}}:00<br>Δ{format_gas_html(var)}: %{{y:.2f}}{unit_str}<extra></extra>",
                    ),
                    row=row_arg,
                    col=1 if row_arg else None,
                )

                if row_arg:
                    fig.update_yaxes(title_text=f"Δ{format_gas_html(var)}{unit_str}", row=v_idx, col=1)

            if has_data_to_plot:
                fig.add_hline(
                    y=0,
                    line_dash="dash",
                    line_color="black",
                    opacity=0.6,
                    row=v_idx if n_vars > 1 else None,
                    col=1 if n_vars > 1 else None,
                )

    # =========================================================================
    # PLOT OPTION : DIURNAL CYCLE & TIMESERIES
    # =========================================================================
    elif plot_type.lower() in ["diurnal", "timeseries"]:
        if site_names is None:
            print(f"Please specify `site_names` for '{plot_type}' plot mode.")
            return

        sites = [site_names] if isinstance(site_names, str) else list(site_names)

        for v_idx, var in enumerate(variables, start=1):
            row_arg = v_idx if n_vars > 1 else None
            unit_str = get_unit_str(var)

            for s_idx, site in enumerate(sites):
                if site not in station_data_dict:
                    continue

                filtered_df = apply_filters(station_data_dict[site])
                if filtered_df.empty or var not in filtered_df.columns:
                    continue

                filtered_df = filtered_df.dropna(subset=[var])
                if filtered_df.empty:
                    continue

                has_data_to_plot = True
                line_color = colors[s_idx % len(colors)]

                if plot_type.lower() == "diurnal":
                    filtered_df = filtered_df.copy()
                    filtered_df["hour"] = filtered_df.index.hour
                
                    # --- IF PLOTTING DIRECT INTRA-HOUR CV (%) ---
                    if str(variability).lower() in ["cv_line", "cv_percent"]:
                        active_band_label = "Coefficient of Variation (%)"
                
                        # 1. Look up the matching STD column name (e.g., 'co2_std' or 'co2_STD')
                        std_var_name = f"{var}_std" if f"{var}_std" in filtered_df.columns else f"{var}_STD"
                
                        if std_var_name in filtered_df.columns:
                            # Calculate intra-hour CV row-by-row: (STD / Mean) * 100
                            filtered_df["_temp_cv"] = (filtered_df[std_var_name] / filtered_df[var].abs()) * 100
                            
                            # Average the true intra-hour CVs by hour
                            stats = filtered_df.groupby("hour")["_temp_cv"].mean().reset_index()
                            
                            fig.add_trace(
                                go.Scatter(
                                    x=stats["hour"],
                                    y=stats["_temp_cv"], # Now correctly shows ~1.2% instead of ~6%
                                    mode="lines+markers",
                                    name=f"{site} (CV %)" if v_idx == 1 else None,
                                    legendgroup=site,
                                    showlegend=(v_idx == 1),
                                    line=dict(color=line_color, width=2.5),
                                    marker=dict(size=6),
                                    hovertemplate=f"<b>{site}</b><br>Hour: %{{x}}:00<br>CV: %{{y:.2f}}%<extra></extra>",
                                ),
                                row=row_arg,
                                col=1 if row_arg else None,
                            )
                        else:
                            raise KeyError(f"Could not find '{std_var_name}' in DataFrame to calculate intra-hour CV.")
                
                    # --- STANDARD MEAN LINE + VARIABILITY BAND ---
                    else:
                        stats = (
                            filtered_df.groupby("hour")[var]
                            .agg(
                                mean="mean",
                                std="std",
                                count="count",
                                q25=lambda x: x.quantile(0.25),
                                q75=lambda x: x.quantile(0.75),
                            )
                            .reset_index()
                        )
                        
                        lower_bnd, upper_bnd, band_label = compute_bounds(stats, variability)
                        if band_label:
                            active_band_label = band_label
                
                        if lower_bnd is not None and upper_bnd is not None:
                            fig.add_trace(
                                go.Scatter(
                                    x=pd.concat([stats["hour"], stats["hour"][::-1]]),
                                    y=pd.concat([upper_bnd, lower_bnd[::-1]]),
                                    fill="toself",
                                    fillcolor=line_color,
                                    opacity=0.18,
                                    line=dict(color="rgba(255,255,255,0)"),
                                    hoverinfo="skip",
                                    showlegend=False,
                                ),
                                row=row_arg,
                                col=1 if row_arg else None,
                            )
                
                        fig.add_trace(
                            go.Scatter(
                                x=stats["hour"],
                                y=stats["mean"],
                                mode="lines+markers",
                                name=f"{site}" if v_idx == 1 else None,
                                legendgroup=site,
                                showlegend=(v_idx == 1),
                                line=dict(color=line_color, width=2.5),
                                marker=dict(size=6),
                                hovertemplate=f"<b>{site}</b><br>Hour: %{{x}}:00<br>{format_gas_html(var)}: %{{y:.2f}}{unit_str}<extra></extra>",
                            ),
                            row=row_arg,
                            col=1 if row_arg else None,
                        )

                elif plot_type.lower() == "timeseries":
                    ts_resample = (
                        filtered_df[var].resample(resample_freq).mean()
                    )

                    if split_day_night:
                        hrs = ts_resample.index.hour
                        if day_start < day_end:
                            is_day = (hrs >= day_start) & (hrs < day_end)
                        else:
                            is_day = (hrs >= day_start) | (hrs < day_end)

                        # Day Trace: Filled Circles
                        fig.add_trace(
                            go.Scatter(
                                x=ts_resample.index[is_day],
                                y=ts_resample.values[is_day],
                                mode="markers",
                                marker=dict(
                                    size=5,
                                    symbol="circle",
                                    color=line_color,
                                    opacity=0.85,
                                ),
                                name=f"{site} (Day)" if v_idx == 1 else None,
                                legendgroup=f"{site}_day",
                                showlegend=(v_idx == 1),
                                hovertemplate=f"<b>{site} (Day)</b><br>Time: %{{x}}<br>{format_gas_html(var)}: %{{y:.2f}}{unit_str}<extra></extra>",
                            ),
                            row=row_arg,
                            col=1 if row_arg else None,
                        )

                        # Night Trace: Hollow Circles
                        fig.add_trace(
                            go.Scatter(
                                x=ts_resample.index[~is_day],
                                y=ts_resample.values[~is_day],
                                mode="markers",
                                marker=dict(
                                    size=5,
                                    symbol="circle-open",
                                    color=line_color,
                                    line=dict(width=1.5),
                                    opacity=0.7,
                                ),
                                name=f"{site} (Night)" if v_idx == 1 else None,
                                legendgroup=f"{site}_night",
                                showlegend=(v_idx == 1),
                                hovertemplate=f"<b>{site} (Night)</b><br>Time: %{{x}}<br>{format_gas_html(var)}: %{{y:.2f}}{unit_str}<extra></extra>",
                            ),
                            row=row_arg,
                            col=1 if row_arg else None,
                        )
                    else:
                        fig.add_trace(
                            go.Scatter(
                                x=ts_resample.index,
                                y=ts_resample.values,
                                mode="markers",
                                marker=dict(
                                    size=3,
                                    color=line_color,
                                    opacity=0.8,
                                ),
                                name=site if v_idx == 1 else None,
                                legendgroup=site,
                                showlegend=(v_idx == 1),
                                hovertemplate=f"<b>{site}</b><br>Time: %{{x}}<br>{format_gas_html(var)}: %{{y:.2f}}{unit_str}<extra></extra>",
                            ),
                            row=row_arg,
                            col=1 if row_arg else None,
                        )

            if row_arg:
                fig.update_yaxes(title_text=f"{format_gas_html(var)}{unit_str}", row=v_idx, col=1)

    if not has_data_to_plot:
        print("No data available to plot after applying all filters.")
        return

    # --- Subtitle Filter Tags ---
    filter_tags = []
    if sectors:
        s_str = ",".join(sectors) if isinstance(sectors, (list, set)) else str(sectors)
        filter_tags.append(f"Wind Sector: {s_str}")
    if min_speed is not None or max_speed is not None:
        filter_tags.append(
            f"Speed: {min_speed if min_speed is not None else 0}-{max_speed if max_speed is not None else '∞'} m/s"
        )
    if seasons:
        sea_str = ",".join(seasons) if isinstance(seasons, (list, set)) else str(seasons)
        filter_tags.append(f"Season: {sea_str}")
    if years:
        y_str = ",".join(map(str, years)) if isinstance(years, (list, set)) else str(years)
        filter_tags.append(f"Year: {y_str}")
    if day_type:
        filter_tags.append(f"{str(day_type).capitalize()}s")

    if hours is not None or start_hour is not None or end_hour is not None:
        if hours is not None:
            h_str = ",".join(map(str, hours)) if isinstance(hours, (list, tuple, range, set)) else str(hours)
            filter_tags.append(f"Hours: {h_str}")
        else:
            sh = start_hour if start_hour is not None else 0
            eh = end_hour if end_hour is not None else 23
            filter_tags.append(f"Hours: {sh:02d}:00–{eh:02d}:00")

    if split_day_night and plot_type.lower() == "timeseries":
        filter_tags.append(f"Day/Night Split ({day_start:02d}:00–{day_end:02d}:00)")

    if active_band_label and plot_type.lower() in ["diurnal", "excess"]:
        filter_tags.append(f"Band: {active_band_label}")

    title_suffix = (
        "<br><sup>Filters: " + " | ".join(filter_tags) + "</sup>"
        if filter_tags
        else ""
    )

    # --- Final Layout Adjustments ---
    if is_polar:
        var = variables[0]
        var_html = format_gas_html(var)
        unit_str = get_unit_str(var)
        plot_title = (
            f"<b>Δ{var_html} Excess Rose ({site_names} − {background_station})</b>{title_suffix}"
            if "excess" in plot_type.lower() or "delta" in plot_type.lower()
            else f"<b>{var_html} Pollutant Rose ({site_names})</b>{title_suffix}"
        )
        legend_title = (
            f"Δ{var.upper()}{unit_str} Bins"
            if "excess" in plot_type.lower() or "delta" in plot_type.lower()
            else f"{var.upper()}{unit_str} Bins"
        )

        fig.update_layout(
            title=dict(text=plot_title, x=0.02, y=0.95),
            polar=dict(
                barmode="stack",
                radialaxis=dict(
                    visible=True,
                    ticksuffix="%",
                    showticklabels=True,
                    gridcolor="lightgray",
                    angle=90,
                ),
                angularaxis=dict(
                    direction="clockwise",
                    period=360,
                    rotation=90,
                    ticks="outside",
                    gridcolor="lightgray",
                ),
            ),
            template="plotly_white",
            height=650,
            width=780,
            legend=dict(
                title=legend_title,
                orientation="v",
                yanchor="top",
                y=0.9,
                xanchor="left",
                x=1.05,
            ),
        )
    else:
        var_str = ", ".join([format_gas_html(v) for v in variables])
        if plot_type.lower() == "excess":
            plot_title = f"<b>Diurnal Excess Δ{var_str} (vs {background_station})</b>{title_suffix}"
        else:
            plot_title = f"<b>{var_str} {plot_type.capitalize()}</b>{title_suffix}"

        calculated_height = max(560, 310 * n_vars)

        fig.update_layout(
            title=dict(text=plot_title, x=0.02, y=0.98),
            template="plotly_white",
            hovermode="x" if plot_type.lower() == "timeseries" else "x unified",
            height=calculated_height,
            width=950,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1
            ),
        )

        fig.update_xaxes(
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=1,
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor="lightgray",
            gridwidth=1,
        )

        # Handle Y-axis labels when single-variable or plotting CV
        if str(variability).lower() in ["cv_line", "cv_percent"]:
            # When plotting relative variability, overwrite Y-axis to Percentage (%)
            fig.update_yaxes(title_text="Coefficient of Variation (%)")
        elif n_vars == 1:
            var_single = variables[0]
            unit_str = get_unit_str(var_single)
            y_label = (
                f"Δ{format_gas_html(var_single)}{unit_str}"
                if plot_type.lower() == "excess"
                else f"{format_gas_html(var_single)}{unit_str}"
            )
            fig.update_yaxes(title_text=y_label)

        # Set X-axis title safely
        x_label = "Hour of Day (UTC)" if plot_type.lower() in ["diurnal", "excess"] else "TIMESTAMP"
        
        if n_vars > 1:
            fig.update_xaxes(title_text=x_label, row=n_vars, col=1)
        else:
            fig.update_xaxes(title_text=x_label)

        if plot_type.lower() in ["diurnal", "excess"]:
            fig.update_xaxes(dtick=2, range=[-0.5, 23.5])

        

    return fig