# Standard library imports.
from datetime import datetime
import asyncio
import os
# Related third party imports.
from IPython import get_ipython
import nest_asyncio
import requests


# Enable nested event loops in Jupyter Notebook
nest_asyncio.apply()

raw_cell_content = None

async def log_event():
    matomo_url = "https://matomo.icos-cp.eu/matomo.php"
    payload = {
        'idsite': '10',  # Matomo site ID
        'rec': '1',  # Record the request
        'action_name': 'cell execution',
        'url': 'https://ganymede.icos-cp.eu',
        'uid': os.getenv('JUPYTERHUB_USER').replace('-', '_'),
    }
    requests.get(matomo_url, params=payload)

def capture_raw_cell_content(info):
    global raw_cell_content
    raw_cell_content = info.raw_cell.strip()

def log_cell_execution(info):
    global raw_cell_content
    if raw_cell_content is not None:
        asyncio.run(log_event())
        raw_cell_content = None

ipython = get_ipython()
if ipython:
    ipython.events.register('pre_run_cell', capture_raw_cell_content)
    ipython.events.register('post_run_cell', log_cell_execution)
