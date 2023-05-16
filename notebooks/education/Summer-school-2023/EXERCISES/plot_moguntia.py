from pylab import *
import glob, os, sys
from datetime import *

try:
    from ipywidgets import *
except:
    from IPython.html.widgets import *
import subprocess
from IPython.display import display, clear_output
# from mpl_toolkits.basemap import Basemap
import cartopy

import functools

matplotlib.rcParams.update({'font.size': 12})


class plot_moguntia:

    def __init__(self):
        # os.chdir('/home/lcur0000/JHL_notebooks/MAQ11306_P01_Moguntia/')
        # teacher_dir  = os.getenv('TEACHER_DIR')
        # self.moguntiapath = os.path.join(teacher_dir,'JHL_notebooks/P01_Moguntia')
        # self.moguntiapath = '//home/wouter/summerschool/2023/'
        # self.moguntiapathe = '/home/wouter/summerschool/2023/'
        # self.moguntiapathe = '/home/lcur0571/JHL_prepare/P06_Moguntia_ENKF/'
        self.moguntiapath = os.path.join(
            '/',
            os.path.expanduser('~'),
            'education',
            'Summer-school-2023'
        )
        # Path to the MOGUNTIA executable.
        self.moguntiapathe = os.path.join(
            os.path.expanduser('~'),
            'education',
            'Summer-school-2023',
            'build',
            'MODEL',
            'MOGUNTIA'
        )

        self.localpath = os.getcwd()
        self.nlev = 10
        self.conv = 1.0
        self.overplot = False
        self.xmax = 1e10
        self.xmin = 0.0
        self.tmin = datetime(1900, 1, 1, 0, 0, 0)
        self.tmax = datetime(2020, 1, 1, 0, 0, 0)
        self.stations = False
        self.infiles = glob.glob('*.in')
        self.infiles.sort()
        self.name = 'DUMMY'
        self.molmass = '28.5'
        self.station_out = False
        self.ll_out = False
        self.za_out = False
        #        interact_manual(self.Moguntia,inputfile = self.infiles)

        # to support python2.7 widgets, set up two types of windows:
        # 1. windows that allow selection of multiple files (SelectMultiple)
        #    select output file, select overplot file, select station
        # 2. widgets that can be passed through the interact call.
        #     grid (T/F), overplot (T/F), coneversion (ToggleButto
        #
        #        if len(self.outputfiles) == 0:
        #            print("==============================================================")
        #            print("No outputfiles generated, bailing out")
        #            print("Please add STATION and/or OUTPUT statements in your input file")
        #            print("==============================================================")
        #            sys.exit(1)
        self.wdoit = ToggleButton(description='Make Plots', value=False)
        options = []
        for ii, filen in enumerate(self.infiles):
            options.append(filen)
        self.Input = Dropdown(description="Inputfile", options=options)
        self.moguntia = Button(description="Run Model")
        self.moguntia.on_click(self.Moguntia)

        self.fetch = Button(description="Fetch Output")
        self.fetch.on_click(self.Fetch)

        # button.on_click(functools.partial(on_button_clicked, 2))

        self.outputfiles = ['xxx']
        options = []
        for ii, filen in enumerate(self.outputfiles):
            filen = filen[:-1]
            options.append(filen)
        self.wof = SelectMultiple(description="Output", options=options)
        self.wof.width = 200
        self.wof.value = (options[0],)

        self.station_names = ['no station']
        self.wstat = SelectMultiple(description='',
                                    options=self.station_names)
        self.wstat.width = 200
        self.wstat.value = (self.station_names[0],)
        oplotfiles = ['no station']
        self.wo = SelectMultiple(description='', options=oplotfiles)
        self.wo.width = 200
        self.woplot = ToggleButton(description='Overplot', value=False)
        self.woplot.on_trait_change(self.set_visibility)
        self.automatic = Checkbox(True, description='automatic')
        self.automatic.on_trait_change(self.set_visibility)

        self.grid = Checkbox(True, description='grid')

        self.wlev = IntSlider(min=5, max=30, value=self.nlev)
        self.wmax = BoundedFloatText(value=self.xmax, max=10 * self.xmax,
                                     min=self.xmin, description="Max")
        self.wmin = BoundedFloatText(value=self.xmin, max=self.xmax, min=0.0,
                                     description="Min")
        tmin = self.convert_datetime(self.tmin)
        tmax = self.convert_datetime(self.tmax)
        self.wtmax = BoundedFloatText(value=tmax, max=10 * tmax, min=tmin,
                                      description="Tmax")
        self.wtmin = BoundedFloatText(value=tmin, max=tmax, min=0.0,
                                      description="Tmin")

        form_item_layout = Layout(
            display='flex',
            flex_flow='row',
            justify_content='space-between'
        )

        form_items = [
            Box([self.Input, self.moguntia, self.fetch, self.wdoit,
                 self.woplot], layout=form_item_layout),
            Box([self.wof, self.wstat, self.wo], layout=form_item_layout),
            Box([Label(value='conversion'),
                 ToggleButtons(options=['mol/mol', 'ppm', 'ppb', 'ppt'])],
                layout=form_item_layout),
            Box([Label(value='# levels'), self.wlev, self.grid,
                 self.automatic], layout=form_item_layout),
            Box([Label(value='yMin, yMax'), self.wmin, self.wmax],
                layout=form_item_layout),
            Box([Label(value='xMin, xMax'), self.wtmin, self.wtmax],
                layout=form_item_layout)
        ]

        self.form = Box(form_items, layout=Layout(
            display='flex',
            flex_flow='column',
            border='solid 2px',
            align_items='stretch',
            width='100%'
        ))
        # start the main interaction window:
        self.set_visibility()
        display(self.form)
        wmain = interact(self.plot_file, doit=self.wdoit)

    def set_visibility(self):

        self.station_out = False
        self.za_out = False
        self.ll_out = False
        for ioutput in self.wof.value:
            if (ioutput.endswith('stations')):
                self.station_out = True
            elif (ioutput.find('za.') != -1):
                self.za_out = True
            elif (ioutput.find('ll.') != -1):
                self.ll_out = True

        self.wmax.value = self.xmax
        self.wmin.value = self.xmin
        tmin = self.convert_datetime(self.tmin)
        tmax = self.convert_datetime(self.tmax)
        self.wtmin.value = tmin
        self.wtmax.value = tmax

        if self.automatic.value:
            self.form.children[3].children[0].layout.visibility = 'hidden'
            self.form.children[3].children[1].layout.visibility = 'hidden'
            for j in range(3):
                self.form.children[4].children[j].layout.visibility = 'hidden'
                self.form.children[5].children[j].layout.visibility = 'hidden'
        else:
            if self.za_out or self.ll_out:
                vis = 'visible'
            else:
                vis = 'hidden'
            self.form.children[3].children[0].layout.visibility = vis
            self.form.children[3].children[1].layout.visibility = vis
            if self.station_out or self.za_out or self.ll_out:
                vis = 'visible'
            else:
                vis = 'hidden'
            for j in range(3):
                self.form.children[4].children[j].layout.visibility = vis
            if self.station_out:
                vis = 'visible'
            else:
                vis = 'hidden'
            for j in range(3):
                self.form.children[5].children[j].layout.visibility = vis

        if self.woplot.value:
            self.wo.layout.visibility = 'visible'
        else:
            self.wo.layout.visibility = 'hidden'

    def run_moguntia(self, infile):
        """Call the executable with a given inputfile"""
        with open(os.path.join(self.localpath, infile), 'r') as xfile:
            outp = subprocess.check_output([self.moguntiapathe], stdin=xfile)
            print(outp.decode("utf-8"))

    def Moguntia(self, dummy):
        inputfile = self.Input.value
        self.run_moguntia(inputfile)
        self.Fetch(None)

    def Fetch(self, dummy):
        inputfile = self.Input.value
        xfile = open(inputfile, 'r')
        # now process the output:
        lines = xfile.readlines()
        for line in lines:
            if line.startswith('TITLE'): self.title = line.split()[1]
            if line.startswith('START_DATE'): self.start_date = line.split()[
                1]
            if line.startswith('END_DATE'): self.end_date = line.split()[1]
            if line.startswith('MOLMASS'): self.molmass = line.split()[1]
            if line.startswith('NAME'): self.name = line.split()[1]
        xfile.close()
        xfile = open(os.path.join(self.localpath, 'OUTPUT',
                                  self.title + 'files_written'))
        lines = xfile.readlines()
        lines.sort()
        self.outputfiles = lines
        options = []
        for ii, filen in enumerate(self.outputfiles):
            filen = filen[:-1]
            options.append(filen)
            self.wof.options = options
        for ioutput in options:
            if (ioutput.endswith('stations')):
                self.wof.value = (ioutput,)
                self.stations = True
                ofile = open(os.path.join(self.localpath, 'OUTPUT', ioutput),
                             'r')
                lines = ofile.readlines()
                ofile.close()
                self.nstat = int(lines[0].split()[0])
                self.navg = int(lines[0].split()[1])
                self.station_names = []
                data = []
                for line in lines[self.nstat + 1:]:
                    y = [float(x) for x in line.split()]
                    data.extend(y)
                data = array(data)
                self.xlen = shape(data)[0]
                self.nrec = int(self.xlen / self.nstat)
                self.data = data.reshape((self.nrec, self.nstat))
                for i in range(self.nstat):
                    self.station_names.append(lines[i + 1].split()[0])
                # only create widget if station output:
                self.wstat.options = self.station_names
                self.wstat.value = (self.station_names[0],)
                # also create the overplot window:

                os.chdir(os.path.join(self.moguntiapath, 'MEASUREMENTS'))
                oplotfiles = glob.glob(self.name.upper() + '_*')
                oplotfiles.sort()
                os.chdir(self.localpath)
                self.wo.options = oplotfiles
        # Check if you want to run the model:

    def plot_file(self, doit=ToggleButton()):

        conversion = self.form.children[2].children[1].value
        self.conversion = conversion

        if conversion == 'mol/mol':
            self.conv = 1.0
        elif conversion == 'ppm':
            self.conv = 1e6
        elif conversion == 'ppb':
            self.conv = 1e9
        elif conversion == 'ppt':
            self.conv = 1e12

        if doit:
            if self.automatic.value == False:  # read values from max/min
                self.xmin = self.wmin.value
                self.xmax = self.wmax.value
                self.get_levels(self.wtmin.value, self.wtmax.value)
            for ioutput in self.wof.value:
                if (ioutput.endswith('stations')):
                    self.plot_station()
                elif (ioutput.find('za.') != -1):
                    self.plot_za(ioutput)
                elif (ioutput.find('ll.') != -1):
                    self.plot_ll(ioutput)
            self.set_visibility()
            self.wdoit.value = False

    def get_levels(self, Tmin, Tmax):
        self.tmin = self.convert_partial_year(Tmin)
        self.tmax = self.convert_partial_year(Tmax)

    def plot_station(self):
        # set up time:
        start_date = [int(self.start_date[0:4]), int(self.start_date[4:6]),
                      int(self.start_date[6:8])]
        xtime = self.navg * (arange(self.nrec) + 0.5) / (12.0 * 360.0) + \
                start_date[0] + (start_date[1] - 1) / 12.0 + (
                            start_date[2] - 1) / 360.0
        idate = []
        for itime in xtime:
            idate.append(self.convert_partial_year(itime))
        f, ax = subplots()
        f.set_figheight(7)
        f.set_figwidth(10)
        f.autofmt_xdate()

        stat = self.wstat.value
        COLORS = ['r', 'g', 'b', 'm', 'c', 'k', 'y', 'r', 'g', 'b', 'm', 'c',
                  'k', 'y', 'r', 'g', 'b', 'm', 'c', 'k', 'y', 'r', 'g', 'b',
                  'm', 'c', 'k', 'y']
        for istat, name in enumerate(self.station_names):
            if name in self.wstat.value:
                ax.plot(idate, self.data[:, istat] * self.conv,
                        label='MOD:' + name, color=COLORS[istat])
        if self.wo.layout.visibility == 'visible':
            ioverstat = -1
            for ostat in self.wo.value:
                ioverstat += 1
                opl = open(
                    os.path.join(self.moguntiapath, 'MEASUREMENTS', ostat),
                    'r')
                ov = []
                ot = []
                for line in opl.readlines():
                    xx = line.split()
                    year = int(xx[0])
                    mnth = float(xx[1])
                    if mnth >= 13.0:
                        year += 1
                        mnth -= 12.
                    imnth = int(mnth)
                    day = 30 * (mnth - imnth)
                    if day <= 0: day = 15
                    if day < 1: day = 1
                    day = int(day)
                    ot.append(datetime(year, imnth, day, 0, 0, 0))
                    ov.append(float(xx[2]))
                opl.close()
                stationname = ostat
                try:
                    stationname = stationname.split('_')[2]
                except:
                    None
                stationname = 'OBS:' + stationname.split('.')[0]
                ax.plot(ot, ov, 'o', label=stationname,
                        color=COLORS[ioverstat], markersize=4)

        ax.set_ylabel(self.name + ' (' + self.conversion + ')')
        ax.set_xlabel('Time')
        ax.legend(loc="best")
        ax.grid(self.grid.value)
        if self.automatic.value:
            self.xmin = ax.get_ylim()[0]
            self.xmax = ax.get_ylim()[1]
            self.tmin = num2date(ax.get_xlim()[0])
            self.tmax = num2date(ax.get_xlim()[1])
            tmin = self.convert_datetime(self.tmin)
            tmax = self.convert_datetime(self.tmax)
            self.wtmin.value = tmin
            self.wtmax.value = tmax
            self.wmin.value = self.xmin
            self.wmax.value = self.xmax
        else:
            ax.set_ylim((self.wmin.value, self.wmax.value))
            ax.set_xlim((self.tmin, self.tmax))
        f.show()

    def convert_partial_year(self, number):
        year = int(number)
        d = timedelta(days=(number - year) * 365)
        day_one = datetime(year, 1, 1)
        date = d + day_one
        return date

    def convert_datetime(self, date):
        number = date.year + min((date.month * 30 + date.day) / 365.0, 0.999)
        return number

    def plot_za(self, ioutput):
        from copy import deepcopy
        self.zaname = ioutput
        if self.automatic.value:
            self.nlev = 10
        else:
            self.nlev = self.wlev.value
        with open(os.path.join(self.localpath, 'OUTPUT', ioutput),
                  'r') as ofile:
            lines = ofile.readlines()
            self.zafield = zeros((10, 18))
            test = array([float(x) for x in lines[0].split()])
            self.zafield = test.reshape((10, 18))
            self.zafield *= self.conv
            if self.automatic.value:
                self.xmin = self.zafield.min()
                self.xmax = self.zafield.max()
        # self.xmin=Min
        # self.xmax=Max
        x = arange(18) * 10. - 85.
        y = 1000.0 - arange(10) * 100.0
        X, Y = meshgrid(x, y)
        if self.automatic.value:
            v = self.xmin + arange(self.nlev) * (self.xmax - self.xmin) / (
                        self.nlev - 1)
        else:
            v = self.wmin.value + arange(self.nlev) * (
                        self.wmax.value - self.wmin.value) / (self.nlev - 1)
        pf = deepcopy(self.zafield)
        pf = pf[:, ::-1]
        f, ax = subplots()
        f.set_figheight(7)
        f.set_figwidth(10)
        ax1 = ax.contourf(X, Y, pf, v)
        ax.set_title('Zonally-averaged concentration ' + self.zaname)
        ax.set_ylim([1000, 100])
        ax.set_ylabel('Pressure (hPa)')
        ax.set_xlabel('Latitude')
        ax.grid(self.grid.value)
        cbar = colorbar(mappable=ax1, orientation='horizontal')
        cbar.set_label(self.name + ' (' + self.conversion + ')')

    def plot_ll(self, ioutput):
        from copy import deepcopy
        self.llname = ioutput
        if self.automatic.value:
            self.nlev = 10
        else:
            self.nlev = self.wlev.value

        x = arange(36) * 10. - 175.
        y = arange(18) * 10. - 85.
        X, Y = meshgrid(x, y)
        if self.automatic.value:
            v = self.xmin + arange(self.nlev) * (self.xmax - self.xmin) / (
                        self.nlev - 1)
        else:
            v = self.wmin.value + arange(self.nlev) * (
                        self.wmax.value - self.wmin.value) / (self.nlev - 1)

        with open(os.path.join(self.localpath, 'OUTPUT', ioutput),
                  'r') as ofile:
            lines = ofile.readlines()
            nll = int(lines[0])
            self.field = zeros((18, 36, nll))
            self.levels = []
            i = 1
            for l in range(nll):
                self.levels.append(int(lines[i]))
                test = array([float(x) for x in lines[i + 1].split()])
                self.field[:, :, l] = test.reshape((18, 36))
                i += 2

            self.field *= self.conv
            if self.automatic.value:
                self.xmin = self.field.min()
                self.xmax = self.field.max()
                v = self.xmin + arange(self.nlev) * (
                            self.xmax - self.xmin) / (self.nlev - 1)
            else:
                v = self.wmin.value + arange(self.nlev) * (
                            self.wmax.value - self.wmin.value) / (
                                self.nlev - 1)

            for il, level in enumerate(self.levels):
                #               f,ax = subplots()
                #               f.set_figheight(7)
                #               f.set_figwidth(10)
                height = '%5i hPa' % (1100 - level * 100)
                pf = deepcopy(self.field[:, :, il])
                pf = roll(pf, 18, axis=1)
                pf = pf[::-1, :]

                # --- Cartopy
                import matplotlib.ticker as mticker
                from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, \
                    LATITUDE_FORMATTER

                fig1 = plt.figure(1, figsize=(16, 9))
                ax = fig1.add_subplot(111,
                                      projection=cartopy.crs.PlateCarree(),
                                      facecolor='w')
                h = ax.contourf(X, Y, pf, v)
                ax.set_xlabel('longitude (deg E)')
                ax.set_ylabel('latitude (deg N)')

                ax.add_feature(cartopy.feature.COASTLINE)
                ax.gridlines(crs=cartopy.crs.PlateCarree(), linewidth=1,
                             color='black', draw_labels=True, alpha=0.5,
                             linestyle='--')
                ax.xlabels_top = False
                ax.ylabels_left = False
                ax.ylabels_right = True
                ax.xlines = True
                ax.xlocator = mticker.FixedLocator(
                    [-160, -140, -120, 120, 140, 160, 180, ])
                ax.xformatter = LONGITUDE_FORMATTER
                ax.yformatter = LATITUDE_FORMATTER
                ax.xlabel_style = {'size': 15, 'color': 'gray'}
                ax.xlabel_style = {'color': 'red', 'weight': 'bold'}
                t = ax.set_title(
                    'Concentration at ' + height + ' ' + self.llname)
                t.set_position((0.5, 1.07))
                cax = fig1.add_axes(
                    [ax.get_position().x1 + 0.05, ax.get_position().y0, 0.02,
                     ax.get_position().height])
                cb = plt.colorbar(h, cax=cax)
                cb.set_label(self.name + ' (' + self.conversion + ')')
                plt.show(fig1)  # display the plot





