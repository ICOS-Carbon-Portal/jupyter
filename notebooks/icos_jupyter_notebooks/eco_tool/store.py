#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Local storage of reports.
"""

__author__ = ["Anders Dahlner"]
__credits__ = "ICOS Carbon Portal"
__license__ = "GPLv3+"
__version__ = "0.0.1"
__date__ = "2023-06-11"
__maintainer__ = "ICOS Carbon Portal, Elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']

import datetime
import os

if os.getcwd()[-2:] == 'pi':
    import json_handler as json_manager
else:
    from pi import json_handler as json_manager




