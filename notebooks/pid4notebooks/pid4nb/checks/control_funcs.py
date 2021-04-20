"""
    This file contains functions in Python that are used
    to check the input parameters of the notebook metadata
    tab in the pid4nb wizard's widget form.
    
"""

__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['jupyter-info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2021-02-25"



def check_meta_entries(rel_d, nb_title, form_out):
    
    import datetime
    from IPython.display import clear_output
    from pid4nb.formats.msg_funcs import printmd

    #Initialize control variables:
    check_dates = False
    check_title = False

    #If release and update dates have been entered:
    if (isinstance(rel_d, datetime.date)):

        #Set control variable to true:
        check_dates = True

    #If release and/or update dates have not been entered:
    else:
        
        with form_out:
            
            clear_output()
            
            #Prompt error message:
            printmd('<font color=darkred>Please select a date for the release and/or update!</font>')
    
    #Check if notebook has a title:
    if(nb_title==''):
        
        with form_out:
            
            clear_output()
            
            #Prompt error message:
            printmd('<font color=darkred>Please enter a title for the notebook!</font>')
    
    else:
        
        #Set control variable to true:
        check_title = True
        
    if (check_dates & check_title):
        
        return True
    
    else:
        return False