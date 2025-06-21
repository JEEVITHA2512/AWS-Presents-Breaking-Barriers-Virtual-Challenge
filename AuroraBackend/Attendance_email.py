import cv2
from pyzbar import pyzbar
from pymongo import MongoClient
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# MongoDB setup
try:
    client = MongoClient('mongodb://localhost:27017/')  # replace with your MongoDB connection string if different
    db = client['AttendanceDB']
    collection = db['NepheleA']
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

# AWS SES setup
ses_client = boto3.client('ses', region_name='ap-south-1')  # Specify your AWS region

# Dictionary to store QR code data and their "present" status
qr_code_status = {}

# Set to store already processed QR codes
processed_qr_codes = set()

def verify_email_identity(recipient_email):
    try:
        response = ses_client.verify_email_identity(EmailAddress=recipient_email)
        print(f"Verification email sent to {recipient_email}.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Credentials error: {e}")
    except Exception as e:
        print(f"Error sending email verification: {e}")

def send_email(recipient_email):
    # Construct the email
    sender_email = "meganth.mail@gmail.com"
    subject = "Attendance Marked as Present"
    body_html = """
    <html>
    <body>
      <h1>Attendance Marked</h1>
      <p>You have been marked as present.</p>
    </body>
    </html>
    """

    try:
        # Check if email is verified before sending
        response = ses_client.list_verified_email_addresses()
        verified_emails = response['VerifiedEmailAddresses']

        if recipient_email not in verified_emails:
            print(f"Email {recipient_email} is not verified. Sending verification request.")
            verify_email_identity(recipient_email)
        else:
            response = ses_client.send_email(
                Source=sender_email,
                Destination={
                    'ToAddresses': [recipient_email],
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': body_html,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            print(f"Email sent to {recipient_email}")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Credentials error: {e}")
    except Exception as e:
        print(f"Error sending email: {e}")

def decode_qr(frame):
    # Find QR codes in the frame
    qr_codes = pyzbar.decode(frame)
    
    # List to store decoded QR code data
    qr_data_list = []

    # Loop over the detected QR codes
    for qr_code in qr_codes:
        # Decode the QR code data
        qr_data = qr_code.data.decode('utf-8')

        # Check if the QR code has already been processed
        if qr_data in processed_qr_codes:
            continue  # Skip already processed QR codes

        # Add the QR code data to the list
        qr_data_list.append(qr_data)

        # Extract the bounding box location of the QR code and draw a rectangle around it
        (x, y, w, h) = qr_code.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Draw the QR code data and type on the frame
        qr_type = qr_code.type
        text = f'{qr_data} ({qr_type})'
        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Check if the QR code exists in the database
        qr_document = collection.find_one({'qr_data': qr_data})
        if qr_document:
            # If present in the database, update the status to "marked as present"
            collection.update_one({'qr_data': qr_data}, {'$set': {'status': 'present'}})
            qr_code_status[qr_data] = True
            print(f"QR Code {qr_data} marked as present.")

            # Send email to the user
            if 'email' in qr_document:
                recipient_email = qr_document['email']
                send_email(recipient_email)

            # Add the QR code to the processed set to avoid reprocessing
            processed_qr_codes.add(qr_data)
        else:
            qr_code_status[qr_data] = False
            print(f"QR Code {qr_data} is not recognized.")

    return frame, qr_data_list

def main():
    # Initialize the video stream
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
        frame, qr_data_list = decode_qr(frame)

        # Print the QR code data
        if qr_data_list:
            for qr_data in qr_data_list:
                print(f"QR Code Data: {qr_data} - Status: {'Present' if qr_code_status[qr_data] else 'Not Recognized'}")
                # Break the loop after processing the first valid QR code
                if qr_code_status[qr_data]:
                    cap.release()
                    cv2.destroyAllWindows()
                    return

        # Display the frame
        cv2.imshow('QR Code Scanner', frame)

        # Break the loop if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture object and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
