import cv2
from pyzbar import pyzbar
from pymongo import MongoClient
import tempfile

# Load the pre-trained Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# MongoDB setup
try:
    client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB connection string if different
    db = client['AttendanceDB']
    collection = db['AuroraA']
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

def decode_qr(frame):
    """Function to decode QR code and return the name if found in MongoDB."""
    qr_codes = pyzbar.decode(frame)

    for qr_code in qr_codes:
        qr_data = qr_code.data.decode('utf-8')
        qr_document = collection.find_one({'qr_data': qr_data})

        if qr_document:
            name = qr_document.get('name', 'Name not found')
            email = qr_document.get('email', 'Email not found')
            print(f"Name: {name}, Email: {email}")
            return True, name, frame

    return False, None, frame

def capture_image_temp(frame):
    """Function to capture and return the image as a temporary file."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    cv2.imwrite(temp_file.name, frame)
    print(f"Image captured and stored temporarily at {temp_file.name}")
    return temp_file

def detect_face(name):
    """Function to detect a human face using Haar Cascade and return the temp file of the image."""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # If a face is detected, capture and return the image as a temporary file
        if len(faces) > 0:
            print(f"Detected {len(faces)} face(s).")
            temp_file = capture_image_temp(frame)
            break

        # Show the live feed for face detection
        cv2.imshow('Face Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    return temp_file

def main():
    """Main function to execute both QR code scanning and face detection."""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    # QR code scanning loop
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        found, name, frame = decode_qr(frame)

        if found:
            print("QR code successfully scanned. Stopping the camera.")
            break

        cv2.imshow('QR Code Scanner', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if found:
        # Start face detection loop after QR code is scanned and return the temp image file
        temp_file = detect_face(name)
        return temp_file

if __name__ == '__main__':
    temp_image_file = main()
    print(f"Temporary image file stored at: {temp_image_file.name}")

