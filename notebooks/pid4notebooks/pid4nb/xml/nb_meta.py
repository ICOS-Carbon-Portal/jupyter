"""
    This file contains functions in Python that are used
    to convert metadata about a Jupyter notebook from 
    json to xml. The xml file produced is compliant to 
    the DataCite Metadata Schema v.4.4.
    
    For more information on the DataCite Metadata Schema v.4.4,
    please visit:
    https://schema.datacite.org/meta/kernel-4.4/doc/DataCite-MetadataKernel_v4.4.pdf
    
"""

__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['jupyter-info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se']
__date__        = "2021-04-13"


#####################################################################################

#Import modules
import json
import xml.etree.cElementTree as e
from pathlib import Path
#####################################################################################


def json_to_xml(path, jsonfile):
    
    #Create path to json & xml files:
    if(path==''):
        json_file = Path(jsonfile)
        xml_file = "metadata.xml"
    else:
        json_file = Path(path+"/"+jsonfile)
        xml_file = path+"/metadata.xml"

        
    #Check if jsonfile exists:
    try:
        path = json_file.is_file()
        
    #File doesn't exist:
    except FileNotFoundError:
        
        print('Error! Can not find JSON-metadata file...')
        
    #If file exists:
    else:
       
        #Open json-file with metadata:
        with open(json_file) as json_format_file:
            d = json.load(json_format_file)

        #Create XML root element: 
        r = e.Element("resource")

        #Add attributes to root element:
        r.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        r.set('xmlns', 'http://datacite.org/schema/kernel-4')
        r.set('xsi:schemaLocation', 'http://datacite.org/schema/kernel-4 https://schema.datacite.org/meta/kernel-4.4/metadata.xsd')


        #Create subelements to root:
        identifier = e.SubElement(r, "identifier")
        identifier.text = d['identifier'] #add identifier
        identifier.set('identifierType', 'DOI') #add identifier-attribute


        #Add root sub-element which contains sub-elements:
        creators = e.SubElement(r, "creators") #add authors

        ###Create sub-elements to sub-element###
        #Add sub-elements for all authors:
        for c in d["creators"]:
            creator = e.SubElement(creators,"creator")

            creatorName = e.SubElement(creator,'creatorName')
            creatorName.text = c['creatorName']
            creatorName.set('nameType',c['nameType'])

            e.SubElement(creator,'givenName').text = c['givenName']
            e.SubElement(creator,'familyName').text = c['familyName']

            #Check if ORCiD is provided:
            if(c["nameIdentifier"]!=''):
                nameIdentifier = e.SubElement(creator,"nameIdentifier ")
                nameIdentifier.text = c["nameIdentifier"]
                nameIdentifier.set('schemeURI', c['schemeURI'])
                nameIdentifier.set('nameIdentifierScheme', c['nameIdentifierScheme'])

            e.SubElement(creator,'affiliation').text = c['affiliation']


        #Create root sub-element for "titles":
        titles = e.SubElement(r, "titles") 

        #Create sub-elements for "titles":
        for t in d["titles"]:
            title = e.SubElement(titles,"title")
            title.set('xml:lang', t['xml:lang'])
            title.text = t['title']


        #Create root sub-element for "publisher":
        e.SubElement(r, "publisher").text = d['publisher']  


        #Create root sub-element for "publication year":
        e.SubElement(r, "publicationYear").text = d['publicationYear'] 


        #Create root sub-element for "keywords" (i.e. subjects):
        subjects = e.SubElement(r, "subjects") 

        #Create sub-elements for "subjects":
        for s in d["subjects"]:
            e.SubElement(subjects,"subject").text = s


        #contributors...


        #Create root sub-element for "dates":
        dates = e.SubElement(r, "dates") 

        #Create sub-elements for "dates":
        for di in d["dates"]:

            date = e.SubElement(dates,"date")
            date.set('dateType', di['dateType'])
            date.text = di['date']


        #Add root sub-element for "language":
        e.SubElement(r, 'language').text = d['language']


        #Add root sub-element for "resourceType":
        resource_type = e.SubElement(r, 'resourceType')
        resource_type.set('resourceTypeGeneral', d['resourceTypeGeneral']) #add attr for "general"
        resource_type.text = d['resourceType'] #add text for "resourceType"


        #Add root sub-element for "relatedIdentifiers":
        rel_identifiers = e.SubElement(r, 'relatedIdentifiers')

        ###Create sub-elements to sub-element###
        #Add sub-elements for all "relatedIdentifiers":
        for ri in d["relatedIdentifiers"]:

            rel_ident = e.SubElement(rel_identifiers, "relatedIdentifier")
            rel_ident.set('relationType', ri['relationType'])
            rel_ident.set('relatedIdentifierType', ri['relatedIdentifierType'])
            rel_ident.text = ri['relatedIdentifier']


        #Add root sub-element for "formats":
        formats = e.SubElement(r, 'formats')   

        #Create sub-elements for "formats":
        for f in d["formats"]:
            e.SubElement(formats,"format").text = f['format']

        #Add root sub-element for "version":
        e.SubElement(r, 'version').text = d['version']


        #Add root sub-element for "rightsList":
        rightsls = e.SubElement(r, 'rightsList')

        #Create sub-elements for "rightsList":
        for rights in d["rightsList"]:

            right = e.SubElement(rightsls, 'rights') 
            right.set('xml:lang', rights['xml:lang'])
            right.set('schemeURI', rights['schemeURI'])
            right.set('rightsIdentifierScheme', rights['rightsIdentifierScheme'])
            right.set('rightsIdentifier', rights['rightsIdentifier'])
            right.set('rightsURI', rights['rightsURI'])


        #Add root sub-element for "descriptions":
        descriptions = e.SubElement(r, 'descriptions')

        #Create sub-elements for "descriptions":
        for descr in d["descriptions"]:

            description = e.SubElement(descriptions, 'description')
            description.set('xml:lang', descr['xml:lang'])
            description.set('descriptionType', descr['descriptionType'])
            description.text = descr['description']


        #Create XML element tree
        a = e.ElementTree(r)

        #Set encoding before writing XML element-tree to file:
        a.write(xml_file, encoding = "UTF-8", xml_declaration = True)
#####################################################################################