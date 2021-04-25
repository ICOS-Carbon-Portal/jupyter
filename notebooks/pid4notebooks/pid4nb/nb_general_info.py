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
from ipywidgets import Output, VBox, HBox, Dropdown, DatePicker, Text, Textarea, Layout, Combobox
from IPython.display import clear_output

from pid4nb.formats.msg_funcs import printmd
from pid4nb.spdx.licenses import spdx_URl, spdx_get_json, get_spdx_license_ls, license_in_SPDX, licenseURl_in_SPDX
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
        layout = Layout(width='90.6%') #set width and height
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
        self.publisher = Combobox(value='',
                               placeholder='Enter the publisher of the code... (e.g. ICOS Carbon Portal)',
                               options=['ICOS Carbon Portal'],
                               description='Publisher*',
                               #ensure_option=True,
                               style=style,
                               layout=layout2,
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
        self.nb_format = Text(value='',
                              placeholder='Enter file extension or MIME type... (e.g. application/zip or ipynb)',
                              description='Format',
                              style=style,
                              layout=layout2,
                              disabled=False)

        #Add a "notebook version-number" text-box:
        self.version = Text(value='',
                            placeholder='e.g. v.0.1.0',
                            description='Version',
                            style=style,
                            layout=layout3,
                            disabled=False)


        ####Need for multiple rights - different license for data & different for software?) 
        ####What happends if ICOS CP collaborates with an external partner and receives part
        ####of the code in the package from them and they wish to have a different software 
        ####license?
        #Add a "notebook license" text-box: 
        self.rights = Combobox(value='',
                               placeholder='Select or type a license',
                               options=sorted([l['licenseId']
                                               for l in get_spdx_license_ls(spdx_URl,'licenses.json')]),
                               description='License',
                               #ensure_option=True,
                               style=style,
                               layout=layout3,
                               disabled=False)

        #Add a "license URI" text-box: 
        self.rights_url = Combobox(value='',
                                   placeholder='Select or type a license URl',
                                   description='License URl',
                                   #ensure_option=True,
                                   style=style,
                                   layout=layout2,
                                   disabled=False)
        
        def on_change_rights_widget(val):
    
            #Function that checks if the license dictionary
            #includes a URl and, if so, returns it:
            def get_url_ls(l_dict):

                if('seeAlso' in l_dict.keys()):
                    return list(l_dict['seeAlso'])
                else:
                    return []

            #Get dict with license info:
            license_dict = spdx_get_json(spdx_URl, val['new']+'.json')

            #If license dict includes a "seeAlso" key:
            if(len(license_dict)>0):

                #Change options of license-URl combo-widget :
                self.rights_url.options = get_url_ls(license_dict)

                #Check if returning list of URls is empty:
                if(len(get_url_ls(license_dict))>0):
                    self.rights_url.value = get_url_ls(license_dict)[0] #set default value
                else:
                    self.rights_url.value = [] #set default value

            #If license dict does not include a "seeAlso" key:  
            else:
                self.rights_url.options = []
                self.rights_url.value = ''


        #Add event-handler (license/rights widget):
        self.rights.observe(on_change_rights_widget, 'value')
        
        #Create output obj to add a message to the user:
        self.user_msg = Output()

        with self.user_msg:
            
            clear_output()
            
            printmd("<br><p><font color='darkred'>Fields with an asterisk (*) are mandatory</font></p><br>")               
############################################################################################################
    
    #Function that sets the object value-fields
    #to prior initial values:
    def clear(self):
        
        self.title.value = ""
        self.publisher.value = ""
        self.publication_date.value = datetime.now()
        self.subject.value = ""
        self.nb_format.value = ""
        self.version.value = ""
        self.rights.value = ""
        self.rights_url.value = ""
############################################################################################################            
    
    
    #Function that returns a string of the notebook's publication year:
    def publication_year(self):
        
        #Check if publication date is a valid datetime obj:
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
        
        #Check if publication date is a valid datetime obj:
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
        
        #Check if rights-info came from SPDX:
        if((license_in_SPDX(self.rights.value))&
           (licenseURl_in_SPDX(self.rights.value, self.rights_url.value))):
            rights_scheme_URI = 'https://spdx.org/licenses/'
            rights_identifier_scheme = 'SPDX'
        else:
            rights_scheme_URI = ''
            rights_identifier_scheme = ''
            
            
        
        #Create a dictionary to store notebook metadata:
        meta_dict = {"identifier" : '',
                     "identifierType" : 'DOI',
                     "titles" : [{"xml:lang": 'en',
                                 "title" : self.title.value}],
                     "publisher" : self.publisher.value, 
                     "publicationYear" : self.publication_year(), 
                     "subjects" : list(dict.fromkeys(self.subject.value.lower().replace(" ","").split(','))),
                     "dates" : [{"dateType" : "Issued",
                                 "date" : self.publication_date_str()},
                                {"dateType" :  "Available",
                                "date" :  self.publication_date_str()}],
                     "language" : 'en',
                     "resourceType" : 'Jupyter Notebook',
                     "resourceTypeGeneral" : 'ComputationalNotebook', #as of DataCite v.4.4.
                     "size" : '',
                     "formats" : [{"format" : self.nb_format.value}],
                     "version" : self.version.value,
                     "rightsList" : [{"xml:lang": 'en-GB',
                                      "schemeURI" : rights_scheme_URI,
                                      "rightsIdentifierScheme" : rights_identifier_scheme,
                                      "rightsIdentifier" : self.rights.value,
                                      "rightsURI" : self.rights_url.value}]
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
    
    
    
    

    
    