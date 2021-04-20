#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    
    Description:      This file contains structures in Python that are used
                      to store metadata information about the author(s) of 
                      an ICOS Jupyter notebook. The author metadata information
                      complies to the DataCite metadata schema v.4.4.
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


################################################################################################
#Import modules:
from ipywidgets import Text, Output, Button, Layout, VBox, HBox, Accordion
from IPython.display import clear_output
from pid4nb.orcidpy import orcid
from pid4nb.formats.msg_funcs import printmd
################################################################################################


class Author():
    
    #Initialize object:
    def __init__(self): 
        
        #Set widget layout:
        layout = Layout(width='60.0%') #set width
    
        #Add text-widgets to hold author information:
        self.orcid_id = Text(value='',
                     placeholder="Enter author's ORCiD...",
                     description='ORCiD',
                     layout=layout,
                     disabled=False)

        self.fname = Text(value='',
                     placeholder="Enter author's first name...",
                     description='First name',
                     layout=layout,
                     disabled=False)

        self.lname = Text(value='',
                     placeholder="Enter author's last name...",
                     description='Last name',
                     layout=layout,
                     disabled=False)

        self.affiliation = Text(value='',
                            placeholder="Enter author's affiliation...",
                            description='Affiliation',
                            layout=layout,
                            disabled=False)

        self.email = Text(value='',
                     placeholder="Enter author's email...",
                     description='Email',
                     layout=layout,
                     disabled=False)

        #Create widget to hold error message for orcid user input:
        self.comment = Output()
############################################################################################################    
    
    
    #Return widget-set for single creator:
    def author_wdgt(self):
        
        #Add button widget to retrieve information from ORCID:
        orcid_bttn = Button(description='',
                            disabled=False,
                            button_style='success', # 'success', 'info', 'warning', 'danger' or ''
                            tooltip='Click to retrieve author information from ORCID',
                            icon='fa-file-text') #fa-user-circle

        #Style button:
        orcid_bttn.style.button_color = '#759AA3'
        orcid_bttn.layout.width = '30px'

        #Function that fills the author fields using the
        #ORCID API (public):
        def on_orcid_bttn_clicked(button_c):

            #Clear input fields:
            self.fname.value = ''
            self.lname.value = ''
            self.affiliation.value = ''
            self.email.value = ''

            #Check if orcid input field is empty:
            if(self.orcid_id.value==''):

                #Open comment widget object:
                with self.comment:

                    #Delete previous comment:
                    clear_output()

                    #Prompt error message:
                    printmd("<font color='darkred'>Please enter a value in the ORCID field</font>")

            #If orcid input field is not empty:
            else:

                #Get all info based on author's ORCID (returns a dictionary):
                orcid_info = orcid.get(self.orcid_id.value)

                #Check orcid response:
                if ('response-code' in orcid_info.keys()):

                    #Open comment widget object:
                    with self.comment:

                        #Delete previous comment:
                        clear_output()

                        #Prompt error message:
                        printmd("<font color='darkred'>Please enter a valid ORCID...</font>")

                #If orcid exists:
                else:

                    #Get first name:
                    self.fname.value = orcid.get_orcid_name(orcid_info)

                    #Get last name:
                    self.lname.value = orcid.get_orcid_surname(orcid_info)

                    #Get affiliation:
                    self.affiliation.value = orcid.get_orcid_affiliation(orcid_info)

                    #Get email:
                    self.email.value = orcid.get_orcid_email(orcid_info)

                    #Open comment widget object:
                    with self.comment:

                        #Delete previous comment:
                        clear_output()




        #Call function on button_click-event (save input to file):
        orcid_bttn.on_click(on_orcid_bttn_clicked)

        #Return a Vertical Box widget with all the widgets for one author:
        return VBox([HBox([self.orcid_id, orcid_bttn, self.comment]),
                     self.fname, self.lname, self.affiliation, self.email])
################################################################################################

def author_wdgt_form():

    #Create author obj:
    author1 = Author().author_wdgt() 

    #Create button for adding new author widgets:
    add_author_bttn = Button(description='Add author',
                             button_style='warning', # 'success', 'info', 'warning', 'danger' or ''
                             tooltip='Click to add new author',
                             icon='plus',
                             disabled=False)

    #Create button for deleting selected author widget:
    del_author_bttn = Button(description='Remove author',
                             button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                             tooltip='Click to remove selected author',
                             icon='minus',
                             disabled=False)

    #Create output obj to add description:
    author_description = Output()

    with author_description:
        printmd("<p>Fill the fields below with information related to the notebook's authors. Keep in mind that you have to provide information for at least one author.</p><br>")
        
    #Add output widget to store error message:
    err_msg = Output()

    #Add author-widgets to accordion-widget:
    authors = Accordion(children=[author1])

    #Set title to accordion-widget options:
    authors.set_title(0, 'Author 1')

    def on_add_author_bttn_clicked(button_c):
        
        with err_msg:
            
            #Clear content of previous form:
            clear_output()

        #Add author-widget to accordion children-tuple:
        authors.children = authors.children + (Author().author_wdgt(),)

        #Add title:
        authors.set_title(len(authors.children)-1, 'Author '+ str(len(authors.children)))



    def on_del_author_bttn_clicked(button_c):

        with err_msg:

                #Clear content of previous form:
                clear_output()

        #Check list of authors (there has to be at least one author):
        if((len(authors.children)>1) & (isinstance(authors.selected_index, int))):
            
            #Open output widget obj:
            with err_msg:

                #Clear content of previous error message:
                clear_output()

            #Remove an accordion option:
            authors.children[authors.selected_index].close()

            #Tuples are immutable - cannot delete item from tuple.
            #Convert tuple to list:
            authors_ls = list(authors.children)

            #Remove selected accordion child from list:
            authors_ls.remove(authors.children[authors.selected_index])

            #Convert list to tuple and update initial accordion-content:
            authors.children = tuple(authors_ls)

            #Set author accordion-titles:
            for i in range(len(authors.children)):

                authors.set_title(i, 'Author ' + str(i+1))
                
        #If only one description is available:
        elif((len(authors.children)==1)):
            
            with err_msg:

                #Clear content of previous form:
                clear_output()

                printmd("<font color='red'>You cannot remove all authors.<br>You need to add information for at least one author.</font>")


        else:

            with err_msg:

                #Clear content of previous form:
                clear_output()

                printmd("<font color='red'>Please select an author</font>") 


    #Call function on button_click-event (add author):
    add_author_bttn.on_click(on_add_author_bttn_clicked)

    #Call function on button_click-event (remove author):
    del_author_bttn.on_click(on_del_author_bttn_clicked)

    return VBox([author_description, authors, HBox([add_author_bttn, del_author_bttn]), err_msg])
################################################################################################


#Function that returns a dictionary with the stored
#minformation for every notebook creator/author:
def to_dict(creators_wdgt_form):

    return {"creators" : [{'nameType' : 'Personal',
                           'creatorName' : creator.children[2].value +', '+ creator.children[1].value,
                           'schemeURI' : 'https://orcid.org',
                           'nameIdentifierScheme' : 'ORCID',
                           'nameIdentifier' : creator.children[0].children[0].value, #orcid_id
                           'givenName' : creator.children[1].value,
                           'familyName' : creator.children[2].value,
                           'affiliation' : creator.children[3].value,
                           'email' : creator.children[4].value}
                          for creator in creators_wdgt_form.children[1].children]}
################################################################################################


#Function that returns a dictionary with the stored
#minformation for every notebook creator/author:
def clear_fields(creators_wdgt_form):
    
    #Loop through all authors/creators:
    for creator in creators_wdgt_form.children[1].children:
        
        #Restore initial values:
        creator.children[0].children[0].value = '' #orcid
    
        #Delete orcid-related error message (if applicable...):
        with creator.children[0].children[2]:
            clear_output()
        
        #Restore initial values:
        creator.children[1].value = '' #firstname
        creator.children[2].value = '' #lastname
        creator.children[3].value = '' #affiliation
        creator.children[4].value = '' #email
       
    
    #Delete error message (if applicable...):
    with creators_wdgt_form.children[3]:
        
        clear_output()
######################################################################################