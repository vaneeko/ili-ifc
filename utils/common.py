import ifcopenshell
import ifcopenshell.util.element
import uuid

def generate_guid():
    """Generates a unique GUID."""
    return ifcopenshell.guid.compress(uuid.uuid1().hex)

def create_cartesian_point(ifc_file, coordinates):
    # Create a Cartesian point entity
    return ifc_file.create_entity('IfcCartesianPoint', Coordinates=coordinates)

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

def create_local_placement(ifc_file, point, direction=None, relative_to=None):
    location = create_cartesian_point(ifc_file, point)
    if direction:
        axis = ifc_file.create_entity("IfcDirection", DirectionRatios=direction)
        ref_direction = ifc_file.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0))
        axis2placement = ifc_file.create_entity("IfcAxis2Placement3D", Location=location, Axis=axis, RefDirection=ref_direction)
    else:
        axis2placement = ifc_file.create_entity("IfcAxis2Placement3D", Location=location)

    local_placement = ifc_file.create_entity('IfcLocalPlacement', PlacementRelTo=relative_to, RelativePlacement=axis2placement)
    return local_placement

def create_swept_disk_solid(ifc_file, polyline, outer_radius, inner_radius):
    # Create a swept disk solid entity
    return ifc_file.create_entity('IfcSweptDiskSolid',
        Directrix=polyline,
        Radius=outer_radius,
        InnerRadius=inner_radius,
        StartParam=None,
        EndParam=None
    )

def create_property_single_value(ifc_file, name, value, value_type='IfcText'):
    if value_type == 'IfcText':
        nominal_value = ifc_file.create_entity('IfcText', value)
    elif value_type == 'IfcLabel':
        nominal_value = ifc_file.create_entity('IfcLabel', value)
    elif value_type == 'IfcReal':
        nominal_value = ifc_file.create_entity('IfcReal', float(value))
    else:
        raise ValueError(f"Unsupported value type: {value_type}")

    return ifc_file.create_entity('IfcPropertySingleValue',
                                  Name=name,
                                  NominalValue=nominal_value)

def add_property_set(ifc_file, ifc_object, name, properties=None):
    if properties is None:
        properties = []
    else:
        properties = [
            create_property_single_value(ifc_file, key, value)
            for key, value in properties.items()
        ]
        
    property_set = ifc_file.create_entity('IfcPropertySet', 
        GlobalId=generate_guid(),
        Name=name,
        HasProperties=properties
    )
    ifc_file.create_entity('IfcRelDefinesByProperties',
        GlobalId=generate_guid(),
        RelatingPropertyDefinition=property_set,
        RelatedObjects=[ifc_object]
    )