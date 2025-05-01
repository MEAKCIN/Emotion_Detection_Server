import cv2
from deepface import DeepFace
import numpy as np

# Define emotion mapping
emotion_map = {
    "neutral": "Neutral",
    "happy": "Happy",
    "sad": "Sad",
    "angry": "Angry",
    "fear": "Sad",     # Map fear to Sad
    "disgust": "Angry",  # Map disgust to Angry
    "surprise": "Happy"  # Map surprise to Happy
}

def detect_emotion_from_image(image_bytes):
    """
    Detects emotion from a JPEG image.

    Args:
        image_bytes (bytes): The JPEG image as bytes.

    Returns:
        str: The detected emotion or an error message.
    """
    try:
        # Convert bytes to a NumPy array and decode to an image
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Load OpenCV face detector
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        # Convert frame to grayscale (for better face detection)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        if len(faces) == 0:
            return "No face detected"

        for (x, y, w, h) in faces:
            face = frame[y:y + h, x:x + w]  # Extract face ROI

            # Analyze emotion only on detected face
            result = DeepFace.analyze(face, actions=['emotion'], enforce_detection=False)
            detected_emotion = result[0]['dominant_emotion']

            # Map detected emotion to one of the 4 categories
            emotion_label = emotion_map.get(detected_emotion, "Neutral")  # Default to Neutral

            return emotion_label

    except Exception as e:
        return f"Error: {str(e)}"
