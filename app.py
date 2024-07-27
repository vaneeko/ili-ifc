import logging
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_exit_signal(sig, frame):
    logger.info('Shutting down and cleaning up...')
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
    
    file = request.files['xtfFile']
    if file.filename == '':
        return jsonify({'error': 'Keine Datei ausgewählt'}), 400
    
    if file and file.filename.endswith('.xtf'):
        filename = os.path.join(BASE_TEMP_DIR, file.filename)
        file.save(filename)
        
        config_values = read_config()
        parser = XTFParser()
        try:
            data = parser.parse(filename, config_values)
            return jsonify(data)
        except Exception as e:
            logger.error(f"Fehler beim Parsen der XTF-Datei: {str(e)}")
            return jsonify({'error': 'Fehler beim Parsen der XTF-Datei'}), 500
        finally:
            os.remove(filename)
    
    return jsonify({'error': 'Ungültiger Dateityp'}), 400

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