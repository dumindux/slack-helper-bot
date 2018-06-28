"""Tasks"""

import utilities

def execute_task(params, tasks):
    if params[0] in tasks:
        task = tasks[params[0]]

        #switch between different task types and call the appropriate handler
        if task["type"] == "jenkins":
            return execute_jenkins(task, params)
        else:
            return "I am sorry I cannot identify this task"
    else:
        return "I am sorry I cannot identify this task"

def execute_jenkins(task, params):
    if "params" in task:
        all_params = task["params"].split('&') + params[1:]
    else:
        all_params = params[1:]
    try:
        if task["auth"] == "basic":
            response = utilities.rest_request(task, method=task["method"], url=task["url"], auth=(task["username"], task["password"]), params=dict(s.split('=') for s in all_params))
            if response.status_code == 201:
                return "I have executed the task successfully"
            else:
                return "It seems you have provided invalid parameter values"
        if task["auth"] == "crumb":
            crumb_response = utilities.rest_request(task, method="GET", url=task["crumb_url"], auth=(task["username"], task["password"]))
            response = utilities.rest_request(task, method=task["method"], url=task["url"], auth=(task["username"], task["password"]), params=dict(s.split('=') for s in all_params), headers={"Jenkins-Crumb": crumb_response.json()["crumb"]})
            if response.status_code == 201:
                return "I have executed the task successfully"
            else:
                return "It seems you have provided invalid parameter values"
    except Exception:
        return "It seems you have provided invalid parameter values"
