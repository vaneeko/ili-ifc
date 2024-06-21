import xml.etree.ElementTree as ET
import logging
from default_values import get_default_values

class XTFParser:
    def parse(self, xtf_file_path):
        try:
            tree = ET.parse(xtf_file_path)
        except ET.ParseError as e:
            logging.error(f"Fehler beim Parsen der XTF-Datei: {e}")
            raise

        root = tree.getroot()
        namespace = {'ili': 'http://www.interlis.ch/INTERLIS2.3'}

        default_sohlenkote, default_durchmesser, default_hoehe, default_wanddicke, default_bodendicke, einfaerben = get_default_values()

        try:
            haltungspunkte = self.parse_haltungspunkte(root, namespace, default_sohlenkote)
            abwasserknoten, haltungspunkt_sohlenkoten = self.parse_abwasserknoten(root, namespace, default_sohlenkote, default_durchmesser, default_hoehe)
            normschachte, nicht_verarbeitete_normschachte = self.parse_normschachte(root, namespace, abwasserknoten, default_durchmesser, default_hoehe, default_sohlenkote)
            kanale, nicht_verarbeitete_kanale = self.parse_kanale(root, namespace)
            haltungen, nicht_verarbeitete_haltungen = self.parse_haltungen(root, namespace, haltungspunkte, default_sohlenkote)
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
            'default_wanddicke': default_wanddicke,
            'default_bodendicke': default_bodendicke,
            'nicht_verarbeitete_kanale': nicht_verarbeitete_kanale,
            'nicht_verarbeitete_haltungen': nicht_verarbeitete_haltungen,
            'nicht_verarbeitete_normschachte': nicht_verarbeitete_normschachte,
            'defaults': (default_sohlenkote, default_durchmesser, default_hoehe, default_wanddicke, default_bodendicke, einfaerben)
        }

        return data

    def get_element_text(self, element, tag, namespace):
        found_element = element.find(tag, namespace)
        if found_element is not None and found_element.text is not None:
            return found_element.text
        return ''

    def parse_abwasserknoten(self, root, namespace, default_sohlenkote, default_durchmesser, default_hoehe):
        logging.info("Starting to parse sewer nodes.")
        abwasserknoten_data = []
        haltungspunkt_sohlenkoten = {}

        knoten_paths = [
            './/ili:DSS_2020_LV95.Siedlungsentwaesserung.Abwasserknoten',
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Abwasserknoten'
        ]

        for path in knoten_paths:
            for abwasserknoten in root.findall(path, namespace):
                try:
                    haltungspunkt_ref = abwasserknoten.find('ili:Lage/ili:COORD', namespace)
                    if haltungspunkt_ref is None:
                        logging.error(f"Fehler: Abwasserknoten {abwasserknoten.get('TID')} hat keine Koordinaten.")
                        continue

                    c1 = haltungspunkt_ref.find('ili:C1', namespace).text
                    c2 = haltungspunkt_ref.find('ili:C2', namespace).text

                    # Transform coordinates if necessary
                    c1_transformed = self.transform_coordinate(c1)
                    c2_transformed = self.transform_coordinate(c2)

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

    def parse_normschachte(self, root, namespace, abwasserknoten_data, default_durchmesser, default_hoehe, default_sohlenkote):
        logging.info("Starting to parse norm shafts.")
        normschachte = []
        nicht_verarbeitete_normschachte = []

        schacht_paths = [
            './/ili:DSS_2020_LV95.Siedlungsentwaesserung.Normschacht',
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Normschacht'
        ]

        for path in schacht_paths:
            for ns in root.findall(path, namespace):
                normschacht_id = ns.get('TID')
                abwasserknoten_id = normschacht_id.replace('dvabwN', 'dvaneA').strip()
                abwasserknoten = next((ak for ak in abwasserknoten_data if ak['id'].strip() == abwasserknoten_id), None)
                if abwasserknoten:
                    normschachte.append({
                        'id': ns.get('TID'),
                        'abwasserknoten_id': abwasserknoten_id,
                        'lage': abwasserknoten['lage'],
                        'kote': abwasserknoten['kote'],
                        'dimension1': self.get_element_text(ns, 'ili:Dimension1', namespace) if self.get_element_text(ns, 'ili:Dimension1', namespace) != '0' else str(default_durchmesser * 1000),
                        'dimension2': self.get_element_text(ns, 'ili:Dimension2', namespace) if self.get_element_text(ns, 'ili:Dimension2', namespace) != '0' else str(default_hoehe * 1000),
                        'dimorg1': self.get_element_text(ns, 'ili:Dimension1', namespace),
                        'dimorg2': self.get_element_text(ns, 'ili:Dimension2', namespace),
                        'bezeichnung': self.get_element_text(ns, 'ili:Bezeichnung', namespace),
                        'standortname': self.get_element_text(ns, 'ili:Standortname', namespace),
                        'funktion': self.get_element_text(ns, 'ili:Funktion', namespace),
                        'material': self.get_element_text(ns, 'ili:Material', namespace)
                    })
                else:
                    print(f"Normschacht {ns.get('TID')} hat keinen zugehörigen Abwasserknoten")
                    nicht_verarbeitete_normschachte.append(ns.get('TID'))

        return normschachte, nicht_verarbeitete_normschachte

    def parse_kanale(self, root, namespace):
        logging.info("Starting to parse channels.")
        kanale = []
        nicht_verarbeitete_kanale = []

        kanal_paths = [
            './/ili:DSS_2020_LV95.Siedlungsentwaesserung.Kanal',
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Kanal'
        ]

        for path in kanal_paths:
            for kanal in root.findall(path, namespace):
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

    def parse_haltungspunkte(self, root, namespace, default_sohlenkote):
        haltungspunkte = []

        haltungspunkt_paths = [
            './/ili:DSS_2020_LV95.Siedlungsentwaesserung.Haltungspunkt',
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Haltungspunkt'
        ]

        for path in haltungspunkt_paths:
            for element in root.findall(path, namespace):
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

    def transform_coordinate(self, coordinate):
        return float(coordinate)

    def parse_haltungen(self, root, namespace, haltungspunkte, default_sohlenkote):
        haltungen = []
        nicht_verarbeitete_haltungen = []

        haltung_paths = [
            './/ili:DSS_2020_LV95.Siedlungsentwaesserung.Haltung',
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Haltung'
        ]

        for path in haltung_paths:
            for haltung in root.findall(path, namespace):
                try:
                    bezeichnung = haltung.find('ili:Bezeichnung', namespace).text
                    lichte_hoehe_element = haltung.find('ili:Lichte_Hoehe', namespace)
                    laenge_effektiv = haltung.find('ili:LaengeEffektiv', namespace)
                    material = haltung.find('ili:Material', namespace)

                    lichte_hoehe = float(lichte_hoehe_element.text) / 1000.0 if lichte_hoehe_element is not None else 0.5
                    laenge_effektiv = float(laenge_effektiv.text) if laenge_effektiv is not None else 0.0
                    material = material.text if material is not None else ""

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
                            'durchmesser': lichte_hoehe,
                            'material': material,
                            'length': laenge_effektiv,
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
