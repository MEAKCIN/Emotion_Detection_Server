import cv2
from deepface import DeepFace

# Initialize webcam
cap = cv2.VideoCapture(0)

# Load OpenCV face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

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

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert frame to grayscale (for better face detection)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in faces:
        face = frame[y:y + h, x:x + w]  # Extract face ROI

        try:
            # Analyze emotion only on detected face
            result = DeepFace.analyze(face, actions=['emotion'], enforce_detection=False)
            detected_emotion = result[0]['dominant_emotion']

            # Map detected emotion to one of the 4 categories
            emotion_label = emotion_map.get(detected_emotion, "Neutral")  # Default to Neutral

            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Display mapped emotion name
            cv2.putText(frame, f"Emotion: {emotion_label}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        except:
            pass

    # Show the video feed
    cv2.imshow("Emotion Detection", frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()