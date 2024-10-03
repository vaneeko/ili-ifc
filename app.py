import logging
import json
from flask import Flask, render_template, request, jsonify, send_file
import os
import time
import signal
import sys
from controllers.conversion_controller import handle_conversion_request, BASE_TEMP_DIR
from utils.cleanup import cleanup_old_files, remove_pycache
from utils.common import read_config
import threading
from models.xtf_model import XTFParser

app = Flask(__name__, 
            template_folder='views/templates',
            static_folder='views/static')

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def handle_exit_signal(sig, frame):
    # logger.info('Shutting down and cleaning up...')
    remove_pycache()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit_signal)
signal.signal(signal.SIGTERM, handle_exit_signal)

cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/')
def index():
    config = read_config()
    return render_template('index.html', config=config)

@app.route('/convert', methods=['POST'])
def convert():
    config_values = read_config()
    config = {
        'default_sohlenkote': float(request.form.get('default_sohlenkote', config_values['default_sohlenkote'])),
        'default_durchmesser': float(request.form.get('default_durchmesser', config_values['default_durchmesser'])),
        'default_hoehe': float(request.form.get('default_hoehe', config_values['default_hoehe'])),
        'default_wanddicke': float(request.form.get('default_wanddicke', config_values['default_wanddicke'])),
        'default_bodendicke': float(request.form.get('default_bodendicke', config_values['default_bodendicke'])),
        'default_rohrdicke': float(request.form.get('default_rohrdicke', config_values['default_rohrdicke'])),
        'einfaerben': request.form.get('einfaerben', config_values['einfaerben']) == 'true'
    }

    try:
        result = handle_conversion_request(config, request.files)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Fehler bei der Konvertierung: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/extract', methods=['POST'])
def extract_data():
    if 'xtfFile' not in request.files:
        return jsonify({'error': 'Keine Datei ausgewählt'}), 400
    
    files = request.files.getlist('xtfFile')
    if not files:
        return jsonify({'error': 'Keine Datei ausgewählt'}), 400
    
    config_values = read_config()
    parser = XTFParser()
    all_data = {'models': {}}

    try:
        for file in files:
            logging.info(f"Processing file: {file.filename}")
            if file and file.filename.endswith('.xtf'):
                filename = os.path.join(BASE_TEMP_DIR, file.filename)
                file.save(filename)
                
                data = parser.parse(filename, config_values)
                model_name = data.get('model', 'Unbekanntes Modell')
                logging.info(f"Extracted model: {model_name}")
                all_data['models'][model_name] = data

                # Temporäre Datei nicht löschen, damit sie für DataTables verfügbar bleibt
                # os.remove(filename)

        logging.info(f"All extracted models: {list(all_data['models'].keys())}")
        logging.info(f"Extracted data: {json.dumps(all_data, default=str, indent=2)}")
        return jsonify(all_data)
    except Exception as e:
        logger.error(f"Fehler beim Parsen der XTF-Datei(en): {str(e)}", exc_info=True)
        return jsonify({'error': f'Fehler beim Parsen der XTF-Datei(en): {str(e)}'}), 500

@app.route('/get_datatable_data', methods=['GET'])
def get_datatable_data():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': 'Kein Dateiname angegeben'}), 400

    file_path = os.path.join(BASE_TEMP_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Datei nicht gefunden'}), 404

    config_values = read_config()
    parser = XTFParser()

    try:
        data = parser.parse(file_path, config_values)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Fehler beim Parsen der Datei {filename}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Fehler beim Parsen der Datei: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(BASE_TEMP_DIR, filename)
    logger.info(f'Trying to send file: {file_path}')
    for i in range(5):
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