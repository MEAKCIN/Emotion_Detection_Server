from emotion_detection import detect_emotion_from_image

# Define the mapping of other emotions to the main emotions
EMOTION_MAPPING = {
    "happy": ["happy"],
    "angry": ["angry"],
    "neutral": ["neutral"],
    "sad": ["sad"],
    "surprise": ["happy", "neutral"],
    "fear": ["sad", "angry"],
    "disgust": ["angry", "neutral"]
}

def calculate_main_emotions(image_bytes):
    """
    Processes the emotions returned by emotion_detection and maps them to the main emotions.

    Args:
        image_bytes (bytes): The image data in bytes.

    Returns:
        dict: A dictionary containing the main emotions and their calculated values.
    """
    # Get the detected emotions from emotion_detection
    detected_data = detect_emotion_from_image(image_bytes)

    if "error" in detected_data:
        return {"error": detected_data["error"]}

    emotions = detected_data.get("emotions", {})
    main_emotions = {"happy": 0, "angry": 0, "neutral": 0, "sad": 0}

    # Process each emotion and map it to the main emotions
    for emotion, value in emotions.items():
        if emotion in EMOTION_MAPPING:
            mapped_emotions = EMOTION_MAPPING[emotion]
            split_value = value / len(mapped_emotions)  # Split the value equally among mapped emotions
            for mapped_emotion in mapped_emotions:
                main_emotions[mapped_emotion] += split_value

    # Clamp the values to be between 0 and 59
    main_emotions = {k: max(0, min(59, round(v, 2))) for k, v in main_emotions.items()}

    # Remove keys with 0 values
    main_emotions = {k: v for k, v in main_emotions.items() if v > 0}

    return main_emotions