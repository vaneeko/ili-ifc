import logging
from flask import Flask, render_template, request, jsonify, send_file
import os
import time
import signal
import sys
from controllers.conversion_controller import handle_conversion_request, BASE_TEMP_DIR
from utils.cleanup import cleanup_old_files, remove_pycache
from config.default_config import DEFAULT_CONFIG
import threading

app = Flask(__name__, 
            template_folder='views/templates',
            static_folder='views/static')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_exit_signal(sig, frame):
    logger.info('Shutting down and cleaning up...')
    remove_pycache()
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, handle_exit_signal)
signal.signal(signal.SIGTERM, handle_exit_signal)

cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

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
    
    result = handle_conversion_request(config, request.files)
    return jsonify(result)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(BASE_TEMP_DIR, filename)
    logger.info(f'Trying to send file: {file_path}')
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