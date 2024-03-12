import json
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import time
import csv
from io import StringIO
import logging
import os

# initialize clients
datazone = boto3.client('datazone')
athena_client = boto3.client('athena')
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)
bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime",
                              config=bedrock_config)
bedrock_agent_client = boto3.client('bedrock-agent')

# get Athena query result location
outputLocation = os.environ['ATHENA_QUERY_LOCATION']
# get Bedrock knowledge base name to identify knowledge base id
kbName = os.environ['KNOWLEDGEBASE_NAME']

# get knowledge base id
paginator = bedrock_agent_client.get_paginator('list_knowledge_bases')
response_iterator = paginator.paginate()
for page in response_iterator:
    for kb in page['knowledgeBaseSummaries']:
        if kb['name'] == kbName:
            knowledge_base_id = kb['knowledgeBaseId']

def retrieveKBreferences(query, model_id = "anthropic.claude-v2", region_id = "us-east-1"):
    model_arn = f'arn:aws:bedrock:{region_id}::foundation-model/{model_id}'

    response = bedrock_agent_runtime_client.retrieve_and_generate(
        input={
            'text': query
        },
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': knowledge_base_id,
                'modelArn': model_arn
            }
        },
    )
    print(f'knowledge base search response: {response}')
    citations = response["citations"]
    contexts = []
    for citation in citations:
        retrievedReferences = citation["retrievedReferences"]
        for reference in retrievedReferences:
            contexts.append(reference["content"]["text"])

    return contexts
    
def claude_prompt_format(prompt: str) -> str:
    # Add headers to start and end of prompt
    return "\n\nHuman: " + prompt + "\n\nAssistant:"


def call_claude(prompt):
    prompt_config = {
        "prompt": claude_prompt_format(prompt),
        "max_tokens_to_sample": 4096,
        "temperature": 0,
        "top_k": 250,
        "top_p": 0.999,
        "stop_sequences": [],
    }

    body = json.dumps(prompt_config)

    modelId = "anthropic.claude-v2"
    accept = "application/json"
    contentType = "application/json"

    response = bedrock_runtime.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )
    response_body = json.loads(response.get("body").read())

    results = response_body.get("completion")
    return results


# Call Titan model
def call_titan(prompt):
    prompt_config = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 4096,
            "stopSequences": [],
            "temperature": 0.7,
            "topP": 1,
        },
    }

    body = json.dumps(prompt_config)

    modelId = "amazon.titan-text-lite-v1"
    accept = "application/json"
    contentType = "application/json"

    response = bedrock_runtime.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )
    response_body = json.loads(response.get("body").read())
    results = response_body.get("results")[0].get("outputText")
    return results

def get_schema(database_name, table_names):
    try:
        glue_client = boto3.client('glue') 
        table_schema_list=[]
        response = glue_client.get_tables(DatabaseName=database_name)
        
        table_names = [table['Name'] for table in response['TableList']]
        for table_name in table_names:
            response = glue_client.get_table(DatabaseName=database_name, Name=table_name)
            columns = response['Table']['StorageDescriptor']['Columns']
            schema = {column['Name']: column['Type'] for column in columns}
            table_schema_list.append({"Table: {}".format(table_name): 'Schema: {}'.format(schema)})
    except Exception as e:
        print(f"Error: {str(e)}")
    return table_schema_list

def execute_athena_query(database, query):
    # Start query execution
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': database
        },
        ResultConfiguration={
            'OutputLocation': outputLocation
        }
    )

    # Get query execution ID
    query_execution_id = response['QueryExecutionId']
    print(f"Query Execution ID: {query_execution_id}")

    # Wait for the query to complete
    response_wait = athena_client.get_query_execution(QueryExecutionId=query_execution_id)

    while response_wait['QueryExecution']['Status']['State'] in ['QUEUED', 'RUNNING']:
        print("Query is still running...")
        response_wait = athena_client.get_query_execution(QueryExecutionId=query_execution_id)

    print(f'response_wait {response_wait}')

    # Check if the query completed successfully
    if response_wait['QueryExecution']['Status']['State'] == 'SUCCEEDED':
        print("Query succeeded!")

        # Get query results
        query_results = athena_client.get_query_results(QueryExecutionId=query_execution_id)

        # Extract and return the result data
        code = 'SUCCEEDED'
        return code, extract_result_data(query_results)

    else:
        print("Query failed!")
        code = response_wait['QueryExecution']['Status']['State']
        message = response_wait['QueryExecution']['Status']['StateChangeReason']
    
        return code, message

def extract_result_data(query_results):
    #Return a cleaned response to the agent
    result_data = []

    # Extract column names
    column_info = query_results['ResultSet']['ResultSetMetadata']['ColumnInfo']
    column_names = [column['Name'] for column in column_info]

    # Extract data rows
    for row in query_results['ResultSet']['Rows']:
        data = [item['VarCharValue'] for item in row['Data']]
        result_data.append(dict(zip(column_names, data)))

    return result_data

def generate_sql(query, sqlerrormessage = "", db = "", schema=""):
    table_information = ""
    if sqlerrormessage == "":
        # use LLM to extract main entities from query
        prompt = f"""Extract main entities and metrics from the below question. 
                {query}                
                Respond only with the entities and metrics and nothing else."""
        entities = call_claude(prompt)
        print(f'entities: {entities}')
        KnowledgeBaseSearchPrompt = f'List all table schema(s) that are relevant to {entities}'
        datasets = retrieveKBreferences(KnowledgeBaseSearchPrompt)
        print(f'datasets: {datasets}')
        if len(datasets) == 0:
            return "", f"no datasets identified in knowledge base for entities {entities}"
        else:
            for dataset in datasets:
                dataset = json.loads(dataset)
                table_arn = dataset["glue_table_arn"]
                print(f'table_arn: {table_arn}')
                table_information += "\n"+ dataset["glue_table_arn"] + " \n"
                table_information += f'table name: {dataset["name"]} \n'
                table_information += f'table columns: \n'
                if dataset["glue_table_business_columns"] != '':
                    business_columns = dataset["glue_table_business_columns"]
                    business_columns = business_columns.split("[")[1].split("]")[0]
                    business_columns = "[" + business_columns.replace("'", "\"") + "]"
                    business_columns = json.loads(business_columns)
                else:
                    business_columns = []
                #print(f'business columns: {business_columns}')
                #print(f'business columns type: {type(business_columns)}')
                technical_columns = dataset["glue_table_columns"]
                technical_columns = technical_columns.split("[")[1].split("]")[0]
                technical_columns = "[" + technical_columns.replace("'", "\"") + "]"
                #print (f'technical_columns: {technical_columns}')
                technical_columns = json.loads(technical_columns)
                #print(f'dict technical columns: {technical_columns}')
                #print(f'technical columns type: {type(technical_columns)}')
                if len(business_columns) > 0:
                    for column, business_column in zip(technical_columns, business_columns):
                        print(f'business_column: {business_column}')
                        print(f'business_column type: {type(business_column)}')     
                        table_information += f'{column["columnName"]} {column["dataType"]} , --{business_column["description"]} \n'
                else:
                    for column in technical_columns:
                        #print(f'column: {column}')
                        #print(f'column type: {type(column)}')
                        table_information += f'{column["columnName"]} {column["dataType"]}, \n'

            # parse table_arn to extract database name
            database = ""
            try:
                database = table_arn.split(":")[-1].split("/")[1]
            except:
                print(f'error in extraction of database name from {table_arn}')
            print(f'extracted database name: {database}')

            print(f'table_information: {table_information}')

            sql_schema = table_information

    else:
        # keep previously identified database
        database = db
        sql_schema = schema

    details = "It is important that the SQL query complies with Athena syntax. \
                During join if column name are same please use alias ex llm.customer_id \
                in select statement. It is also important to respect the type of columns: \
                if a column is string, the value should be enclosed in quotes. \
                If you are writing CTEs then include all the required columns. \
                While concatenating a non string column, make sure cast the column to string."
                #For date columns comparing to string , please cast the string input."
    # use LLM to generate SQL statement
    if sqlerrormessage != "":
        prompt = f"""You are a SQL expert, review {sqlerrormessage}. {details} Generate a SQL statement for the following question {query} using the below sql schema.
                {sql_schema} 
                Respond with only the SQL and nothing else."""
    else:
        prompt = f"""You are a SQL expert. {details} Generate a SQL statement for the following question "{query}" using the below sql schema.
            {sql_schema} 
            Respond with only the SQL and nothing else."""

    sql = call_claude(prompt)

    return database, sql_schema, sql


def run_sql(query):
    print(f'run sql for query: {query}')

    database, sql_schema, sql = generate_sql(query)
    print(f'database: {database}')
    print(f'generated sql_schema: {sql_schema}')
    print(f'generated sql: {sql}')
    code, sql_results = execute_athena_query(database, sql)
    retry_max = 3
    retry_counter = 0
    while True:
        if code != 'SUCCEEDED': #'COLUMN_NOT_FOUND' in sql_results or 'FUNCTION_NOT_FOUND' in sql_results:
            # try to correct SQL
            sqlerrormessage = f'generatd SQL query: {sql} produced the following error: {sql_results}'
            print(sqlerrormessage)
            database, sql_schema, sql = generate_sql(query, sqlerrormessage, database, sql_schema)
            print(f'database: {database}')
            print(f'generated sql_schema: {sql_schema}')
            print(f'generated sql: {sql}')
            code, sql_results = execute_athena_query(database, sql)

        # stop loop if it exceeds max retries
        if code == 'SUCCEEDED' or retry_counter > retry_max:
            break

        retry_counter = retry_counter + 1
        print(f'retry_counter: {retry_counter}')

    return sql, sql_results