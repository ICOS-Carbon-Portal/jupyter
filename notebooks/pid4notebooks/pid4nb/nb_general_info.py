#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    
    Description:      Class that creates objects for storing general metadata about a notebook.
                      
    
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
from datetime import datetime, date
from ipywidgets import Output, VBox, HBox, Dropdown, DatePicker, Text, Textarea, Layout
from IPython.display import clear_output

from pid4nb.formats.msg_funcs import printmd
############################################################################################################



class NbGeneralInfo():
    
    """
    Description: Class that stores general information about a Jupyter notebook.
                 This metadata is mandatory information for every ICOS notebook.
                 More in particular, the metadata describe the following
                 notebook-related variables:
                 1.  Description
                 2.  Title
                 3.  Publisher
                 4.  Date of publication
                 5.  Subject (e.g. list of comma-separated keywords)
                 6.  Format
                 7.  Version
                 8.  Size
                 9.  Rights
                 10. Rights URL
                 11. User message
    
    """
    
       
    
    #Initialize object:
    def __init__(self):
        
        #Set label format:
        style = {'description_width': '100px'}

        #Set widget format:
        layout = Layout(width='90.4%') #set width and height
        layout2 = Layout(width='60.0%') #set width and height
        layout3 = Layout(width='30.0%') #set width and height
        
        #########################
        ### Object attributes ###
        #########################
        
        #Create output obj to add description:
        self.gen_info_description = Output()

        with self.gen_info_description:
            clear_output()
            printmd("<p>Add general information about your notebook by entering values in the fields below.</p><br>")
        
        #Add notebook title text-widget:
        self.title = Text(value="",
                          placeholder="Enter notebook title...",
                          description="Title*",
                          layout=layout,
                          style=style,
                          disabled=False)    

        #Add "publisher" text-box:
        self.publisher = Text(value='',
                              placeholder='Enter the publisher of the code... (e.g. ICOS Carbon Portal)',
                              description='Publisher*',
                              layout=layout2,
                              style=style,
                              disabled=False)

        #Add "date of publication" date-picker:
        self.publication_date = DatePicker(value=datetime.now(),
                                           description='Publication date*',
                                           layout=layout3,
                                           style=style,
                                           disabled=False)

        #Add "keywords" text-area-box:
        self.subject = Textarea(value='',
                                placeholder="Enter keywords separated by a comma...",
                                description='Keywords',
                                style=style,
                                layout=layout,
                                disabled=False)  

        #Add "notebook file format" dropdown:
        self.nb_format = Dropdown(options=['ipynb', 'py'],
                                  value='ipynb',
                                  description='Format',
                                  style=style,
                                  layout=layout3,
                                  disabled=False)

        ####Should this field be automatically filled once the
        ####zipped folder is created, to reflect the size of the 
        ####entire "package" ??? -perhaps better for this case...
        #Add "resource size (e.g. in kilobytes)" text-box:
        #self.size = Text(value='',
                         #placeholder='Enter size in e.g. kilobytes...',
                         #description='Size',
                         #style=style,
                         #layout=layout3,
                         #disabled=False)

        #Add a "notebook version-number" text-box:
        self.version = Text(value='',
                            placeholder='Enter version number...',
                            description='Version',
                            style=style,
                            layout=layout2,
                            disabled=False)


        ####Need for multiple rights - different license for data & different for software?) 
        ####What happends if ICOS CP collaborates with an external partner and receives part
        ####of the code in the package from them and they wish to have a different software 
        ####license?
        #Add a "notebook license" text-box: 
        self.rights = Text(value='',
                           placeholder='Enter software license ...',
                           description='Rights',
                           style=style,
                           layout=layout3,
                           disabled=False)

        #Add a "license URI" text-box: 
        self.rights_url = Text(value='',
                               placeholder='Enter the URI of the license... (e.g. https://www.gnu.org/licenses/gpl-3.0.en.html)',
                               description='Rights URI',
                               style=style,
                               layout=layout2,
                               disabled=False)
        
        #Create output obj to add a message to the user:
        self.user_msg = Output()

        with self. user_msg:
            
            clear_output()
            
            printmd("<br><p><font color='darkred'>Fields with an asterisk (*) are mandatory</font></p><br>")               
############################################################################################################
    
    #Function that sets the object value-fields
    #to theor initial values:
    def clear(self):
        
        self.title.value = ""
        self.publisher.value = ""
        self.publication_date.value = datetime.now()
        self.subject.value = ""
        self.nb_format.value = "ipynb"
        self.version.value = ""
        #self.size.value = ""
        self.rights.value = ""
        self.rights_url.value = ""
############################################################################################################            
    
    
    #Function that returns a string of the notebook's publication year:
    def publication_year(self):
        
        #Check if piblication date is a valid datetime obj:
        if(isinstance(self.publication_date.value, date)):
            
            #Extract year from datetime obj:
            year_str = str(self.publication_date.value.year)
        
        #If no date has been selected in the widget:
        else:
            year_str = ""
        
        #Return variable with the notebook's publication year:
        return year_str
   ############################################################################################################         
       
    
    #Function that returns a string of the notebook's publication date:
    def publication_date_str(self):
        
        #Check if piblication date is a valid datetime obj:
        if(isinstance(self.publication_date.value, date)):
            
            #Extract year from datetime obj:
            date_str = self.publication_date.value.strftime("%Y-%m-%d")
        
        #If no date has been selected in the widget:
        else:
            date_str = ""
        
        #Return variable with the notebook's publication date:
        return date_str     
############################################################################################################


    #Function that returns a dictionary of the object's
    #notebook-related metadata values:
    def to_dict(self):
        
        #Create a dictionary to store notebook metadata:
        meta_dict = {"title" : self.title.value,
                     "publisher" : self.publisher.value, 
                     "publicationYear" : self.publication_year(), 
                     "subjects" : self.subject.value.replace(" ","").split(','),
                     "dateIssued" :  self.publication_date_str(),
                     "dateAvailable" :  self.publication_date_str(),
                     "language" : 'en',
                     "resourceType" : 'Jupyter notebook',
                     "resourceTypeGeneral" : 'Software',
                     "size" : '',
                     "format" : self.nb_format.value,
                     "version" : self.version.value,
                     "rights" : self.rights.value,
                     "rightsURI" : self.rights_url.value
                    }
        
        #Return dictionary with notebook metadata:
        return meta_dict
############################################################################################################        
    
    
    #Function that returns a Vertical Box widget with all the obj's widgets:
    def general_info_wdgt(self):

        return VBox([self.gen_info_description,
                     self.title,
                     HBox([self.publisher, self.publication_date]),
                     self.subject,
                     HBox([self.nb_format, self.version]),
                     HBox([self.rights, self.rights_url]), self.user_msg])
############################################################################################################ 
    
    
    
    

    
    