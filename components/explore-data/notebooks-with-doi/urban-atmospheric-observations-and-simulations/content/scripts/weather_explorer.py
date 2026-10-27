# Functions to explore weather data


import io
import urllib.request
import pandas as pd
import numpy as np
import plotly.express as px


def fetch_met_data(
    station="LEBL",
    vars_to_fetch=None,
    start_year=2025,
    end_year=2026,
    resample_hourly=True,
):
    """Fetches METAR/ASOS weather data for any specified airport from IEM

    and returns a clean, hourly-aggregated DataFrame with half-hour timestamps.

    Parameters:
    - station: Airport ICAO/IATA code (e.g., 'LEBL' for Barcelona, 'EGLL' for London Heathrow)
    - vars_to_fetch: List of variables to download (e.g., ['drct', 'sknt', 'tmpf', 'relh', 'mslp']).
                     If None, fetches wind direction and speed by default.
    - start_year, end_year: Year range for historical data
    - resample_hourly: If True, aggregates data to 1-hour intervals shifted to the half-hour.
    """
    if vars_to_fetch is None:
        vars_to_fetch = ["drct", "sknt"]

    # Map requested variables to IEM URL query parameter
    # Ensure 'valid' is always fetched for timestamping
    data_params = "".join([f"&data={v}" for v in vars_to_fetch])

    url = (
        f"https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?"
        f"network=ES__ASOS&station={station}{data_params}"
        f"&year1={start_year}&month1=1&day1=1"
        f"&year2={end_year}&month2=7&day2=30&tz=Etc%2FUTC&format=onlycomma"
        f"&latlon=no&elev=no&missing=null&trace=null&direct=yes&report_type=3&report_type=4"
    )

    print(f"Fetching {station} weather data from IEM...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urllib.request.urlopen(req) as response:
        csv_text = response.read().decode("utf-8")

    # Read CSV, skipping IEM header comments starting with '#'
    df_met = pd.read_csv(io.StringIO(csv_text), comment="#", low_memory=False)

    if df_met.empty or "valid" not in df_met.columns:
        print(f"No data returned for station '{station}'.")
        return pd.DataFrame()

    # Convert numeric columns
    numeric_cols = [c for c in vars_to_fetch if c in df_met.columns]
    for col in numeric_cols:
        df_met[col] = pd.to_numeric(df_met[col], errors="coerce")

    # Standardize TIMESTAMP as Index (UTC, tz-naive)
    df_met["TIMESTAMP"] = pd.to_datetime(df_met["valid"])
    df_met = df_met.set_index("TIMESTAMP").sort_index()

    if df_met.index.tz is not None:
        df_met.index = df_met.index.tz_localize(None)

    # Unit Conversions (if present)
    if "tmpf" in df_met.columns:
        df_met["temp_c"] = (df_met["tmpf"] - 32) * 5 / 9
    if "sknt" in df_met.columns:
        df_met["wind_speed_ms"] = df_met["sknt"] * 0.514444

    # --- Hourly Resampling Strategy ---
    if resample_hourly:
        print("Resampling to regular 1-hour intervals and shifting to half-hour...")

        # 1. Identify scalar columns to take simple hourly mean
        scalar_cols = [
            c
            for c in df_met.columns
            if c not in ["valid", "drct"] and pd.api.types.is_numeric_dtype(df_met[c])
        ]
        df_hourly = df_met[scalar_cols].resample("1h").mean()

        # 2. Wind Direction: Pick the observation closest to the top of the hour (:00)
        if "drct" in df_met.columns:
            # Distance in minutes from exact top of the hour
            df_met["min_from_hour"] = np.abs(df_met.index.minute)

            # Filter for records within 20 mins of the full hour, then pick the minimum distance
            top_of_hour_obs = (
                df_met[df_met["min_from_hour"] <= 20]
                .sort_values("min_from_hour")
                .groupby(pd.Grouper(freq="1h"))["drct"]
                .first()
            )

            df_hourly["drct"] = top_of_hour_obs

        # 3. Shift timestamps by 30 minutes (e.g., 14:00 becomes 14:30)
        df_hourly.index = df_hourly.index + pd.Timedelta(minutes=30)

        df_met = df_hourly

    print(
        f"Loaded {len(df_met)} hourly records for {station} "
        f"({df_met.index.min().strftime('%Y-%m-%d')} to {df_met.index.max().strftime('%Y-%m-%d')})"
    )

    return df_met

########################################################################################################
########################################################################################################

# Function to plot windrose from the data retrieved

def plot_windrose_plotly(
    df, station_name="LEBL", hours=None, months=None, time_col="TIMESTAMP"
):
    """Generates an interactive Plotly wind rose with optional time filtering."""
    # 1. Clean missing values
    data = df.dropna(subset=["drct", "wind_speed_ms"]).copy()

    # 2. Extract DateTime for filtering
    if hours is not None or months is not None:
        if time_col in data.columns:
            data[time_col] = pd.to_datetime(data[time_col])
            hour_series = data[time_col].dt.hour
            month_series = data[time_col].dt.month
        elif isinstance(data.index, pd.DatetimeIndex):
            # DatetimeIndex properties are accessed directly without .dt
            hour_series = data.index.hour
            month_series = data.index.month
        else:
            print(
                f"⚠️ Timestamp column '{time_col}' or DatetimeIndex not found."
                " Plotting full dataset."
            )
            hour_series, month_series = None, None

        # Apply filters if we have datetime info
        if hour_series is not None:
            if hours is not None:
                data = data[hour_series.isin(hours)]
                # Re-evaluate month_series after filtering index
                if time_col in data.columns:
                    month_series = data[time_col].dt.month
                elif isinstance(data.index, pd.DatetimeIndex):
                    month_series = data.index.month

            if months is not None:
                data = data[month_series.isin(months)]

    total_observations = len(data)

    if total_observations == 0:
        print("No valid wind data remaining after applying filters.")
        return

    # 3. Map Wind Directions (16 Sectors using centered bins)
    dir_labels = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]

    dir_bins = np.arange(11.25, 360, 22.5)
    drct_clean = data["drct"] % 360

    sector_indices = np.digitize(drct_clean, dir_bins)
    sector_map = {0: "N", 16: "N"}
    sector_map.update({i: label for i, label in enumerate(dir_labels[1:], 1)})

    data["dir_sector"] = pd.Categorical(
        [sector_map[i] for i in sector_indices],
        categories=dir_labels,
        ordered=True,
    )

    # 4. Bin Wind Speeds (m/s)
    speed_bins = [-0.1, 2, 4, 6, 8, 10, np.inf]
    speed_labels = [
        "0-2 m/s",
        "2-4 m/s",
        "4-6 m/s",
        "6-8 m/s",
        "8-10 m/s",
        ">10 m/s",
    ]

    data["speed_range"] = pd.cut(
        data["wind_speed_ms"],
        bins=speed_bins,
        labels=speed_labels,
        ordered=True,
    )

    # 5. Calculate Frequencies
    freq_df = (
        data.groupby(["dir_sector", "speed_range"], observed=False)
        .size()
        .reset_index(name="count")
    )

    freq_df["frequency_pct"] = (freq_df["count"] / total_observations) * 100
    freq_df["total_sector_pct"] = freq_df.groupby(
        "dir_sector", observed=False
    )["frequency_pct"].transform("sum")

    freq_df = freq_df.sort_values(by=["dir_sector", "speed_range"])

    # 6. Build Title Sub-text
    filter_desc = []
    if hours is not None:
        filter_desc.append(f"Hours: {min(hours):02d}:00–{max(hours):02d}:00")
    if months is not None:
        filter_desc.append(f"Months: {months}")
    subtitle = f" ({', '.join(filter_desc)})" if filter_desc else ""

    # 7. Build Plotly Chart
    fig = px.bar_polar(
        freq_df,
        r="frequency_pct",
        theta="dir_sector",
        color="speed_range",
        custom_data=["total_sector_pct"],
        template="plotly_white",
        color_discrete_sequence=px.colors.sequential.Viridis,
        title=f"Wind Rose - {station_name}{subtitle}",
        category_orders={
            "speed_range": speed_labels,
            "dir_sector": dir_labels,
        },
    )

    fig.update_traces(
        hovertemplate=(
            "<b>Direction:</b> %{theta}<br>"
            + "<b>Speed Bin:</b> %{fullData.name}<br>"
            + "<b>This Bin:</b> %{r:.2f}%<br>"
            + "<b>Total Sector Frequency:</b> %{customdata[0]:.2f}%"
            + "<extra></extra>"
        )
    )

    fig.update_layout(
        polar=dict(angularaxis=dict(direction="clockwise", rotation=90))
    )

    fig.show()


#########################################################################################################
#########################################################################################################

#Function to merge weather data (and here is specifically to merge with wind speed and direction) and the stations data

def add_wind_to_station_data(
    station_data,
    df_weather,
    tolerance_minutes=30,
    flag_col="Flag",
    valid_flag_value=0,
):
    """Creates a copy of station_data with wind parameters merged.

    Filters each site to keep only valid quality flag observations (e.g. Flag
    == 0) and drops null timestamps to ensure error-free merge_asof.
    """
    # 1. Clean and prepare weather dataframe
    weather_cols = ["drct", "wind_speed_ms"]
    avail_cols = [c for c in weather_cols if c in df_weather.columns]

    df_met_clean = df_weather[avail_cols].dropna(how="all").copy()

    # Ensure tz-naive DatetimeIndex cast to standard nanoseconds [ns]
    if not isinstance(df_met_clean.index, pd.DatetimeIndex):
        df_met_clean.index = pd.to_datetime(df_met_clean.index)
    if df_met_clean.index.tz is not None:
        df_met_clean.index = df_met_clean.index.tz_localize(None)

    # Drop null timestamps & sort
    df_met_clean = df_met_clean[df_met_clean.index.notna()].sort_index()
    df_met_clean.index = df_met_clean.index.astype("datetime64[ns]")

    df_met_sorted = df_met_clean.reset_index()
    if "index" in df_met_sorted.columns:
        df_met_sorted = df_met_sorted.rename(columns={"index": "TIMESTAMP"})

    # 2. Loop through site DataFrames
    merged_station_data = {}

    for site_name, df_site in station_data.items():
        if df_site is None or df_site.empty:
            print(f"Station '{site_name}' is empty. Skipping...")
            continue

        site_df = df_site.copy()

        # --- Flag Filter Step ---
        # Find flag column (case-insensitive check)
        target_flag = None
        for col in site_df.columns:
            if col.lower() == flag_col.lower():
                target_flag = col
                break

        if target_flag is not None:
            initial_count = len(site_df)
            site_df = site_df[site_df[target_flag] == valid_flag_value]
            filtered_count = len(site_df)
            print(
                f" '{site_name}': Kept {filtered_count}/{initial_count} rows with {target_flag} == {valid_flag_value}"
            )
        else:
            print(
                f" '{site_name}': No flag column matching '{flag_col}' found, keeping all rows."
            )

        if site_df.empty:
            print(f"Station '{site_name}' has 0 rows after flag filtering.")
            continue

        # --- Timestamp Formatting & Cleaning ---
        if "TIMESTAMP" in site_df.columns:
            site_df["TIMESTAMP"] = pd.to_datetime(
                site_df["TIMESTAMP"], errors="coerce"
            )
            site_df = site_df.set_index("TIMESTAMP")
        elif not isinstance(site_df.index, pd.DatetimeIndex):
            site_df.index = pd.to_datetime(site_df.index, errors="coerce")

        if site_df.index.tz is not None:
            site_df.index = site_df.index.tz_localize(None)

        # Drop any null timestamps (NaT) to prevent merge_asof ValueError
        site_df = site_df[site_df.index.notna()].sort_index()
        site_df.index = site_df.index.astype("datetime64[ns]")

        site_sorted = site_df.reset_index()

        # Enforce exact matching timestamp dtypes
        site_sorted["TIMESTAMP"] = site_sorted["TIMESTAMP"].astype(
            "datetime64[ns]"
        )
        df_met_sorted["TIMESTAMP"] = df_met_sorted["TIMESTAMP"].astype(
            "datetime64[ns]"
        )

        # --- Nearest-Neighbor Merge ---
        merged = pd.merge_asof(
            site_sorted,
            df_met_sorted,
            on="TIMESTAMP",
            direction="nearest",
            tolerance=pd.Timedelta(minutes=tolerance_minutes),
        ).set_index("TIMESTAMP")

        merged_station_data[site_name] = merged
        print(f"Station '{site_name}': Successfully merged with wind data.")

    return merged_station_data