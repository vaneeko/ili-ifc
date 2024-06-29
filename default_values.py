import logging
import os

def get_default_values():
    def read_config(config_file='config.txt'):
        config = {}
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_file)
        with open(config_path, 'r') as file:
            for line in file:
                name, value = line.split('=')
                name = name.strip()
                value = value.strip()
                if name in [
                    'default_sohlenkote', 
                    'default_durchmesser', 
                    'default_hoehe', 
                    'default_wanddicke', 
                    'default_bodendicke', 
                    'default_rohrdicke'
                ]:
                    value = float(value)
                config[name] = value
        return config

    config = read_config('config.txt')

    default_sohlenkote = config['default_sohlenkote']
    default_durchmesser = config['default_durchmesser']
    default_hoehe = config['default_hoehe']
    default_wanddicke = config['default_wanddicke']
    default_bodendicke = config['default_bodendicke']
    default_rohrdicke = config['default_rohrdicke']

    try:
        new_sohlenkote = input(f"Standardwert für unbekannte Sohlenkoten von Abwasserknoten ({default_sohlenkote}m): ").strip()
        if new_sohlenkote:
            default_sohlenkote = float(new_sohlenkote)
    except ValueError:
        logging.error("Ungültige Eingabe für Sohlenkoten. Behalte den Standardwert.")

    try:
        new_durchmesser = input(f"Standardwert für Durchmesser von Abwasserschächten ({default_durchmesser}m): ").strip()
        if new_durchmesser:
            default_durchmesser = float(new_durchmesser)
    except ValueError:
        logging.error("Ungültige Eingabe für Durchmesser. Behalte den Standardwert.")

    try:
        new_hoehe = input(f"Standardwert für Höhen von Abwasserschächten ({default_hoehe}m): ").strip()
        if new_hoehe:
            default_hoehe = float(new_hoehe)
    except ValueError:
        logging.error("Ungültige Eingabe für Höhen. Behalte den Standardwert.")

    try:
        new_wanddicke = input(f"Standardwert für Wanddicke von Abwasserschächten ({default_wanddicke}m): ").strip()
        if new_wanddicke:
            default_wanddicke = float(new_wanddicke)
    except ValueError:
        logging.error("Ungültige Eingabe für Wanddicke. Behalte den Standardwert.")

    try:
        new_bodendicke = input(f"Standardwert für Bodendicke von Abwasserschächten ({default_bodendicke}m): ").strip()
        if new_bodendicke:
            default_bodendicke = float(new_bodendicke)
    except ValueError:
        logging.error("Ungültige Eingabe für Bodendicke. Behalte den Standardwert.")

    try:
        new_rohrdicke = input(f"Standardwert für Rohrdicke von Haltungen ({default_rohrdicke}m): ").strip()
        if new_rohrdicke:
            default_rohrdicke = float(new_rohrdicke)
    except ValueError:
        logging.error("Ungültige Eingabe für Rohrdicke. Behalte den Standardwert.")

    einfaerben = input("Möchten Sie bei fehlenden Werten die IFC-Elemente einfärben? (Ja/Nein, Standard: Nein): ").strip().lower()
    einfaerben = einfaerben in ["ja", "j"]

    return default_sohlenkote, default_durchmesser, default_hoehe, default_wanddicke, default_bodendicke, default_rohrdicke, einfaerben
