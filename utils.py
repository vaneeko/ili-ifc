import ifcopenshell
import ifcopenshell.util.element
import uuid

def generate_guid():
    """Generates a unique GUID."""
    return ifcopenshell.guid.compress(uuid.uuid1().hex)

def create_cartesian_point(ifc_file, coordinates):
    # Create a Cartesian point entity
    return ifc_file.create_entity('IfcCartesianPoint', Coordinates=coordinates)

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
