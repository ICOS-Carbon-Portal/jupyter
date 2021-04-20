#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""    
    Description:      This file collects the meta data from the underlying computational
                      System. Machine actionable files are created and stored in the output
                      folder. 
"""

__author__      = ["Claudio D'Onofrio"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.0.1"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['info@icos-cp.eu']
__date__        = "2021-04-07"


from ipyfilechooser import FileChooser
from ipywidgets import Output, VBox
from IPython.display import display, Markdown
import os, platform, socket, json, psutil, logging

fc = FileChooser()  

def tab():
    out = Output(layout={'width':'95.0%', 'border': '1px solid grey'})    
    home = os.path.expanduser("~")        
    with out:
        
        explain = ''' Select the main Notebook. The folder containing the Notebook, and all subfolders and files,
        will be included in the publication.<br>
        Please note: Your notenbook must be inside a folder. A Notebook selected directly from 
        your (root) homefolder will not be accepted.'''
        
        # Create and display a FileChooser widget        
        fc.default_path = home
        fc.filter_pattern = '*.ipynb'
        display(Markdown(explain), fc)
        
    return VBox([out])

def get_path():
    return (fc.selected_path, fc.selected_filename)

def convert(folder, fmt='html'):
    """ convert the main notebook to a human readable version """
    p = get_path()
    run = 'jupyter nbconvert ' + os.path.join(p[0],p[1])
    run += ' --to ' + fmt
    run += ' --output-dir ' + folder   
    os.system(run)                                      
    return 

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

def project(folder):
    # collect the project
    # to remove the leading path structure we change directory into the project
    run = 'tar -czf ' + folder + '/project.tar.gz ' + get_path()[0]    
    os.system(run)
        
def docker_info():
    return 'not implemented yet'

