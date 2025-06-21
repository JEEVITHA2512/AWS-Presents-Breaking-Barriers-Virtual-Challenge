"""
Script to send the image captured to the user through AWS SES.
"""

# Importing the required libraries
import boto3
import os
import base64
from botocore.exceptions import ClientError


def sendEmail(name: str, path: str, recipientemail: str, url: str) -> bool:
    """
    Send the image captured to the user through AWS SES.
    :param name: Name of the User
    :type name: str
    :param path: Path of the image file.
    :type path: str
    :param recipientemail: Email Address of the user
    :type recipientemail: str
    :return: True or False based on the success of the email sent.
    :rtype: bool
    """

    # SETUP
    AWS_REGION = "ap-south-1"
    SENDER = "Aurora <meganth.mail@gmail.com>"
    RECIPIENT = recipientemail
    SUBJECT = "Selfie Captured"
    CHARSET = "UTF-8"

    # Crete the body of the email
    BODY_TEXT = f"""
    
    Hi {name},
    \tHope you are doing good! Here is the selfie you captured.
    
    Regards,
    Aurora
                """

    # Create a HTML version of the body
    BODY_HTML = f"""
    
    <html>
        <head>Test Email</head>
        <body>
          <h1>Thanks for participating in our event!!</h1>
          <p>PFA the link to download your selfie captured by Aurora.
            <a href="{url}"> Download Selfie </a>
          </p>
          <br>
          <br>
          <h3>Regards,</h3>
          <h3>Team Aurora</h3> 
        </body>
    </html>
    
    """

    # Create a client for the AWS SES
    client = boto3.client("ses", region_name=AWS_REGION)

    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                "ToAddresses": [
                    RECIPIENT,
                ],
            },
            Message={
                "Body": {
                    "Html": {
                        "Charset": CHARSET,
                        "Data": BODY_HTML,
                    },
                    "Text": {
                        "Charset": CHARSET,
                        "Data": BODY_TEXT,
                    },
                },
                "Subject": {
                    "Charset": CHARSET,
                    "Data": SUBJECT,
                },
            },
            Source=SENDER,
        )

    except ClientError as e:
        print(e.response["Error"]["Message"])
        return False
    else:
        print("Email sent! Message ID:"),
        print(response["MessageId"])
        return True
