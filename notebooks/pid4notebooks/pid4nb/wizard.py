#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    
    Description:      Functions that are used to set up a widget form
                      for the PID4NB wizard app.
    
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se',
                   'claudio.donofrio@nateko.lu.se']
__date__        = "2020-03-31"

#####################################################################

#Import modules:
import os
import json
from IPython.display import clear_output
from ipywidgets import Button, HTML, VBox, HBox, Tab, Layout, Output
from pid4nb.formats.msg_funcs import printmd
from pid4nb.nb_general_info import NbGeneralInfo
from pid4nb import nb_descriptions, nb_authors, nb_related_identifiers, nb_uploads
from pid4nb import nb_techinfo
from pid4nb.checks.control_funcs import check_meta_entries
from pid4nb.xml.nb_meta import json_to_xml
######################################################################

#Function that gets a string with the 1st author's
#family name, creates the notebook metadata folder
#and returns the name of that folder:
def get_meta_folder(authorname):
    
    #Import modules
    import os
    from pathlib import Path
    from datetime import datetime
    
    #Create widget for error message:
    folder_err_msg = Output()
    
    #Open widget obj and delete previous output:
    with folder_err_msg:
        
        #Clear content of previous form:
        clear_output()
    
    #Check if output-folder already exists:
    if(os.path.exists('output')==False):   
        
        #Create folder:
        try:
            os.mkdir('output')

        #Throw error message:
        except OSError:
            
            #Open widget obj
            with folder_err_msg:
                
                #Clear content:
                clear_output()
                
                #Print error message:
                printmd("<font color=orange>Creation of the directory %s failed</font>" % 'output')


    ''' special characaters in name are note handled
        use unix timestamp instead
    #Store current date-string as "YYYYMMDD":
    date_str = datetime.now().date().strftime("%Y%m%d") 
    
    #Store the name of the notebook metadata-folder as "output/authorYYYYMMDD_"
    meta_folder = 'output/'+authorname+date_str+'_'     
   
   
    #Check if notebook metadata-folder already exists:
    if(os.path.exists(meta_folder+'0')==False):
            
        new_meta_folder = meta_folder+'0'

    #If notebook metadata-folder already exists (increase digit):
    else:
            
        #Initialize counter variable:
        digit = 0
            
        #While path exists, increase counter-variable by one:
        while os.path.exists(meta_folder+"%s" % digit):
            digit += 1
            
        #Create new name for notebook metadata-folder:
        new_meta_folder = 'output/'+authorname+date_str+'_'+str(digit)
'''
    import time
    new_meta_folder = 'output/'+ str(int(time.time()))
 
    #Create new notebook metadata-folder:
    Path(new_meta_folder).mkdir(parents=True, exist_ok=True)

    #Return the name for the new notebook metadata-folder:
    return new_meta_folder
######################################################################

def wizard():
    
    #Set widget style for description width:
    layout = Layout(width='64.4%') #set width and height
    #banner

    #Initialize form output:
    form = Output()
    form_out = Output()

    #Create a notebook "general-info" object:
    general_info = NbGeneralInfo()

    #Call function to get widget form for "descriptions":
    nb_descr = nb_descriptions.create_wdgt_form()

    #Call function to get VBox with "author" fields:
    author_wdgt_form = nb_authors.author_wdgt_form()
    
    #Call function to get VBox with "related identifier" fields:
    rel_ident_wdgt_form = nb_related_identifiers.create_wdgt_form()
    
    #Call function to get widgets for "technical description":
    tech_description_wdgt_form = nb_techinfo.tab() #to be replaced with Claudio's code
    
    #Call function to get widgets for "uploads":
    nb_uploads_obj = nb_uploads.NBuploads() #Create new uploads obj
    uploads_wdgt_form = nb_uploads_obj.uploads_wdgt()
    

    
    
    #Create tab object:
    tabs = Tab()

    #Set tab content:
    tabs.children = [general_info.general_info_wdgt(), nb_descr,
                     author_wdgt_form, rel_ident_wdgt_form,
                     tech_description_wdgt_form, uploads_wdgt_form]
    
    #Set tab titles:
    tabs.set_title(0, 'General metadata*')
    tabs.set_title(1, 'Description')
    tabs.set_title(2, 'Author*')
    tabs.set_title(3, 'Related identifier')
    tabs.set_title(4, 'Technical description*')
    tabs.set_title(5, 'Uploads*')


    #Create button widget (execution):
    button_exe = Button(description='Create metadata file',
                        disabled=False,
                        button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                        tooltip='Click to create metadata file',
                        icon='check')

    #Create button widget (retake quiz):
    button_init = Button(description='   Clear fields',
                         disabled=False,
                         button_style='success', # 'success', 'info', 'warning', 'danger' or ''
                         tooltip='Click to clear all input fields',
                         icon='repeat')

    #Create widget to add banner:
    banner = HTML(value='<img src="https://www.icos-cp.eu/themes/cp_theme_d8/images/icos-header.jpg">')

    #Open form object:
    with form:

        #Clear content of previous form:
        clear_output()

        #Display widgets:
        display(VBox([banner, tabs,
                      HBox([button_exe, button_init])]))


    def on_exe_button_clicked(button_c):

        #Check input:
        if (check_meta_entries(general_info.publication_date.value, general_info.title.value, form_out)):


            #Call func to return dictionaries with notebook metadata (per tab)
            #Merge all dictionaries to one:
            meta_dict = {**general_info.to_dict(),
                         **nb_descriptions.to_dict(nb_descr),
                         **nb_authors.to_dict(author_wdgt_form),
                         **nb_related_identifiers.to_dict(rel_ident_wdgt_form)}


            #Get notebook metadata folder name:
            folder = get_meta_folder(meta_dict['creators'][0]['familyName'])
            
            #Add uploads to notebook metadata folder:
            #nb_uploads_obj.to_folder(folder)
            
            #Convert dictionary to json and save to file:
            with open(folder+"/metadata.json", "w") as metafile:  

                json.dump(meta_dict, metafile) 
                
            #Create xml metadata file (based on json metadata file): 
            json_to_xml(folder, 'metadata.json')
            
            #Prompt message for successful creation of metadata file:
            with form_out:

                #Clear content of previous form:
                clear_output()

                printmd('<font color=orange>Your metadata folder is ready!</font>')
        else:
            #Prompt message for successful creation of metadata file:
            with form_out:

                printmd('<font color=red>Your metadata folder could not be created!</font>')

        nb_techinfo.convert(folder)
        nb_techinfo.freeze(folder)
        nb_techinfo.system_info(folder)
        nb_techinfo.system_info(folder)
        #nb_techinfo.docker_info(folder)
        nb_techinfo.project(folder)
        
        
    #Function that clears all field entries:
    def on_init_button_clicked(button_c):

        ### Clear form field entries ###
        #Clear entries in "notebook-metadata" tab:
        general_info.clear()

        #Call function to remove entries from "descriptions" tab:
        nb_descriptions.clear_fields(nb_descr)

        #Call func to clear the entries from all "author" fields:
        nb_authors.clear_fields(author_wdgt_form)
        
        #Call func to clear the entries from all "related identifier" fields:
        nb_related_identifiers.clear_fields(rel_ident_wdgt_form)
        
        #Call func to remove uploads:
        nb_uploads_obj.clear()
        nb_uploads_obj.clear()

        #Clear error message text (if applicable):
        with form_out:

            #Clear content of previous form:
            clear_output()


    #Call function on button_click-event (save input to file):
    button_exe.on_click(on_exe_button_clicked)

    #Call function on button_click-event (clear input fields):
    button_init.on_click(on_init_button_clicked)

    #Style buttons:
    button_exe.style.button_color = '#2D6572'
    button_exe.layout.width = '750px'
    button_exe.layout.height = '50px'
    #button_exe.layout.margin = '50px 100px 40px 300px'
    button_init.style.button_color = '#87A7B0'
    button_init.layout.width = '250px'
    button_init.layout.height = '50px'
    #button_init.layout.margin = '50px 50px 40px 100px'


    #Display form:
    display(VBox([form, form_out]))