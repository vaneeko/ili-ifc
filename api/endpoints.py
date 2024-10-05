from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from controllers.conversion_controller import handle_conversion_request
from utils.common import read_config

# Blueprint API
api = Blueprint('api', __name__)

# Define upload folder and create it if it doesn't exist
UPLOAD_FOLDER = '/tmp/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Global variable for current configuration, initialized with default values
current_config = read_config()

# Endpoint for converting XTF files to IFC. Accepts XTF files and optional configuration parameters.
@api.route('/convert', methods=['POST'])
def convert():
    if 'xtfFiles' not in request.files:
        return jsonify({'error': 'Keine Dateien ausgewählt'}), 400
    
    files = request.files.getlist('xtfFiles')
    
    # Create a copy of the current configuration and update with values from the request
    config = current_config.copy()
    for key in config.keys():
        if key in request.form:
            config[key] = type(config[key])(request.form.get(key))
    
    # Save uploaded files
    saved_files = []
    for file in files:
        if file and file.filename.endswith('.xtf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            saved_files.append(file_path)
    
    # Perform conversion
    result = handle_conversion_request(config, saved_files)
    
    return jsonify(result)

@api.route('/config', methods=['GET'])
def get_config():
    return jsonify(current_config)

@api.route('/config', methods=['POST'])
def update_config():
    global current_config
    for key, value in request.json.items():
        if key in current_config:
            try:
                # Try to convert the value to the correct type
                current_config[key] = type(current_config[key])(value)
            except ValueError:
                return jsonify({'error': f'Ungültiger Wert für {key}'}), 400
    return jsonify(current_config), 200

@api.route('/config/reset', methods=['POST'])
def reset_config():
    global current_config
    current_config = read_config()
    return jsonify(current_config), 200

@api.route('/config/<key>', methods=['GET'])
def get_config_value(key):
    if key in current_config:
        return jsonify({key: current_config[key]})
    return jsonify({'error': 'Konfigurationsschlüssel nicht gefunden'}), 404

@api.route('/config/<key>', methods=['PUT'])
def update_config_value(key):
    global current_config
    if key in current_config:
        try:
            value = request.json.get('value')
            # Convert the value to the correct type
            current_config[key] = type(current_config[key])(value)
            return jsonify({key: current_config[key]})
        except ValueError:
            return jsonify({'error': 'Ungültiger Wert'}), 400
    return jsonify({'error': 'Konfigurationsschlüssel nicht gefunden'}), 404