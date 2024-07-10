import ifcopenshell
from utils.common import add_color, generate_guid, create_local_placement, create_cartesian_point, create_property_single_value

def create_ifc_normschacht(ifc_file, ns, abwasserknoten, facility, context, abwasserknoten_group, data):
    default_sohlenkote = data['default_sohlenkote']
    default_durchmesser = data['default_durchmesser']
    default_hoehe = data['default_hoehe']
    default_wanddicke = data['default_wanddicke']
    default_bodendicke = data['default_bodendicke']
    einfaerben = data['einfaerben']

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