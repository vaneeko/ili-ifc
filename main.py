import os
import logging
from data_parser import parse_xtf, get_default_values
from ifc_generator import create_ifc

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

def get_xtf_files(xtf_path):
    if os.path.isdir(xtf_path):
        return [os.path.join(xtf_path, file) for file in os.listdir(xtf_path) if file.endswith('.xtf')]
    return [xtf_path]

def main():
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
            default_sohlenkote, default_durchmesser, default_hoehe, default_wanddicke, default_bodendicke, einfaerben = get_default_values()
            xtf_data = parse_xtf(xtf_file_path, default_sohlenkote, default_durchmesser, default_hoehe, default_wanddicke, default_bodendicke, einfaerben)
            create_ifc(ifc_file_path, xtf_data, einfaerben)
        except Exception as e:
            logging.error(f"Fehler: {e}", exc_info=True)

if __name__ == "__main__":
    main()
