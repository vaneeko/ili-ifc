import ifcopenshell
import logging
from utils import add_color, generate_guid, add_property_set, create_local_placement, create_cartesian_point, create_swept_disk_solid, create_property_single_value
from graphics_ns import create_ifc_normschacht
import math

def create_ifc_project_structure(ifc_file):
    logging.info("Erstelle IFC-Projektstruktur.")
    project = ifc_file.create_entity("IfcProject", GlobalId=generate_guid(), Name="Entwässerungsprojekt")
    context = ifc_file.create_entity("IfcGeometricRepresentationContext", ContextType="Model", ContextIdentifier="Building Model")
    site = ifc_file.create_entity("IfcSite", GlobalId=generate_guid(), Name="Perimeter")
   
    ifc_file.create_entity("IfcRelAggregates", GlobalId=generate_guid(), RelatingObject=project, RelatedObjects=[site])
    
    return context, site

def interpolate_z(start_z, end_z, start_x, start_y, end_x, end_y, point_x, point_y):
    total_distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    point_distance = math.sqrt((point_x - start_x)**2 + (point_y - start_y)**2)
    if total_distance != 0:
        interpolated_z = start_z + (end_z - start_z) * (point_distance / total_distance)
        return max(min(interpolated_z, max(start_z, end_z)), min(start_z, end_z))
    else:
        return start_z

def create_ifc_haltungen(ifc_file, data, site, context, haltungen_group, einfaerben, default_sohlenkote):
    haltungen = data['haltungen']
    default_durchmesser = data['default_durchmesser']
    default_rohrdicke = data['default_rohrdicke']  # Verwende den Standardwert für die Rohrdicke

    for haltung in haltungen:
        innendurchmesser = haltung.get('durchmesser', default_durchmesser)
        outer_radius = (innendurchmesser / 2) + default_rohrdicke
        inner_radius = innendurchmesser / 2

        start_point = haltung['von_haltungspunkt']['lage']
        end_point = haltung['nach_haltungspunkt']['lage']

        start_x = float(start_point['c1'])
        start_y = float(start_point['c2'])
        start_z = float(haltung['von_z']) if haltung['von_z'] != 0.0 else default_sohlenkote

        end_x = float(end_point['c1'])
        end_y = float(end_point['c2'])
        end_z = float(haltung['nach_z']) if haltung['nach_z'] != 0.0 else default_sohlenkote

        start_z += inner_radius
        end_z += inner_radius

        ifc_local_placement = create_local_placement(ifc_file, [start_x, start_y, start_z], relative_to=site.ObjectPlacement)

        if 'verlauf' in haltung and haltung['verlauf']:
            polyline_3d = []
            for point in haltung['verlauf']:
                x = float(point['c1']) - start_x
                y = float(point['c2']) - start_y
                if point.get('kote') and float(point['kote']) != 0:
                    z = float(point['kote']) - start_z
                else:
                    z = interpolate_z(start_z, end_z, start_x, start_y, end_x, end_y, float(point['c1']), float(point['c2'])) - start_z
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
                
        add_color(ifc_file, ifc_pipe_segment, farbe, context)

        ifc_file.create_entity("IfcRelContainedInSpatialStructure",
            GlobalId=generate_guid(),
            RelatedElements=[ifc_pipe_segment],
            RelatingStructure=site
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

def create_ifc_normschachte(ifc_file, data, site, context, abwasserknoten_group, einfaerben):
    logging.info(f"Füge Normschächte hinzu: {len(data['normschachte'])}")
    for ns in data['normschachte']:
        abwasserknoten = next((ak for ak in data['abwasserknoten'] if ak['id'] == ns['abwasserknoten_id']), None)
        create_ifc_normschacht(ifc_file, ns, abwasserknoten, site, context, data['default_durchmesser'], data['default_hoehe'], data['default_sohlenkote'], data['default_wanddicke'], data['default_bodendicke'], abwasserknoten_group, einfaerben, data)

def create_ifc(ifc_file_path, data, einfaerben):
    logging.info("Erstelle IFC-Datei...")

    ifc_file = ifcopenshell.file(schema="IFC4X3")

    context, site = create_ifc_project_structure(ifc_file)

    abwasserknoten_group = ifc_file.create_entity("IfcGroup", GlobalId=generate_guid(), Name="Abwasserknoten")
    haltungen_group = ifc_file.create_entity("IfcGroup", GlobalId=generate_guid(), Name="Haltungen")

    default_sohlenkote = data['default_sohlenkote']

    create_ifc_haltungen(ifc_file, data, site, context, haltungen_group, einfaerben, default_sohlenkote)
    create_ifc_normschachte(ifc_file, data, site, context, abwasserknoten_group, einfaerben)

    ifc_file.create_entity("IfcRelAggregates", GlobalId=generate_guid(), RelatingObject=site, RelatedObjects=[abwasserknoten_group])
    ifc_file.create_entity("IfcRelAggregates", GlobalId=generate_guid(), RelatingObject=site, RelatedObjects=[haltungen_group])

    logging.info(f"Speichern der IFC-Datei unter {ifc_file_path}...")
    ifc_file.write(ifc_file_path)