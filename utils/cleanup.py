import os
import time
import shutil
import logging

logger = logging.getLogger(__name__)

BASE_TEMP_DIR = '/tmp/ifc_converter_temp'
FILE_LIFETIME = 600  # 10 minutes

def cleanup_old_files():
    while True:
        now = time.time()
        for filename in os.listdir(BASE_TEMP_DIR):
            file_path = os.path.join(BASE_TEMP_DIR, filename)
            if os.path.isfile(file_path) and now - os.path.getmtime(file_path) > FILE_LIFETIME:
                os.remove(file_path)
        time.sleep(60)  # Check every minute

def remove_pycache():
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                shutil.rmtree(os.path.join(root, dir_name), ignore_errors=True)
                logger.info(f"Removed __pycache__ directory: {os.path.join(root, dir_name)}")

def list_directory(path):
    try:
        files = os.listdir(path)
        logger.info(f"Contents of {path}: {files}")
    except FileNotFoundError:
        logger.error(f"Directory not found: {path}")