import xml.etree.ElementTree as ET
import math
import logging

class XTFParser:
    @staticmethod
    def round_down_to_nearest_10(value):
        if math.isinf(value):
            return value
        return math.floor(value / 10) * 10
    
    def safe_float(self, value):
        if value is None or value == '':
            return None
        try:
            float_value = float(value)
            if math.isinf(float_value):
                logging.warning(f"Unendlicher Wert gefunden: {value}")
                return None
            return float_value
        except ValueError:
            logging.warning(f"Konvertierung zu Float fehlgeschlagen für Wert: {value}")
            return None

    def safe_int(self, value):
        if value is None or value == '':
            return None
        try:
            return int(float(value))
        except ValueError:
            logging.warning(f"Konvertierung zu Integer fehlgeschlagen für Wert: {value}")
            return None

    def parse(self, xtf_file_path, config):
        try:
            tree = ET.parse(xtf_file_path)
        except ET.ParseError as e:
            logging.error(f"Fehler beim Parsen der XTF-Datei: {e}")
            raise

        root = tree.getroot()
        namespace = {'ili': 'http://www.interlis.ch/INTERLIS2.3'}

        default_sohlenkote = config['default_sohlenkote']
        default_durchmesser = config['default_durchmesser']
        default_hoehe = config['default_hoehe']
        default_wanddicke = config['default_wanddicke']
        default_bodendicke = config['default_bodendicke']
        default_rohrdicke = config['default_rohrdicke']
        einfaerben = config['einfaerben']

        try:
            logging.info("Starte das Parsen von Haltungspunkten")
            haltungspunkte = self.parse_haltungspunkte(root, namespace, default_sohlenkote)
            
            logging.info("Starte das Parsen von Abwasserknoten")
            abwasserknoten, haltungspunkt_sohlenkoten = self.parse_abwasserknoten(root, namespace, default_sohlenkote, default_durchmesser, default_hoehe)
            
            logging.info("Starte das Parsen von Normschächten")
            normschachte, nicht_verarbeitete_normschachte = self.parse_normschachte(root, namespace, abwasserknoten, haltungspunkte, default_durchmesser, default_hoehe, default_sohlenkote)
            
            logging.info("Starte das Parsen von Kanälen")
            kanale, nicht_verarbeitete_kanale = self.parse_kanale(root, namespace)
            
            logging.info("Starte das Parsen von Haltungen")
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
            'nicht_verarbeitete_kanale': nicht_verarbeitete_kanale,
            'nicht_verarbeitete_haltungen': nicht_verarbeitete_haltungen,
            'nicht_verarbeitete_normschachte': nicht_verarbeitete_normschachte,
        }

        min_x, min_y, min_z = self.find_min_coordinates(data)
        if any(math.isinf(coord) for coord in (min_x, min_y, min_z)):
            logging.error(f"Ungültige Mindestkoordinaten gefunden: x={min_x}, y={min_y}, z={min_z}")
            raise ValueError("Ungültige Mindestkoordinaten")        
            
        data['min_coordinates'] = {
            'x': min_x,
            'y': min_y,
            'z': min_z
        }

        data.update(config)

        return data

    def get_element_text(self, element, tag, namespace):
        found_element = element.find(tag, namespace)
        if found_element is not None and found_element.text is not None:
            return found_element.text
        return ''

    def parse_coordinates(self, element, namespace):
        c1 = element.find('ili:C1', namespace)
        c2 = element.find('ili:C2', namespace)
        if c1 is not None and c2 is not None:
            return {
                'c1': self.safe_float(c1.text),
                'c2': self.safe_float(c2.text)
            }
        return None

    def parse_abwasserknoten(self, root, namespace, default_sohlenkote, default_durchmesser, default_hoehe):
        logging.info("Starting to parse sewer nodes.")
        abwasserknoten_data = []
        haltungspunkt_sohlenkoten = {}

        knoten_paths = [
            './/ili:DSS_2020_LV95.Siedlungsentwaesserung.Abwasserknoten',
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Abwasserknoten',
            './/ili:DSS_2015_LV95.Siedlungsentwaesserung.Abwasserknoten'  # Hinzugefügt für DSS_2015
        ]

        for path in knoten_paths:
            for abwasserknoten in root.findall(path, namespace):
                try:
                    lage = abwasserknoten.find('ili:Lage/ili:COORD', namespace)
                    if lage is None:
                        logging.error(f"Fehler: Abwasserknoten {abwasserknoten.get('TID')} hat keine Koordinaten.")
                        continue

                    coords = self.parse_coordinates(lage, namespace)
                    if coords is None:
                        continue

                    sohlenkote_element = abwasserknoten.find('ili:Sohlenkote', namespace)
                    sohlenkote = self.safe_float(sohlenkote_element.text) if sohlenkote_element is not None else default_sohlenkote

                    dimension1 = self.safe_float(self.get_element_text(abwasserknoten, 'ili:Dimension1', namespace))
                    dimension2 = self.safe_float(self.get_element_text(abwasserknoten, 'ili:Dimension2', namespace))
                    dimension1 = dimension1 if dimension1 is not None and dimension1 != 0 else default_durchmesser * 1000
                    dimension2 = dimension2 if dimension2 is not None and dimension2 != 0 else default_hoehe * 1000

                    haltungspunkt_id = abwasserknoten.get('TID')

                    abwasserknoten_data.append({
                        'id': haltungspunkt_id,
                        'lage': coords,
                        'dimension1': dimension1,
                        'dimension2': dimension2,
                        'kote': sohlenkote,
                        'ref': abwasserknoten.find('ili:AbwasserbauwerkRef', namespace).get('REF') if abwasserknoten.find('ili:AbwasserbauwerkRef', namespace) is not None else None
                    })

                    haltungspunkt_sohlenkoten[haltungspunkt_id] = sohlenkote

                except AttributeError as e:
                    logging.error(f"Fehler beim Parsen des Abwasserknotens {abwasserknoten.get('TID')}: {e}")

        return abwasserknoten_data, haltungspunkt_sohlenkoten

    def parse_normschachte(self, root, namespace, abwasserknoten_data, haltungspunkte, default_durchmesser, default_hoehe, default_sohlenkote):
        logging.info("Starting to parse norm shafts.")
        normschachte = []
        nicht_verarbeitete_normschachte = []

        schacht_paths = [
            './/ili:DSS_2020_LV95.Siedlungsentwaesserung.Normschacht',
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Normschacht',
            './/ili:DSS_2015_LV95.Siedlungsentwaesserung.Normschacht'  # Hinzugefügt für DSS_2015
        ]

        for path in schacht_paths:
            for ns in root.findall(path, namespace):
                normschacht_id = ns.get('TID')

                abwasserbauwerk_ref = ns.find('ili:AbwasserbauwerkRef', namespace)
                if abwasserbauwerk_ref is not None:
                    abwasserbauwerk_id = abwasserbauwerk_ref.get('REF')
                    abwasserknoten = next((ak for ak in abwasserknoten_data if ak['id'].strip() == abwasserbauwerk_id or ak.get('ref') == abwasserbauwerk_id), None)
                else:
                    abwasserknoten = next((ak for ak in abwasserknoten_data if ak['id'].strip() == normschacht_id or ak.get('ref') == normschacht_id), None)

                if abwasserknoten:
                    normschachte.append({
                        'id': ns.get('TID'),
                        'abwasserknoten_id': abwasserknoten['id'],
                        'lage': abwasserknoten['lage'],
                        'kote': abwasserknoten['kote'],
                        'dimension1': self.safe_float(self.get_element_text(ns, 'ili:Dimension1', namespace)) or default_durchmesser * 1000,
                        'dimension2': self.safe_float(self.get_element_text(ns, 'ili:Dimension2', namespace)) or default_hoehe * 1000,
                        'dimorg1': self.get_element_text(ns, 'ili:Dimension1', namespace),
                        'dimorg2': self.get_element_text(ns, 'ili:Dimension2', namespace),
                        'bezeichnung': self.get_element_text(ns, 'ili:Bezeichnung', namespace),
                        'standortname': self.get_element_text(ns, 'ili:Standortname', namespace),
                        'funktion': self.get_element_text(ns, 'ili:Funktion', namespace),
                        'material': self.get_element_text(ns, 'ili:Material', namespace)
                    })
                else:
                    lage = ns.find('ili:Lage/ili:COORD', namespace)
                    if lage is not None:
                        coords = self.parse_coordinates(lage, namespace)
                        normschachte.append({
                            'id': ns.get('TID'),
                            'abwasserknoten_id': None,
                            'lage': coords,
                            'kote': default_sohlenkote,
                            'dimension1': self.safe_float(self.get_element_text(ns, 'ili:Dimension1', namespace)) or default_durchmesser * 1000,
                            'dimension2': self.safe_float(self.get_element_text(ns, 'ili:Dimension2', namespace)) or default_hoehe * 1000,
                            'dimorg1': self.get_element_text(ns, 'ili:Dimension1', namespace),
                            'dimorg2': self.get_element_text(ns, 'ili:Dimension2', namespace),
                            'bezeichnung': self.get_element_text(ns, 'ili:Bezeichnung', namespace),
                            'standortname': self.get_element_text(ns, 'ili:Standortname', namespace),
                            'funktion': self.get_element_text(ns, 'ili:Funktion', namespace),
                            'material': self.get_element_text(ns, 'ili:Material', namespace)
                        })
                    else:
                        zugehoerige_haltungspunkte = [hp for hp in haltungspunkte if hp['lage']['c1'] and hp['lage']['c2'] and ns.get('TID') in hp['id']]
                        if len(zugehoerige_haltungspunkte) >= 2:
                            mittelpunkt_c1 = sum(self.safe_float(hp['lage']['c1']) for hp in zugehoerige_haltungspunkte) / len(zugehoerige_haltungspunkte)
                            mittelpunkt_c2 = sum(self.safe_float(hp['lage']['c2']) for hp in zugehoerige_haltungspunkte) / len(zugehoerige_haltungspunkte)
                            normschachte.append({
                                'id': ns.get('TID'),
                                'abwasserknoten_id': None,
                                'lage': {'c1': mittelpunkt_c1, 'c2': mittelpunkt_c2},
                                'kote': default_sohlenkote,
                                'dimension1': self.safe_float(self.get_element_text(ns, 'ili:Dimension1', namespace)) or default_durchmesser * 1000,
                                'dimension2': self.safe_float(self.get_element_text(ns, 'ili:Dimension2', namespace)) or default_hoehe * 1000,
                                'dimorg1': self.get_element_text(ns, 'ili:Dimension1', namespace),
                                'dimorg2': self.get_element_text(ns, 'ili:Dimension2', namespace),
                                'bezeichnung': self.get_element_text(ns, 'ili:Bezeichnung', namespace),
                                'standortname': self.get_element_text(ns, 'ili:Standortname', namespace),
                                'funktion': self.get_element_text(ns, 'ili:Funktion', namespace),
                                'material': self.get_element_text(ns, 'ili:Material', namespace)
                            })
                        else:
                            logging.warning(f"Normschacht {ns.get('TID')} hat keine Koordinaten")
                            nicht_verarbeitete_normschachte.append(ns.get('TID'))

        return normschachte, nicht_verarbeitete_normschachte

    def parse_haltungspunkte(self, root, namespace, default_sohlenkote):
        haltungspunkte = []

        haltungspunkt_paths = [
            './/ili:DSS_2020_LV95.Siedlungsentwaesserung.Haltungspunkt',
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Haltungspunkt',
            './/ili:DSS_2015_LV95.Siedlungsentwaesserung.Haltungspunkt'
        ]

        for path in haltungspunkt_paths:
            for element in root.findall(path, namespace):
                try:
                    lage = element.find('ili:Lage/ili:COORD', namespace)
                    kote = element.find('ili:Kote', namespace)

                    if lage is not None:
                        coords = self.parse_coordinates(lage, namespace)
                        if coords:
                            z_value = self.safe_float(kote.text) if kote is not None else None
                            if z_value is None:
                                z_value = default_sohlenkote
                                logging.warning(f"Fehlende Kote für Haltungspunkt {element.get('TID')}, verwende Standardwert: {default_sohlenkote}")

                            haltungspunkte.append({
                                'id': element.get('TID'),
                                'lage': {
                                    'c1': coords['c1'],
                                    'c2': coords['c2'],
                                    'z': z_value
                                }
                            })
                except AttributeError as e:
                    logging.error(f"Fehler beim Parsen des Haltungspunkts {element.get('TID')}: {e}")
        return haltungspunkte

    def find_min_coordinates(self, data):
        min_x = float('inf')
        min_y = float('inf')
        min_z = float('inf')
        
        for element in data['haltungspunkte'] + data['abwasserknoten'] + data['normschachte']:
            if 'lage' in element:
                c1 = self.safe_float(element['lage'].get('c1'))
                c2 = self.safe_float(element['lage'].get('c2'))
                if c1 is not None and not math.isinf(c1):
                    min_x = min(min_x, c1)
                if c2 is not None and not math.isinf(c2):
                    min_y = min(min_y, c2)
                if 'z' in element['lage']:
                    z = self.safe_float(element['lage']['z'])
                    if z is not None and not math.isinf(z):
                        min_z = min(min_z, z)
                elif 'kote' in element:
                    kote = self.safe_float(element['kote'])
                    if kote is not None and not math.isinf(kote):
                        min_z = min(min_z, kote)
        
        min_x = self.round_down_to_nearest_10(min_x)
        min_y = self.round_down_to_nearest_10(min_y)
        min_z = self.round_down_to_nearest_10(min_z)
        
        return min_x, min_y, min_z

    def parse_haltungen(self, root, namespace, haltungspunkte, default_sohlenkote):
        haltungen = []
        nicht_verarbeitete_haltungen = []

        haltung_paths = [
            './/ili:DSS_2020_LV95.Siedlungsentwaesserung.Haltung',
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Haltung',
            './/ili:DSS_2015_LV95.Siedlungsentwaesserung.Haltung'  # Hinzugefügt für DSS_2015
        ]

        for path in haltung_paths:
            for haltung in root.findall(path, namespace):
                try:
                    bezeichnung = self.get_element_text(haltung, 'ili:Bezeichnung', namespace)
                    lichte_hoehe = self.safe_float(self.get_element_text(haltung, 'ili:Lichte_Hoehe', namespace))
                    laenge_effektiv = self.safe_float(self.get_element_text(haltung, 'ili:LaengeEffektiv', namespace))
                    material = self.get_element_text(haltung, 'ili:Material', namespace)

                    lichte_hoehe = lichte_hoehe / 1000.0 if lichte_hoehe is not None else 0.5
                    laenge_effektiv = laenge_effektiv if laenge_effektiv is not None else 0.0

                    verlauf = []
                    polyline_element = haltung.find('ili:Verlauf/ili:POLYLINE', namespace)
                    if polyline_element is not None:
                        for coord in polyline_element.findall('ili:COORD', namespace):
                            coords = self.parse_coordinates(coord, namespace)
                            if coords:
                                verlauf.append(coords)

                    von_haltungspunkt_ref = haltung.find('ili:vonHaltungspunktRef', namespace)
                    nach_haltungspunkt_ref = haltung.find('ili:nachHaltungspunktRef', namespace)

                    von_haltungspunkt = next((p for p in haltungspunkte if p['id'] == von_haltungspunkt_ref.get('REF')), None) if von_haltungspunkt_ref is not None else None
                    nach_haltungspunkt = next((p for p in haltungspunkte if p['id'] == nach_haltungspunkt_ref.get('REF')), None) if nach_haltungspunkt_ref is not None else None

                    if von_haltungspunkt and nach_haltungspunkt:
                        von_z = self.safe_float(von_haltungspunkt['lage'].get('z', default_sohlenkote))
                        nach_z = self.safe_float(nach_haltungspunkt['lage'].get('z', default_sohlenkote))

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
                    logging.error(f"Fehler bei der Verarbeitung der Haltung {haltung.get('TID')}: {e}")

        return haltungen, nicht_verarbeitete_haltungen

    def parse_kanale(self, root, namespace):
        logging.info("Starting to parse channels.")
        kanale = []
        nicht_verarbeitete_kanale = []

        kanal_paths = [
            './/ili:DSS_2020_LV95.Siedlungsentwaesserung.Kanal',
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Kanal',
            './/ili:DSS_2015_LV95.Siedlungsentwaesserung.Kanal'  # Hinzugefügt für DSS_2015
        ]

        for path in kanal_paths:
            for kanal in root.findall(path, namespace):
                try:
                    kanale.append({
                        'id': kanal.get('TID'),
                        'letzte_aenderung': self.get_element_text(kanal, 'ili:Letzte_Aenderung', namespace) or "Unbekannt",
                        'standortname': self.get_element_text(kanal, 'ili:Standortname', namespace) or "Unbekannt",
                        'zugaenglichkeit': self.get_element_text(kanal, 'ili:Zugaenglichkeit', namespace) or "Unbekannt",
                        'bezeichnung': self.get_element_text(kanal, 'ili:Bezeichnung', namespace) or "Unbekannt",
                        'nutzungsart_ist': self.get_element_text(kanal, 'ili:Nutzungsart_Ist', namespace) or "Unbekannt"
                    })
                except AttributeError as e:
                    nicht_verarbeitete_kanale.append(kanal.get('TID'))
                    logging.error(f"Fehler bei der Verarbeitung des Kanals {kanal.get('TID')}: {e}")

        return kanale, nicht_verarbeitete_kanale