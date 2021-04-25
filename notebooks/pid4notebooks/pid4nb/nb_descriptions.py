#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    
    Description:      Class that creates objects for storing different types
                      of descriptions in relation to a notebook. The types
                      are defined by the DataCite metadata schema v.4.4.
                      For more information, please visit: 
                      https://schema.datacite.org/meta/kernel-4.4/doc/DataCite-MetadataKernel_v4.4.pdf
                      
    
"""

__author__      = ["Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.0.1"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2021-03-31"
############################################################################################################

#Import modules:
from ipywidgets import Layout, Textarea, Dropdown, HBox, VBox, Button, Accordion, Output
from IPython.display import clear_output
from pid4nb.formats.msg_funcs import printmd
######################################################################################


class Descriptions():
    
    """
    Description: Class that stores different kinds of descriptions
                 (e.g. abstract, methods, table of contents, user message)
                 of a Jupyter notebook.
                 More in particular, a description consists of the
                 following variables:
                 1.  Description (text)
                 2.  Decription type (category of description)
    
    """
    
       
    
    #Initialize object:
    def __init__(self):
        
        #Set label format:
        style = {'description_width': '100px'}

        #Set widget format:
        layout1 = Layout(width='60.0%', height='200px') #set width and height
        layout2 = Layout(width='60.0%') #set width
        
        #########################
        ### Object attributes ###
        #########################

        #Add "description" text-area-box:
        self.description = Textarea(value='',
                                    placeholder="Enter a description...",
                                    description='Description',
                                    style=style,
                                    layout=layout1,
                                    disabled=False)

        #Add "description type" dropdown:
        self.description_type = Dropdown(options=['Abstract','Methods','SeriesInformation',
                                                  'TableOfContents','Other'],
                                         value='Abstract',
                                         description='Description type',
                                         style=style,
                                         layout=layout2,
                                         disabled=False)
######################################################################################


    #Function that creates a single "notebook description" widget set:
    def create_wdgt(self):
        
        return VBox([self.description_type, self.description])
######################################################################################


def create_wdgt_form():
    
    #Organize the object's widgets to a form:
    descr_wdgt = Descriptions().create_wdgt()
    
    #Set button layout:
    layout_btn = Layout(width='20.0%') #set width and height

    #Create button for adding a new description widget set:
    add_descr_bttn = Button(description='Add description',
                                button_style='warning',
                                tooltip='Click to add new description',
                                icon='plus',
                                layout=layout_btn,
                                disabled=False)

    #Create button for deleting selected description widget set:
    del_descr_bttn = Button(description='Remove description',
                                button_style='danger',
                                tooltip='Click to remove selected description',
                                icon='minus',
                                layout=layout_btn,
                                disabled=False)

    #Create output obj to add a message to the user:
    user_msg = Output()

    #Open output object:
    with user_msg:

        #Delete previous message:
        clear_output()

        #Add message to user:
        printmd("<p>The fields below provide you with the opportunity to add text describing your notebook. Note that there are different types of descriptions to choose from. For more information regarding what those types are and what text you should include for each one, have a look at the <a href='https://schema.datacite.org/meta/kernel-4.4/doc/DataCite-MetadataKernel_v4.4.pdf'>DataCite metadata documentation</a>.</p><br>")

    #Create output obj to add an error message to the user:
    error_msg = Output()

    #Add author-widgets to accordion-widget:
    descriptions = Accordion(children=[descr_wdgt])

    #Set title to accordion-widget options:
    descriptions.set_title(0, 'Description 1')


    #Add function to handle button-click (add description): 
    def on_add_descr_bttn_clicked(button_c):
        
        
        with error_msg:
            
            #Clear content of previous form:
            clear_output()

        #Add description-widget-set to accordion children-tuple:
        descriptions.children = descriptions.children + (Descriptions().create_wdgt(),)

        #Add title:
        descriptions.set_title(len(descriptions.children)-1, 'Description '+ str(len(descriptions.children)))


    #Add function to handle button-click (delete description): 
    def on_del_descr_bttn_clicked(button_c):

        with error_msg:

                #Clear content of previous msg:
                clear_output()

        #Check list of descriptions (there has to be at least one description):
        if((len(descriptions.children)>1) & (isinstance(descriptions.selected_index, int))):

            #Remove an accordion option:
            descriptions.children[descriptions.selected_index].close()

            #Tuples are immutable - cannot delete item from tuple.
            #Convert tuple to list:
            descriptions_ls = list(descriptions.children)

            #Remove selected accordion child from list:
            descriptions_ls.remove(descriptions.children[descriptions.selected_index])

            #Convert list to tuple and update initial accordion-content:
            descriptions.children = tuple(descriptions_ls)

            #Set description accordion-titles:
            for i in range(len(descriptions.children)):

                descriptions.set_title(i, 'Description ' + str(i+1))
        
        #If only one description is available:
        elif((len(descriptions.children)==1)):
            
            with error_msg:

                #Clear content of previous form:
                clear_output()

                printmd("<font color='red'>You cannot remove all descriptions.<br>You need to add at least one description.</font>")
            

        else:

            with error_msg:

                #Clear content of previous form:
                clear_output()

                printmd("<font color='red'>Please select a description</font>") 



    #Call function on button_click-event (add description):
    add_descr_bttn.on_click(on_add_descr_bttn_clicked)

    #Call function on button_click-event (remove description):
    del_descr_bttn.on_click(on_del_descr_bttn_clicked)

    return VBox([user_msg, descriptions, HBox([add_descr_bttn, del_descr_bttn]), error_msg])
######################################################################################


#Function that deletes the user entries in the widget fields:
def clear_fields(wdgt_form):
    
    #Loop through all descriptions:
    for descr in wdgt_form.children[1].children:
        
        #Set initial values:
        descr.children[0].value = 'Abstract' #description type
        descr.children[1].value = ''         #description text
    
    #Delete error message (if applicable...):
    with wdgt_form.children[3]:
        
        clear_output()
######################################################################################


#Function that returns a dictionary with the values for the separate
#description widget fields:
def to_dict(wdgt_form):
    
    #Create dictionary to store metadata about the descriptions:  
    meta_dict ={"descriptions" : [{'xml:lang': 'en',
                                   'descriptionType' : descr.children[0].value,
                                   'description' : descr.children[1].value}
                                  if descr.children[1].value!=''
                                  else {'xml:lang': '',
                                        'descriptionType' : '',
                                        'description' : ''}
                                  for descr in wdgt_form.children[1].children]}  
    
    #Return disctionary:
    return meta_dict
######################################################################################    
    