#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    
    Description:      Functions that are used to create a bibtex
                      citation for the resource metadata folder 
                      produced by the PID4NB wizard app.
    
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2020-04-19"
########################################################################################################


#Function that creates a bibTex citation file:
def get_bibtex_citation(metadata_dict, path):
    
    #Create bibtex citation-string:
    bibtex = """@misc{"""+metadata_dict['identifier']+""",
                author = {"""+' and '.join([c['creatorName'] for c in metadata_dict['creators']])+"""},
                Email = {"""+', '.join([c['email'] for c in metadata_dict['creators']])+"""},
                title = {"""+metadata_dict['titles'][0]['title']+"""},
                year = {"""+metadata_dict['publicationYear']+"""},
                publisher = {"""+metadata_dict['publisher']+"""},
                type = {"""+metadata_dict['resourceTypeGeneral']+"""},
                doi = {"""+metadata_dict['identifier']+"""}}"""
    
    #Save bibtex citation-string to file:
    with open(path+'/bibtex.bib', 'w') as bibfile:
        bibfile.write(bibtex)
########################################################################################################