"""
A python script to upload an image to a AWS S3 bucket.
"""

import boto3
import argparse
from botocore.exceptions import ClientError
import requests
import os
import sys
import typing


# Setup region
REGION = "ap-south-1"


def uploadImage(image_path, bucket_name) -> str:
    """
    Upload an image to an AWS S3 bucket.
    :param image_path: Path of the image to upload.
    :type image_path: str
    :param bucket_name: Name of the bucket to upload the image to.
    :type bucket_name: str
    :return: Return the URL of the uploaded image.
    :rtype: str
    """

    # Check if images exists
    if not os.path.exists(image_path):
        print(f"Image {image_path} does not exist.")
        return False

    # Check if image is a file
    if not os.path.split(".")[-1] != "jpg":
        print(f"Image {image_path} is not a valid image file.")
        return False

    # Check if bucket exists
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)
    if not bucket.creation_date:
        print(f"Bucket {bucket_name} does not exist.")
        return False

    # Use exception handling to upload image
    try:
        s3.meta.client.upload_file(
            image_path, bucket_name, os.path.basename(image_path)
        )

    except Exception as e:
        print(f"Error uploading image: {e}")
        return False

    else:
        return f"https://{bucket_name}.s3.{REGION}.amazonaws.com/{os.path.basename(image_path)}"
