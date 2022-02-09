import radiocarbon_functions
from ipywidgets import Dropdown, Button, Output, VBox, RadioButtons
from IPython.display import clear_output
from icoscp.station import station as station_data
from IPython.core.display import display, HTML 

#want to have a dropdown with the names of the nuclear facilities ranked by their emissions year 2018
list_facility_names=[]   
list_emissions_2018=[]

dictionary_radiocarbon_emissions=radiocarbon_functions.dictionary_radiocarbon_emissions
for key in dictionary_radiocarbon_emissions:

    list_facility_names.append(dictionary_radiocarbon_emissions[key]['name']) 

    list_emissions_2018.append(dictionary_radiocarbon_emissions[key]['2018']) 

list_facility_names_sorted=[x for _,x in sorted(zip(list_emissions_2018,list_facility_names), reverse=True)]

#Create dropdown list for emission facilities:

header_interactive_map = Output()
with header_interactive_map:
    display(HTML('<p style="font-size:16px;font-weight:bold;">Interactive map showing nuclear facilities and ICOS stations</p>'))

header_select_facility = Output()

with header_select_facility:
    display(HTML('<p style="font-size:15px;"><ul><li>All European nuclear facilities will be shown on the map</li>\
    <li>This dropdown lists all the facilities sorted by emissions in 2018 with the highest emitters listed first</li>\
    <li>The selected facility will be highlighted on the map with a yellow marker whereas the other facilities are represented with red markers. Blue markers represent the ICOS stations.</li>\
    <li>Hoover over the markers to show the names of the facilities and stations</li>\
    <li>Click on the markers to see information on emissions and information about the stations respectively</li></ul></p>'))

select_facility = Dropdown(options = list_facility_names_sorted,

                         description='')

#Create dropdown list basemap options:
header_select_basemap = Output()

with header_select_basemap:
    
    display(HTML('<p style="font-size:15px;">Select basemap:</p>'))
    
select_basemap = Dropdown(options = ['Imagery', 'OpenStreetMap'], description='')

header_year_data= Output()
with header_year_data:
    display(HTML('<p style="font-size:15px;">Choose year:</p>'))
    
header_static_map = Output()
with header_static_map:
    display(HTML('<p style="font-size:16px;font-weight:bold;"><br>Static map showing nuclear facilities\' emissions and ICOS atmospheric stations</p>'))


year_data=RadioButtons(
    options=['2006','2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020'],
    value='2020',
    description=' ',
    disabled=False)

#Create button widget (execution):

button_exe = Button(description='Update maps',

                    disabled=False,

                    button_style='danger', # 'success', 'info', 'warning', 'danger' or ''

                    tooltip='Press the button to update map',

                    icon='check')

#Format widgets:

select_facility.layout.width = '379px'

select_facility.style.description_width = 'initial'

select_facility.layout.margin = '2px 2px 2px 10px'

select_basemap.layout.width = '200px'

select_basemap.style.description_width = 'initial'

select_basemap.layout.margin = '2px 2px 2px 10px'

button_exe.style.button_color = '#3973ac'

button_exe.layout.width = '150px'

button_exe.layout.margin = '10px 50px 40px 30px'

#Create form object:

form_out = Output()
#Create output object:

plot_out = Output() 

#Function that executes on button_click (calculate score):

def on_exe_bttn_clicked(button_c):

    #Open output object:

    with plot_out:

        #Delete previous output:

        clear_output()

        all_stations=station_data.getIdList()

        atm_stations=all_stations[all_stations['theme']== 'AS']

        #list of atmospheric stations, selected station, basemap choice
        radiocarbon_functions.plotmap(atm_stations, select_facility.value, select_basemap.value, d_icon='cloud', icon_col='orange')
        
        #here static map
        
        radiocarbon_functions.plotmap_static(atm_stations, year_data.value)


#Call function on button_click-event (calculate score):

button_exe.on_click(on_exe_bttn_clicked)

#Open output obj:a

with form_out:

    #Clean previous values:

    clear_output()

    #Show plot:

    display(VBox([header_interactive_map, header_select_facility, select_facility, header_select_basemap, select_basemap, header_static_map, header_year_data, year_data, button_exe, plot_out]))

#Display form:

display(form_out)