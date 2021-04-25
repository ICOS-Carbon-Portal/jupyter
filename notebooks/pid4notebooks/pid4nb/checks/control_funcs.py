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


########################################################################################


#Function that checks if a single author entry is valid:
def check_author_entry(a_dict):
    
    #Get a list of the author numbers for entries that are invalid:
    wrong_entry_ls = ['Author '+str(i+1) for i in range(len(a_dict['creators']))
                      if not(((a_dict['creators'][i]['nameIdentifier']!='')&
                              (a_dict['creators'][i]['email']!='')) |
                             ((a_dict['creators'][i]['givenName']!='') &
                              (a_dict['creators'][i]['familyName']!='') &
                              (a_dict['creators'][i]['email']!='')))]

    #Return list of author numbers that
    #correspond to invalid entries:
    return wrong_entry_ls
########################################################################################


#Function that checks for duplicate author entries:
def check_author_duplicates(authors_dict):
    
    #Import module:
    from collections import Counter
    
    #Get a dictionary describing the number of author entries
    #with the same email address:
    auth_counter = Counter([c['email'] for c in authors_dict['creators'] if c['email']!='' ])
    
    #Return a list of email-addresses that appear more than once:
    return [a for a in auth_counter if auth_counter[a]>1]
########################################################################################


#Function that checks for duplicate description entries:
def check_descriptions(descr_dict):
    
    #Import module:
    from collections import Counter

    #Get a dictionary describing the number of entries per description category:
    counter = Counter([d['descriptionType'] for d in descr_dict['descriptions']])
    
    #Return a list of the names of the description-categories
    #that have more than one entries:
    return [c for c in counter if counter[c]>1]
########################################################################################


#Function that checks for duplicate related-identifier-entries:
def check_rel_ident(i_dict):
    
    #Import module:
    from collections import Counter
    
    #Get a dictionary describing the number of entries per trinity of
    #(relatedIdentifier, relatedIdentifierType, relationType):
    counter = Counter([(d['relatedIdentifier'], d['relatedIdentifierType'], d['relationType'])
                       for d in i_dict['relatedIdentifiers']])
    
    #Return a list of tuples with multiple entries of the same trinity
    #of (relatedIdentifier, relatedIdentifierType, relationType):
    return [c for c in counter if counter[c]>1]
########################################################################################


#Function that checks the user input in the PID4NB GUI:
def check_meta_entries(rel_d, nb_title, nb_publisher, nb_description, nb_authors, nb_rel_ident, nb_dependencies, form_out):
    
    import datetime
    from IPython.display import clear_output
    from pid4nb.formats.msg_funcs import printmd

    #Initialize control variables:
    check_title = False
    check_publisher = False
    check_dates = False
    check_uploads = False
    author_check = False
    author_duplicate_check = False
    check_rel_ident_duplicates = False
    check_descr = False
    
    #Delete previous error messages:
    with form_out:
        clear_output()
   ##############################################################    
    
    
    #Check if notebook has a title:
    if(nb_title==''):
        with form_out:
            #Prompt error message:
            printmd('<font color=darkred>Please enter a title for the notebook!</font>')
    else:
        #Set control variable to true:
        check_title = True
    
    
    #Check if notebook has a title:
    if(nb_publisher==''):
        with form_out:
            #Prompt error message:
            printmd('<font color=darkred>Please add publisher!</font>')
    else:
        #Set control variable to true:
        check_publisher = True
        
        
    #If release and update dates have been entered:
    if (isinstance(rel_d, datetime.date)):
        #Set control variable to true:
        check_dates = True
    #If release and/or update dates have not been entered:
    else:
        with form_out:
            #Prompt error message:
            printmd('<font color=darkred>Please select a date for the release and/or update!</font>')
    
    
    #Must include info for at least one author:
    if((len(nb_authors['creators'])>=1)&(len(check_author_entry(nb_authors))==0)):
        author_check = True
    else:
        with form_out:
            #Prompt error message:
            printmd('<font color=darkred>'+'Check entries for: '+ ','.join(check_author_entry(nb_authors))+'</font>')
   
        
    #Check author entries for duplicates:
    if (len(check_author_duplicates(nb_authors))==0):
        author_duplicate_check = True
    else:
        with form_out:
            #Prompt error message:
            printmd('<font color=darkred>'+'Check author entries. The following email addresses appear more than once: '+ ','.join(check_author_duplicates(nb_authors))+'</font>')
    
    
    #Check related-identifier-entries for duplicates:
    if(len(check_rel_ident(nb_rel_ident))==0):
        check_rel_ident_duplicates = True

    else:
        with form_out:
            #Prompt error message:
            printmd('<font color=darkred><br> Attention! Duplicate related identifier entries: </font>')
            
            for ri in check_rel_ident(nb_rel_ident):
                printmd('<font color=black>'+'Identifier: %s, IdentifierType: %s, Relation: %s' %(ri[0], ri[1],ri[2])+'</font>')
    
    
    #Check for duplicate description entries:
    if(len(check_descriptions(nb_description))==0):
        check_descr = True
    else:
        with form_out:
            #Prompt error message:
            for descr in check_descriptions(nb_description):
                printmd('<font color=darkred>There are more than one description categories titled: ' + descr+'</font>')
    
    
    #Check dependencies/uploads:
    if(nb_dependencies.check_nb_screenshot()):
        check_uploads = True
    else:
        #Open output obj:
        with form_out:
            #Prompt error message:
            printmd('<font color=darkred>'+nb_dependencies.error_msg+'</font>')
    
    ##############################################################
    
    #Cummulative check of all conditions:
    if (check_dates & check_title & check_publisher & author_check & author_duplicate_check & check_rel_ident_duplicates & check_descr & check_uploads):
        
        return True
    
    else:
        return False
#######################################################################################################