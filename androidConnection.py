# Python
from flask import Flask, request, jsonify
import base64
import os
import json
import emotion_detection 

app = Flask(__name__)

# Define a directory to save uploads (optional but good practice)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define the path for the device configuration file
DEVICE_CONFIG_FILE = 'device_config.json' # Using JSON format as requested

def get_device_config():
    """Reads device configuration from JSON file, creates a default if not found."""
    try:
        with open(DEVICE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            # Ensure the loaded data has the expected top-level keys
            if "deviceOn" not in config_data or "emotions" not in config_data:
                print(f"Warning: {DEVICE_CONFIG_FILE} is missing expected keys. Using default structure.")
                return {"deviceOn": False, "emotions": []}
            return config_data
    except FileNotFoundError:
        # Default configuration if the file doesn't exist
        return {"deviceOn": False, "emotions": []}
    except json.JSONDecodeError:
        print(f"Warning: {DEVICE_CONFIG_FILE} is corrupted or not valid JSON. Using default config.")
        return {"deviceOn": False, "emotions": []}


def save_device_config(config):
    """Saves device configuration to JSON file."""
    with open(DEVICE_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2) # Using indent=2 to match user's example format

@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body provided'}), 400

    photo_data = data.get('photo')
    if not photo_data:
        return jsonify({'error': 'No photo field provided'}), 400

    try:
        if isinstance(photo_data, str) and photo_data.startswith("data:image"):
            _, encoded_data = photo_data.split(',', 1)
            photo_data = encoded_data

        image_bytes = base64.b64decode(photo_data)

        # Calculate main emotions
        from emotion_calculation import calculate_main_emotions
        calculated_emotions = calculate_main_emotions(image_bytes)
        print(f"Calculated emotions: {calculated_emotions}")

        if "error" in calculated_emotions:
            return jsonify({'error': calculated_emotions["error"]}), 400

        # Convert np.float32 values to native float
        calculated_emotions = {k: float(v) for k, v in calculated_emotions.items()}

        # Update device_config.json based on calculated emotions
        config = get_device_config()
        for emotion_config in config["emotions"]:
            emotion_name = emotion_config["name"].lower()
            if emotion_name in calculated_emotions:
                emotion_config["isActive"] = True
                emotion_config["sprayDuration"] = round(calculated_emotions[emotion_name])
            else:
                emotion_config["isActive"] = False

        save_device_config(config)

        return jsonify({'message': 'Photo processed and device configuration updated', 'calculated_emotions': calculated_emotions}), 200

    except base64.binascii.Error as e:
        return jsonify({'error': f'Invalid base64 data: {str(e)}'}), 400
    except Exception as e:
        print(f"Error in /upload-photo: {str(e)}")
        return jsonify({'error': f'An error occurred during photo processing: {str(e)}'}), 500

@app.route('/upload-manual', methods=['POST'])
def upload_manual():

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    print(f"Received data: {data}")  # Debugging line to see the received data
    if not data:
        return jsonify({'error': 'No JSON body provided'}), 400

    device_on = data.get('deviceOn')
    emotions_settings = data.get('emotions')

    if device_on is None or not isinstance(device_on, bool):
        return jsonify({'error': 'Invalid or missing "deviceOn" field (must be boolean)'}), 400

    if emotions_settings is None or not isinstance(emotions_settings, list):
        return jsonify({'error': 'Invalid or missing "emotions" field (must be a list)'}), 400

    for i, setting in enumerate(emotions_settings):
        if not isinstance(setting, dict):
            return jsonify({'error': f'Emotion setting at index {i} is not a valid object.'}), 400
        if not all(k in setting for k in ("name", "sprayPeriod", "sprayDuration", "isActive")):
            return jsonify({'error': f'Emotion setting at index {i} is missing one or more required keys (name, sprayPeriod, sprayDuration, isActive)'}), 400
        # Further type checks for each field within an emotion object can be added here if desired
        if not isinstance(setting.get("name"), str):
             return jsonify({'error': f'Emotion setting "name" at index {i} must be a string.'}), 400
        if not isinstance(setting.get("sprayPeriod"), (int, float)): # Allowing int or float
             return jsonify({'error': f'Emotion setting "sprayPeriod" at index {i} must be a number.'}), 400
        if not isinstance(setting.get("sprayDuration"), (int, float)): # Allowing int or float
             return jsonify({'error': f'Emotion setting "sprayDuration" at index {i} must be a number.'}), 400
        if not isinstance(setting.get("isActive"), bool):
             return jsonify({'error': f'Emotion setting "isActive" at index {i} must be a boolean.'}), 400

    try:
        # Create the new configuration directly from the input
        new_config = {
            "deviceOn": device_on,
            "emotions": emotions_settings
        }
        save_device_config(new_config)
        return jsonify({'message': 'Device configuration updated successfully'}), 200
    except Exception as e:
        print(f"Error in /upload-manual: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/device', methods=['GET'])
def get_device_data():
    try:
        config = get_device_config() # This will return the dict with "deviceOn" and "emotions"
        return jsonify(config), 200
    except Exception as e:
        print(f"Error in /device: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
