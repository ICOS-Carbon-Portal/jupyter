# -*- coding: utf-8 -*-
"""
Functions to run create a valid tex file which can be processed
by pdflatex
"""

import os

def _icos_template():
    '''
    Return the texfile as a string. The string is a complete texfile representing the station characterization, 
    but is NOT adapted to the specific run. String replacements are marked with a double **, like **stationId**, 
    which then should be replaced with stationId etc.
    
    '''
    
    tex = """
        \\documentclass[a4paper,8pt]{article}
        \\usepackage{graphicx,caption}
        \\usepackage[bottom=1in,top=1in, left=1in, right=1in]{geometry}
        \\usepackage{subcaption}
        %\\graphicspath{{figures/}} 
        \\usepackage{geometry}
        \\pagenumbering{gobble}
        \\usepackage{sidecap}
        \\usepackage[export]{adjustbox}
        \\usepackage[margin=1cm]{caption}
        \\captionsetup[subfigure]{labelformat=empty}
        \\usepackage{pdfpages}
        \\usepackage{sectsty}
        %
        \\sectionfont{\fontsize{12}{15}\selectfont}
        \\usepackage{siunitx}
        %hyperlinks
        \\usepackage{hyperref}
        \\hypersetup{
            colorlinks=true,
            linkcolor=blue,
            filecolor=blue,      
            urlcolor=blue,
        }

        %top-right corner logo
        \\usepackage[T1]{fontenc}
        \\usepackage[ngerman]{babel}

        %to add text in margins
        \\usepackage[absolute]{textpos}
        \\setlength{\TPHorizModule}{1mm}
        \\setlength{\TPVertModule}{1mm}

        \\usepackage{blindtext}

        %nicer date at bottom:
        \\usepackage[yyyymmdd]{datetime}
        %
        
        \\begin{document}

        %date 
        \\renewcommand{\dateseparator}{--}
        \\newcommand\AtPageUpperRight[1]{\AtPageUpperLeft{%
           \\makebox[\paperwidth][r]{#1}}}

        \\AddToShipoutPictureBG*{%
          \\AtPageUpperRight{\\raisebox{-\height}{\includegraphics[trim={0 0 10cm 0},clip, width=8cm]{Icos_cp_Logo_RGB}}}}

        \\begin{flushleft}
        \\begin{huge}
        **name** station characterization
        \\end{huge}\n
        \\begin{large}
        \\bigskip
Station characterization based on STILT model footprints, an anthropogenic emissions database, a biogenic flux model and ancillary datalayers. More details are found at the end of this document.
        **name** is **class_type_text** located in **country** (latitude: **lat** \\unskip, longitude: **lon** \\unskip).
        \\end{large}
        \\end{flushleft}\n

        \\begin{figure}[!h]
        \\includegraphics[width=0.53\\textwidth]{**sensitivity**}
        \\raisebox{4.7cm}[0pt][0pt]{%
        \\hspace{-0.35cm}%
        \\captionsetup{labelformat=empty}
        
        \\parbox{7.9cm}{\\caption{\\begin{small}\\textbf{Date range:} **date_range**\\\\
        \\textbf{Hour(s):} **hours**\\\\
        The map bins are **degrees** degrees at **increment** km increments.\\\\\\\\
        The \\textbf{sensitivity area map} shows the average footprint/sensitivity area. The darker the colour the more important the area was as a potential source to the measured concentrations. The total sensitivity for the surface varies between stations and **name** is in the **quartile_sensitivity** compared to reference ICOS certified atmospheric stations (see multiple variable graph).
        \\end{small}}}}
        \\end{figure}

        \\begin{figure}[!h]
        \\begin{subfigure}[t]{0.5\\textwidth}
        \\includegraphics[width=0.85\\linewidth]{**population**}
        \\centering
        \\captionsetup{width=.8\\linewidth}
        \\caption{\\begin{small}The \\textbf{population sensitivity map} is the result of the average sensitivity map multiplied by the number of people living within each footprint cell. Relative to the reference atmospheric stations, **name** is in the **quartile_population** when it comes to sensitivity to population.\\end{small}}
        \\end{subfigure}%
        \\begin{subfigure}[t]{0.5\\textwidth}
        \\includegraphics[width=0.85\\linewidth]{**pointsource**}
        \\centering
        \\captionsetup{width=.8\\linewidth}
        \\caption{\\begin{small}The \\textbf{point source contribution map} is the result of the average sensitivity map multiplied by the {\\ensuremath{\\mathrm{CO_2}}} emissions within each footprint cell which in turn have been translated into expected influence of the {\\ensuremath{\\mathrm{CO_2}}} concentration at the station. Relative to the reference atmospheric stations, **name** is in the **quartile_pointsource**when it comes to contibution from point sources.\\end{small}}
        \\end{subfigure}
        \\end{figure}\n
        
        %added- text in margin
        \\begin{textblock}{70}(115,280)
        \\noindent Date and time generated: \\today \\hspace{0.1cm} \\currenttime
        \\end{textblock}

        \\pagebreak\n
        
        \\begin{figure}[!h]
        \\centering
        \\includegraphics[width=1\\textwidth]{**seasonal**}
        \\end{figure}
        
        %added- text in margin
        \\begin{textblock}{70}(115,280)
        \\noindent Date and time generated: \\today \\hspace{0.1cm} \\currenttime
        \\end{textblock}
        
        \\begin{flushleft}
        \\begin{small}The first three variables in the \\textbf{seasonal variations table} are the results of summarizing average footprints from December **dec_year** to December **year** for sensitivity, population and point source. These values are found in the ``Annual'' column. Average footprints for the different parts of the year have in turn been computed, multiplied by the ancillary datalayers, and calculate relative (\\%) to the average for the whole year. The remaining three variables – gross ecosystem exchange (GEE), respiration and anthropogenic contribution – are the modelled averages. 
        \\end{small}
        \\end{flushleft}
        
        \\begin{figure}[!h]
        \\includegraphics[width=1\\textwidth]{**landcover_bar**}
        \\end{figure}
    
        \\begin{flushleft}
        \\begin{small}The land cover breakdown within **name**´s average footprint is shown in the  \\textbf{land cover bar graph}. The total for each land cover type is found in the legend and their relative occurence in the different directions of the stations (North-East, East, South-East etc.) are indicated by the graph. \\end{small}
        \\end{flushleft}
        
        \\pagebreak

        \\begin{flushleft}
        \\begin{large}
        \\textbf{Advanced figures}\\\\
        
        \\bigskip
We advice careful reading of the explanations before attempting to understand the following figures. For further information and understanding, please read the specifications at the end of this documnet.
        \\end{large}
        \\end{flushleft}
        
        \\begin{figure}[!h]
        \\includegraphics[width=0.75\\textwidth]{**landcover_windrose**}
        \\raisebox{6.5cm}[0pt][0pt]{%
        \\hspace{9.05cm}%
        \\captionsetup{labelformat=empty}
        \\parbox{7.9cm}{\\caption{\\begin{small}The \\textbf{land cover polar graph} shows the distribution of land cover types around the station located in the center. It indicates the directions (**degrees** degrees bins) in which the land cover types are found within the average footprint. The area of a type in the graph corresponds its relative contribution with the highest contributing type located closest to the center. \\end{small}}}}
        \\end{figure}
        
        \\begin{figure}[!h]
        \\includegraphics[width=0.57\\textwidth]{**multivar**}
        \\raisebox{4.8cm}[0pt][0pt]{%
        \\hspace{-0.3cm}%
        \\captionsetup{labelformat=empty}
        \\parbox{7.9cm}{\\caption{\\begin{small}The reference atmospheric stations are compared in this \\textbf{multiple variable graph}. **name**'s values are shown with the black line and the points' placements on the y-axis are determined relative to the minimum (0\\%) and maximum (100\\%) of the other stations. The variables are the same as the ones in the seasonal variations table. \\end{small}}}}
        \\end{figure}
        
        %added- text in margin
        \\begin{textblock}{70}(115,280)
        \\noindent Date and time generated: \\today \\hspace{0.1cm} \\currenttime
        \\end{textblock}
        \\pagebreak
        
        \\input{specifications.tex}
        
        \end{document}
        """
    return tex


def icos(stc):
    """       
    Provide an stc object, which contains all the necessary information to create the texfile
    see class stationchar.py based on a template for icos stations
    Parameters
    ----------
    stc : stationchar object, contains figures, captions, etc
            
    Returns
    -------
    STR: the complete tex file as string, which can be run on the system to create a pdf file output.

    """
    
    output = stc.settings['output_folder']
        
    tex = _icos_template()

    tex=tex.replace('**sensitivity**', os.path.join(output, stc.figures['1'][2])) 
    tex=tex.replace('**pointsource**', os.path.join(output, stc.figures['2'][2]))
    tex=tex.replace('**population**', os.path.join(output, stc.figures['3'][2]))
    tex=tex.replace('**landcover_bar**', os.path.join(output, stc.figures['4'][2]))
    tex=tex.replace('**seasonal**', os.path.join(output, stc.figures['5'][2]))
    tex=tex.replace('**landcover_windrose**', os.path.join(output, stc.figures['6'][2]))
    tex=tex.replace('**multivar**', os.path.join(output, stc.figures['7'][2]))
    
    tex=tex.replace('**quartile_sensitivity**', stc.settings['Sensitivity'])
    tex=tex.replace('**quartile_population**', stc.settings['Population'])
    tex=tex.replace('**quartile_pointsource**', stc.settings['Point source'])
    
    tex=tex.replace('**country**', stc.country)
    
    tex=tex.replace('**year**', str(stc.settings['startYear']))
    tex=tex.replace('**dec_year**', str(int(stc.settings['startYear'])-1))
    
    tex=tex.replace('**degrees**', str(stc.settings['binSize']))
    tex=tex.replace('**increment**', str(stc.settings['binInterval']))
    
    date_string=str(stc.settings['startYear']) + '-' + str(stc.settings['startMonth']) + '-' + str(stc.settings['startDay']) + ' to ' + str(stc.settings['endYear']) + '-' + str(stc.settings['endMonth']) + '-' + str(stc.settings['endDay'])
    
    timeselect_list = stc.settings['timeOfDay']
    timeselect_string=[str(value) for value in timeselect_list]
    hours_string =':00, '.join(timeselect_string) + ':00'
    
    tex=tex.replace('**date_range**', date_string)
    tex=tex.replace('**hours**', hours_string)
    
    
    try:   
        tex=tex.replace('**name**', stc.settings['icos']['name'])
        tex=tex.replace('**lat**', str(stc.settings['icos']['lat']))
        tex=tex.replace('**lon**', str(stc.settings['icos']['lon']))
        tex=tex.replace('**class_type_text**', ('a class ' + str(stc.settings['icos']['icosclass']) +\
                       ' ICOS atmospheric station of the type ' + str(stc.settings['icos']['siteType'])))
    
    except:
        tex=tex.replace('**name**', stc.settings['stilt']['name'])
        tex=tex.replace('**class_type_text**', 'not an ICOS certified station, ')
        tex=tex.replace('**lat**', str(stc.settings['stilt']['lat']))
        tex=tex.replace('**lon**', str(stc.settings['stilt']['lon']))

    return tex