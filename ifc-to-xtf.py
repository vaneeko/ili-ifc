import logging
import os
import sys
from data_parser_ifc import IFCParser
from xtf_generator import XTFGenerator

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')

def read_config(config_file):
    config = {}
    with open(config_file, 'r') as file:
        for line in file:
            name, value = line.strip().split('=')
            config[name.strip()] = value.strip()
    return config

def get_ifc_files(ifc_path):
    if os.path.isdir(ifc_path):
        return [os.path.join(ifc_path, file) for file in os.listdir(ifc_path) if file.endswith('.ifc')]
    return [ifc_path]

def convert_ifc_to_xtf(ifc_file, xtf_file):
    parser = IFCParser()
    data = parser.parse(ifc_file)

    generator = XTFGenerator()
    generator.generate(data, xtf_file)
    logging.info(f"XTF file saved: {xtf_file}")

if __name__ == '__main__':
    setup_logging()
    if len(sys.argv) != 2:
        print("Usage: python ifc_to_xtf.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]
    config = read_config(config_file)

    ifc_path = config.get('ifc_files', '')
    output_folder = config.get('output_folder', '')

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    ifc_files = get_ifc_files(ifc_path)
    for ifc_file_path in ifc_files:
        ifc_file_name = os.path.basename(ifc_file_path)
        xtf_file_name = os.path.splitext(ifc_file_name)[0] + '.xtf'
        xtf_file_path = os.path.join(output_folder, xtf_file_name)

        logging.info(f"Converting IFC file: {ifc_file_path} to XTF file: {xtf_file_path}")
        try:
            convert_ifc_to_xtf(ifc_file_path, xtf_file_path)
        except Exception as e:
            logging.error(f"Error converting IFC to XTF: {e}", exc_info=True)
