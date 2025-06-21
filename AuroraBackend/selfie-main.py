from captureImage import captureImage
from sendEmail import sendEmail
from uploadImage import uploadImage
import cv2
from pyzbar import pyzbar
from pymongo import MongoClient
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# AWS SES setup
REGION = "ap-south-1"
ses_client = boto3.client('ses', region_name=REGION)

bucket_name = "selfiebucket11"
name = ""
email = ""
url = ""
cameo_path = r"C:\Users\gabri\OneDrive\Desktop\Selfie-Mode\images\Aurora_cartoon.jpg"

# MongoDB setup
try:
    client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB connection string if different
    db = client['AttendanceDB']
    collection = db['AuroraA']
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

def verify_email_identity(recipient_email):
    """Verifies the email address using AWS SES if not verified already."""
    try:
        response = ses_client.verify_email_identity(EmailAddress=recipient_email)
        print(f"Verification email sent to {recipient_email}.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Credentials error: {e}")
    except Exception as e:
        print(f"Error sending email verification: {e}")

def check_email_verification(recipient_email):
    """Checks if the email is verified and triggers verification if not."""
    try:
        # Check if email is verified before proceeding
        response = ses_client.list_verified_email_addresses()
        verified_emails = response['VerifiedEmailAddresses']
        
        if recipient_email not in verified_emails:
            print(f"Email {recipient_email} is not verified. Sending verification request.")
            verify_email_identity(recipient_email)
        else:
            print(f"Email {recipient_email} is already verified.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Credentials error: {e}")
    except Exception as e:
        print(f"Error checking email verification: {e}")

def decode_qr(frame):
    """Scans the QR code and returns name and email if valid QR is found."""
    qr_codes = pyzbar.decode(frame)

    for qr_code in qr_codes:
        # Decode the QR code data
        qr_data = qr_code.data.decode('utf-8')

        # Check if the QR code exists in the database
        qr_document = collection.find_one({'qr_data': qr_data})
        if qr_document:
            # Retrieve the name and email from the database
            name = qr_document.get('name', 'Name not found')
            email = qr_document.get('email', 'Email not found')
            print(f"Name: {name}, Email: {email}")
            
            # Verify the email address
            check_email_verification(email)
            
            # Return True to indicate that a valid QR code was found
            return True, name, email, frame

    # Return False if no valid QR code is found
    return False, "", "", frame

def main():
    """Main function to handle the QR scanning, image capture, and email logic."""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        
        # Decode QR codes in the frame
        found, name, email, frame = decode_qr(frame)

        # Break the loop if a valid QR code is found
        if found:
            print("QR code successfully scanned. Stopping the camera.")
            break

        # Display the frame
        cv2.imshow('QR Code Scanner', frame)

        # Break the loop if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture object and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

    # Capture the image using the name retrieved from QR
    path = captureImage(name,cameo_path)
    
    # Upload the image and get the URL
    url = uploadImage(path,bucket_name)
    
    # Send email with the captured image and URL
    sendEmail(name, path, email, url)

if __name__ == '__main__':
    main()

Aurora