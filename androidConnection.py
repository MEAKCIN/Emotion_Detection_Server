# Python
from flask import Flask, request, jsonify
import base64
import os
import emotion_detection

app = Flask(__name__)

# Define a directory to save uploads (optional but good practice)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    # Ensure the request contains JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415  # Use 415 for unsupported media type

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body provided'}), 400

    photo_data = data.get('photo')
    if not photo_data:
        return jsonify({'error': 'No photo field provided'}), 400

    try:
        # Remove data URL header if present, e.g. "data:image/jpeg;base64,"
        if isinstance(photo_data, str) and photo_data.startswith("data:image"):
            header, encoded_data = photo_data.split(',', 1)
            photo_data = encoded_data  # Use only the base64 part

        # Decode the base64 string
        image_bytes = base64.b64decode(photo_data)

        # Process image with the emotion_detection module
        emotion = emotion_detection.detect_emotion_from_image(image_bytes)
        print(emotion)

        # Read current device.txt values
        try:
            with open('device.txt', 'r', encoding='utf-8') as file:
                device_data = file.read().strip()
                spray_period, spray_duration, device_on, _ = device_data.split(',')
        except Exception:
            # If file doesn't exist or is invalid, use defaults
            spray_period, spray_duration, device_on = '', '', ''

        # Write updated values back to device.txt
        with open('device.txt', 'w', encoding='utf-8') as file:
            file.write(f"{spray_period},{spray_duration},{device_on},{emotion}\n")

        return jsonify({'message': 'Everything is okay', 'emotion': emotion}), 200

    except base64.binascii.Error as e:
        return jsonify({'error': f'Invalid base64 data: {str(e)}'}), 400

@app.route('/upload-manual', methods=['POST'])
def upload_manual():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body provided'}), 400

    # Extract fields with defaults if missing
    spray_period = data.get('sprayPeriod', '')
    spray_duration = data.get('sprayDuration', '')
    device_on = data.get('deviceOn', '')
    current_emotion = data.get('currentEmotion', '')

    # Create the line to write
    line = f"{spray_period},{spray_duration},{device_on},{current_emotion}\n"

    # Write to device.txt (overwrite)
    with open('device.txt', 'w', encoding='utf-8') as f:
        f.write(line)

    return jsonify({'message': 'device.txt updated successfully'}), 200

@app.route('/device', methods=['GET'])
def get_device_data():
    try:
        with open('device.txt', 'r') as file:
            data = file.read().strip()
            # Split the comma-separated values
            spray_period, spray_duration, device_on, current_emotion = data.split(',')
            
            # Create a response dictionary
            response = {
                'sprayPeriod': spray_period,
                'sprayDuration': spray_duration,
                'deviceOn': device_on,
                'currentEmotion': current_emotion
            }
            
            return jsonify(response), 200
    except FileNotFoundError:
        return jsonify({'error': 'device.txt file not found'}), 404
    except ValueError:
        return jsonify({'error': 'Invalid data format in device.txt'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

