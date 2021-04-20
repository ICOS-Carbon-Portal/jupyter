

#Import modules:
from ipywidgets import Layout, Text, Dropdown, HBox, VBox, Button, Accordion, Output
from IPython.display import clear_output
from pid4nb.formats.msg_funcs import printmd
######################################################################################


class RelatedIdentifiers():
    
    """
    Description: Class that stores information about identifiers of resources 
                 that are related to the current Jupyter notebook
                 (e.g. previous version of notebook, article, datasets, etc.)
                 More in particular, for every "related identifier"/resource
                 the user needs to enter the following information:
                 1. Alphanumerical text describing the identifier
                    (text: e.g. DOI-string)
                 2. Identifier type (e.g. DOI, URL, etc.)
                 3. How the identifier is related to the notebook
                    (e.g. IsNewVersionOf, IsCitedBy, IsPublishedIn, Compiles, etc.)
    
    """
    
       
    
    #Initialize object:
    def __init__(self):
        
        #Set label format:
        style = {'description_width': '100px'}

        #Set widget format:
        layout1 = Layout(width='90.4%') #set width 
        layout2 = Layout(width='45.0%') #set width 
        #layout3 = Layout(width='30.0%') #set width and height
        
        #########################
        ### Object attributes ###
        #########################

        #Add "related identifier" text-box:
        self.identifier = Text(value='',
                               placeholder="Enter string of related identifier...",
                               description='Related identifier',
                                    style=style,
                                    layout=layout1,
                                    disabled=False)

        #Add related identifier "type" dropdown:
        self.identifier_type = Dropdown(options=['ARK', 'arXiv', 'bibcode','DOI',
                                                 'EAN13', 'EISSN', 'Handle', 'IGSN',
                                                 'ISBN', 'ISSN', 'ISTC', 'LISSN',
                                                 'LSID', 'PMID', 'PURL', 'UPC', 'URL',
                                                 'URN', 'w3id'],
                                         value='ARK',
                                         description='Identifier type',
                                         style=style,
                                         layout=layout2,
                                         disabled=False)
        
        #Add related identifier "relation type" dropdown:
        self.relation_type = Dropdown(options=['IsCitedBy', 'Cites', 'IsSupplementTo',
                                                 'IsSupplementedBy', 'IsContinuedBy',
                                                 'Continues', 'IsDescribedBy', 'Describes',
                                                 'HasMetadata', 'IsMetadataFor', 'HasVersion',
                                                 'IsVersionOf', 'IsNewVersionOf', 'IsPreviousVersionOf',
                                                 'IsPartOf', 'HasPart', 'IsPublishedIn', 'IsReferencedBy',
                                                 'References', 'IsDocumentedBy', 'Documents', 
                                                 'IsCompiledBy','Compiles',
                                                 'IsVariantFormOf', 'IsOriginalFormOf', 'IsIdenticalTo',
                                                 'IsReviewedBy', 'Reviews', 'IsDerivedFrom', 'IsSourceOf',
                                                 'IsRequiredBy', 'Requires', 'IsObsoletedBy', 'Obsoletes'],
                                         value='IsCitedBy',
                                         description='Relation type',
                                         style=style,
                                         layout=layout2,
                                         disabled=False)
        
######################################################################################


    #Function that creates a single "notebook related identifier" widget set:
    def create_wdgt(self):
        
        return VBox([self.identifier, HBox([self.identifier_type, self.relation_type])])
######################################################################################


def create_wdgt_form():
    
    #Organize the object's widgets to a form:
    rel_ident_wdgt = RelatedIdentifiers().create_wdgt()
    
    #Set button layout:
    layout_btn = Layout(width='20.0%') #set width and height

    #Create button for adding a new identifier widget set:
    add_ident_bttn = Button(description='Add related identifier',
                                button_style='warning',
                                tooltip='Click to add new identifier',
                                icon='plus',
                                layout=layout_btn,
                                disabled=False)

    #Create button for deleting selected identifier widget set:
    del_ident_bttn = Button(description='Remove related identifier',
                                button_style='danger',
                                tooltip='Click to remove selected identifier',
                                icon='minus',
                                layout=layout_btn,
                                disabled=False)

    #Create output obj to add a message to the user:
    user_msg = Output()

    #Open output object:
    with user_msg:

        #Delete previous message:
        clear_output()

        #Add message to user:
        printmd("<p>The fields below provide you with the opportunity to add information about resources that are related to your notebook. For every resource you should add its corresponding identifier (e.g. DOI), the type of the identifier and how it is related to your notebook. Note that there are many different kinds of identifier types as well as relation types. For more information regarding what those types are and what they represent, have a look at the <a href='https://schema.datacite.org/meta/kernel-4.4/doc/DataCite-MetadataKernel_v4.4.pdf'>DataCite metadata documentation</a>.</p><br>")

    #Create output obj to add an error message to the user:
    error_msg = Output()

    #Add identifier-widgets to accordion-widget:
    identifiers = Accordion(children=[rel_ident_wdgt])

    #Set title to accordion-widget options:
    identifiers.set_title(0, 'Related identifier 1')


    #Add function to handle button-click (add identifier): 
    def on_add_ident_bttn_clicked(button_c):
        
        
        with error_msg:
            
            #Clear content of previous form:
            clear_output()

        #Add identifier-widget-set to accordion children-tuple:
        identifiers.children = identifiers.children + (RelatedIdentifiers().create_wdgt(),)

        #Add title:
        identifiers.set_title(len(identifiers.children)-1, 'Related identifier '+ str(len(identifiers.children)))


    #Add function to handle button-click (delete identifier): 
    def on_del_ident_bttn_clicked(button_c):

        with error_msg:

                #Clear content of previous msg:
                clear_output()

        #Check list of identifiers (there has to be at least one identifier):
        if((len(identifiers.children)>1) & (isinstance(identifiers.selected_index, int))):

            #Remove an accordion option:
            identifiers.children[identifiers.selected_index].close()

            #Tuples are immutable - cannot delete item from tuple.
            #Convert tuple to list:
            identifiers_ls = list(identifiers.children)

            #Remove selected accordion child from list:
            identifiers_ls.remove(identifiers.children[identifiers.selected_index])

            #Convert list to tuple and update initial accordion-content:
            identifiers.children = tuple(identifiers_ls)

            #Set identifier accordion-titles:
            for i in range(len(identifiers.children)):

                identifiers.set_title(i, 'Related identifier ' + str(i+1))
        
        #If only one identifier is available:
        elif((len(identifiers.children)==1)):
            
            with error_msg:

                #Clear content of previous form:
                clear_output()

                printmd("<font color='red'>You cannot remove all related identifiers.<br>You need to add at least one related identifier.</font>")
            

        else:

            with error_msg:

                #Clear content of previous form:
                clear_output()

                printmd("<font color='red'>Please select a related identifier</font>") 



    #Call function on button_click-event (add description):
    add_ident_bttn.on_click(on_add_ident_bttn_clicked)

    #Call function on button_click-event (remove description):
    del_ident_bttn.on_click(on_del_ident_bttn_clicked)

    return VBox([user_msg, identifiers, HBox([add_ident_bttn, del_ident_bttn]), error_msg])
######################################################################################


#Function that deletes the user entries in the widget fields:
def clear_fields(wdgt_form):
    
    #Loop through all descriptions:
    for ident in wdgt_form.children[1].children:
        
        #Set initial values:
        ident.children[0].value = '' #related identifier
        ident.children[1].children[0].value = 'ARK' #identifier type
        ident.children[1].children[1].value = 'IsCitedBy' #identifier relation
    
    #Delete error message (if applicable...):
    with wdgt_form.children[3]:
        
        clear_output()
######################################################################################


#Function that returns a dictionary with the values for the separate
#description widget fields:
def to_dict(wdgt_form):
    
    #Create dictionary to store metadata about the descriptions:  
    meta_dict ={"relatedIdentifiers" : [{'relatedIdentifier' : ident.children[0].value,
                                         'relatedIdentifierType' : ident.children[1].children[0].value,
                                         'relationType' : ident.children[1].children[1].value}
                                        for ident in wdgt_form.children[1].children]}  
    
    #Return disctionary:
    return meta_dict
######################################################################################   