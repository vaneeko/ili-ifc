XTF to IFC Converter

The XTF to IFC Converter is a tool for converting XML-based Transfer Format (XTF) files into Industry Foundation Classes (IFC) files. It focuses on infrastructure data, such as sewer systems, and facilitates the translation of attributes and geometries from XTF to IFC formats. This converter automates the transformation of data from GIS systems into BIM-compatible formats, enhancing data management and integration in construction and infrastructure projects.

- Features
  - Parsing XTF Files: Efficiently parses XTF files to extract data such as nodes, pipes, and other infrastructure components.
  - IFC File Creation: Converts parsed data into IFC format, ensuring compatibility with BIM tools and standards.
  - Error Handling: Manages missing or incorrect data during parsing and conversion with robust error handling mechanisms.
  - Color Coding: Uses color coding (red, orange, green) to highlight elements with missing or default values in the IFC file.
  - User Interaction: Requests user input for default values and preferences, allowing flexibility and customization in the conversion process.

Files:
- Main Script (main.py)
  - Initiates the program and handles the overall workflow.
  - Prompts the user for default values and preferences.
  - Calls the parser to extract data from the XTF file.
  - Initiates the creation of the IFC file from the parsed data.

- Parser (parser.py)
  - Functions:
    - get_default_values(): Prompts the user for default values for missing data.
    - parse_xtf(): Main function to parse the XTF file and organize data into a structured format.
    - parse_abwasserknoten(): Extracts and processes sewer nodes from the XTF file.
    - parse_normschachte(): Extracts and processes standard shafts.
    - parse_kanale(): Extracts and processes canal data.
    - parse_haltungspunkte(): Extracts and processes holding points.
    - parse_haltungen(): Extracts and processes holdings, including geometric data.
    - Data Extraction: Efficiently extracts and structures data, handling various data types and ensuring compatibility with the IFC schema.
- IFC Creator (ifc_creator.py)
  - Functions
    - create_ifc_project_structure(): Sets up the basic IFC project structure including project, site, and facility elements.
    - create_ifc_haltungen(): Creates IFC representations for holdings, applying default or user-provided geometries and properties.
    - create_ifc_normschachte(): Creates IFC representations for standard shafts, ensuring the correct placement and property assignment.
    - add_color(): Applies color coding to IFC elements based on the completeness of the data.
    - IFC Generation: Utilizes ifcopenshell library to create IFC entities, ensuring the generated IFC files adhere to the IFC4X3_ADD2 standard.
- Utilities (utils.py)
  - Functions:
    - generate_guid(): Generates unique identifiers for IFC entities.
    - add_property_set(): Adds property sets to IFC elements.
    - create_cartesian_point(): Helper function to create 3D points in the IFC file.
    - Getting Started
    - Prerequisites

Python 3.x
Required libraries: ifcopenshell, xml.etree.ElementTree, logging

Follow the prompts to input default values and preferences.
The converted IFC file will be generated in the specified output directory.

Contributing
Contributions are welcome! Please fork the repository and submit pull requests for any enhancements or bug fixes.
