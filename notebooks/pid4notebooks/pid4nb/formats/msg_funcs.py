"""
    This file contains functions in Python that are used
    to format strings that are prompted as error messages.
    
"""

__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['jupyter-info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2021-02-25"



def printmd(string):
    
    """
    Project:         'ICOS Carbon Portal'
    Created:          Fri May 10 12:00:00 2019
    Last Changed:     Fri May 10 12:00:00 2019
    Version:          1.0.0
    Author(s):        Karolina Pantazatou
    
    Description:      Function that allows you to print the string input parameter using
                      markdown formatting code.
                      
    Input parameters: String of characters
                      (var_name: 'string', var_type: String)

    Output:           String     
    
    """
    
    #import module:
    from IPython.display import Markdown, display
    
    #Enable displaying string with markdown code:
    display(Markdown(string))