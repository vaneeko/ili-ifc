import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
from models.xtf_model import XTFParser
from models.ifc_model import create_ifc
from utils.common import read_config

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')

def get_xtf_files(xtf_path):
    if os.path.isdir(xtf_path):
        return [os.path.join(xtf_path, file) for file in os.listdir(xtf_path) if file.endswith('.xtf')]
    return [xtf_path]

def convert_xtf_to_ifc(xtf_file, ifc_file, config):
    parser = XTFParser()
    data = parser.parse(xtf_file, config)

    create_ifc(ifc_file, data)
    logging.info(f"IFC file saved: {ifc_file}")

def delete_pycache():
    pycache_path = os.path.join(os.path.dirname(__file__), '__pycache__')
    if os.path.exists(pycache_path):
        shutil.rmtree(pycache_path)
        logging.info(f"__pycache__ folder deleted: {pycache_path}")

if __name__ == '__main__':
    setup_logging()
    logging.info("Program start")
    
    config = read_config()

    xtf_path = config.get('xtf_files', 'C:\\converter\\xtf\\')
    xtf_files = get_xtf_files(xtf_path)
    output_folder = config.get('output_folder', 'C:\\converter\\')

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for xtf_file_path in xtf_files:
        xtf_file_name = os.path.basename(xtf_file_path)
        ifc_file_name = os.path.splitext(xtf_file_name)[0] + '.ifc'
        ifc_file_path = os.path.join(output_folder, ifc_file_name)

        logging.info(f"XTF file path: {xtf_file_path}")
        logging.info(f"IFC file path: {ifc_file_path}")

        try:
            convert_xtf_to_ifc(xtf_file_path, ifc_file_path, config)
        except Exception as e:
            logging.error(f"Error during XTF to IFC conversion: {e}", exc_info=True)

    delete_pycache()