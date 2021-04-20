"""
    This file contains functions in Python that are used
    to extract author information with the ORCID API.
    
"""

__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['jupyter-info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2021-02-25"




############################## Set constants #############################
ORCID_PUBLIC_BASE_URL = 'http://pub.orcid.org/'
BASE_HEADERS = {'Accept':'application/orcid+json'}
##########################################################################



#Fubction that returns author info for a given ORCID:
def get(orcid_id):
    
    """
    Get author info based on ORCID ID.
    """
    
    #Import modules:
    import requests
    
    #In case orcid_id is a URL:
    orcid_id = orcid_id.replace('https://orcid.org/', '')
    
    #Get request response from ORCID:
    resp = requests.get(ORCID_PUBLIC_BASE_URL + orcid_id,
                        headers=BASE_HEADERS)
    
    #Get response in json format:
    json_resp = resp.json()
    
    #Return orcid-info as dict:
    return json_resp



#Function that returns the affiliation of an author for a given ORCID:
def get_orcid_affiliation(orcid_resp):
    
    #Get list of employment records:
    employmentrecords_ls = orcid_resp['activities-summary']['employments']['affiliation-group']
    
    #Get a list of employment records that do not have an end-date:
    current_employment_ls = [(summary['employment-summary']['department-name'],
                              summary['employment-summary']['organization']['name'])
                             for rec in employmentrecords_ls
                             for summary in rec['summaries']
                             if(summary['employment-summary']['end-date']==None)]
    
    #Remove None values from list:
    current_employment_ls = [[i[0], i[1]]
                             if((isinstance(i[0], str)==True)&(isinstance(i[1], str)==True))
                             else [i[1]]
                             if((isinstance(i[0], str)==False)&(isinstance(i[1], str)==True))
                             else [i[0]]
                             if((isinstance(i[0], str)==False)&(isinstance(i[1], str)==False))
                             else [] for i in current_employment_ls]
    
    #Get affiliation:
    affiliation = ', '.join([', '.join(rec) for rec in current_employment_ls])
    
    return affiliation



#Function that returns the name of an author for a given ORCID:
def get_orcid_name(orcid_resp):
    
    #Get first name:
    name = orcid_resp['person']['name']['given-names']['value']
    
    if(isinstance(name, str)==False):
        name = ''
    
    #Return first name:
    return name  


#Function that returns the surname of an author for a given ORCID:
def get_orcid_surname(orcid_resp):
    
    #Get family name:
    surname = orcid_resp['person']['name']['family-name']['value']
    
    if(isinstance(surname, str)==False):
        surname = ''
    
    #Return family name:
    return surname  



#Function that returns the email of an author for a given ORCID:
def get_orcid_email(orcid_resp):
    
    #Initialize variable to store public email(s):
    email_str = ''
    
    #Get list of email addresses:
    email_ls = orcid_resp['person']['emails']['email']
    
    #Check if person has registered any emails that are public:
    if((isinstance(email_ls, list)==True) & (len(email_ls)>0)):
        
        #Extract all registered public email addresses:
        emails = [i['email'] for i in email_ls]
        
        #Convert list to string (string of email addresses)
        email_str = ', '.join(emails)
        
    #Return email address:
    return email_str 