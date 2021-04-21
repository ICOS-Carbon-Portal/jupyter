# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 09:16:50 2021

@author: Claudio
"""
import pid4nb
import requests
import os

URL = 'https://zenodo.org/api/deposit/depositions'
PARAMS = {"access_token": pid4nb.__zk()}
HEADERS = {"Content-Type": "application/json"}

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

def create():    
    r = requests.post(URL, params=PARAMS, json={}, headers = HEADERS)
    bucket_url = r.json()["links"]["bucket"]
    return bucket_url

def upload(path, file, bucket):    
    path = os.path.join(path, file)
    with open(path, "rb") as fp:
        r = requests.put("%s/%s" % (bucket, file),data=fp,params=PARAMS)
    r.json()
    
def save(bucket):
    print('not yet')
    
