import logging
from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import shutil
from werkzeug.utils import secure_filename
from data_parser_xtf import XTFParser
from ifc_generator import create_ifc
import threading
import time
import signal
import sys

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'xtf'}
BASE_TEMP_DIR = '/tmp/ifc_converter_temp'
FILE_LIFETIME = 600  # 10 minutes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_temp_dir():
    if not os.path.exists(BASE_TEMP_DIR):
        os.makedirs(BASE_TEMP_DIR)
    logger.info(f"Ensured temporary directory: {BASE_TEMP_DIR}")

def cleanup_old_files():
    while True:
        now = time.time()
        for filename in os.listdir(BASE_TEMP_DIR):
            file_path = os.path.join(BASE_TEMP_DIR, filename)
            if os.path.isfile(file_path) and now - os.path.getmtime(file_path) > FILE_LIFETIME:
                os.remove(file_path)
        time.sleep(60)  # Check every minute

def list_directory(path):
    try:
        files = os.listdir(path)
        logger.info(f"Contents of {path}: {files}")
    except FileNotFoundError:
        logger.error(f"Directory not found: {path}")

def remove_pycache():
    # Remove the __pycache__ directory
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                shutil.rmtree(os.path.join(root, dir_name), ignore_errors=True)
                logger.info(f"Removed __pycache__ directory: {os.path.join(root, dir_name)}")

def handle_exit_signal(sig, frame):
    logger.info('Shutting down and cleaning up...')
    remove_pycache()
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, handle_exit_signal)
signal.signal(signal.SIGTERM, handle_exit_signal)

cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

DEFAULT_CONFIG = {
    'default_sohlenkote': 405.0,
    'default_durchmesser': 0.8,
    'default_hoehe': 0.8,
    'default_wanddicke': 0.04,
    'default_bodendicke': 0.02,
    'default_rohrdicke': 0.02,
    'einfaerben': False
}

@app.route('/')
def index():
    return render_template('index.html', config=DEFAULT_CONFIG)

@app.route('/convert', methods=['POST'])
def convert():
    config = {
        'default_sohlenkote': float(request.form.get('default_sohlenkote', DEFAULT_CONFIG['default_sohlenkote'])),
        'default_durchmesser': float(request.form.get('default_durchmesser', DEFAULT_CONFIG['default_durchmesser'])),
        'default_hoehe': float(request.form.get('default_hoehe', DEFAULT_CONFIG['default_hoehe'])),
        'default_wanddicke': float(request.form.get('default_wanddicke', DEFAULT_CONFIG['default_wanddicke'])),
        'default_bodendicke': float(request.form.get('default_bodendicke', DEFAULT_CONFIG['default_bodendicke'])),
        'default_rohrdicke': float(request.form.get('default_rohrdicke', DEFAULT_CONFIG['default_rohrdicke'])),
        'einfaerben': request.form.get('einfaerben', DEFAULT_CONFIG['einfaerben']) == 'true'
    }
    
    ensure_temp_dir()
    
    if 'xtfFiles' not in request.files:
        return jsonify({'error': 'Keine Dateien ausgewählt'}), 400
    
    files = request.files.getlist('xtfFiles')

    converted_files = []
    errors = []
    download_links = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            xtf_path = os.path.join(BASE_TEMP_DIR, filename)

            try:
                file.save(xtf_path)
                logger.info(f'File saved to {xtf_path}')
                list_directory(BASE_TEMP_DIR)

                parser = XTFParser()
                data = parser.parse(xtf_path, config)
                
                ifc_filename = os.path.splitext(filename)[0] + '.ifc'
                ifc_path = os.path.join(BASE_TEMP_DIR, ifc_filename)
                
                create_ifc(ifc_path, data)
                time.sleep(1)  # Wait for a second to ensure file is created

                if os.path.exists(ifc_path):
                    logger.info(f'IFC file successfully created: {ifc_path}')
                    list_directory(BASE_TEMP_DIR)
                    converted_files.append(ifc_filename)
                    
                    # Generiere Download-Link
                    download_links.append({
                        'url': f'/download/{ifc_filename}',
                        'filename': ifc_filename
                    })
                else:
                    logger.error(f'Failed to create IFC file: {ifc_path}')
                    list_directory(BASE_TEMP_DIR)
            except Exception as e:
                logger.error(f'Fehler bei der Konvertierung von {filename}: {str(e)}')
                errors.append(f'Fehler bei der Konvertierung von {filename}: {str(e)}')
            finally:
                # Entferne die temporäre XTF-Datei
                if os.path.exists(xtf_path):
                    os.remove(xtf_path)
                else:
                    logger.error(f'Failed to remove XTF file: {xtf_path}')

    if converted_files:
        success_message = f'Erfolgreich konvertierte Dateien: {", ".join(converted_files)}'
    else:
        success_message = 'Keine Dateien wurden konvertiert.'

    if errors:
        error_message = '\n'.join(errors)
    else:
        error_message = ''

    return jsonify({
        'message': success_message,
        'errors': error_message,
        'downloadLinks': download_links
    })

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(BASE_TEMP_DIR, filename)
    logger.info(f'Trying to send file: {file_path}')
    list_directory(BASE_TEMP_DIR)
    for i in range(5):  # Check up to 5 times, waiting each time
        if os.path.exists(file_path):
            logger.info('File exists and will be sent')
            return send_file(file_path, as_attachment=True)
        else:
            logger.warning(f'File not found, waiting ({i + 1}/5)')
            time.sleep(1)
    logger.error('File not found after waiting')
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)