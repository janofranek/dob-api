import os
import json
from flask import Flask, request, jsonify
from google.cloud import secretmanager
from firebase_admin import credentials, firestore, initialize_app, storage
from dob import paste_image_on_position, show_position_on_template, get_template, get_position, test_paste, test_show

# Global constants
PROJECT_ID = "dobappgae"
GOOGLE_CLOUD_PROJECT_NUMBER = 330540757080
FIREBASE_SA_SECRET_NAME = "firebase"
FIREBASE_SA_SECRET_VERSION = "1"
CUSTOMER_ID = "zenavico.cz"

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

# Placeholder for the overlay image stored in the service's configuration.
# You can replace this with the actual path or data for the overlay image.
# For simplicity, let's assume we have a file named 'overlay_image.png'.
overlay_image_filename = 'overlay_image.png'


@app.route('/ukaz_pozici', methods=['POST'])
def show_position():
    try:
        data = request.get_json()
        template_name = data.get("vzor")
        position_name = data.get("pozice")

        # Check if the required parameters are present in the request.
        if not template_name or not position_name:
            return jsonify({'error': 'Invalid request. Chybí parametry.'}), 400

        # Validate parameters
        if not get_template(config_data, template_name):
            return jsonify({'error': 'Neznámý vzor.'}), 404
        if not get_position(config_data, template_name, position_name):
            return jsonify({'error': 'Pozice ve vzoru nenalezena.'}), 404

        # Call the function to combine the images.
        combined_image = show_position_on_template(config_data, template_name, position_name)

        # Return the result as base64 encoded data.
        return jsonify({'vzor_pozice': combined_image}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/nalep_obrazek', methods=['POST'])
def paste_image():
    try:
        data = request.get_json()
        template_name = data.get("vzor")
        position_name = data.get("pozice")
        image_base64 = data.get("pozice")

        # Check if the required parameters are present in the request.
        if not template_name or not position_name or not image_base64:
            return jsonify({'error': 'Invalid request. Missing parameters.'}), 400

        # Validate parameters
        if not get_template(config_data, template_name):
            return jsonify({'error': 'Neznámý vzor.'}), 404
        if not get_position(config_data, template_name, position_name):
            return jsonify({'error': 'Pozice ve vzoru nenalezena.'}), 404

        # Call the function to combine the images.
        combined_image = paste_image_on_position(config_data, template_name, position_name, image_base64)

        # Return the result as base64 encoded data.
        return jsonify({'combined_image': combined_image}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verze')
def show_version():
    try:
        version = "0.0.2"

        # Return the result as base64 encoded data.
        return jsonify({'verze': version}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/konfigurace')
def show_config(): 
    try:
        return jsonify({'konfigurace': config_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def show_info():
    try:
        app = "DOB API"

        # Return the result as base64 encoded data.
        return jsonify({'aplikace': app}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

#TEST
# test_paste(config_data, "Dívka v černém tričku", "vepředu vlevo nahoře", "./pics/srdicko.jpg")
# test_show(config_data, "Dívka v černém tričku", "vepředu vlevo nahoře")
