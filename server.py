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
    session = boto3.Session(profile_name=AWS_PROFILE)
    return session.client("ec2", region_name=AWS_REGION)

def get_instance_state(ec2):
    """Return (state_name, public_ip_or_None) for the configured instance."""
    response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    instance = response["Reservations"][0]["Instances"][0]
    state = instance["State"]["Name"]
    public_ip = instance.get("PublicIpAddress")
    return state, public_ip

def cmd_status(ec2):
    state, public_ip = get_instance_state(ec2)
    print(f"The server({INSTANCE_ID}) is currently {state}")
    if public_ip:
        print(f"The Public IP is {public_ip}.")

def cmd_start(ec2):
    state, _ = get_instance_state(ec2)

    if state != "stopped":
        print(f"Can't start if the server ain't stopped. It's currently {state}")
        if state == "running":
            print("Get to work, maggot.")
        elif state == "pending":
            print("That means it's on its way. I'm loving the enthusiasm, just hold on a sec.")
        elif state == "stopping":
            print("Once I've confirmed the server is stopped, you can go ahead and start it again. You lil' bitch.")
        else:
            print("ERROR [69]! UNKNOWN STATE!! EVERYONE PANIC!!!")
        return

    print("Clocking in? Spinning up the server...")

    try:
        ec2.start_instances(InstanceIds=[INSTANCE_ID])
    except ClientError as e:
        print(f"Summin broke. Failed to start instance: {e}")
        sys.exit(1)

    print("Waiting for the server to be serving...")
    waiter = ec2.get_waiter("instance_running")
    try:
        waiter.wait(InstanceIds=[INSTANCE_ID])
    except WaiterError as e:
        print(f"We timed out, or maybe failed, while waiting for the server to serve: {e}")
        sys.exit(1)

    state, public_ip = get_instance_state(ec2)
    print(f"Instance is now: {state}")
    if public_ip:
        print(f"Server should be reachable at this IP: {public_ip}")
    print("It might take a minute for Satisfactory to put its pants on. Give it a min and refresh if it's still showing as offline in the Server Manager.")


def cmd_stop(ec2):
    state, _ = get_instance_state(ec2)

    if state != "running":
        print(f"Can't stop if the server ain't running. It's currently {state}")
        if state == "stopped":
            print("So it's already down.")
        elif state == "pending":
            print("It'll be up in a mo. Try again once it's running.")
        elif state == "stopping":
            print("It'll be stopped in a mo.")
        else:
            print("ERROR [69]! UNKNOWN STATE!! EVERYONE PANIC!!!")  
        return

    print("Stopping the server...")
    try:
        ec2.stop_instances(InstanceIds=[INSTANCE_ID])
    except ClientError as e:
        print(f"Failed to stop instance: {e}")
        sys.exit(1)

    print("Waiting for the server to stop serving...")
    waiter = ec2.get_waiter("instance_stopped")
    try:
        waiter.wait(InstanceIds=[INSTANCE_ID])
    except WaiterError as e:
        print("Wow, the server literally couldn't stop serving when it tried.")
        print(f"It timed out, or maybe failed: {e}")
        sys.exit(1)

    state, _ = get_instance_state(ec2)
    print(f"Instance is now: {state}")

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