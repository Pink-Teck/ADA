import boto3

session = boto3.Session(profile_name='satisfactory')
ec2 = session.client('ec2', region_name='eu-west-2')

response = ec2.describe_instances()

for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        print(f"Instance ID: {instance['InstanceId']}")
        print(f"State: {instance['State']['Name']}")
        print(f"Instance Type: {instance['InstanceType']}")