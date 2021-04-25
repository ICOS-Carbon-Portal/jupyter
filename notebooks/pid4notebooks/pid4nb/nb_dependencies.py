#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    
    Description:      Class that creates objects for collecting meta data
                      from the underlying computational System. Machine
                      actionable files are created and stored in the output
                      folder.    
"""

__author__      = ["Claudio D' Onofrio, Karolina Pantazatou"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.0.1"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['info@icos-cp.eu']
__date__        = "2021-04-23"
############################################################################################################

#Import widgets:
import os, platform, socket, json, psutil, logging
from ipywidgets import Output, Button, FileUpload, Layout, VBox, HBox
from ipyfilechooser import FileChooser
from IPython.display import clear_output
from pid4nb.formats.msg_funcs import printmd
############################################################################################################

class NbDependencies():
    
    #Set path:
    home = os.path.expanduser("~")
    
    def __init__(self, home=home):

        #Initialize attributes:
        self.style = {'description_width': '100px'} #Set label format
        self.bttn_style = {'button_color':'#87A7B0'}#Format button widget
        self.layout1 = Layout(width='60.0%') #set width
        self.layout2 = Layout(width='25.0%') #set width
        self.layout3 = Layout(width='10.0%') 
        self.tab_description = Output()
        self.fc = FileChooser() #Create upload-widget
        self.fc.default_path = home
        self.fc.filter_pattern = '*.ipynb'
        self.nb_screenshot_descr = Output(layout=self.layout1)   
        self.upload_scrnshot = FileUpload(accept='image/*',
                                          multiple=False,
                                          description='Upload screenshot',
                                          style=self.style,
                                          layout=self.layout2,
                                          tooltip='Click to upload file')
        self.clear_nb_scrn_bttn = Button(description='   Clear', #Clear notebook screesnhot upload-button content
                                         disabled=False,
                                         button_style='success', 
                                         tooltip='Click to delete "notebook screenshot" uploads',
                                         icon='repeat',
                                         style = self.bttn_style,
                                         layout=self.layout3)
        self.error_msg = '' 
        
        

        #Open output obj to describe the content of this tab to the user:
        with self.tab_description:
            clear_output()
            printmd('Select the main Notebook. The folder containing the Notebook, and all subfolders and files, will be included in the publication.<br><b>Please note:</b> Your notenbook must be inside a folder. A Notebook selected directly from your (root) homefolder will not be accepted.<br><br>')

        #Open output obj to describe the purpose of the screenshot upload-widget to the user:
        with self.nb_screenshot_descr:
            clear_output()
            printmd("<p>Click on the button to add a screenshot of the notebook: </p><br>")
            
        #Function that clears all field entries:
        def on_clear_nb_scrn_bttn(button_c):
            
            self.upload_scrnshot.value.clear() #delete content
            self.upload_scrnshot._counter = 0  #update counter value
            self.upload_scrnshot.value.clear() 
            self.upload_scrnshot._counter = 0
            
            #Delete error message:
            self.error_msg = ''
        
        #Call function on button_click-event:
        self.clear_nb_scrn_bttn.on_click(on_clear_nb_scrn_bttn)   
                    
    ###############################################################################################
    #Function that sets the object value-fields
    #to prior initial values
    #(Needs to be called 2 times to clear content...)
    def clear(self):
        
        #Add functionality to clear notebook-selection from fc (not implemented yet...)
        self.upload_scrnshot.value.clear()#delete content
        self.upload_scrnshot._counter = 0 #update counter value
        self.error_msg = ''               #Delete error message
    ############################################################################################### 
    
    #Function that returns a Vertical Box widget with all the obj's widgets:
    def wdgt_form(self):
        
        return VBox([self.tab_description, self.fc,
                     HBox([self.nb_screenshot_descr, self.upload_scrnshot, self.clear_nb_scrn_bttn])])
    ###############################################################################################
    
    #Check user input:
    def check_nb_screenshot(self):
        
        #Create control variable:
        check = False
        
        #Delete previous error message:
        self.error_msg = ''

        if(self.upload_scrnshot._counter>1):
            self.error_msg='Please upload only one screenshot of the notebook!'
        
        #If all conditions are met:
        else:
            check = True
            self.error_msg = ''
        
        #Return control variable:
        return check
    #################################################################################################
    
    #Function that stores the uploaded files into the
    #notebook metadata folder:
    def to_folder(self, foldername):
        
        #Check if a copy of the NB has been uploaded:
        if(self.upload_scrnshot._counter>0):
            
            #Store uploaded file content:
            uploaded_screenshot = self.upload_scrnshot.value
            screenshot_filename = self.upload_scrnshot.metadata[0]['name']

            #Save copy of notebook in pdf:
            with open(foldername+"/notebook_screenshot."+uploaded_screenshot[screenshot_filename]['metadata']['type'].replace('image/', ''), "wb") as fp:
                fp.write(uploaded_screenshot[screenshot_filename]['content'])
    ########################################################################################################

    def get_path(self):
        return (self.fc.selected_path, self.fc.selected_filename)
    ########################################################################################################
    
    def convert(self, folder, fmt='html'):
        """ convert the main notebook to a human readable version """
        p = self.get_path()
        run = 'jupyter nbconvert ' + os.path.join(p[0],p[1])
        run += ' --to ' + fmt
        run += ' --output-dir ' + folder   
        os.system(run)                                      
        return 
    ########################################################################################################
    
    def project(self, folder):
        # collect the project
        # to remove the leading path structure we change directory into the project
        run = 'tar -czf ' + folder + '/project.tar.gz ' + self.get_path()[0]    
        os.system(run)
############################################################################################################




def freeze(folder):
    """ 
        save machine actionable lists (pip and conda) to 
        create the python environment
    """
    
    #pip
    run = 'pip list --format=freeze > '
    run += '"' + os.path.join(folder, 'pip_requirements.txt') +'"'
    os.system(run)
    #conda
    run = 'conda list -e > '
    run += '"' + os.path.join(folder, 'conda_requirements.txt') +'"'
    os.system(run)
    
    #locallib
    run = 'tar -czf '
    run += '"' + os.path.join(folder, 'locallib.tar.gz" ~/.local/lib/')
    os.system(run)
    


def system_info(folder):
    """
        returns system information as seen by the jupyter notebook
        that is the system from the docker container viewpoint
    """
    try:
        info={}
        info['platform']=platform.system()
        info['platform-release']=platform.release()
        info['platform-version']=platform.version()
        info['architecture']=platform.machine()
        info['hostname']=socket.gethostname()        
        info['processor']=platform.processor()
        info['ram']=str(round(psutil.virtual_memory().total / (1024.0 **3)))+" GB"
        f = os.path.join(folder, 'system.json')
        with open(f,'w') as f:
            f.write(json.dumps(info))
    except Exception as e:
        logging.exception(e)
        
        
def docker_info():
    return 'not implemented yet'

    
    
