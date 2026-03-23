import boto3
from botocore.exceptions import ClientError
import logging

ec2 = boto3.resource('ec2')
s3 = boto3.client('s3')

def create_bucket(bucket_name, region='us-east-1'):
    try:
        bucket_config = {}
        s3_client = boto3.client('s3', region_name=region)
        if region != 'us-east-1':
            bucket_config['CreateBucketConfiguration'] = {'LocationConstraint': region}

        s3_client.create_bucket(Bucket=bucket_name, **bucket_config)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def html_script(instance_id, availability_zone):
    return f"""
    <html>
    <head><title>Automated Cloud Services Assignment 1</title></head>
    <body>
    <h1>Welcome to Eugene Tipas Web Server</h1>
    <p>Instance ID: {instance_id}</p>
    <p>Availability Zone: {availability_zone}</p>
    <img src="image_cloud_services_assignment.jpeg" alt="Uploaded Image" width="200">
    </body>
    </html>
    """

instance_list = []

for inst in ec2.instances.all():
    instance_list.append(inst)

instances = ec2.create_instances(
    ImageId='ami-02dfbd4ff395f2a1b',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    KeyName='automated_cloud_services_assignment_one',
    UserData="#!/bin/bash\nyum update -y"
)

mainInstance = instances[0]
mainInstance.wait_until_running()
mainInstance.reload()
bucket_name = f"eugene-tipa-{mainInstance.id}"
create_bucket(bucket_name=bucket_name)


with open("index.html", "w") as f:
    f.write(html_script(instance_id=mainInstance.id, availability_zone=mainInstance.placement["AvailabilityZone"]))

s3.upload_file("index.html", bucket_name, "index.html")

s3.upload_file("image_cloud_services_assignment.jpeg", bucket_name, "image_cloud_services_assignment.jpeg")

print(f"Instance public_ip: {mainInstance.public_ip_address}")