import os
import time
import shutil
import logging
from controllers.conversion_controller import BASE_TEMP_DIR, FILE_LIFETIME, list_directory

logger = logging.getLogger(__name__)

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
                # logger.info(f"Removed __pycache__ directory: {os.path.join(root, dir_name)}")