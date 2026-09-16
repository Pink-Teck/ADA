"""
server.py - Python/boto3 control script for Satisfactory didicated server on EC2 instance.

Usage:
    python server.py start
    python server.py stop
    python server.py status
"""

import argparse
import sys
import time

import boto3
from botocore.exceptions import ClientError, WaiterError

#=== CONFIG ===

AWS_PROFILE = "satisfactory"
AWS_REGION = "eu-west-2"
INSTANCE_ID = "i-0a2c3c2f99e224951"

#================

def get_ec2_client():
    #session = boto3.Session(profile_name=AWS_PROFILE) #needed for local testing
    session = boto3.Session()
    return session.client("ec2", region_name=AWS_REGION)

    #TEST COMMENT

def get_instance_state(ec2):
    """Return (state_name, public_ip_or_None) for the configured instance."""
    response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    instance = response["Reservations"][0]["Instances"][0]
    state = instance["State"]["Name"]
    public_ip = instance.get("PublicIpAddress")
    return state, public_ip

def cmd_status(ec2):
    state, public_ip = get_instance_state(ec2)
    print(f"The instance({INSTANCE_ID}) is currently {state}")
    if public_ip:
        print(f"The Public IP is {public_ip}.")
    return state, public_ip

#===START===
def cmd_start(ec2):
    state, _ = get_instance_state(ec2)

    #Check the state is 'stopped'
    if state != "stopped":
        return False, f"Can't start, instance is currently {state}"

    print("Spinning up the instance...")

    #Try to start:
    try:
        ec2.start_instances(InstanceIds=[INSTANCE_ID])
        waiter = ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=[INSTANCE_ID])

    #If unsuccessful:
    except (ClientError, WaiterError) as e:
        return False, f"{e}"


    #Return True when up
    state, public_ip = get_instance_state(ec2)
    print(f"Instance is now: {state}")
    if public_ip:
        print(f"Server should be reachable at this IP: {public_ip}")
    print("It might take a minute for Satisfactory to put its pants on. Give it a min and refresh if it's still showing as offline in the Server Manager.")
    return True, f"Instance is now {state}, reachable at {public_ip}"

#Could use yield from bot to provide multiple returns? Stetch goal maybe.

#====STOP===== Set this one up like start command
def cmd_stop(ec2):
    state, _ = get_instance_state(ec2)

    #Check it's in the correct state to be stopped
    if state != "running": 
        return False, f"Can't stop, instance is currently {state}"

    #Print to console
    print("Stopping the instance...")

    #Try to stop instance:
    try:
        ec2.stop_instances(InstanceIds=[INSTANCE_ID])
        waiter = ec2.get_waiter("instance_stopped")
        waiter.wait(InstanceIds=[INSTANCE_ID])
    #If unsuccessful:
    except (ClientError, WaiterError) as e:
        return False, f"Failed to stop instance: {e}"

    state, _ = get_instance_state(ec2)
    return True, f"Instance is now {state}."

def main():
    parser = argparse.ArgumentParser(description="Control the Satisfactory EC2 Instance")
    parser.add_argument("command", choices=["start", "stop", "status"], help="Action to perform")
    args = parser.parse_args()

    ec2 = get_ec2_client()

    if args.command == "start":
        cmd_start(ec2)
    elif args.command == "stop":
        cmd_stop(ec2)
    elif args.command == "status":
        cmd_status(ec2)

if __name__ == "__main__":
    main()