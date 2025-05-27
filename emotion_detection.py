import cv2
from deepface import DeepFace
import numpy as np
import os

def detect_emotion_from_image(image_bytes):
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
            return {"error": "No face detected"}

        for (x, y, w, h) in faces:
            face = frame[y:y + h, x:x + w]  # Extract face ROI

            # Analyze emotion, age and gender on detected face
            result = DeepFace.analyze(face, actions=['emotion', 'age', 'gender'], enforce_detection=False)

            # Get all emotions with values > 1%
            emotions = result[0]['emotion']
            significant_emotions = {k: v for k, v in emotions.items() if v > 1}

            # Extract the required information
            face_info = {
                "emotions": significant_emotions,
                "dominant_emotion": result[0]['dominant_emotion'],
                "age": result[0]['age'],
                "gender": result[0]['dominant_gender']
            }

            return face_info

    except Exception as e:
        return {"error": f"Error: {str(e)}"}

