"""
    This folder contains functions in Python that are used
    to extract author information with the ORCID API.
    
"""

__credits__     = "ICOS Carbon Portal"
__license__     = "GPL-3.0"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, Elaborated Products Team"
__email__       = ['info@icos-cp.eu', 'karolina.pantazatou@nateko.lu.se', 'claudio.donofrio@nateko.lu.se']
__date__        = "2021-02-25"


def __zk():
    import os
    import codecs    
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)),'.zksand')
    c=3
    with open(f)as f:
        k=f.read()
        return codecs.decode(k[:-c**c], 'rot_13')
