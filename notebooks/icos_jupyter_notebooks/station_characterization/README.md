<img src="https://www.icos-cp.eu/sites/default/files/2017-11/ICOS_CP_logo.png" width="300" align="right"/>
<br>
<br>
<br> 

# Content
This folder contains everything needed to run the station characterization notebook <b>station_characterization.ipynb</b>.

## Background

The aim of the ICOS atmosphere station characterization tool is to provide users of ICOS data with basic information on what potentially influences 
the tracer concentrations at the station and to support them in the selection of stations. The station characterization tool is based on the stations’ 
influence regions, also called footprints. Footprints are calculated by atmospheric transport models – the STILT (Stochastic Time Inverted Lagrangian 
Transport model) model in this case – and indicate the contribution of the surface exchange fluxes to the atmospheric concentration of the tracer.

As these footprints can be computed on demand in the ICOS footprint tool ([on demand calculator](https://stilt.icos-cp.eu/worker/)), the characterization 
can be produced also for hypothetical stations, e.g. to aid in the process of picking a station location. 

The idea is that these footprints can be used to characterize the average sensitivity of a station to different influences, i.a.: 

* anthropogenic CO2 emissions based on the EDGAR (Emission Database for Global Atmospheric Research) emission inventory,
* biospheric CO2 uptake and respiration based on the VPRM (Vegetation Photosynthesis and Respiration Model) model,
* land cover (e.g. forest, crop land, pastures, urban, ocean) based on the CORINE (Coordination of Information on the Environment) classification,
* population density based on GEOSTAT, 
* emissions from point sources based on the E-PRTR (The European Pollutant Release and Transfer Register) database

## Output figures

The station’s total average sensitivity and sensitivity within certain distances and directions of the station are further investigated by aggregating 
the footprints on different time scales (e.g. seasons, months or specific dates). The same type of aggregation is used to visualize the sensitivity to
population and point source emissions. Sensitivities to different land cover classes are visualized in a bar graph showing sensitivities by direction (N, NE, E, SE, S, SW, W, NW)
as well as a polar graph where smaller "direction binning" is possible. All the different influencers except land cover are also included in a 
seasonal variations table. Averages for a whole meterological year (December of the year before the user-selected start date until December of the user selected start date)
are compared to the different seasons. The same influencers are also included in the multiple variables graph where a handful of ICOS stations are used used as reference
for the user-selected station. The selected station is placed on the y-axis in relation to the minimum and maximum influencer values of the ICOS stations. 

The figures can be saved, and in the future there will be an option to use the saved figures to generate the same type of station characterization PDFs as on the 
station landing pages.

## License
* Copyright © 2019-2020 ICOS ERIC
* This work is licensed under a
Creative Commons Attribution 4.0 International License ([CC BY 4.0](http://creativecommons.org/licenses/by/4.0/)).
