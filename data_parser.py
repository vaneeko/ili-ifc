import xml.etree.ElementTree as ET
import logging

def get_default_values():
    logging.info("Default-Werte werden gesetzt.")
    
    # Setze Standardwerte
    default_sohlenkote = 100.0
    default_durchmesser = 2.0
    default_hoehe = 3.0

    # Frage den Benutzer nach neuen Werten oder bestätige Standardwerte
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

    einfaerben = input("Möchten Sie bei fehlenden Werten die IFC-Elemente einfärben? (Ja/Nein, Standard: Nein): ").strip().lower()
    einfaerben = einfaerben in ["ja", "j"]

    return default_sohlenkote, default_durchmesser, default_hoehe, einfaerben

def parse_abwasserknoten(root, namespace, default_sohlenkote, default_durchmesser, default_hoehe):
    logging.info("Starting to parse sewer nodes.")
    abwasserknoten_data = []
    haltungspunkt_sohlenkoten = {}

    for abwasserknoten in root.findall('.//ili:DSS_2020_LV95.Siedlungsentwaesserung.Abwasserknoten', namespace):
        try:
            haltungspunkt_ref = abwasserknoten.find('ili:Lage/ili:COORD', namespace)
            if haltungspunkt_ref is None:
                logging.error(f"Fehler: Abwasserknoten {abwasserknoten.get('TID')} hat keine Koordinaten.")
                continue

            c1 = haltungspunkt_ref.find('ili:C1', namespace).text
            c2 = haltungspunkt_ref.find('ili:C2', namespace).text

            # Transform coordinates if necessary
            c1_transformed = transform_coordinate(c1)
            c2_transformed = transform_coordinate(c2)

            sohlenkote = default_sohlenkote
            sohlenkote_element = abwasserknoten.find('ili:Sohlenkote', namespace)
            if sohlenkote_element is not None and sohlenkote_element.text is not None:
                try:
                    sohlenkote = float(sohlenkote_element.text)
                except ValueError:
                    logging.warning(f"Warnung: Ungültige Sohlenkote für Abwasserknoten {abwasserknoten.get('TID')}: {sohlenkote_element.text}")

            dimension1 = abwasserknoten.find('ili:Dimension1', namespace)
            dimension2 = abwasserknoten.find('ili:Dimension2', namespace)
            dimension1 = dimension1.text if dimension1 is not None and dimension1.text != '0' else str(default_durchmesser * 1000)
            dimension2 = dimension2.text if dimension2 is not None and dimension2.text != '0' else str(default_hoehe * 1000)

            haltungspunkt_id = abwasserknoten.get('TID')

            abwasserknoten_data.append({
                'id': haltungspunkt_id,
                'lage': {
                    'c1': c1_transformed,
                    'c2': c2_transformed
                },
                'dimension1': dimension1,
                'dimension2': dimension2,
                'kote': sohlenkote
            })

            haltungspunkt_sohlenkoten[haltungspunkt_id] = sohlenkote

        except AttributeError as e:
            logging.error(f"Fehler beim Parsen des Abwasserknotens {abwasserknoten.get('TID')}: {e}")

    return abwasserknoten_data, haltungspunkt_sohlenkoten

def parse_normschachte(root, namespace, abwasserknoten_data, default_durchmesser, default_hoehe, default_sohlenkote):
    # Parse norm shafts from XML
    logging.info("Starting to parse norm shafts.")
    normschachte = []
    nicht_verarbeitete_normschachte = []

    for ns in root.findall('.//ili:DSS_2020_LV95.Siedlungsentwaesserung.Normschacht', namespace):
        normschacht_id = ns.get('TID')
        abwasserknoten_id = normschacht_id.replace('dvabwN', 'dvaneA').strip()
        abwasserknoten = next((ak for ak in abwasserknoten_data if ak['id'].strip() == abwasserknoten_id), None)
        if abwasserknoten:
            normschachte.append({
                'id': ns.get('TID'),
                'abwasserknoten_id': abwasserknoten_id,
                'lage': abwasserknoten['lage'],
                'kote': abwasserknoten['kote'],
                'dimension1': ns.find('ili:Dimension1', namespace).text if ns.find('ili:Dimension1', namespace).text != '0' else str(default_durchmesser * 1000),
                'dimension2': ns.find('ili:Dimension2', namespace).text if ns.find('ili:Dimension2', namespace).text != '0' else str(default_hoehe * 1000)
            })
        else:
            print(f"Normschacht {ns.get('TID')} hat keinen zugehörigen Abwasserknoten")
            nicht_verarbeitete_normschachte.append(ns.get('TID'))

    return normschachte, nicht_verarbeitete_normschachte

def parse_kanale(root, namespace):
    # Parse channels from XML
    logging.info("Starting to parse channels.")
    kanale = []
    nicht_verarbeitete_kanale = []

    for kanal in root.findall('.//ili:DSS_2020_LV95.Siedlungsentwaesserung.Kanal', namespace):
        try:
            kanale.append({
                'id': kanal.get('TID'),
                'letzte_aenderung': kanal.find('ili:Letzte_Aenderung', namespace).text if kanal.find('ili:Letzte_Aenderung', namespace) is not None else "Unbekannt",
                'standortname': kanal.find('ili:Standortname', namespace).text if kanal.find('ili:Standortname', namespace) is not None else "Unbekannt",
                'zugaenglichkeit': kanal.find('ili:Zugaenglichkeit', namespace).text if kanal.find('ili:Zugaenglichkeit', namespace) is not None else "Unbekannt",
                'bezeichnung': kanal.find('ili:Bezeichnung', namespace).text if kanal.find('ili:Bezeichnung', namespace).text is not None else "Unbekannt",
                'nutzungsart_ist': kanal.find('ili:Nutzungsart_Ist', namespace).text if kanal.find('ili:Nutzungsart_Ist', namespace) is not None else "Unbekannt"
            })
        except AttributeError as e:
            nicht_verarbeitete_kanale.append(kanal.get('TID'))

    return kanale, nicht_verarbeitete_kanale

def parse_haltungspunkte(root, namespace, default_sohlenkote):
    haltungspunkte = []
    for element in root.findall('.//ili:DSS_2020_LV95.Siedlungsentwaesserung.Haltungspunkt', namespace):
        try:
            c1 = element.find('ili:Lage/ili:COORD/ili:C1', namespace)
            c2 = element.find('ili:Lage/ili:COORD/ili:C2', namespace)
            kote = element.find('ili:Kote', namespace)

            if c1 is not None and c2 is not None:
                c1_text = c1.text if c1.text is not None else "0"
                c2_text = c2.text if c2.text is not None else "0"
                z_text = float(kote.text) if kote is not None and kote.text is not None else default_sohlenkote

                haltungspunkte.append({
                    'id': element.get('TID'),
                    'lage': {
                        'c1': float(c1_text),
                        'c2': float(c2_text),
                        'z': z_text
                    }
                })
        except AttributeError as e:
            print(f"Fehler beim Parsen des Haltungspunkts {element.get('TID')}: {e}")
    return haltungspunkte


def transform_coordinate(coordinate):
    # Transform coordinate if necessary
    return float(coordinate)

def parse_haltungen(root, namespace, haltungspunkte, default_sohlenkote):
    haltungen = []
    nicht_verarbeitete_haltungen = []

    for haltung in root.findall('.//ili:DSS_2020_LV95.Siedlungsentwaesserung.Haltung', namespace):
        try:
            bezeichnung = haltung.find('ili:Bezeichnung', namespace).text
            lichte_hoehe_element = haltung.find('ili:Lichte_Hoehe', namespace)
            durchmesser = float(lichte_hoehe_element.text) / 1000.0 if lichte_hoehe_element is not None else 0.5

            verlauf = []
            polyline_element = haltung.find('ili:Verlauf/ili:POLYLINE', namespace)
            if polyline_element is not None:
                for coord in polyline_element.findall('ili:COORD', namespace):
                    c1 = coord.find('ili:C1', namespace).text
                    c2 = coord.find('ili:C2', namespace).text
                    verlauf.append({
                        'c1': float(c1),
                        'c2': float(c2)
                    })

            von_haltungspunkt_ref = haltung.find('ili:vonHaltungspunktRef', namespace).get('REF')
            nach_haltungspunkt_ref = haltung.find('ili:nachHaltungspunktRef', namespace).get('REF')

            von_haltungspunkt = next((p for p in haltungspunkte if p['id'] == von_haltungspunkt_ref), None)
            nach_haltungspunkt = next((p for p in haltungspunkte if p['id'] == nach_haltungspunkt_ref), None)

            if von_haltungspunkt and nach_haltungspunkt:
                von_z = von_haltungspunkt['lage']['z']
                nach_z = nach_haltungspunkt['lage']['z']

                haltungen.append({
                    'id': haltung.get('TID'),
                    'bezeichnung': bezeichnung,
                    'durchmesser': durchmesser,
                    'verlauf': verlauf,
                    'von_haltungspunkt': von_haltungspunkt,
                    'nach_haltungspunkt': nach_haltungspunkt,
                    'von_z': von_z,
                    'nach_z': nach_z
                })
            else:
                nicht_verarbeitete_haltungen.append(haltung.get('TID'))
        except AttributeError as e:
            nicht_verarbeitete_haltungen.append(haltung.get('TID'))
            print(f"Fehler bei der Verarbeitung der Haltung {haltung.get('TID')}: {e}")
    
    return haltungen, nicht_verarbeitete_haltungen

def parse_xtf(xtf_file_path, default_sohlenkote, default_durchmesser, default_hoehe, einfaerben):
    try:
        tree = ET.parse(xtf_file_path)
    except ET.ParseError as e:
        logging.error(f"Fehler beim Parsen der XTF-Datei: {e}")
        raise

    root = tree.getroot()
    namespace = {'ili': 'http://www.interlis.ch/INTERLIS2.3'}

    try:
        haltungspunkte = parse_haltungspunkte(root, namespace, default_sohlenkote)
        abwasserknoten, haltungspunkt_sohlenkoten = parse_abwasserknoten(root, namespace, default_sohlenkote, default_durchmesser, default_hoehe)
        normschachte, nicht_verarbeitete_normschachte = parse_normschachte(root, namespace, abwasserknoten, default_durchmesser, default_hoehe, default_sohlenkote)
        kanale, nicht_verarbeitete_kanale = parse_kanale(root, namespace)
        haltungen, nicht_verarbeitete_haltungen = parse_haltungen(root, namespace, haltungspunkte, default_sohlenkote)
    except Exception as e:
        logging.error(f"Fehler beim Parsen der Daten: {e}")
        raise

    data = {
        'haltungspunkte': haltungspunkte,
        'abwasserknoten': abwasserknoten,
        'normschachte': normschachte,
        'kanale': kanale,
        'haltungen': haltungen,
        'default_durchmesser': default_durchmesser,
        'default_hoehe': default_hoehe,
        'default_sohlenkote': default_sohlenkote,
        'nicht_verarbeitete_kanale': nicht_verarbeitete_kanale,
        'nicht_verarbeitete_haltungen': nicht_verarbeitete_haltungen,
        'nicht_verarbeitete_normschachte': nicht_verarbeitete_normschachte
    }

    return data