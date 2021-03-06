"""Utils"""
import requests

def rest_request(method, url, params=None, data=None, headers=None, auth=None):
    """
        Executes an HTTP request
        
        Args:
            method: HTTP method
            url: HTTP url
            params: Query parameters
            json: JSON body
            headers: HTTP headers
            auth: Authorization information

        Returns:
            Message to be sent to the user
    """
    return requests.request(method=method, url=url, params=params,
                            json=data, headers=headers, auth=auth)
