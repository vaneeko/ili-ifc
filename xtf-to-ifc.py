import logging
import os
import shutil
from data_parser_xtf import XTFParser
from ifc_generator import create_ifc

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')

def read_config(config_file='config.txt'):
    config = {}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, config_file)
    with open(config_path, 'r') as file:
        for line in file:
            name, value = line.strip().split('=')
            config[name.strip()] = value.strip()
    return config

def get_xtf_files(xtf_path):
    if os.path.isdir(xtf_path):
        return [os.path.join(xtf_path, file) for file in os.listdir(xtf_path) if file.endswith('.xtf')]
    return [xtf_path]

def convert_xtf_to_ifc(xtf_file, ifc_file):
    parser = XTFParser()
    data = parser.parse(xtf_file)

    create_ifc(ifc_file, data, data['defaults'][5])
    logging.info(f"IFC file saved: {ifc_file}")

def delete_pycache():
    pycache_path = os.path.join(os.path.dirname(__file__), '__pycache__')
    if os.path.exists(pycache_path):
        shutil.rmtree(pycache_path)
        logging.info(f"__pycache__ Ordner wurde gelöscht: {pycache_path}")

if __name__ == '__main__':
    setup_logging()
    logging.info("Programmstart")
    
    config = read_config('config.txt')

    xtf_path = config['xtf_files']
    xtf_files = get_xtf_files(xtf_path)
    output_folder = config['output_folder']

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for xtf_file_path in xtf_files:
        xtf_file_name = os.path.basename(xtf_file_path)
        ifc_file_name = os.path.splitext(xtf_file_name)[0] + '.ifc'
        ifc_file_path = os.path.join(output_folder, ifc_file_name)

        logging.info(f"XTF-Dateipfad: {xtf_file_path}")
        logging.info(f"IFC-Dateipfad: {ifc_file_path}")

        try:
            convert_xtf_to_ifc(xtf_file_path, ifc_file_path)
        except Exception as e:
            logging.error(f"Fehler bei der Konvertierung von XTF zu IFC: {e}", exc_info=True)

    delete_pycache()