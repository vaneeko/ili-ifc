import ifcopenshell
import ifcopenshell.util.element
import uuid
from ifcopenshell.api import run

def generate_guid():
    """Generates a unique GUID."""
    return ifcopenshell.guid.compress(uuid.uuid1().hex)

def create_cartesian_point(ifc_file, coordinates):
    # Create a Cartesian point entity
    return ifc_file.create_entity('IfcCartesianPoint', Coordinates=coordinates)

def create_swept_disk_solid(ifc_file, polyline, radius):
    # Create a swept disk solid entity
    return ifc_file.create_entity('IfcSweptDiskSolid',
        Directrix=polyline,
        Radius=radius,
        InnerRadius=None,
        StartParam=None,
        EndParam=None
    )

def add_property_set(ifc_file, ifc_object, name):
    # Add a property set to an IFC object
    property_set = ifc_file.create_entity('IfcPropertySet', 
        GlobalId=generate_guid(),
        Name=name,
        HasProperties=[]
    )
    ifc_file.create_entity('IfcRelDefinesByProperties',
        GlobalId=generate_guid(),
        RelatingPropertyDefinition=property_set,
        RelatedObjects=[ifc_object]
    )
