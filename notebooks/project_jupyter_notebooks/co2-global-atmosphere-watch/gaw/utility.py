"""
Functions for data processing and analysis used by Wu et al 2023.

"""
import numpy as np
import scipy as sp
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from os import listdir, makedirs, remove
from os.path import isfile, join, exists
import ccg_filter
from sklearn.utils import resample

def decimalDate_ymd (year, month, day=15):
    """ Convert a date to a fractional year. """
    pd_date = pd.to_datetime(year*10000 + month*100 + day, format='%Y%m%d')
    
    return pd_date.dt.year + pd_date.dt.dayofyear / [366 if x else 365 for x in pd_date.dt.is_leap_year]

def decimalDate_ym (year, month):
    """ Convert a date to a fractional year. 1 months = 0.08333 years"""
    
    return year + month*0.08333 - 0.08333/2

def decimalDate_datetime (datetime):
    """ Convert a date to a fractional year. """
    
    return datetime.dt.year + datetime.dt.dayofyear / [366 if x else 365 for x in datetime.dt.is_leap_year]

# We find the z score for each of the data point in the dataset and if the z score is greater than 3 
# than we can classify that point as an outlier. Any point outside of 3 standard deviations would be an outlier.

def detect_outlier(data_1):
    outliers=[]
    threshold=3
    mean_1 = np.mean(data_1)
    std_1 =np.std(data_1)
    for y in data_1:
        z_score= (y - mean_1)/std_1 
        if np.abs(z_score) > threshold:
            outliers.append(y)
    return outliers

def apply_fit_filter(IN_PATH, file, OUT_PATH, ifplot=1, ifsaveplot=0, station_patten = "_brw_", station = "BRW", source = "CT", co2obs = 1,
                     from2000 = True, xmin=0, xmax=0):
    """ 
    apply fit fuction and filter, and save the output as csv format 
    source: "wdcgg" or "CT"
    co2obs: 1: observation, 0: model output
    
    """
    ################################################################################################ 
    # mark if it is measured in shipboard
    ################################################################################################ 
    pre_filename = file.split(".")[0]
    shipboard = 0
    if any(item in pre_filename for item in ['shipboard', 'poc8', 'scs8']):
        shipboard = 1
    
    ################################################################################################ 
    # read data and primary data clean
    ################################################################################################ 
    PLOT_PATH_PREFIX = OUT_PATH
    if source == "wdcgg":
        dat = pd.read_table(IN_PATH+file, delimiter="\s+", skiprows=24)
        dat = dat.reset_index()
        dat = dat.iloc[:,0:3]
        dat.columns = ['yy','mm','co2']
        OUT_PATH = OUT_PATH + "co2obs/"
        PLOT_PATH_PREFIX = PLOT_PATH_PREFIX + "co2obs_"
        if not exists(OUT_PATH):
            makedirs(OUT_PATH)
    else:
        dat = pd.read_table(IN_PATH+file, delimiter="\s+")
        if co2obs ==1:
            dat = dat.rename(columns={"co2obs":"co2"})
            OUT_PATH = OUT_PATH + "co2obs/"
            PLOT_PATH_PREFIX = PLOT_PATH_PREFIX + "co2obs_"
        else:
            dat = dat.rename(columns={"co2model":"co2"})
            OUT_PATH = OUT_PATH + "co2model/"
            PLOT_PATH_PREFIX = PLOT_PATH_PREFIX + "co2model_"
        # get daily mean, the CTE data is in hourly
        dat.loc[(dat["co2"]>600) | (dat["co2"]<=100),"co2"] = np.nan
        dat = pd.DataFrame(dat.groupby(["yy","mm","dd"])["co2"].mean().sort_index(ascending=True))
        dat = dat.reset_index()
        if not exists(OUT_PATH):
            makedirs(OUT_PATH)

    # set outlier to NaN
    dat.loc[(dat["co2"]>600) | (dat["co2"]<=100),"co2"] = np.nan
    outlier_datapoints = detect_outlier(dat.co2)
    N=np.where(np.isin(dat.co2,outlier_datapoints))
    dat.loc[N[0].tolist(),"co2"] = np.nan
    dat = dat.loc[~np.isnan(dat.co2)]
    
    # get monthly mean
    df_monthly = dat.groupby(["yy","mm"])["co2"].mean().sort_index(ascending=True)

    # trim leading and trailing NAs 
    first_valid = df_monthly[df_monthly.notnull()].index[0]
    last_valid = df_monthly[df_monthly.notnull()].index[-1]
    df_monthly = df_monthly.loc[first_valid:last_valid]

    # set date and decimal date
    df_monthly = df_monthly.reset_index()
    df_monthly["date"] = pd.to_datetime(df_monthly.yy*10000+df_monthly.mm*100+15,format='%Y%m%d')
    df_monthly["decimalyear"] = decimalDate_ym(df_monthly.yy, df_monthly.mm)
    if from2000 == True:
        df_monthly = df_monthly[df_monthly.date > "2000-1-1"]
    df_monthly = df_monthly.set_index("date")
    ################################################################################################ 
    # apply fit fuction and filter 
    ################################################################################################ 
    xp = df_monthly["decimalyear"]
    yp = df_monthly["co2"]

    # skip the station which has less than 12 monthes data
    if len(xp) < 15:
        print(f"There is only {len(xp)} monthes data at this station ({pre_filename}), ...... skip")
        return 0

    # set shortterm cutoff as 200 for the measurement on shipboard
    if shipboard == 0:
        try:
            filt = ccg_filter.ccgFilter(xp, yp, shortterm=80, longterm=667, sampleinterval=0,
                                numpolyterms=3, numharmonics=4, timezero=-1, gap=0, use_gain_factor=False, debug=False,)
        except:
            print(f"error at this station ({pre_filename})")
    else:
        #https://www.esrl.noaa.gov/gmd/webdata/ccgg/trends/co2_DEconfig.txt
        try:
            filt = ccg_filter.ccgFilter(xp, yp, shortterm=200, longterm=667, sampleinterval=0,
                                numpolyterms=3, numharmonics=4, timezero=-1, gap=0, use_gain_factor=False, debug=False,)
        except:
            print(f"error at this station ({pre_filename})")
    
    # check if the numharmonics is appropriate
    # e.g. station FPK, no 62, gives extreme harmonic/seasonality, the numharmonics needs to reduce
    x0 = filt.xinterp
    harmonics = filt.getHarmonicValue(x0)
    if abs(sum(harmonics)) > 500 or all(v == 0 for v in harmonics):
        print(f"The numharmonics setting causes extreme output at this station ({pre_filename}), ...... skip")
        print(f"The harmonics are: {harmonics}")
        print(f"The solution is to reduce numharmonics, e.g. 3 or 2, here we just exclude this station data")
        return 0
    ################################################################################################ 
    # estimate co2 during full period 
    ################################################################################################ 
    df_fullmonthly = df_monthly.resample('M').mean().reset_index()
    df_fullmonthly.date = df_fullmonthly.date.apply(lambda dt: dt.replace(day=15))
    df_fullmonthly.decimalyear = decimalDate_ym(df_fullmonthly.date.dt.year, df_fullmonthly.date.dt.month)

    # for fit plot
    x0 = df_fullmonthly.decimalyear
    y1 = filt.getFunctionValue(x0)
    y2 = filt.getPolyValue(x0)
    y3 = filt.getSmoothValue(x0)
    y4 = filt.getTrendValue(x0)
    harmonics = filt.getHarmonicValue(x0)
    resid_from_func = df_fullmonthly.co2 - y1
    resid_smooth = y3 - y1
    resid_trend = y4 -y2
    if ifplot and station_patten in pre_filename:
        plot_fit(PLOT_PATH_PREFIX, xp, yp, x0, y1, y2, harmonics, resid_from_func, resid_smooth, resid_trend, station, xmin, xmax, ifsaveplot)

    # for growth rate plot
    trendp = filt.getTrendValue(xp)
    tck = sp.interpolate.splrep(x0, y4)
    trend_spl = sp.interpolate.splev(x0, tck)
    trend_der1 = sp.interpolate.splev(x0, tck, der=1)
    if ifplot and station_patten in pre_filename:
        plot_growthrate(PLOT_PATH_PREFIX, xp, trendp, x0, trend_spl, trend_der1, station, xmin, xmax, ifsaveplot)
    ################################################################################################    
    # save the file
    ################################################################################################ 
    df_fullmonthly["polypart"] = y2
    df_fullmonthly["harmpart"] = harmonics
    df_fullmonthly["resid"] = resid_from_func
    df_fullmonthly["resid_smooth"] = resid_smooth
    df_fullmonthly["resid_trend"] = resid_trend
    df_fullmonthly["growth_rate"] = trend_der1

    # df_fullmonthly.to_csv(OUT_PATH + pre_filename + "_fit_filter.csv", header=True,index=False, na_rep= "NaN")
    return 1

def plot_fit (OUT_PATH, xp, yp, x0, y1, y2, harmonics, resid_from_func, resid_smooth, resid_trend, station, xmin=0, xmax=0, ifsaveplot=0):
    """ Print fit curve and filter curve. """
    fig, axes = plt.subplots(4, 1, sharex=True, sharey=False, figsize=(15,14))
    (ax1, ax2, ax3, ax4) = axes

    ax1.plot(xp, yp,'ko', ms=6, label = 'raw data')
    ax1.plot(x0, y1,'r', label = 'fitted curve (2 deg + 4 harmonic)')
    ax1.plot(x0, y2,'b', label = 'polynomial part')
    ax1.set_ylim(min(yp)-4,max(yp)+4)
    ax1.set_ylabel('$\mathregular{CO_2}$, ppm')
    ax1.set_xticks(np.arange(np.floor(xp.min()),np.ceil(xp.max())+1))
    ax1.legend(loc='upper left', fontsize='small')
    ax1.set_title("a. Fitted curve", loc = "left")
    if xmax>0:
        ax1.set_xlim(xmin,xmax)

    ax2.plot(x0, harmonics,'g', label = 'harmonic part')
    ax2.set_ylim(min(harmonics)-2,max(harmonics)+4.5)
    ax2.set_ylabel('$\mathregular{CO_2}$, ppm')
    ax2.legend(loc='upper left', fontsize='small')
    ax2.set_title("b. Harmonic part", loc = "left")

    ax3.plot(x0, resid_from_func,'ko', label = 'raw - fitted curve')
    ax3.plot(x0, resid_smooth,'r', label = 'short term filter')
    ax3.plot(x0, resid_trend,'b', label = 'long term filter')
    ax3.plot(x0, resid_from_func- resid_smooth,"co", label = 'raw - (fitted curve + short term filter)')
    ax3.axhline(y=0, linestyle='--', color='k')
    ax3.set_ylim(min(resid_from_func)-1,max(resid_from_func)+3)
    ax3.set_ylabel('$\mathregular{CO_2}$, ppm')
    ax3.legend(fontsize='small',ncol=4)
    ax3.set_title("c. Residuals", loc = "left")

    ax4.plot(xp, yp,'ko', ms=6, label = 'raw data')
    ax4.plot(x0, y1 + resid_smooth,'r', label = 'fitted curve + short term filter')
    ax4.plot(x0, y2 + resid_trend,'b', label = 'polynomial part + long term filter')
    ax4.set_ylim(min(yp)-4,max(yp)+4)
    ax4.set_ylabel('$\mathregular{CO_2}$, ppm')
    ax4.set_xlabel('year')
    ax4.legend(loc='upper left', fontsize='small')
    ax4.set_title("d. Combine fit fuction with filtered residucals", loc = "left")
    plt.setp(ax4.get_xticklabels(), rotation=30)
    
#     if ifsaveplot==1:
#         if isfile("../image/" + "publish_method_figure1.png"):
#             remove("../image/" + "publish_method_figure1.png")
#         plt.savefig("../image/" + "publish_method_figure1.png",bbox_inches='tight')
    
    fig.suptitle("$\mathregular{CO_2}$ fit curve and filter curve at " + station + " station", fontsize=20)

def plot_growthrate(OUT_PATH, xp, trendp, x0, trend_spl, trend_der1, station, xmin=0, xmax=0, ifsaveplot=0):
    """ Print growth rate curve. """
    fig,axes = plt.subplots(2,1, sharex=True, figsize = (15,10))
#     print(axes.shape)
    
    (ax1, ax2) = axes
    
    ax1.plot(xp, trendp, 'ko', label = "trend points")
    ax1.plot(x0, trend_spl, 'b',label = "interpolated cubic spline curve")
    ax1.set_ylabel("$\mathregular{CO_2}$, ppm")
    if xmax>0:
        ax1.set_xlim(xmin,xmax)
    ax1.legend()
    ax1.set_xticks(np.arange(np.floor(xp.min()),np.ceil(xp.max())+1))
    ax1.set_title("a. Trend", loc = "left")

    ax2.plot(x0, trend_der1,'mo', label="derivative of the spline curve" )
    ax2.set_xlabel("year")
    ax2.set_ylabel("$\mathregular{CO_2}$ ppm/year")
    ax2.legend()
    ax2.set_title("b. Growth rate", loc = "left")
    plt.setp(ax2.get_xticklabels(), rotation=30)
    
#     if ifsaveplot==1:
#         if isfile("../image/" + "publish_method_figure2.png"):
#             remove("../image/" + "publish_method_figure2.png")
#         plt.savefig("../image/" + "publish_method_figure2.png",bbox_inches='tight')
    
    fig.suptitle("$\mathregular{CO_2}$ growth rate at " + station + " station", fontsize=20)

def grid_area (resolution=0.5):
    """Calculate the area of each grid cell for a user-provided
    grid cell resolution. Area is in square meters, but resolution
    is given in decimal degrees."""
    # Calculations needs to be in radians
    lats = np.deg2rad(np.arange(-90,90+resolution, resolution))
    r_sq = 6371000**2
    n_lats = int(360./resolution) 
    area = r_sq*np.ones(n_lats)[:, None]*np.deg2rad(resolution)*(
                np.sin(lats[1:]) - np.sin(lats[:-1]))
    return area.T

def weighted_zonal_mean(df_co2_raw,zonal_deg):
    """ weighted zonal average """
    # 90 divided zonal_deg with no remainder
    if 90 % zonal_deg !=0:
        sys.exit("Reset zonal_deg, making 90 divided by zonal_deg with no remainder")

    df_zonal_raw = zonal_mean(df_co2_raw, zonal_deg, df_co2_raw.columns[4:], "lat")

    nanindex_raw  = df_zonal_raw.apply(np.isnan)

    # area weight
    df_area = pd.DataFrame(grid_area(0.5))
    area_lat = df_area.iloc[:,0]
    area_zonal = area_lat.groupby(np.arange(len(area_lat))//(zonal_deg/0.5)).sum()

    NH_index = [i for i in range(int(len(area_zonal)/2))]
    SH_index = [i for i in range(int(len(area_zonal)/2),len(area_zonal))]

    global_weight = area_zonal/area_zonal.sum()
    NH_weight = area_zonal[NH_index] /(area_zonal.sum()/2)
    SH_weight = area_zonal[SH_index] /(area_zonal.sum()/2)

    global_weight = global_weight.set_axis(df_zonal_raw.index)
    NH_weight = NH_weight.set_axis(df_zonal_raw.index[NH_index])
    SH_weight = SH_weight.set_axis(df_zonal_raw.index[SH_index])

    # replicate weight column wise
    df_global_weight= pd.concat([global_weight]*df_zonal_raw.shape[1], ignore_index=True, axis=1)
    df_NH_weight= pd.concat([NH_weight]*df_zonal_raw.shape[1], ignore_index=True, axis=1)
    df_SH_weight= pd.concat([SH_weight]*df_zonal_raw.shape[1], ignore_index=True, axis=1)
    df_global_weight.columns = df_zonal_raw.columns
    df_NH_weight.columns = df_zonal_raw.columns
    df_SH_weight.columns = df_zonal_raw.columns

    # recalculate weight due to some NAN
    df_global_weight_raw = df_global_weight[~nanindex_raw].div(df_global_weight[~nanindex_raw].sum(), axis = 1) 
    df_NH_weight_raw = df_NH_weight[~nanindex_raw].div(df_NH_weight[~nanindex_raw].sum(), axis = 1) 
    df_SH_weight_raw = df_SH_weight[~nanindex_raw].div(df_SH_weight[~nanindex_raw].sum(), axis = 1)

    # raw global weighted average
    global_co2_raw = df_zonal_raw.mul(df_global_weight_raw, axis = 0).sum(min_count=1)
    NH_co2_raw = df_zonal_raw.iloc[NH_index,:].mul(df_NH_weight_raw, axis = 0).sum(min_count=1)
    SH_co2_raw = df_zonal_raw.iloc[SH_index,:].mul(df_SH_weight_raw, axis = 0).sum(min_count=1)

    # calculate annual co2
    datetime = pd.to_datetime(pd.DataFrame(global_co2_raw.index)[0],format='%Y-%m-%d')
    co2_monthly = pd.concat([global_co2_raw,NH_co2_raw,SH_co2_raw],axis=1)
    co2_monthly.columns = ["global","NH","SH"]
    co2_monthly["year"] = datetime.dt.year.tolist()
    co2_annual = co2_monthly.groupby(["year"]).mean().T

    return co2_monthly[["global","NH","SH"]].T, co2_annual

def zonal_mean(df, zonal_deg, dat_cols, lat_col = "lat"):
    """ Latitude zonal average """
    
    lat_range = range(-90,90,zonal_deg)
    df_zonal_raw = pd.DataFrame()
    
    for i in lat_range:
        lat_id = (i < df[lat_col]) & (df[lat_col] <= i+zonal_deg)
        temp_raw = df.loc[lat_id,:]
        df_zonal_raw = pd.concat([df_zonal_raw,  pd.DataFrame(temp_raw[dat_cols].mean()).T] )

    df_zonal_raw["lat"] = [str(i) + "_" + str(i+zonal_deg)  for i in lat_range]
    cols_new = df_zonal_raw.columns.to_list()
    cols_new = cols_new[-1:] + cols_new[:-1]
    df_zonal_raw = df_zonal_raw.loc[:,cols_new]
    df_zonal_raw = df_zonal_raw.iloc[::-1] 
    df_zonal_raw = df_zonal_raw.set_index(["lat"])
    return df_zonal_raw

def calculate_boot_sample(df,n_bootstraps,zonal_deg,suffix="_raw",samplesize=0):
    ''' calculate result for each sample and put them into list
    df: dataframe, stations/locations as rows, dates as columns   
    n_bootstraps: Number of bootstrapping iterations
    zonal_deg: width of each zone, in degree
    suffix: if applying fit and filter, "_raw" means without applying fit and filter, "_cal" means with applying fit and filter
    samplesize: number of samples, the sample size is the same as the original dataset (default)
    '''
    if samplesize==0:
        samplesize = df.shape[0]
    index = [zone + suffix for zone in ["global","NH","SH"]]
    df_boot = pd.DataFrame()
    lst_boot_monthly = []
    lst_boot_annual = []
    for i in range(n_bootstraps):
        boot = resample(range(df.shape[0]), replace=True, n_samples=samplesize,random_state=i)

        df_monthly, df_annual = weighted_zonal_mean(df.iloc[boot,],zonal_deg)
        df_annual.index = index
        df_monthly.index = index
        
        lst_boot_annual.append(df_annual)
        lst_boot_monthly.append(df_monthly)

        df_boot = pd.concat([df_boot,pd.DataFrame(boot)], axis=1)
    df_boot.columns = range(n_bootstraps)
    return lst_boot_annual, lst_boot_monthly, df_boot

def org_boot(lst_boot,zonal="global_raw"):
    ''' Get bootstrap results base on the zonal'''
    df_boot = pd.DataFrame()
    for i in range(len(lst_boot)):
        boot_sample = pd.DataFrame(lst_boot[i].loc[zonal]).T
        df_boot = pd.concat([df_boot,boot_sample])
    return df_boot

def get_boot_stats(df,confidence):
    '''get statistics from bootstrap method'''
    boot_stats = df.agg(["mean","std"])

    numOfTails = 2
    for i in range(len(confidence)): 
        # significant level alpha
        alpha = (1 - confidence[i])/numOfTails
        # z-critical that corresponds to the confidence level
        z_crit = sp.stats.norm.ppf(1 - alpha)

        strci = "CI_"+str(confidence[i])
        ci = boot_stats.loc["std"] * z_crit
        boot_stats.loc[strci] = ci
    
    return boot_stats