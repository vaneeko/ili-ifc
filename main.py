# Import necessary modules
import os
import logging
from data_parser import parse_xtf, get_default_values
from ifc_generator import create_ifc

# Function to set up logging configuration
def setup_logging():
    # Configure logging settings
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')

# Main function to handle the program execution
def main():
    # Set up logging
    setup_logging()
    logging.info("Programmstart")
    
    # Get the current working directory
    current_directory = os.getcwd()
    
    # Define paths for the input XTF file and output IFC file
    xtf_file_path = os.path.join(current_directory, 'Abwasser.xtf')
    ifc_file_path = os.path.join(current_directory, 'Abwasser.ifc')

    logging.info(f"XTF-Dateipfad: {xtf_file_path}")
    logging.info(f"IFC-Dateipfad: {ifc_file_path}")

    try:
        # Retrieve default values for various parameters
        default_sohlenkote, default_durchmesser, default_hoehe, zusatz_hoehe_haltpunkt, einfaerben = get_default_values()

        # Parse the XTF file with the default values
        xtf_data = parse_xtf(xtf_file_path, default_sohlenkote, zusatz_hoehe_haltpunkt, default_durchmesser, default_hoehe)
        
        # Create the IFC file from the parsed data
        create_ifc(ifc_file_path, xtf_data, einfaerben)
    except Exception as e:
        # Log any errors that occur during the process
        logging.error(f"Fehler: {e}", exc_info=True)

# Entry point of the script
if __name__ == "__main__":
    main()
