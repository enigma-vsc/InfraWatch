import os
import boto3

client = boto3.client('ec2')

# response = client.describe_account_attributes(
#     DryRun=True|False,
#     AttributeNames=[
#         'supported-platforms'|'default-vpc',
#     ]
# )