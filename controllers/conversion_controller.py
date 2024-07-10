import os
import logging
from werkzeug.utils import secure_filename
from models.xtf_model import XTFParser
from models.ifc_model import create_ifc
import time
from utils.cleanup import list_directory

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'xtf'}
BASE_TEMP_DIR = '/tmp/ifc_converter_temp'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_temp_dir():
    if not os.path.exists(BASE_TEMP_DIR):
        os.makedirs(BASE_TEMP_DIR)
    logger.info(f"Ensured temporary directory: {BASE_TEMP_DIR}")

def handle_conversion_request(config, files):
    ensure_temp_dir()
    
    if 'xtfFiles' not in files:
        return {'error': 'Keine Dateien ausgewählt'}, 400
    
    files = files.getlist('xtfFiles')

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
                if os.path.exists(xtf_path):
                    os.remove(xtf_path)
                else:
                    logger.error(f'Failed to remove XTF file: {xtf_path}')

    return prepare_response(converted_files, errors, download_links)

def prepare_response(converted_files, errors, download_links):
    if converted_files:
        success_message = f'Erfolgreich konvertierte Dateien: {", ".join(converted_files)}'
    else:
        success_message = 'Keine Dateien wurden konvertiert.'

    error_message = '\n'.join(errors) if errors else ''

    return {
        'message': success_message,
        'errors': error_message,
        'downloadLinks': download_links
    }