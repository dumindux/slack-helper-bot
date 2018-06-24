"""Utils"""
import requests

def rest_request(task, method, url, params=None, data=None, headers=None, auth=None):
    print(method,url,params,auth)
    return requests.request(method = method, url = url, params = params, 
    json = data, headers = headers, auth = auth)
