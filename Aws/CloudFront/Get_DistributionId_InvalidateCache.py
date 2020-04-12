# Importing libraries 

import boto3
from time import time

# Assign Values to below variables from Octopus variable set or Update it based on how you are managing your variables

S3Bucket = get_octopusvariable("S3Bucket")
aws_access_key_id = get_octopusvariable("AwsAccessKey")
aws_secret_access_key = get_octopusvariable("AwsSecretKey")
InvalidationPaths = get_octopusvariable("InvalidationPaths")


# boto3 to get Distribution Id from aws Cloudfront 

client = boto3.client('cloudfront', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
response = client.list_distributions()
Filter1 = response["DistributionList"]["Items"]
for distribution in range(0, len(Filter1)):
   Origin_Name = Filter1[distribution]["Origins"]["Items"][0]["DomainName"]
   Sorted_Origin_Name = Origin_Name.split(".s3")[0]
   if S3Bucket == Sorted_Origin_Name:
       Invalidate_DistributionId = Filter1[distribution]["Id"]
       print ("The Distribution id is {} ".format(Invalidate_DistributionId))
       break
print ("Invalidating cache for Distribution id {} ".format(Invalidate_DistributionId))
response = client.create_invalidation(
DistributionId = Invalidate_DistributionId,
InvalidationBatch={
    'Paths': {
       'Quantity': 1,
          'Items': [
              InvalidationPaths,
            ]
        },
        'CallerReference': str(time()).replace(".", "")
    }
)
   
print ("Please note that it may take up to 15-20 minutes for AWS to complete the cloudfront cache invalidation")

