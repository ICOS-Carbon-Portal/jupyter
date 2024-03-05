import stationchar
import stc_functions

from datetime import datetime
import os
from icoscp.station import station as cpstation
from icoscp.stilt import stiltstation
import datetime as dt
stiltstations= stiltstation.find()
def generate_PDFs(list_stations):

    for station in list_stations:
        
        settings = {}

        settings['stationCode'] = station
        if stiltstations[station]['icos']:
            settings['icos'] = cpstation.get(station[0:3].upper()).info()
        settings['stilt'] = stiltstations[station]
        settings['startYear'] = 2020
        settings['startMonth'] = 1
        settings['startDay'] = 1
        settings['endYear'] = 2020
        settings['endMonth'] = 12
        settings['endDay'] = 31
        settings['timeOfDay'] = [0,3,6,9,12,15,18,21]
        settings['binSize'] = 15
        settings['binInterval'] = 100
        settings['unit'] = 'percent'
        settings['labelPolar'] = 'no'
        settings['saveFigs'] = 'yes'
        settings['titles'] = 'no'
        settings['figFormat'] = 'pdf'

        stc=stationchar.StationChar(settings)

        now = datetime.now()
        stc.settings['date/time generated'] =  now.strftime("%Y%m%d_%H%M%S_")
        stc.settings['output_folder'] = os.path.join('output', (stc.settings['date/time generated']+stc.stationId))
        if not os.path.exists('output'):
            os.makedirs('output')

        os.mkdir(stc.settings['output_folder'])

        fig, caption = stc_functions.polar_graph(stc, 'sensitivity')
        stc.add_figure(1, fig, caption)


        fig, caption=stc_functions.polar_graph(stc, 'point source contribution', colorbar='Purples')
        stc.add_figure(2, fig, caption)


        fig, caption =stc_functions.polar_graph(stc, 'population sensitivity', colorbar='Greens')
        stc.add_figure(3, fig, caption)
        
        fig, caption=stc_functions.land_cover_bar_graph(stc)
        stc.add_figure(4, fig, caption)
                
        fig, caption=stc_functions.seasonal_table(stc)
        stc.add_figure(5, fig, caption)

        fig, caption=stc_functions.land_cover_polar_graph(stc)
        stc.add_figure(6, fig, caption)

        fig, caption= stc_functions.multiple_variables_graph(stc)
        stc.add_figure(7, fig, caption)

        stc_functions.save(stc, 'pdf')