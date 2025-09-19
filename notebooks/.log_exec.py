# Standard library imports
import os
from IPython import get_ipython
from pprint import pprint

# Related third party imports.
import requests
import pandas as pd

# Globals
raw_cell_content = None
token = os.getenv("JUPYTERHUB_API_TOKEN")
username = os.getenv("JUPYTERHUB_USER")
server_url = f"http://127.0.0.1:8888/user/{username}"
matomo_url = "https://matomo.icos-cp.eu/matomo.php"
log_file = "/home/jovyan/.stats_log.txt"


def capture_response():
    """Capture the response from the Jupyter server sessions API."""
    try:
        headers = {"Authorization": f"token {token}"}
        resp = requests.get(f"{server_url}/api/sessions", headers=headers)
        notebook = pd.DataFrame(
            [
                {
                    "Notebook": d["notebook"]["name"],
                    "LastActivity": pd.to_datetime(d["kernel"]["last_activity"]),
                }
                for d in resp.json()
            ]
        ).loc[lambda df: df["LastActivity"].idxmax(), "Notebook"]
        payload = {
            "idsite": "10",  # Matomo site ID
            "rec": "1",  # Record the request
            "action_name": f"{username}:{notebook}",
            "url": "https://ganymede.icos-cp.eu",
            "uid": f"{username}:{notebook}",
        }
        requests.get(matomo_url, params=payload)
    except Exception as e:
        with open("/home/jovyan/.stats_log.txt", "a") as f:
            f.write(f"{e}\n---")


def capture_raw_cell_content(info):
    global raw_cell_content
    raw_cell_content = info.raw_cell.strip()


def log_cell_execution(info):
    global raw_cell_content
    if raw_cell_content:
        capture_response()
        raw_cell_content = None


# Register events
ipython = get_ipython()
if ipython:
    ipython.events.register("pre_run_cell", capture_raw_cell_content)
    ipython.events.register("post_run_cell", log_cell_execution)
    print("Cell API logging enabled.")
