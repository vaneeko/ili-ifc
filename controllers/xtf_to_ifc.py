import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutil
from models.xtf_model import XTFParser
from models.ifc_model import create_ifc
from config.default_config import DEFAULT_CONFIG

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')

def read_config(config_file='config.txt'):
    config = DEFAULT_CONFIG.copy()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, config_file)
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            for line in file:
                if '=' in line:
                    name, value = line.strip().split('=')
                    name = name.strip()
                    value = value.strip()
                    if name in DEFAULT_CONFIG:
                        # Convert to the same type as in DEFAULT_CONFIG
                        config[name] = type(DEFAULT_CONFIG[name])(value)
                    else:
                        config[name] = value
    else:
        logging.warning(f"Config file not found: {config_path}. Using default configuration.")
    return config

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
    
    config = read_config('config.txt')

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