# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 09:16:50 2021

@author: Claudio
"""
import pid4nb
import requests, json
import os

URL = 'https://zenodo.org/api/deposit/depositions'
PARAMS = {"access_token": pid4nb.__zk()}
HEADERS = {"Content-Type": "application/json"}
BUCKET  = 'bucket.json'
# To test, redirect to sandbox
URL = 'https://sandbox.zenodo.org/api/deposit/depositions'

def get(q=''):
    ''' default get all depositions back 
        otherwise search for q
        q = elastic search expression
        https://developers.zenodo.org/#representation
    '''
    param = PARAMS # leave the constant alone..
    if q:
        param['q'] = q        
    r = requests.get(URL,params=param)
    return r.json()

def create(folder):
    # create a new bucket at zenodo, and save json to folder as
    # bucket.json
    
    # check if bucket exists
    if os.path.isfile(os.path.join(folder, BUCKET)):
        return 
    
    r = requests.post(URL, params=PARAMS, json={}, headers = HEADERS)    
    fn = os.path.join(folder, BUCKET)
    with open(fn, 'w') as f:
        json.dump(r.json(), f)
    return

def upload(folder):
    # folder is the 'output' folder from gui processing, containing all the
    # files to be added to the bucket. 
    url = read_bucket(folder)['links']['bucket']
    files = os.listdir(folder)
    for f in files:
        path = os.path.join(folder, f)
        with open(path, "rb") as data:
            requests.put("%s/%s" % (url, f),data=data, params=PARAMS)
    return

def file_list(folder):
    url = read_bucket(folder)['links']['files']
    r = requests.get(url, params=PARAMS, json={}, headers = HEADERS)   
    return r.json()


def read_bucket(folder):
    fn = os.path.join(folder, BUCKET)    
    with open(fn, 'r') as f:
        return json.load(f)
    
