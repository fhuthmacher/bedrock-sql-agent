# Amazon Bedrock SQL Agent

In this tutorial, you will learn how to create a SQL Agent that uses Amazon DataZone's business metadata to create and execute SQL queries.

The full tutorial can be found on [Medium](https://medium.com/@fhuthmacher/text-to-sql-how-amazon-bedrock-agents-and-amazon-datazone-enable-non-technical-users-to-get-to-d9c63d810298).

By the end of this tutorial, you will have gained valuable hands-on experience with Amazon Bedrock Agents and Amazon DataZone.

Some familiarly with Python and using services such as Lambda and Elastic Container Registry is helpful. No AI/ML experience is necessary.

## Prerequisites

This tutorial assumes you are working in an environment with access to [Python 3.9](https://www.python.org/getit/) or later and [Docker](https://www.docker.com/). 

## Deployment instructions
If you want to deploy the entire solution with IaC, log into your AWS management console. Then click the Launch Stack button below to deploy the required resources.

[![Launch CloudFormation Stack](https://felixh-github.s3.amazonaws.com/misc_public/launchstack.png)](https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=sqlagent&templateURL=https://felixh-github.s3.amazonaws.com/misc_public/bedrock-sql-agent.yml)

Prerequisites:
1. This stack requires an existing Amazon DataZone DOMAIN ID.
2. A DefaultDataLake blueprint within Amazon DataZone that has been activated.
3. A role that has sufficient AWS LakeFormation & Amazon DataZone access to deploy resources.

To avoid incurring additional charges to your account, stop and delete all of the resources by deleting the CloudFormation template at the end of this tutorial.