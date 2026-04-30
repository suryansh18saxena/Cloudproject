"""
cleanup_user.py — Called by Terraform destroy provisioner to remove
any lingering IAM login profiles before destroying the user.
"""
import sys
import boto3
from botocore.exceptions import ClientError

def cleanup_iam_user(username):
    iam = boto3.client('iam')

    # Delete login profile (console password)
    try:
        iam.delete_login_profile(UserName=username)
        print(f"[cleanup] Deleted login profile for {username}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"[cleanup] No login profile found for {username} (already clean)")
        else:
            print(f"[cleanup] Warning deleting login profile: {e}")

    # Detach all user policies
    try:
        paginator = iam.get_paginator('list_attached_user_policies')
        for page in paginator.paginate(UserName=username):
            for policy in page['AttachedPolicies']:
                iam.detach_user_policy(UserName=username, PolicyArn=policy['PolicyArn'])
                print(f"[cleanup] Detached policy {policy['PolicyName']} from {username}")
    except ClientError as e:
        print(f"[cleanup] Warning detaching policies: {e}")

    print(f"[cleanup] Cleanup complete for {username}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python cleanup_user.py <iam-username>")
        sys.exit(1)
    cleanup_iam_user(sys.argv[1])
