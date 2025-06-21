import cv2
import os

cameo_path = "nephele_cartoon.jpg"

def overlay_cameo_next_to_person(frame, cameo_path):
    """
    Overlay a cameo image next to the detected face in the captured frame.

    :param frame: The captured image from the camera
    :param cameo_path: Path to the cameo image
    :return: The frame with the cameo overlay or the original frame if no face is detected
    """
    # Load the cameo image
    cameo = cv2.imread(cameo_path, -1)  # Load with transparency (if available)

    if cameo is None:
        print("Error: Could not load cameo image.")
        return frame

    # Check if the cameo image has an alpha channel (4 channels)
    if cameo.shape[2] == 4:
        has_alpha = True
        print("Cameo image has an alpha channel.")
    else:
        has_alpha = False
        print("Cameo image does not have an alpha channel.")

    # Convert the frame to grayscale for face detection
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Use Haar Cascade to detect faces
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # If no face is detected, return the original frame
    if len(faces) == 0:
        print("No faces detected.")
        return frame

    # Assuming the first detected face is the primary one
    (x, y, w, h) = faces[0]

    # Resize the cameo image to match the height of the detected face
    scale_factor = h / cameo.shape[0]
    new_cameo_width = int(cameo.shape[1] * scale_factor)
    new_cameo_height = int(cameo.shape[0] * scale_factor)
    cameo_resized = cv2.resize(cameo, (new_cameo_width, new_cameo_height))

    # Determine the position next to the face (to the right)
    x_offset = x + w + 10  # Offset by 10 pixels from the face
    y_offset = y

    # If out of bounds, place the cameo to the left of the face
    if x_offset + new_cameo_width > frame.shape[1]:
        x_offset = x - new_cameo_width - 10

    # Overlay the cameo onto the frame
    if has_alpha:
        # Split the cameo image into BGR and Alpha channels
        cameo_bgr = cameo_resized[:, :, :3]  # BGR channels
        cameo_alpha = cameo_resized[:, :, 3] / 255.0  # Normalize the alpha channel (0 to 1)

        # Blend the cameo with the frame using alpha transparency
        for c in range(0, 3):  # Iterate over the color channels (B, G, R)
            frame[y_offset:y_offset + new_cameo_height, x_offset:x_offset + new_cameo_width, c] = (
                cameo_bgr[:, :, c] * cameo_alpha +
                frame[y_offset:y_offset + new_cameo_height, x_offset:x_offset + new_cameo_width, c] * (1 - cameo_alpha)
            )
    else:
        # If there's no alpha channel, perform a direct overlay
        cameo_bgr = cameo_resized[:, :, :3]
        frame[y_offset:y_offset + new_cameo_height, x_offset:x_offset + new_cameo_width] = cameo_bgr

    return frame

def captureImage(name: str, cameo_path: str) -> str:
    """
    Capture an image with the cameo overlay, save it, and return the image path.

    :param name: Name to use for saving the image
    :param cameo_path: Path to the cameo image
    :return: Path of the saved image or None if error
    """
    # Ensure the images directory exists
    if not os.path.exists("images"):
        os.makedirs("images")

    # Initialize video capture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return None

    try:
        # Capture a frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to capture image.")
            return None

        # Overlay cameo next to detected face
        frame_with_cameo = overlay_cameo_next_to_person(frame, cameo_path)

        # Define the image path
        path = f"images/{name}.jpg"

        # Save the image
        success = cv2.imwrite(path, frame_with_cameo)
        if success:
            print(f"Image with cameo saved at {path}")
            return path
        else:
            print("Error: Unable to save the image.")
            return None

    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

    finally:
        cap.release()
        cv2.destroyAllWindows()
