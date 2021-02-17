def texTemplate():
    '''
    Return the texfile as a string. The string is a complete texfile representing the station characterization, 
    but is NOT adapted to the specific run. Stringreplacements are marked with a double ##, like ##stationId##, 
    which then should be replaced with stationId etc.
    
    '''
    
    tex = """
        \\documentclass[a4paper,8pt]{article}
        \\usepackage{graphicx,caption}
        \\usepackage[bottom=1in,top=1in, left=1in, right=1in]{geometry}
        \\usepackage{subcaption}
        \\graphicspath{{figures/}} 
        \\usepackage{geometry}
        \\pagenumbering{gobble}
        \\usepackage{sidecap}
        \\usepackage[export]{adjustbox}
        \\usepackage[margin=1cm]{caption}
        \\captionsetup[subfigure]{labelformat=empty}
        \\usepackage{pdfpages}
        \\begin{document}
        \\newcommand\stationcode{##station##}
        \\begin{flushleft}
        \\begin{huge}
        ##text1##station characterization
        \\end{huge}\n
        \\begin{large}
        \\bigskip
        Based on footprints for 2018, an anthropogenic emissions database, a biogenic model and ancillary datalayers.
        ##text1## is a class ##text2##}\\unskip, tall tower, ICOS atmospheric measurement station located in \\input{texts/\\stationcode_text_4.txt}(latitue: \\input{texts/\\stationcode_text_5.txt}\\unskip, longitude: \\input{texts/\\stationcode_text_6.txt}\\unskip).
        \\end{large}
        \\end{flushleft}\n

        \\begin{SCfigure}[][h]
        \\includegraphics[width=0.6\\textwidth]{\\stationcode_figure_1}
        \\captionsetup{labelformat=empty}
        \\caption{\\begin{small}The \\textbf{sensitivity area map} shows the average footprint/sensitivity area for 2018. Relative sensitivity is used, but there are great differences in total average sensitivity between the different stations. \\protect\\input{texts/\\stationcode_text_1.txt}is in the \\protect\\input{texts/\\stationcode_text_7.txt}when it comes to total average sensitivity of the ICOS labeled atmospheric stations.\\end{small}\\bigskip\\bigskip\\bigskip\\bigskip\\bigskip\\bigskip\\bigskip\\bigskip\\bigskip\\bigskip}
        \end{SCfigure}\n

        \\begin{figure}[!h]
        \\begin{subfigure}[t]{0.5\\textwidth}
        \\includegraphics[width=0.85\\linewidth]{\\stationcode_figure_2}
        \\centering
        \\captionsetup{width=.8\\linewidth}
        \\caption{\\begin{small}The \\textbf{population sensitivity map} is the result of the average sensitivity map multiplied by the number of people living within each footprint cell. Relative to other labeled atmospheric stations, \\input{texts/\\stationcode_text_1.txt}is in the \\input{texts/\\stationcode_text_8.txt}when it comes to sensitivity to population.\\end{small}}
        \\end{subfigure}%
        \\begin{subfigure}[t]{0.5\\textwidth}
        \\includegraphics[width=0.85\\linewidth]{\\stationcode_figure_3}
        \\centering
        \\captionsetup{width=.8\\linewidth}
        \\caption{\\begin{small}The \\textbf{point source contribution map} is the result of the average sensitivity map multiplied by the {\\ensuremath{\\mathrm{CO_2}}} emissions within each footprint cell which in turn have been translated into expected influence of the {\\ensuremath{\\mathrm{CO_2}}} concentration at the station. \\input{texts/\\stationcode_text_1.txt}is a station with relatively \\input{texts/\\stationcode_text_9.txt}influence of point source emissions, placing in the \\input{texts/\\stationcode_text_10.txt}of the atmospheric stations.\\end{small}}
        \\end{subfigure}
        \\end{figure}\n

        \\pagebreak\n

        \\begin{figure}[!ht]
        \\includegraphics[width=0.9\\textwidth]{\\stationcode_figure_4}
        \\raisebox{4.5cm}[0pt][0pt]{%
        \\hspace{7.5cm}%
        \\captionsetup{labelformat=empty}
        \\parbox{9.2cm}{\\caption{\\begin{small}The \\textbf{land cover wind rose}  is similar to the maps in that the center represents the station and the distribution of the land cover around the center indicate the direction of the different land cover classes in relation to the station.\\end{small}}}}
        \\end{figure}\n

        \\begin{SCfigure}[][h]
        \\includegraphics[width=0.6\\textwidth]{\\stationcode_figure_5}
        \\captionsetup{labelformat=empty}
        \\caption{\\begin{small}In the \\textbf{multiple variables graph} the total of all values used to generate the maps are shown relative to the other atmospheric stations. The remaining three variables – GEE, respiration and anthropogenic contribution – are the averages for 2018. \\protect\\input{texts/\\stationcode_text_1.txt}\\unskip’s placement on the y-axis is determined relative to the minimum and maximum values given all stations.\\newline\\newline
        The 2018 absolute averages are used in the multiple variables graph is found in the \\textbf{seasonal variations table}. The values for the different seasons have been computed relative to these.\\end{small}\\bigskip\\bigskip\\bigskip\\bigskip\\bigskip}
        \\end{SCfigure}\n

        \\begin{figure}[!h]
        \\centering
        \\includegraphics[width=1\\textwidth]{\\stationcode_figure_6}
        \\end{figure}\n

        \\includepdf[pages=-,pagecommand={},width=1.2\\textwidth]{texts/Specifications.pdf}
        """
    return tex


def customTex(stc):
    """       
    Provide a n stc object, which containse all the necessary information to create the texfile
    see class stationchar.py  
    INPUT: 

    Parameters
    ----------
    stc : stationchar object
            contains StationID as string, like 'GAT341' and captions
            
    Returns
    -------
    STR: the complete tex file as string, which can be run on the system to create a pdf file output.

    """
    tex = texTemplate()
    tex.replace('##station##', station)
    for txt in captions:
        tex.replace
