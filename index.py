import tools
import os 
import logging

def handler(event, context):
    # Initialize response code to None
    response_code = None

    # Extract the action group, api path, and parameters from the prediction
    action = event["actionGroup"]
    api_path = event["apiPath"]
    parameters = event["parameters"]
    httpMethod = event["httpMethod"]

    # Get the query value from the parameters
    query = parameters[0]["value"]
    #datasets = parameters[1]["value"]

    # Check the api path to determine which tool function to call
    if api_path == "/run_sql":
        sql, sql_results = tools.run_sql(query)
        # Create a response body with the result
        response_body = {"application/json": {"body": {"generated_sql_query": str(sql), "sql_query_results" :str(sql_results)}}}
        response_code = 200

    else:
        # If the api path is not recognized, return an error message
        body = {"{}::{} is not a valid api, try another one.".format(action, api_path)}
        response_code = 400
        response_body = {"application/json": {"body": str(body)}}

    # Create a dictionary containing the response details
    action_response = {
        "actionGroup": action,
        "apiPath": api_path,
        "httpMethod": httpMethod,
        "httpStatusCode": response_code,
        "responseBody": response_body,
    }

    # Return the list of responses as a dictionary
    api_response = {"messageVersion": "1.0", "response": action_response}

    return api_response