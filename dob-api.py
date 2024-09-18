import os
import json
from flask import Flask, request, jsonify
from google.cloud import secretmanager
from firebase_admin import credentials, firestore, initialize_app, storage
from dob import paste_image_on_position, show_position_on_template, get_template, get_position, get_design

# Global constants
PROJECT_ID = "dob-gae-test"
GOOGLE_CLOUD_PROJECT_NUMBER = 1088427128533
FIREBASE_SA_SECRET_NAME = "firebase-dobconfig-test"
FIREBASE_SA_SECRET_VERSION = "1"
CUSTOMER_ID = "zenavico.cz"
VERSION_STRING = "0.2"
APPLICATION_NAME = "dob-api-test"

# Initialize Flask app
app = Flask(__name__)

# Get data from secret manager
try:
    sec_client = secretmanager.SecretManagerServiceClient()
    name = sec_client.secret_version_path(GOOGLE_CLOUD_PROJECT_NUMBER, FIREBASE_SA_SECRET_NAME, FIREBASE_SA_SECRET_VERSION)
    response = sec_client.access_secret_version(name=name)
    service_account_info = json.loads(response.payload.data.decode('utf-8'))
except Exception as e:
    print(f"Error getting secrets: {e}")
    exit()

# Initialize Firestore
try:
    cred = credentials.Certificate(service_account_info)
    initialize_app(cred)
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection("customers").document("zenavico.cz")
    config_data = doc_ref.get().to_dict()
except Exception as e:
    print(f"Error connecting to Firebase: {e}")
    exit()

# /show_position
@app.route('/show_position', methods=['POST'])
def show_position():
    try:
        data = request.get_json()
        template_name = data.get("template")
        position_name = data.get("position")
        # Check if the required parameters are present in the request.
        if not template_name or not position_name:
            return jsonify({'error': 'Invalid request. Chybí parametry.'}), 400
        # Validate parameters
        template = get_template(config_data, template_name)
        if not template:
            return jsonify({'error': 'Neznámý podklad.'}), 404
        if not get_position(config_data, template, position_name):
            return jsonify({'error': 'Obrázek na podkladu nenalezen.'}), 404
        # Call the function to combine the images.
        combined_image = show_position_on_template(config_data, template_name, position_name)
        # Return the result as base64 encoded data.
        return jsonify({'podklad_obrazek': combined_image}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# /generate_mockup
@app.route('/generate_mockup', methods=['POST'])
def paste_image():
    try:
        data = request.get_json()
        template_name = data.get("template")
        position_name = data.get("position")
        design_name = data.get("design")
        # Check if the required parameters are present in the request.
        if not template_name or not position_name or not design_name:
            return jsonify({'error': 'Invalid request. Missing parameters.'}), 400
        # Validate parameters
        template = get_template(config_data, template_name)
        if not template:
            return jsonify({'error': 'Neznámý podklad.'}), 404
        if not get_position(config_data, template, position_name):
            return jsonify({'error': 'Obrázek na podkladu nenalezen.'}), 404
        if not get_design(config_data, design_name):
            return jsonify({'error': 'Neznámý vzor.'}), 404
        # Call the function to combine the images.
        combined_image = paste_image_on_position(config_data, template_name, position_name, design_name)
        # Return the result as base64 encoded data.
        return jsonify({'mockup': combined_image}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# /version
@app.route('/version')
def show_version():
    try:
        # Return the result as base64 encoded data.
        return jsonify({'version': VERSION_STRING}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# /configuration
@app.route('/configuration')
def show_config(): 
    try:
        return jsonify({'configuration': config_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# /
@app.route('/')
def show_info():
    try:
        # Return the result as base64 encoded data.
        return jsonify({'application': APPLICATION_NAME}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# main
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

