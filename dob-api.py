import os
import io
import sys
import fnmatch
import json
import base64
import requests
from PIL import Image, ImageDraw, ImageOps
from flask import Flask, request, jsonify
from google.cloud import secretmanager
from firebase_admin import credentials, firestore, initialize_app, storage

# Global constants
PROJECT_ID="dob-gae-test"
GOOGLE_CLOUD_PROJECT_NUMBER=1088427128533
FIREBASE_SA_SECRET_NAME="firebase-dobconfig-test"
FIREBASE_SA_SECRET_VERSION="1"
VERSION_STRING="0.3"
APPLICATION_NAME="dob-api-test"

def image_to_bytes(image):
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format=image.format)
    return imgByteArr.getvalue()

def image_to_base64(image):
    return base64.b64encode(image_to_bytes(image)).decode('utf-8')

def base64_to_image(image_base64):
    return Image.open(io.BytesIO(base64.b64decode(image_base64.encode('utf-8'))))

def get_position_size(position):
    return (int(position["width"]), int(position["height"]))

def get_position_left_top(position):
    return (int(position["left"]), int(position["top"]))

def get_position_rectangle(position):
    top = int(position["top"])
    left = int(position["left"])
    bottom = top + int(position["height"])
    right = left + int(position["width"])
    return [(left, top), (right, bottom)]

def get_template(config_data, template_name):
    for item in config_data["templates"]:
        if item["templateName"] == template_name:
            return item
    return False

def get_design(config_data, design_name):
    for item in config_data["designs"]:
        if item["designName"] == design_name:
            return item
    return False

def get_position_def(config_data, position_name):
    for item in config_data["positions"]:
        if item["positionName"] == position_name:
            return item
    return False

def fill_in_height(config_data, position_name, position):
    position_def = get_position_def(config_data, position_name)
    height = 0
    if not position_def:
        height = position["width"]
    elif not (position_def["arWidth"] or position_def["arWidth"]==0):
        height = position["width"]
    else:
        height = position["width"] / position_def["arWidth"] * position_def["arHeight"]
    position["height"] = height
    return position

def get_position(config_data, template, position_name):
    if not template:
        return False
    for pos_item in template["positions"]:
        if pos_item["positionName"] == position_name:
            return fill_in_height( config_data, position_name, pos_item )
    return False

def put_image_on_position(template, position, design):
    #open template photo
    response = requests.get(template["imageUrl"])
    img_template = Image.open(io.BytesIO(response.content))
    #open design, convert to grayscale and set size for position
    response = requests.get(design["imageUrl"])
    img_design = Image.open(io.BytesIO(response.content)).convert("L").resize(get_position_size(position))
    #inverted image
    img_design_inverted = ImageOps.invert(img_design)
    #mask with alpha
    img_mask = img_design_inverted.copy()
    img_mask.putalpha(img_design_inverted)
    #paste template with design, applying mask
    img_template.paste(img_design, get_position_left_top(position), mask=img_mask)
    #return result
    return img_template

def put_position_outline(template, position):
    #open template photo
    response = requests.get(template["imageUrl"])
    img_template = Image.open(io.BytesIO(response.content))
    #draw position outline
    draw = ImageDraw.Draw(img_template, "RGBA")
    draw.rectangle(get_position_rectangle(position), fill=(255,164,0,127))
    draw.rectangle(get_position_rectangle(position), outline=(255,164,0,255), width=3)
    #return result
    return img_template

def paste_image_on_position(config_data, template_name, position_name, design_name):
    #get and check template and position
    template = get_template(config_data, template_name)
    position = get_position(config_data, template, position_name)
    design = get_design(config_data, design_name)
    if not template or not position or not design:
        return False
    #paste
    image = put_image_on_position(template, position, design)
    #return encoded
    return image_to_base64(image)

def show_position_on_template(config_data, template_name, position_name):
    #get and check template and position
    template = get_template(config_data, template_name)
    position = get_position(config_data, template, position_name)
    if not template or not position:
        return False
    #show position
    image = put_position_outline(template, position)
    #return encoded
    return image_to_base64(image)

def load_collection(firestore_client, collection_name):
    col_ref = firestore_client.collection(collection_name)
    col_stream = col_ref.stream()
    col_data = []
    for doc in col_stream:
        doc_dict = doc.to_dict()
        doc_dict["id"] = doc.id
        col_data.append(doc_dict)
    return col_data

def get_customer_id(users_data, api_key):
    for item in users_data:
        if item["apiKey"] == api_key:
            return item["customerId"]
    return False

def get_customer_config_data(customers_data, users_data, api_key):
    customer_id = get_customer_id(users_data, api_key)
    if not customer_id:
        return False
    for item in customers_data:
        if item["id"] == customer_id:
            return item
    return False

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
    customers_data = load_collection(firestore_client, "customers")
    users_data = load_collection(firestore_client, "users")
except Exception as e:
    print(f"Error connecting to Firebase: {e}")
    exit()

# /show_position
@app.route('/show_position', methods=['POST'])
def show_position():
    try:
        # Authorization
        api_key = request.headers.get("x-api-key")
        if not api_key or not get_customer_id(users_data, api_key):
            return jsonify({'error': 'Unauthorized.'}), 401
        # Parameters
        data = request.get_json()
        template_name = data.get("template")
        position_name = data.get("position")
        # Check if the required parameters are present in the request.
        if not template_name or not position_name:
            return jsonify({'error': 'Invalid request. Chybí parametry.'}), 400
        # Validate parameters
        config_data = get_customer_config_data(customers_data, users_data, api_key)
        if not config_data:
            return jsonify({'error': 'Nenalezena konfigurace klienta.'}), 404
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
        # Authorization
        api_key = request.headers.get("x-api-key")
        if not api_key or not get_customer_id(users_data, api_key):
            return jsonify({'error': 'Unauthorized.'}), 401
        # Parameters
        data = request.get_json()
        template_name = data.get("template")
        position_name = data.get("position")
        design_name = data.get("design")
        # Check if the required parameters are present in the request.
        if not template_name or not position_name or not design_name:
            return jsonify({'error': 'Invalid request. Missing parameters.'}), 400
        # Validate parameters
        config_data = get_customer_config_data(customers_data, users_data, api_key)
        if not config_data:
            return jsonify({'error': 'Nenalezena konfigurace klienta.'}), 404
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
        # Authorization
        api_key = request.headers.get("x-api-key")
        if not api_key or not get_customer_id(users_data, api_key):
            return jsonify({'error': 'Unauthorized.'}), 401
        # Return the result as base64 encoded data.
        return jsonify({'version': VERSION_STRING}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# /configuration
@app.route('/users')
def show_users(): 
    try:
        # Authorization
        api_key = request.headers.get("x-api-key")
        if not api_key or not get_customer_id(users_data, api_key):
            return jsonify({'error': 'Unauthorized.'}), 401
        # Return the result as base64 encoded data.
        return jsonify({'users': users_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# /customers
@app.route('/customers')
def show_customers(): 
    try:
        # Authorization
        api_key = request.headers.get("x-api-key")
        if not api_key or not get_customer_id(users_data, api_key):
            return jsonify({'error': 'Unauthorized.'}), 401
        # Return the result as base64 encoded data.
        return jsonify({'customers': customers_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# /
@app.route('/')
def show_info():
    try:
        # Authorization
        api_key = request.headers.get("x-api-key")
        if not api_key or not get_customer_id(users_data, api_key):
            return jsonify({'error': 'Unauthorized.'}), 401
        # Return the result as base64 encoded data.
        return jsonify({'application': APPLICATION_NAME}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# main
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

