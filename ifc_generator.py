import ifcopenshell
import logging
from utils import generate_guid, add_property_set, create_cartesian_point, create_swept_disk_solid, create_property_single_value
import math

def create_ifc_project_structure(ifc_file):
    logging.info("Erstelle IFC-Projektstruktur.")
    project = ifc_file.create_entity("IfcProject", GlobalId=generate_guid(), Name="Entwässerungsprojekt")
    context = ifc_file.create_entity("IfcGeometricRepresentationContext", ContextType="Model", ContextIdentifier="Building Model")
    site = ifc_file.create_entity("IfcSite", GlobalId=generate_guid(), Name="Perimeter")
    facility = ifc_file.create_entity("IfcBuilding", GlobalId=generate_guid(), Name="Entwässerungsanlage")
    
    ifc_file.create_entity("IfcRelAggregates", GlobalId=generate_guid(), RelatingObject=project, RelatedObjects=[site])
    ifc_file.create_entity("IfcRelAggregates", GlobalId=generate_guid(), RelatingObject=site, RelatedObjects=[facility])
    
    return context, facility

def create_local_placement(ifc_file, point, relative_to=None):
    ifc_point = ifc_file.create_entity('IfcCartesianPoint', Coordinates=point)
    axis2placement = ifc_file.create_entity('IfcAxis2Placement3D', Location=ifc_point)

    if relative_to:
        local_placement = ifc_file.create_entity('IfcLocalPlacement', PlacementRelTo=relative_to, RelativePlacement=axis2placement)
    else:
        local_placement = ifc_file.create_entity('IfcLocalPlacement', RelativePlacement=axis2placement)
    
    return local_placement

def interpolate_z(start_z, end_z, start_x, start_y, end_x, end_y, point_x, point_y):
    total_distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    point_distance = math.sqrt((point_x - start_x)**2 + (point_y - start_y)**2)
    if total_distance != 0:
        return start_z + (end_z - start_z) * (point_distance / total_distance)
    else:
        return start_z

def add_color(ifc_file, ifc_element, farbe, context):
    color_map = {
        "Grün": (0.0, 1.0, 0.0),
        "Orange": (1.0, 0.65, 0.0),
        "Rot": (1.0, 0.0, 0.0),
        "Blau": (0.0, 0.0, 1.0)
    }
    rgb = color_map.get(farbe, (1.0, 1.0, 1.0))

    surface_colour = ifc_file.create_entity("IfcColourRgb", Red=rgb[0], Green=rgb[1], Blue=rgb[2])
    surface_style_rendering = ifc_file.create_entity("IfcSurfaceStyleRendering", SurfaceColour=surface_colour)
    surface_style = ifc_file.create_entity("IfcSurfaceStyle", Side="BOTH", Styles=[surface_style_rendering])
    styled_item = ifc_file.create_entity("IfcStyledItem", Item=ifc_element.Representation.Representations[0].Items[0], Styles=[surface_style])

def check_haltung_within_normschacht(haltung, normschacht, default_sohlenkote):
    start_point = haltung['von_haltungspunkt']['lage']
    end_point = haltung['nach_haltungspunkt']['lage']
    von_kote = haltung['von_z']
    nach_kote = haltung['nach_z']

    schacht_lage = normschacht['lage']
    schacht_kote = float(normschacht['kote']) if normschacht['kote'] != 0 else default_sohlenkote
    schacht_hoehe = float(normschacht['dimension2']) / 1000 if normschacht['dimension2'] != '0' else default_sohlenkote
    schacht_radius = float(normschacht['dimension1']) / 2000 if normschacht['dimension1'] != '0' else default_sohlenkote / 2

    start_within = (schacht_lage['c1'] - schacht_radius <= start_point['c1'] <= schacht_lage['c1'] + schacht_radius and
                    schacht_lage['c2'] - schacht_radius <= start_point['c2'] <= schacht_lage['c2'] + schacht_radius and
                    schacht_kote <= von_kote <= schacht_kote + schacht_hoehe)

    end_within = (schacht_lage['c1'] - schacht_radius <= end_point['c1'] <= schacht_lage['c1'] + schacht_radius and
                  schacht_lage['c2'] - schacht_radius <= end_point['c2'] <= schacht_lage['c2'] + schacht_radius and
                  schacht_kote <= nach_kote <= schacht_kote + schacht_hoehe)

    print(f"Check Haltung within Normschacht: Start within {start_within}, End within {end_within}")
    return start_within and end_within

def create_ifc_haltungen(ifc_file, data, facility, context, haltungen_group, einfaerben, default_sohlenkote):
    haltungen = data['haltungen']
    default_durchmesser = data['default_durchmesser']
    wanddicke = 0.03  # 30 mm Wanddicke

    for haltung in haltungen:
        durchmesser = haltung.get('durchmesser', default_durchmesser)
        outer_radius = durchmesser / 2
        inner_radius = outer_radius - wanddicke

        start_point = haltung['von_haltungspunkt']['lage']
        end_point = haltung['nach_haltungspunkt']['lage']

        start_x = float(start_point['c1'])
        start_y = float(start_point['c2'])
        start_z = float(haltung['von_z']) if haltung['von_z'] != 0.0 else default_sohlenkote

        end_x = float(end_point['c1'])
        end_y = float(end_point['c2'])
        end_z = float(haltung['nach_z']) if haltung['nach_z'] != 0.0 else default_sohlenkote

        start_z += outer_radius
        end_z += outer_radius

        ifc_local_placement = create_local_placement(ifc_file, [start_x, start_y, start_z], relative_to=facility.ObjectPlacement)

        if 'verlauf' in haltung and haltung['verlauf']:
            polyline_3d = []
            for point in haltung['verlauf']:
                x = float(point['c1']) - start_x
                y = float(point['c2']) - start_y
                z = float(point['kote']) if point.get('kote') and float(point['kote']) != 0 else interpolate_z(start_z, end_z, start_x, start_y, end_x, end_y, float(point['c1']), float(point['c2'])) - start_z
                polyline_3d.append([x, y, z])
        else:
            polyline_3d = [
                [0.0, 0.0, 0.0],
                [end_x - start_x, end_y - start_y, end_z - start_z]
            ]

        ifc_polyline = ifc_file.create_entity('IfcPolyline', Points=[create_cartesian_point(ifc_file, p) for p in polyline_3d])

        ifc_pipe_segment = ifc_file.create_entity("IfcPipeSegment", GlobalId=generate_guid(), OwnerHistory=None, Name=haltung['bezeichnung'],
                                                  ObjectPlacement=ifc_local_placement, Representation=None)

        swept_disk_solid = create_swept_disk_solid(ifc_file, ifc_polyline, outer_radius, inner_radius)

        shape_representation = ifc_file.create_entity("IfcShapeRepresentation",
                                                      ContextOfItems=context,
                                                      RepresentationIdentifier="Body",
                                                      RepresentationType="SweptSolid",
                                                      Items=[swept_disk_solid])

        product_shape = ifc_file.create_entity("IfcProductDefinitionShape",
                                               Representations=[shape_representation])

        ifc_pipe_segment.Representation = product_shape

        farbe = "Blau"
        if einfaerben:
            if start_z != default_sohlenkote and end_z != default_sohlenkote:
                farbe = "Grün"
            else:
                farbe = "Rot"

            print(f"Haltung: {haltung}")

            abwasserknoten_von = next((ak for ak in data['abwasserknoten'] if ak['id'] == haltung['von_haltungspunkt'].get('abwasserknoten_ref')), None)
            abwasserknoten_nach = next((ak for ak in data['abwasserknoten'] if ak['id'] == haltung['nach_haltungspunkt'].get('abwasserknoten_ref')), None)

            print(f"Abwasserknoten von: {abwasserknoten_von}, Abwasserknoten nach: {abwasserknoten_nach}")

            if abwasserknoten_von and abwasserknoten_nach:
                normschacht_von = next((ns for ns in data['normschachte'] if ns['id'] == abwasserknoten_von.get('abwasserknoten_id')), None)
                normschacht_nach = next((ns for ns in data['normschachte'] if ns['id'] == abwasserknoten_nach.get('abwasserknoten_id')), None)

                if normschacht_von:
                    print(f"Check Haltung within Normschacht von: {haltung['id']} in {normschacht_von['id']}")
                    if not check_haltung_within_normschacht(haltung, normschacht_von, default_sohlenkote):
                        farbe = "Rot"

                if normschacht_nach:
                    print(f"Check Haltung within Normschacht nach: {haltung['id']} in {normschacht_nach['id']}")
                    if not check_haltung_within_normschacht(haltung, normschacht_nach, default_sohlenkote):
                        farbe = "Rot"

        add_color(ifc_file, ifc_pipe_segment, farbe, context)

        ifc_file.create_entity("IfcRelContainedInSpatialStructure",
            GlobalId=generate_guid(),
            RelatedElements=[ifc_pipe_segment],
            RelatingStructure=facility
        )

        properties = {
            "Bezeichnung": haltung['bezeichnung'],
            "Material": haltung.get('material', ''),
            "Länge Effektiv": str(haltung.get('length', '')),
            "Lichte Höhe": str(haltung['durchmesser'])
        }

        add_property_set(ifc_file, ifc_pipe_segment, "TBAKTZH STRE Haltung", properties)

        ifc_file.create_entity("IfcRelAssignsToGroup",
            GlobalId=generate_guid(),
            RelatedObjects=[ifc_pipe_segment],
            RelatingGroup=haltungen_group
        )

def create_ifc_normschacht(ifc_file, ns, abwasserknoten, facility, context, default_durchmesser, default_hoehe, default_sohlenkote, default_wanddicke, default_bodendicke, abwasserknoten_group, einfaerben, data):
    lage = abwasserknoten.get('lage', {})
    x_mitte = float(lage.get('c1'))
    y_mitte = float(lage.get('c2'))
    breite = float(ns['dimension1']) / 1000.0 if ns['dimension1'] != '0' else default_durchmesser
    tiefe = float(ns['dimension2']) / 1000.0 if ns['dimension2'] != '0' else default_hoehe
    radius = breite / 2
    hoehe = tiefe
    wanddicke = default_wanddicke
    bodendicke = default_bodendicke

    kote = abwasserknoten.get('kote')
    z_mitte = float(kote) if kote and float(kote) != 0 else default_sohlenkote

    base_center = create_cartesian_point(ifc_file, (x_mitte, y_mitte, z_mitte))
    axis = ifc_file.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    axis_placement = ifc_file.create_entity("IfcAxis2Placement3D", Location=base_center, Axis=axis)
    ifc_local_placement = ifc_file.create_entity("IfcLocalPlacement", RelativePlacement=axis_placement)

    if breite <= 2 * wanddicke:
        profile = ifc_file.create_entity("IfcCircleProfileDef", ProfileType="AREA", Radius=radius)
        body = ifc_file.create_entity("IfcExtrudedAreaSolid", SweptArea=profile, ExtrudedDirection=axis, Depth=hoehe)
        items = [body]
    else:
        outer_profile = ifc_file.create_entity("IfcCircleProfileDef", ProfileType="AREA", Radius=radius)
        outer_body = ifc_file.create_entity("IfcExtrudedAreaSolid", SweptArea=outer_profile, ExtrudedDirection=axis, Depth=hoehe)

        inner_radius = radius - wanddicke
        inner_profile = ifc_file.create_entity("IfcCircleProfileDef", ProfileType="AREA", Radius=inner_radius)
        inner_body = ifc_file.create_entity("IfcExtrudedAreaSolid", SweptArea=inner_profile, ExtrudedDirection=axis, Depth=hoehe)

        boolean_result = ifc_file.create_entity("IfcBooleanResult", Operator="DIFFERENCE", FirstOperand=outer_body, SecondOperand=inner_body)

        bottom_profile = ifc_file.create_entity("IfcCircleProfileDef", ProfileType="AREA", Radius=inner_radius)
        bottom_body = ifc_file.create_entity("IfcExtrudedAreaSolid", SweptArea=bottom_profile, ExtrudedDirection=axis, Depth=bodendicke)

        bottom_placement = create_local_placement(ifc_file, [x_mitte, y_mitte, z_mitte - bodendicke])
        
        items = [boolean_result, bottom_body]

    schacht = ifc_file.create_entity("IfcDistributionChamberElement",
        GlobalId=generate_guid(),
        Name=ns.get('bezeichnung', 'Normschacht'),
        ObjectPlacement=ifc_local_placement,
        Representation=ifc_file.create_entity("IfcProductDefinitionShape",
            Representations=[ifc_file.create_entity("IfcShapeRepresentation",
                ContextOfItems=context,
                RepresentationIdentifier="Body",
                RepresentationType="SweptSolid",
                Items=items
            )]
        )
    )
    
    properties = {
        "Bezeichnung": ns.get('bezeichnung', ''),
        "Standortname": ns.get('standortname', ''),
        "Höhe": str(hoehe),
        "Durchmesser": str(breite),
        "Funktion": ns.get('funktion', ''),
        "Material": ns.get('material', ''),
        "Sohlenkote": str(z_mitte)
    }

    property_set = ifc_file.create_entity("IfcPropertySet",
        GlobalId=generate_guid(),
        Name="TBAKTZH STRE Schacht",
        HasProperties=[create_property_single_value(ifc_file, key, value) for key, value in properties.items()]
    )

    ifc_file.create_entity("IfcRelDefinesByProperties",
        GlobalId=generate_guid(),
        RelatingPropertyDefinition=property_set,
        RelatedObjects=[schacht]
    )

    ifc_file.create_entity("IfcRelContainedInSpatialStructure",
        GlobalId=generate_guid(),
        RelatedElements=[schacht],
        RelatingStructure=facility
    )

    ifc_file.create_entity("IfcRelAssignsToGroup",
        GlobalId=generate_guid(),
        RelatedObjects=[schacht],
        RelatingGroup=abwasserknoten_group
    )

    fehlende_werte = 0
    farbe = "Blau"
    if einfaerben:
        if ns.get('dimension1') == '0' or ns.get('dimension2') == '0':
            fehlende_werte += 1
        if not abwasserknoten or float(abwasserknoten.get('kote', 0)) == 0:
            fehlende_werte += 1

        farbe = "Grün"
        if fehlende_werte == 1:
            farbe = "Orange"
        elif fehlende_werte >= 2:
            farbe = "Rot"
        else:
            # Prüfen, ob die zugeordneten Haltungspunkte innerhalb des Schachtes sind
            zugeordnete_haltungen = [haltung for haltung in data['haltungen'] if haltung['von_haltungspunkt'].get('abwasserknoten_ref') == abwasserknoten['id'] or haltung['nach_haltungspunkt'].get('abwasserknoten_ref') == abwasserknoten['id']]
            for haltung in zugeordnete_haltungen:
                print(f"Check Haltung within Normschacht für Schacht {ns['id']} und Haltung {haltung['id']}")
                if not check_haltung_within_normschacht(haltung, ns, default_sohlenkote):
                    fehlende_werte += 1
                    break

            if fehlende_werte == 1:
                farbe = "Orange"
            elif fehlende_werte >= 2:
                farbe = "Rot"

    add_color(ifc_file, schacht, farbe, context)

def create_ifc_normschachte(ifc_file, data, facility, context, abwasserknoten_group, einfaerben):
    logging.info(f"Füge Normschächte hinzu: {len(data['normschachte'])}")
    for ns in data['normschachte']:
        abwasserknoten = next((ak for ak in data['abwasserknoten'] if ak['id'] == ns['abwasserknoten_id']), None)
        if abwasserknoten:
            create_ifc_normschacht(ifc_file, ns, abwasserknoten, facility, context, data['default_durchmesser'], data['default_hoehe'], data['default_sohlenkote'], data['default_wanddicke'], data['default_bodendicke'], abwasserknoten_group, einfaerben, data)
        else:
            logging.error(f"Fehler: Normschacht {ns.get('id', 'Unbekannt')} oder zugehöriger Abwasserknoten hat keine Koordinaten.")
            data['nicht_verarbeitete_normschachte'].append(ns['id'])

def create_ifc(ifc_file_path, data, einfaerben):
    logging.info("Erstelle IFC-Datei...")

    ifc_file = ifcopenshell.file(schema="IFC4X3")

    context, facility = create_ifc_project_structure(ifc_file)

    abwasserknoten_group = ifc_file.create_entity("IfcGroup", GlobalId=generate_guid(), Name="Abwasserknoten")
    haltungen_group = ifc_file.create_entity("IfcGroup", GlobalId=generate_guid(), Name="Haltungen")

    default_sohlenkote = data['default_sohlenkote']

    create_ifc_haltungen(ifc_file, data, facility, context, haltungen_group, einfaerben, default_sohlenkote)
    create_ifc_normschachte(ifc_file, data, facility, context, abwasserknoten_group, einfaerben)

    logging.info(f"Speichern der IFC-Datei unter {ifc_file_path}...")
    ifc_file.write(ifc_file_path)