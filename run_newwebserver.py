import subprocess
import time
import webbrowser
import boto3
from botocore.exceptions import ClientError
import logging

ec2 = boto3.resource('ec2')
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')

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

def cleanup_function(ec2_instance_object, s3_object):

    print("Initiating clean up")

    ec2_instance_object.terminate()
    ec2_instance_object.wait_until_terminated()

    s3_object.objects.all().delete()
    s3_object.delete()

    print("cleanup function ran successfully, ec2 instances and buckets were deleted :)")


instance_list = []

for inst in ec2.instances.all():
    instance_list.append(inst)

instances = ec2.create_instances(
    ImageId='ami-02dfbd4ff395f2a1b',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    KeyName='automated_cloud_services_assignment_one',
    SecurityGroupIds=['sg-0d053a60c4d1db66f'],
    IamInstanceProfile={'Name': 'EC2-S3-IAM-Role'},
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

key_file_path = "automated_cloud_services_assignment_one.pem"

time.sleep(60)

check_script = """#!/usr/bin/python3
import subprocess

def check_server():
    try:
     cmd = 'ps -A | grep httpd'
     subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
     print("success: web server is up and running")
    except subprocess.CalledProcessError:
     print("error: web server failed")

if __name__ == '__main__':
    check_server()
"""

with open("check_webserver.py", "w") as f:
    f.write(check_script)

scp_command = f"scp -i {key_file_path} -o StrictHostKeyChecking=no check_webserver.py ec2-user@{mainInstance.public_ip_address}:."
print(f"triggering command: \n{scp_command}")
try:
    subprocess.run(scp_command, shell=True, timeout=90, check=True)
except subprocess.TimeoutExpired:
    print("error with the command above")

linux_commands = f"""
sudo yum install -y httpd
sudo systemctl start httpd
sudo systemctl enable httpd
sudo aws s3 cp s3://{bucket_name}/index.html /var/www/html/
sudo aws s3 cp s3://{bucket_name}/image_cloud_services_assignment.jpeg /var/www/html/
chmod 700 check_webserver.py
python3 check_webserver.py
"""

ssh_command = f"ssh -t -i {key_file_path} -o StrictHostKeyChecking=no ec2-user@{mainInstance.public_ip_address} '{linux_commands}'"
print(f"triggering ssh command: \n{ssh_command}")
try:
    subprocess.run(ssh_command, shell=True, timeout=90, check=True)
except subprocess.TimeoutExpired:
    print("error with the command above")

website_url = f"http://{mainInstance.public_ip_address}"
webbrowser.open(website_url)


print(f"Instance public_ip: {mainInstance.public_ip_address}")

print("\n====================================================================================================================================================================================")
print(f"the web server is currently running. You can view it in your browser or at this url: {website_url}.")
print("when you are finished, type 'cleanup' and press Enter to delete the ec2 and s3 resources.")
print("\n====================================================================================================================================================================================")

user_input = input("\ntype 'cleanup' to terminate or any other key to leave running: ")

if user_input.strip().lower() == 'cleanup':
    cleanup_function(mainInstance, s3_resource.Bucket(bucket_name))
else:
    print("exiting: the ec2 instance and s3 bucket were left running.")
