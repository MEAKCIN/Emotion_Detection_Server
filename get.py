# Python
from flask import Flask, request, jsonify
import base64
import os
import deneme

app = Flask(__name__)

# Define a directory to save uploads (optional but good practice)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
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

        # Process image with the ʹdenemeʹ module
        emotion = deneme.detect_emotion_from_image(image_bytes)
        print(emotion)

        return jsonify({'message': 'Everything is okay', 'emotion': emotion}), 200

    except base64.binascii.Error as e:
        return jsonify({'error': f'Invalid base64 data: {str(e)}'}), 400

@app.route('/upload_try', methods=['POST'])
def upload_try():
    print("Received request on /upload_try")
    print(request.get_json())
    return "completed", 200

if __name__ == '__main__':
    # Debug=True for development; disable or set to False for production
    app.run(host='0.0.0.0', port=5000, debug=True)