from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import shutil
from werkzeug.utils import secure_filename
from data_parser_xtf import XTFParser
from ifc_generator import create_ifc
from default_values import read_config
import threading
import time

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'xtf'}
BASE_TEMP_DIR = os.path.join(tempfile.gettempdir(), 'ifc_converter_temp')
FILE_LIFETIME = 600  # 10 minutes

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_temp_dir():
    if not os.path.exists(BASE_TEMP_DIR):
        os.makedirs(BASE_TEMP_DIR)
    print(f"Ensured temporary directory: {BASE_TEMP_DIR}")

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
        print(f"Contents of {path}: {files}")
    except FileNotFoundError:
        print(f"Directory not found: {path}")

cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/')
def index():
    config = read_config()
    return render_template('index.html', config=config)

@app.route('/convert', methods=['POST'])
def convert():
    ensure_temp_dir()
    
    if 'xtfFiles' not in request.files:
        return jsonify({'error': 'Keine Dateien ausgewählt'}), 400
    
    files = request.files.getlist('xtfFiles')

    # Lese die angepassten Konfigurationswerte aus dem Formular
    config = {
        'default_sohlenkote': float(request.form.get('default_sohlenkote')),
        'default_durchmesser': float(request.form.get('default_durchmesser')),
        'default_hoehe': float(request.form.get('default_hoehe')),
        'default_wanddicke': float(request.form.get('default_wanddicke')),
        'default_bodendicke': float(request.form.get('default_bodendicke')),
        'default_rohrdicke': float(request.form.get('default_rohrdicke')),
        'einfaerben': request.form.get('einfaerben') == 'true'
    }

    converted_files = []
    errors = []
    download_links = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            xtf_path = os.path.join(BASE_TEMP_DIR, filename)

            file.save(xtf_path)
            print(f'File saved to {xtf_path}')
            list_directory(BASE_TEMP_DIR)

            try:
                parser = XTFParser()
                data = parser.parse(xtf_path)
                
                # Füge die Konfigurationswerte zu den Daten hinzu
                data.update(config)
                
                ifc_filename = os.path.splitext(filename)[0] + '.ifc'
                ifc_path = os.path.join(BASE_TEMP_DIR, ifc_filename)
                
                create_ifc(ifc_path, data, config['einfaerben'])
                time.sleep(1)  # Wait for a second to ensure file is created

                if os.path.exists(ifc_path):
                    print(f'IFC file successfully created: {ifc_path}')
                    list_directory(BASE_TEMP_DIR)
                    converted_files.append(ifc_filename)
                    
                    # Generiere Download-Link
                    download_links.append({
                        'url': f'/download/{ifc_filename}',
                        'filename': ifc_filename
                    })
                else:
                    print(f'Failed to create IFC file: {ifc_path}')
                    list_directory(BASE_TEMP_DIR)
            except Exception as e:
                errors.append(f'Fehler bei der Konvertierung von {filename}: {str(e)}')
            finally:
                # Entferne die temporäre XTF-Datei
                if os.path.exists(xtf_path):
                    os.remove(xtf_path)
                else:
                    print(f'Failed to remove XTF file: {xtf_path}')

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
    print(f'Trying to send file: {file_path}')
    list_directory(BASE_TEMP_DIR)
    for i in range(5):  # Check up to 5 times, waiting each time
        if os.path.exists(file_path):
            print('File exists and will be sent')
            return send_file(file_path, as_attachment=True)
        else:
            print(f'File not found, waiting ({i + 1}/5)')
            time.sleep(1)
    print('File not found after waiting')
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)
