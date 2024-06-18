import ifcopenshell
import logging
from utils import generate_guid, add_property_set, create_cartesian_point, create_swept_disk_solid

def create_ifc_project_structure(ifc_file):
    # Create IFC project structure
    logging.info("Erstelle IFC-Projektstruktur.")
    project = ifc_file.create_entity("IfcProject", GlobalId=generate_guid(), Name="Entwässerungsprojekt")
    context = ifc_file.create_entity("IfcGeometricRepresentationContext", ContextType="Model", ContextIdentifier="Building Model")
    site = ifc_file.create_entity("IfcSite", GlobalId=generate_guid(), Name="Perimeter")
    facility = ifc_file.create_entity("IfcFacility", GlobalId=generate_guid(), Name="Entwässerungsanlage")
    
    # Create groups
    abwasserknoten_group = ifc_file.create_entity("IfcGroup", GlobalId=generate_guid(), Name="Abwasserknoten")
    haltungen_group = ifc_file.create_entity("IfcGroup", GlobalId=generate_guid(), Name="Haltungen")

    ifc_file.create_entity("IfcRelAggregates", GlobalId=generate_guid(), RelatingObject=project, RelatedObjects=[site])
    ifc_file.create_entity("IfcRelAggregates", GlobalId=generate_guid(), RelatingObject=site, RelatedObjects=[facility])
    
    return context, facility, abwasserknoten_group, haltungen_group

def create_swept_disk_solid(ifc_file, polyline, radius):
    # Create swept disk solid entity
    return ifc_file.create_entity("IfcSweptDiskSolid", Directrix=polyline, Radius=radius)

def create_local_placement(ifc_file, point, relative_to=None):
    # Create local placement for an entity
    ifc_point = ifc_file.create_entity('IfcCartesianPoint', Coordinates=point)
    axis2placement = ifc_file.create_entity('IfcAxis2Placement3D', Location=ifc_point)

    if relative_to:
        local_placement = ifc_file.create_entity('IfcLocalPlacement', PlacementRelTo=relative_to, RelativePlacement=axis2placement)
    else:
        local_placement = ifc_file.create_entity('IfcLocalPlacement', RelativePlacement=axis2placement)
    
    return local_placement

def interpolate_z(start_z, end_z, num_points):
    # Interpolate Z-values between start and end points
    return [start_z + (end_z - start_z) * i / (num_points - 1) for i in range(num_points)]

def add_color(ifc_file, ifc_element, farbe, context):
    # Add color to an IFC element
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

def create_ifc_haltungen(ifc_file, data, facility, context, haltungen_group, einfaerben):
    haltungen = data['haltungen']
    default_durchmesser = data['default_durchmesser']
    zusatz_hoehe_haltpunkt = data['zusatz_hoehe_haltpunkt']

    for haltung in haltungen:
        durchmesser = haltung.get('durchmesser', default_durchmesser)

        start_point = haltung['von_haltungspunkt']['lage']
        end_point = haltung['nach_haltungspunkt']['lage']

        start_x = float(start_point['c1'])
        start_y = float(start_point['c2'])
        start_z = float(haltung['von_z']) + zusatz_hoehe_haltpunkt + (durchmesser / 2)

        end_x = float(end_point['c1'])
        end_y = float(end_point['c2'])
        end_z = float(haltung['nach_z']) + zusatz_hoehe_haltpunkt + (durchmesser / 2)

        ifc_local_placement = create_local_placement(ifc_file, [start_x, start_y, start_z], relative_to=facility.ObjectPlacement)

        polyline_3d = []
        for point in haltung['verlauf']:
            x = float(point['c1']) - start_x
            y = float(point['c2']) - start_y
            if point.get('kote') and float(point['kote']) != 0:
                z = float(point['kote']) + (durchmesser / 2)
            else:
                if end_x - start_x != 0:
                    z = start_z + (end_z - start_z) * (float(point['c1']) - start_x) / (end_x - start_x)
                else:
                    z = start_z
                z -= start_z
            polyline_3d.append([x, y, z])

        ifc_polyline = ifc_file.create_entity('IfcPolyline', Points=[create_cartesian_point(ifc_file, p) for p in polyline_3d])

        ifc_pipe_segment = ifc_file.create_entity("IfcPipeSegment", GlobalId=generate_guid(), OwnerHistory=None, Name=haltung['bezeichnung'],
                                                  ObjectPlacement=ifc_local_placement, Representation=None)

        swept_disk_solid = create_swept_disk_solid(ifc_file, ifc_polyline, durchmesser / 2)

        shape_representation = ifc_file.create_entity("IfcShapeRepresentation",
                                                      ContextOfItems=context,
                                                      RepresentationIdentifier="Body",
                                                      RepresentationType="SweptSolid",
                                                      Items=[swept_disk_solid])

        product_shape = ifc_file.create_entity("IfcProductDefinitionShape",
                                               Representations=[shape_representation])

        ifc_pipe_segment.Representation = product_shape

        if einfaerben:
            missing_count = sum(1 for point in haltung['verlauf'] if point.get('kote') is None or float(point['kote']) == 0)
            if missing_count == 0:
                farbe = "Grün"
            else:
                farbe = "Rot"
            add_color(ifc_file, ifc_pipe_segment, farbe, context)
        else:
            farbe = "Blau"
            add_color(ifc_file, ifc_pipe_segment, farbe, context)
            
        ifc_file.create_entity("IfcRelContainedInSpatialStructure",
            GlobalId=generate_guid(),
            RelatedElements=[ifc_pipe_segment],
            RelatingStructure=facility
        )

        add_property_set(ifc_file, ifc_pipe_segment, "PipeSegmentPropertySet")

        ifc_file.create_entity("IfcRelAssignsToGroup",
            GlobalId=generate_guid(),
            RelatedObjects=[ifc_pipe_segment],
            RelatingGroup=haltungen_group
        )

def create_ifc_normschacht(ifc_file, ns, abwasserknoten, facility, context, default_durchmesser, default_hoehe, default_sohlenkote, abwasserknoten_group, einfaerben):
    # Create a normschacht element
    lage = abwasserknoten.get('lage', {})
    x_mitte = float(lage.get('c1'))
    y_mitte = float(lage.get('c2'))
    breite = float(ns['dimension1']) / 1000.0 if ns['dimension1'] != '0' else default_durchmesser
    tiefe = float(ns['dimension2']) / 1000.0 if ns['dimension2'] != '0' else default_hoehe
    radius = breite / 2
    hoehe = tiefe

    kote = abwasserknoten.get('kote')
    z_mitte = float(kote) if kote and float(kote) != 0 else default_sohlenkote

    base_center = create_cartesian_point(ifc_file, (x_mitte, y_mitte, z_mitte))
    axis = ifc_file.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    axis_placement = ifc_file.create_entity("IfcAxis2Placement3D", Location=base_center, Axis=axis)
    ifc_local_placement = ifc_file.create_entity("IfcLocalPlacement", RelativePlacement=axis_placement)

    profile = ifc_file.create_entity("IfcCircleProfileDef", ProfileType="AREA", Radius=radius)
    body = ifc_file.create_entity("IfcExtrudedAreaSolid", SweptArea=profile, ExtrudedDirection=axis, Depth=hoehe)

    schacht = ifc_file.create_entity("IfcDistributionChamberElement",
        GlobalId=generate_guid(),
        Name=ns.get('bezeichnung', 'Normschacht'),
        ObjectPlacement=ifc_local_placement,
        Representation=ifc_file.create_entity("IfcProductDefinitionShape",
            Representations=[ifc_file.create_entity("IfcShapeRepresentation",
                ContextOfItems=context,
                RepresentationIdentifier="Body",
                RepresentationType="SweptSolid",
                Items=[body]
            )]
        )
    )
    add_property_set(ifc_file, schacht, "Normschacht")
    ifc_file.create_entity("IfcRelContainedInSpatialStructure",
        GlobalId=generate_guid(),
        RelatedElements=[schacht],
        RelatingStructure=facility
    )
    
    # Add to abwasserknoten group
    ifc_file.create_entity("IfcRelAssignsToGroup",
        GlobalId=generate_guid(),
        RelatedObjects=[schacht],
        RelatingGroup=abwasserknoten_group
    )

    # Add color to normschacht
    if einfaerben:
        fehlende_werte = sum([1 for key in ['dimension1', 'dimension2'] if ns.get(key) is None or ns.get(key) == '0'])
        if abwasserknoten is None or abwasserknoten.get('kote') is None or float(abwasserknoten.get('kote', 0)) == 0:
            fehlende_werte += 1

        if fehlende_werte == 0:
            farbe = "Grün"
        elif fehlende_werte == 1:
            farbe = "Orange"
        else:
            farbe = "Rot"
        add_color(ifc_file, schacht, farbe, context)
    else:
        farbe = "Blau"
        add_color(ifc_file, schacht, farbe, context)
    
def create_ifc_normschachte(ifc_file, data, facility, context, abwasserknoten_group, einfaerben):
    # Create IFC elements for normschachte
    logging.info(f"Füge Normschächte hinzu: {len(data['normschachte'])}")
    for ns in data['normschachte']:
        abwasserknoten = next((ak for ak in data['abwasserknoten'] if ak['id'] == ns['abwasserknoten_id']), None)
        if abwasserknoten:
            create_ifc_normschacht(ifc_file, ns, abwasserknoten, facility, context, data['default_durchmesser'], data['default_hoehe'], data['default_sohlenkote'], abwasserknoten_group, einfaerben)
        else:
            logging.error(f"Fehler: Normschacht {ns.get('id', 'Unbekannt')} oder zugehöriger Abwasserknoten hat keine Koordinaten.")
            data['nicht_verarbeitete_normschachte'].append(ns['id'])

def create_ifc(ifc_file_path, data, einfaerben):
    # Main function to create the IFC file
    logging.info("Erstelle IFC-Datei...")

    ifc_file = ifcopenshell.file(schema="IFC4X3")

    context, facility, abwasserknoten_group, haltungen_group = create_ifc_project_structure(ifc_file)

    create_ifc_haltungen(ifc_file, data, facility, context, haltungen_group, einfaerben)

    create_ifc_normschachte(ifc_file, data, facility, context, abwasserknoten_group, einfaerben)

    logging.info(f"Speichern der IFC-Datei unter {ifc_file_path}...")
    ifc_file.write(ifc_file_path)
    logging.info("IFC-Datei erfolgreich erstellt.")
