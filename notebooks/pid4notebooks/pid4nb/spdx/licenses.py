"""
    This file contains functions in Python that are used
    to retrieve license information from SPDX.
    
    For more information on SPDX and what licenses it
    provides metadata about, please visit:
    https://spdx.org/licenses/
    
"""

__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['jupyter-info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2021-04-16"

####################################################################################


#Define SPDX URl (use as constant):
spdx_URl = 'https://spdx.org/licenses/'


####################################################################################

def spdx_get_json(url, json_file):
    
    #Import module:
    import requests
    
    #Create variable to store the response:
    response = []
    
    #Build URL and send request:
    r = requests.get(url+json_file)
    
    #Check if response is valid:
    if(r.ok):
        response = r.json()
    
    #Return response:
    return response
####################################################################################


def get_spdx_license_ls(spdx_url, json_filename):
    
    #Call function to get SPDX license list in JSON:
    spdx_json = spdx_get_json(spdx_URl, json_filename)
    
    if(len(spdx_json)>0):
        #Get a list of dictionaries with license info
        #for non-deprecated licenses:
        licenseList = [license for license in spdx_json['licenses']
                       if(license['isDeprecatedLicenseId']==False)]
    else:
        licenseList = []
    
    return licenseList
####################################################################################    


#Function that takes a license name (string) as input,
#checks if it is included in the SPDX list of licenses
#and returns a boolean value:
def license_in_SPDX(l_str):
    
    if(l_str in [l['licenseId'] for l in get_spdx_license_ls(spdx_URl,'licenses.json')]):
        return True
    else:
        return False
####################################################################################


#Function that takes two strings as input parameters
#(i.e. license name and license URl), checks if they
#are included in the SPDX list of license-URls and
#returns a boolean value:
def licenseURl_in_SPDX(l_str , url):
    
    #Control variable:
    check = False
    
    #Get dict with license info:
    l_dict = spdx_get_json(spdx_URl, l_str+'.json')
    
    #If  SPDX includes info about the given license:
    if(len(l_dict)>0):
        
        #If dictionary includes a "seeAlso"-key with the URl:
        if('seeAlso' in l_dict.keys()):
            url_ls = list(l_dict['seeAlso'])
            
            #Check if input license-url is included:
            if(url in url_ls):
                check = True
        
    #Return control variable:    
    return check
####################################################################################