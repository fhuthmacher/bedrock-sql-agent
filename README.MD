# Amazon Bedrock SQL Agent

In this tutorial, you will learn how to create a SQL Agent that uses Amazon DataZone's business metadata to create and execute SQL queries.

The full tutorial can be found on [Medium](https://medium.com/@fhuthmacher/text-to-sql-how-amazon-bedrock-agents-and-amazon-datazone-enable-non-technical-users-to-get-to-d9c63d810298).

By the end of this tutorial, you will have gained valuable hands-on experience with Amazon Bedrock Agents and Amazon DataZone.

Some familiarly with Python and using services such as Lambda and Elastic Container Registry is helpful. No AI/ML experience is necessary.

![Solution Architecture](/images/arch.png)

The above solution architecture addresses three common Text-to-SQL challenges.
1. Lack of technical and business metadata  
The solution uses Amazon DataZone's built-in GenAI capabilities to accelerate the creation of business friendly metadata such as table names, column names, and data asset descriptions. Rather than having to start from scratch manually, you can create and refine this metadata with GenAI for thousands of tables in minutes. Further, this centrally stored, reviewed and approved metadata then can be used to augment the Text-to-SQL generation and improve accuracy.

2. LLM Context Window Length Limits
Having a centralized data catalog not only provides a single pane of glass of the company's data sources, but if used in a RAG system, it also allows us to only include tables in the prompt to the LLM that are relevant for a given user query. 
Here we use a Bedrock Knowledge Base as a vector store for the metadata from Amazon DataZone. 
Without it, we would have to include all of table definitions with each and every prompt. This can be a challenge, especially at enterprise scale, as LLM's are still restricted by their context window length, which defines how many tokens can be provided in a prompt.

3. Latency and Cost of Text-to-SQL
The above approach not only provides more accurate responses, but also enables you to potentially use use smaller LLMs with smaller context windows, which further reduces inference latency and cost.


## Deployment instructions
If you want to deploy the entire solution with IaC, log into your AWS management console. Then click the Launch Stack button below to deploy the required resources.

[![Launch CloudFormation Stack](https://felixh-github.s3.amazonaws.com/misc_public/launchstack.png)](https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=sqlagent&templateURL=https://felixh-github.s3.amazonaws.com/misc_public/bedrock-sql-agent.yml)

To avoid incurring additional charges to your account, stop and delete all of the resources by deleting the CloudFormation template at the end of this tutorial.

## Configuration
### Amazon Bedrock Foundation Model Access
Amazon Bedrock offers a choice of high-performing foundation models (FMs) from leading AI companies like AI21 Labs, Anthropic, Cohere, Meta, Stability AI, and Amazon. In the Amazon Bedrock console, you can see the descriptions for these foundation models by the Base models link in the navigation pane.

You need to request access to the foundation models before using them. In the Amazon Bedrock console, do the following:

Go to the Amazon Bedrock console. 
In the navigation pane, select Model access.
In the Model access page, you should see a list of base models. Click on the Manage model access button to edit your model access.
Select the check box next to the following models to get started.
Titan Embeddings G1 - Text
Titan Text G1 - Lite
Titan Text G1 - Express
Claude
Claude Instant

![Amazon Bedrock Model Access](/images/modelaccess.png)

Click on the Save changes button and it may take several minutes to save the changes. This also brings you back to the Model access page.
Models will show as Access granted on the Model access page under the Access status column, if access is granted.

### Run Knowledge Base Synchronization
To synchronize the business metadata from Amazon DataZone with Amazon Bedrock's Knowledge Base, follow the below steps.

Go to AWS Lambda console, then select the "SyncDZassetsToKB" function.

![Lambda Sync Function](/images/71_LambdaSync.png)

Click on the **"Test"** button.

![Lambda Sync Test](/images/72_LambdaTest.png)

Click on the **"Invoke"** button to run the Lambda.

![Lambda Sync Invoke](/images/73_LambdaInvoke.png)

 Review Lambda Runtime Results.

![Lambda Sync Invoke Results](/images/74_LambdaResults.png)