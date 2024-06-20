import os
import logging
from data_parser import parse_xtf, get_default_values
from ifc_generator import create_ifc

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')

def main():
    setup_logging()
    logging.info("Programmstart")
    
    current_directory = os.getcwd()
    
    xtf_file_path = os.path.join(current_directory, 'Abwasser.xtf')
    ifc_file_path = os.path.join(current_directory, 'Abwasser.ifc')

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
    