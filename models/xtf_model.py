import xml.etree.ElementTree as ET
import math
import logging

class XTFParser:
    @staticmethod
    def round_down_to_nearest_10(value):
        return math.floor(value / 10) * 10
    
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
            haltungspunkte = self.parse_haltungspunkte(root, namespace, default_sohlenkote)
            abwasserknoten, haltungspunkt_sohlenkoten = self.parse_abwasserknoten(root, namespace, default_sohlenkote, default_durchmesser, default_hoehe)
            normschachte, nicht_verarbeitete_normschachte = self.parse_normschachte(root, namespace, abwasserknoten, haltungspunkte, default_durchmesser, default_hoehe, default_sohlenkote)
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
            'nicht_verarbeitete_kanale': nicht_verarbeitete_kanale,
            'nicht_verarbeitete_haltungen': nicht_verarbeitete_haltungen,
            'nicht_verarbeitete_normschachte': nicht_verarbeitete_normschachte,
        }

        min_x, min_y, min_z = self.find_min_coordinates(data)
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
            './/ili:SIA405_ABWASSER_2015_LV95.SIA405_Abwasser.Normschacht'
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
                    lage = ns.find('ili:Lage/ili:COORD', namespace)
                    if lage is not None:
                        c1 = lage.find('ili:C1', namespace).text
                        c2 = lage.find('ili:C2', namespace).text
                        normschachte.append({
                            'id': ns.get('TID'),
                            'abwasserknoten_id': None,
                            'lage': {'c1': c1, 'c2': c2},
                            'kote': default_sohlenkote,
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
                        zugehoerige_haltungspunkte = [hp for hp in haltungspunkte if hp['lage']['c1'] and hp['lage']['c2'] and ns.get('TID') in hp['id']]
                        if len(zugehoerige_haltungspunkte) >= 2:
                            mittelpunkt_c1 = sum(float(hp['lage']['c1']) for hp in zugehoerige_haltungspunkte) / len(zugehoerige_haltungspunkte)
                            mittelpunkt_c2 = sum(float(hp['lage']['c2']) for hp in zugehoerige_haltungspunkte) / len(zugehoerige_haltungspunkte)
                            normschachte.append({
                                'id': ns.get('TID'),
                                'abwasserknoten_id': None,
                                'lage': {'c1': mittelpunkt_c1, 'c2': mittelpunkt_c2},
                                'kote': default_sohlenkote,
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
                            print(f"Normschacht {ns.get('TID')} hat keine Koordinaten")
                            nicht_verarbeitete_normschachte.append(ns.get('TID'))

        return normschachte, nicht_verarbeitete_normschachte

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

    def find_min_coordinates(self, data):
        min_x = float('inf')
        min_y = float('inf')
        min_z = float('inf')
        
        for element in data['haltungspunkte'] + data['abwasserknoten'] + data['normschachte']:
            if 'lage' in element:
                min_x = min(min_x, float(element['lage']['c1']))
                min_y = min(min_y, float(element['lage']['c2']))
                if 'z' in element['lage']:
                    min_z = min(min_z, float(element['lage']['z']))
                elif 'kote' in element:
                    min_z = min(min_z, float(element['kote']))
        
        min_x = self.round_down_to_nearest_10(min_x)
        min_y = self.round_down_to_nearest_10(min_y)
        min_z = self.round_down_to_nearest_10(min_z)
        
        return min_x, min_y, min_z

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