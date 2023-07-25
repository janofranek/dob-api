import os
from flask import Flask, request, jsonify
from dob import paste_image_on_position, show_position_on_template, get_template, get_position

app = Flask(__name__)

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
        if not get_template(template_name):
            return jsonify({'error': 'Neznámý vzor.'}), 404
        if not get_position(template_name, position_name):
            return jsonify({'error': 'Pozice ve vzoru nenalezena.'}), 404

        # Call the function to combine the images.
        combined_image = show_position_on_template(template_name, position_name)

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
        if not get_template(template_name):
            return jsonify({'error': 'Neznámý vzor.'}), 404
        if not get_position(template_name, position_name):
            return jsonify({'error': 'Pozice ve vzoru nenalezena.'}), 404

        # Call the function to combine the images.
        combined_image = paste_image_on_position(template_name, position_name, image_base64)

        # Return the result as base64 encoded data.
        return jsonify({'combined_image': combined_image}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verze')
def show_version():
    try:
        version = "0.0.1"

        # Return the result as base64 encoded data.
        return jsonify({'verze': version}), 200

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
