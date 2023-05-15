import glob, os
import subprocess
import copy
import pandas as pd
import numpy as np

measurementsdir = '/home/wouter/summerschool/2023/MEASUREMENTS/'

sitedict = {'Alert': 'alt',
            'Mauna_Loa': 'mlo',
            'Ny_Alesund': 'zep',
            'Hyytiala': 'pal',
            'Mace_Head': 'mhd',
            'Trinidad_Head':'thd',
            'Barbados': 'rpb',
            'Samoa': 'smo',
            'Tasmania': 'cgo',
            'Cape_Grim': 'cgo',
            'Crozet_Island': 'czr',
            'South_Pole': 'spo',
            'Oregon': 'thd'}

def get_concentrations(runname, obsset):
    """ Get concentrations and observations for a MOGUNTIA run"""
    from collections import OrderedDict

    simulation_df = pd.DataFrame()
    outfile = f'OUTPUT/{runname:s}.stations'
    if not os.path.exists(outfile):
        print('File not found  %s'%outfile)
        return None, None
    
    with open(outfile, 'r') as fromfile:
        lines=fromfile.readlines()
        stations = [l.split('  ')[0] for l in lines if not l.startswith('  ')]
        nstations = len(stations)
        data=[]
        for line in lines[nstations+1:]:
            data.append(np.array([float(x) for x in line.split()]))
    data=np.array(data)
    nyears = data.shape[0]/12
    simulations = pd.DataFrame(data)
    simulations.columns = stations
    simulations = simulations.melt()
    simulations['time'] = np.tile(pd.date_range(pd.to_datetime('2000-01-01'), 
                                                    pd.to_datetime('%04d-01-01'%(2000+nyears)), 
    #                                                 pd.to_datetime('2007-12-01'),
                                                  freq='M'),
                                      len(stations))
    
    simulation_df['moguntia'] = simulations.value
    simulation_df['site'] = simulations.variable
    simulation_df['time'] = simulations.time.dt.to_period('M')
    
    #simulation_df['site'] = simulation_df['site'].replace('_', ' ')
    
    #print(simulation_df.head())
    #print(simulation_df.tail())
    
    for site in simulation_df.site.unique():
        if '(' in site:
            siteshort = site[0:site.find('(')]
        else:
            siteshort = site
    
        #print(site,siteshort)
        simulation_df.loc[simulation_df.site==site, 'site'] = sitedict[siteshort]
        
        
    dfs = []
    for ss in obsset:
        obsfile = glob.glob(measurementsdir + f'CO2_{ss}*.data')[0]
        df = pd.read_csv(obsfile, sep='  ', header=None)
        df.columns=['year', 'month', 'mole_fraction', 'scaling', 'unit', 'site']
        df.month = df.month.astype(int)
        df.month[df.month ==13] = 1
        df = df.groupby([df.year, df.month, df.site]).mean()

        dfs.append(df.reset_index())
    df = pd.concat(dfs)

    df['time'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    df = df.drop(['year', 'month'], axis=1)
    df['time'] = df.time.dt.to_period('M')
   
    #print(simulation_df.head())
    all_concs = pd.merge(df,simulation_df,on=['time', 'site'])
    
    Hx_p = all_concs.moguntia.values * 1e6
    y = all_concs.mole_fraction.values 
    
    info=OrderedDict()
    for ss in obsset:
        info[ss] = all_concs['site'].value_counts()[ss]

    return y, Hx_p, info

def get_H(obsset, glob=False):
    """ return the H-matrix, either for a run with 3 parameters, or 1 """
   
    
    y, Hx_b, info = get_concentrations('basefunc_base',obsset)
    y, Hx_gl, info = get_concentrations('basefunc_gl',obsset)
    y, Hx_nh, info = get_concentrations('basefunc_nh',obsset)
    y, Hx_tr, info = get_concentrations('basefunc_tr',obsset)
    y, Hx_sh, info = get_concentrations('basefunc_sh',obsset)
                                  
    if glob:
        H = Hx_gl-Hx_b
        return H
    else:
        H=[] 
        H.append(Hx_nh-Hx_b)
        H.append(Hx_tr-Hx_b)
        H.append(Hx_sh-Hx_b)
        return np.array(H).transpose()
    
def draw_members(P,N=10):
    """ draw N ensemble members with structure P """
    

    I = np.identity(len(P))
    C = np.linalg.cholesky(P)

    X_prime = np.zeros((len(P), N))
    X = np.empty_like(X_prime)

    for n in np.arange(N): # Loop over all ensemble members
        xp = np.dot(C.T, np.random.randn(len(P)))
        X_prime[:, n] = xp

    return X_prime

def cov2corr(P):
    """ make a correlation matrix for the covariance P"""
    
    varsq = np.sqrt(P.diagonal())
    corr = np.empty_like(P)
    for i in range(len(varsq)):
        for j in range(len(varsq)):
            corr[i,j] = P[i,j]/(varsq[i]*varsq[j])
    return corr   

def propagate_ensemble(x_mean,X_prime):
    """ propagate ensemble through MOGUNTIA """
    
    # Open the template file and read template
    templatefile = './inputtemplate.in'
    with open(templatefile, 'r') as fromfile:
        template = fromfile.read()

    # Write mean value

    nh, tropics, sh = x_mean
    formatdict = {'TITLE': 'MEMBER_000',
                      'NH': round(nh, 3),
                      'TROPICS': round(tropics, 3),
                      'SH': round(sh, 3)}

    newinput = template.format(**formatdict)
    newfile = f'./input_000'
    print(f'propagating member_000 (mean)')

    with open(newfile, 'w') as tofile:
        tofile.write(newinput)

    run_moguntia(newfile)
    
    # Write ensemble values
    for n in range(X_prime.shape[1]):
        nh, tropics, sh = x_mean+X_prime[:, n]
        formatdict = {'TITLE': f'MEMBER_{n+1:03}',
                      'NH': round(nh, 3),
                      'TROPICS': round(tropics, 3),
                      'SH': round(sh, 3)}

        newinput = template.format(**formatdict)
        newfile = f'./input_{n+1:03}'

        with open(newfile, 'w') as tofile:
            tofile.write(newinput)        
            
    # For all members: create mole fractions
    
        print(f'propagating member_{n+1:03}')
        run_moguntia(newfile)
    
    return True

moguntiapathe = '/home/wouter/summerschool/2023/'

def run_moguntia(infile):
    
    """Call the executable with a given inputfile"""
    with open(os.path.join(os.getcwd(), infile), 'r') as xfile:
        outp = subprocess.check_output([moguntiapathe + '/MODEL_ext/MOGUNTIA'], stdin=xfile)
        #print(outp.decode("utf-8")) 
        
def enkf(x_p, P, obsset, mdm, NMEMBERS,dtf=1):
    """ Make enkf estimate """

    X_prime = draw_members(P, N = NMEMBERS)
    result = propagate_ensemble(x_p,X_prime)
    
    y0, Hx_p, info = get_concentrations(f'MEMBER_000', obsset)

    R = make_R(info,mdm) # 0.5 ppm^2 measurement uncertainty for all observations 
        
    HX_prime = []

    for n in range(1,NMEMBERS+1): 
    
        y, Hx, info = get_concentrations(f'MEMBER_{n:03}', obsset)
        HX_prime.append(Hx-Hx_p)

    HX_prime=np.array(HX_prime).transpose()


    xa, Pa, J = serialensemblekalmanfilterestimate(R, y, x_p, X_prime, Hx_p, HX_prime,dtf=dtf)

    return xa,Pa, J
   
        
def serialensemblekalmanfilterestimate(R, y, x_p, X_prime, Hx, HX_prime,dtf=1):
    """ ensemble Kalman Filter solution for a system with more obs than parameters, serial algorithm
    R: Uncertainty on observations
    y: observations
    wb: prior scaling factor estimate
    Hx: Simulated mole fractions
    Pb: prior uncertainty estimate on scaling factors
    X_prime: Deviations from mean"""
    

    okdebug = False
    
    wzero = copy.deepcopy(x_p)
    Hx_mean = copy.deepcopy(Hx)
    
    NMEMBERS = X_prime.shape[1]
 
    for n in range(0,len(y),dtf): # Loop over all the observations  # DTF is the sub-selection of observations, data thinning factor


        PHt   = 1. / (NMEMBERS - 1) * np.dot(X_prime , HX_prime[n, :])# eq 9
        HPHR  = 1. / (NMEMBERS - 1) * (HX_prime[n, :] * HX_prime[n, :]).sum() + R[n, n]

        KG    = PHt / HPHR # eq 4; '/' omdat ^(-1)

        alpha = 1.0 / (1.0 + np.sqrt((R[n, n]) / HPHR)) # Eq 11.

        res   = y[n] - Hx_mean[n] # difference between observations and prior
        
        if okdebug: print(n,res,KG,wzero,KG*res)
        
        wzero = wzero + KG * res # Eq 2

        for r in range(0,NMEMBERS): 
            
            X_prime[:,r] = X_prime[:, r] - alpha * KG * (HX_prime[n, r]) # eq 10. Update deviations from the mean state vector

            #WP !!!! Very important to first do all obervations from n=1 
            #WP through the end, and only then update 1,...,n. The current observation
            #WP should always be updated last because it features in the loop !!!!

        for m in range(n+1,len(y)):
            fac           = 1.0 / (NMEMBERS-1) * (HX_prime[n, :] * HX_prime[m, :]).sum() / HPHR
            Hx_mean[m]         = Hx_mean[m] + fac * res # Equation 12 and 13 Peters 2005
            #if okdebug and m==92: print(n,m,wzero,fac,res,Hx_mean[n],Hx_mean[92] )  

            HX_prime[m,:] = HX_prime[m, :] - alpha * fac * HX_prime[n, :] # Equation 12 and 13 Peters 2005
        for m in range(n+1):
            fac           = 1.0 / (NMEMBERS-1) * (HX_prime[n, :] * HX_prime[m, :]).sum() / HPHR
            Hx_mean[m]         = Hx_mean[m] + fac * res # Equation 12 and 13 Peters 2005
            HX_prime[m,:] = HX_prime[m, :] - alpha * fac * HX_prime[n, :] # Equation 12 and 13 Peters 2005
            #if okdebug and m==92: print(n,m,wzero,fac,res,Hx_mean[n],Hx_mean[92] )  


    P_opt = np.dot(X_prime, X_prime.T) / (NMEMBERS-1) # Eq 7
    w_opt = wzero
    
    J1 =  np.dot(np.transpose(y-Hx_mean),np.linalg.inv(R)).dot(y-Hx_mean)   # make J for this run
    J2 = np.dot(np.transpose(w_opt-x_p),np.linalg.inv(P_opt)).dot(w_opt-x_p)
    J = J1 + J2

    return w_opt, P_opt, J        

def write_member(x_a, name):
    
    # Open the template file and read template
    templatefile = './inputtemplate.in'
    with open(templatefile, 'r') as fromfile:
        template = fromfile.read()
    
    nh=x_a[0]
    tr=x_a[1]
    sh=x_a[2]

    # Write ensemble values
    for n in range(1):
        formatdict = {'TITLE': name,
                      'NH': round(nh, 6),
                      'TROPICS': round(tr, 6),
                      'SH': round(sh, 6)}

        newinput = template.format(**formatdict)
        newfile = f'./{name:s}.in'

        with open(newfile, 'w') as tofile:
            tofile.write(newinput)

def make_R(info, mdm):
    
    assert len(info) == len(mdm)
    nobs=np.array([v for v in info.values()]).sum()
    R=np.eye(nobs)
    
    diag = []
    for i,nobs in enumerate(info.values()):
        R[i,i] = mdm[i]**2
    return R
