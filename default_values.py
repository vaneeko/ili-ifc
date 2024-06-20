import logging

def get_default_values():
    logging.info("Default-Werte werden gesetzt.")
    
    # Default values
    default_sohlenkote = 100.0
    default_durchmesser = 2.0
    default_hoehe = 3.0
    default_wanddicke = 0.05
    default_bodendicke = 0.02

    # Default values
    try:
        new_sohlenkote = input(f"Standardwert für unbekannte Sohlenkoten von Abwasserknoten ({default_sohlenkote}m): ")
        if new_sohlenkote.strip():
            default_sohlenkote = float(new_sohlenkote)
    except ValueError:
        print("Ungültige Eingabe. Behalte den Standardwert.")

    try:
        new_durchmesser = input(f"Standardwert für Durchmesser von Abwasserschächten ({default_durchmesser}m): ")
        if new_durchmesser.strip():
            default_durchmesser = float(new_durchmesser)
    except ValueError:
        print("Ungültige Eingabe. Behalte den Standardwert.")

    try:
        new_hoehe = input(f"Standardwert für Höhen von Abwasserschächten ({default_hoehe}m): ")
        if new_hoehe.strip():
            default_hoehe = float(new_hoehe)
    except ValueError:
        print("Ungültige Eingabe. Behalte den Standardwert.")

    try:
        new_wanddicke = input(f"Standardwert für Wanddicke von Abwasserschächten ({default_wanddicke}m): ")
        if new_wanddicke.strip():
            default_wanddicke = float(new_wanddicke)
    except ValueError:
        print("Ungültige Eingabe. Behalte den Standardwert.")

    try:
        new_bodendicke = input(f"Standardwert für Bodendicke von Abwasserschächten ({default_bodendicke}m): ")
        if new_bodendicke.strip():
            default_bodendicke = float(new_bodendicke)
    except ValueError:
        print("Ungültige Eingabe. Behalte den Standardwert.")

    einfaerben = input("Möchten Sie bei fehlenden Werten die IFC-Elemente einfärben? (Ja/Nein, Standard: Nein): ").strip().lower()
    einfaerben = einfaerben in ["ja", "j"]

    return default_sohlenkote, default_durchmesser, default_hoehe, default_wanddicke, default_bodendicke, einfaerben