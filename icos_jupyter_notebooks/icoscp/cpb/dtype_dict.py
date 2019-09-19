#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Created on Fri Aug  9 10:40:27 2019
    Helper functions to translate between
    data type from IOCOS, Numpy, Struct
"""

__author__ = "Claudio D'Onofrio"
__credits__ = ["ICOS Carbon Portal Dev Team"]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Claudio D'Onofrio"
__email__ = ["claudio.donofrio at nateko.lu.se", 'info@icos-cp.eu']
__status__ = "Development"



#-----------------------------------------------------------------------
def structTypes(columnDescriptor, repeat=1):
    """ create the format descriptor to read binary data
        the data types and order are documented in 
        https://docs.python.org/2/library/struct.html
        :param columnDescriptor (output form function mapDataTypesCP)        
        :param repeat (int) (how many time the same format is read)        
    """
    dictionary = {
			'FLOAT':'f',
			'DOUBLE':'d',
			'CHAR': 'h',
			'INT':'i',
			'STRING': 's'
			}
    return str(repeat) + dictionary.get(columnDescriptor)
#-----------------------------------------------------------------------
def structEndian(endianness='big'):
    """:param endianness (str) 
        return: str the code how "struct" is interpreting the bin data
        default is big endiann
    """
    dictionary = {
            '@': '@',
            'native': '@',
            '=': '=',
            'standard': '=',
            '<': '<',
            'little':'<',
            '>': '>',
            'big': '>',
            '!': '!',
            'network': '!'
            }
    return dictionary.get(endianness)    
#-----------------------------------------------------------------------    
def numpyTypes(columnDescriptor, repeat=1):
    """ Convert numerical descriptor to numpy.dtype object
    
        :param columnDescriptor (output form function mapDataTypesCP)
        :param repeat (int) (how many time the same format is read)
        output numpy.dtype
        https://docs.scipy.org/doc/numpy-1.13.0/user/basics.types.html
    """
    dictionary = {
			'FLOAT':'float32',
			'DOUBLE':'float64',
			'CHAR': 'int16',
			'INT':'int32'			
			}
    return str(repeat) + dictionary.get(columnDescriptor)
#-----------------------------------------------------------------------
def numpyEndian(endianness='big'):
    dictionary = {
            'native':'=',
            '<': '<',
            'little':'<',
            '>': '>',
            'big': '>',
            }
    return dictionary.get(endianness)

#-----------------------------------------------------------------------
def mapDataTypesCP(valueFormatUrl):
    """ Convert meta data descriptor to numerical descriptor
    
        :param valueFormatUrl = full url to the description
            example: https://meta.icos-cp.eu/ontologies/cpmeta/float32
        return: numerical descriptor to build schema to send a post
        request for retrieving binary data.
    """
    dictionary = {
			'float32': 'FLOAT',
			'float64': 'DOUBLE',
			'bmpChar': 'CHAR',
			'etcDate': 'INT',
			'iso8601date':'INT',
			'iso8601timeOfDay':'INT',
			'iso8601dateTime': 'DOUBLE',
			'isoLikeLocalDateTime' : 'DOUBLE',
			'etcLocalDateTime': 'DOUBLE',
			'int32':'INT',
			'string':'STRING'
			}
    return dictionary.get(valueFormatUrl.split('/')[-1], False)
#-----------------------------------------------------------------------