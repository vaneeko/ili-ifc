import ifcopenshell
import math
from utils import add_color, generate_guid, create_local_placement, create_cartesian_point, create_property_single_value

def berechne_richtung(start_point, end_point):
    dx = float(end_point['c1']) - float(start_point['c1'])
    dy = float(end_point['c2']) - float(start_point['c2'])
    length = math.sqrt(dx ** 2 + dy ** 2)
    if length == 0:
        return {'x': 0.0, 'y': 0.0, 'z': 0.0}
    return {'x': dx / length, 'y': dy / length, 'z': 0.0}

def create_ifc_normschacht(ifc_file, ns, abwasserknoten, facility, context, default_durchmesser, default_hoehe, default_sohlenkote, default_wanddicke, default_bodendicke, abwasserknoten_group, einfaerben, data, haltungen):
    if abwasserknoten:
        lage = abwasserknoten.get('lage', {})
        x_mitte = float(lage.get('c1'))
        y_mitte = float(lage.get('c2'))
        kote = abwasserknoten.get('kote')
        z_mitte = float(kote) if kote and float(kote) != 0 else default_sohlenkote
    else:
        lage = ns.get('lage', {})
        x_mitte = float(lage.get('c1'))
        y_mitte = float(lage.get('c2'))
        z_mitte = default_sohlenkote

    try:
        breite = float(ns['dimension1']) / 1000.0 if ns['dimension1'] != '0' else default_durchmesser
    except ValueError:
        breite = default_durchmesser

    try:
        tiefe = float(ns['dimension2']) / 1000.0 if ns['dimension2'] != '0' else default_hoehe
    except ValueError:
        tiefe = default_hoehe

    radius = breite / 2
    hoehe = tiefe
    wanddicke = default_wanddicke
    bodendicke = default_bodendicke

    base_center = create_cartesian_point(ifc_file, (x_mitte, y_mitte, z_mitte))
    axis = ifc_file.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    axis_placement = ifc_file.create_entity("IfcAxis2Placement3D", Location=base_center, Axis=axis)
    ifc_local_placement = ifc_file.create_entity("IfcLocalPlacement", RelativePlacement=axis_placement)

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

    # Add boolean difference for each Haltung
    for haltung in haltungen:
        if (haltung['von_haltungspunkt']['lage']['c1'], haltung['von_haltungspunkt']['lage']['c2']) == (x_mitte, y_mitte) or (haltung['nach_haltungspunkt']['lage']['c1'], haltung['nach_haltungspunkt']['lage']['c2']) == (x_mitte, y_mitte):
            richtung = berechne_richtung(haltung['von_haltungspunkt']['lage'], haltung['nach_haltungspunkt']['lage'])
            
            pipe_outer_radius = (haltung['durchmesser'] / 2) + data['default_rohrdicke']
            pipe_profile = ifc_file.create_entity("IfcCircleProfileDef", ProfileType="AREA", Radius=pipe_outer_radius)
            pipe_body = ifc_file.create_entity("IfcExtrudedAreaSolid", SweptArea=pipe_profile, ExtrudedDirection=axis, Depth=wanddicke)

            pipe_local_placement = create_local_placement(ifc_file, [x_mitte, y_mitte, z_mitte], [richtung['x'], richtung['y'], richtung['z']])
            pipe_placement = ifc_file.create_entity("IfcLocalPlacement", RelativePlacement=pipe_local_placement)
            
            # Create boolean operation for the hole
            hole_boolean = ifc_file.create_entity("IfcBooleanResult", Operator="DIFFERENCE", FirstOperand=boolean_result, SecondOperand=pipe_body)
            boolean_result = hole_boolean  # Update the boolean_result with the new hole

    schacht = ifc_file.create_entity("IfcDistributionChamberElement",
        GlobalId=generate_guid(),
        Name=ns.get('bezeichnung', 'Normschacht'),
        ObjectPlacement=ifc_local_placement,
        Representation=ifc_file.create_entity("IfcProductDefinitionShape",
            Representations=[ifc_file.create_entity("IfcShapeRepresentation",
                ContextOfItems=context,
                RepresentationIdentifier="Body",
                RepresentationType="SweptSolid",
                Items=[boolean_result]  # Update items to boolean_result
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

    if abwasserknoten:
        ifc_file.create_entity("IfcRelAssignsToGroup",
            GlobalId=generate_guid(),
            RelatedObjects=[schacht],
            RelatingGroup=abwasserknoten_group
        )

    fehlende_werte = 0
    farbe = "Blau"
    if einfaerben:
        if ns.get('dimorg1') == '0' or ns.get('dimorg2') == '0':
            fehlende_werte += 1
        if not abwasserknoten or float(abwasserknoten.get('kote', 0)) == 0:
            fehlende_werte += 1

        farbe = "Grün"
        if fehlende_werte == 1:
            farbe = "Orange"
        elif fehlende_werte >= 2:
            farbe = "Rot"

    add_color(ifc_file, schacht, farbe, context)
