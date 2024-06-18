import ifcopenshell
import ifcopenshell.util.element
import uuid
from ifcopenshell.api import run

def generate_guid():
    """Generates a unique GUID."""
    return ifcopenshell.guid.compress(uuid.uuid1().hex)

def create_cartesian_point(ifc_file, coordinates):
    return ifc_file.create_entity('IfcCartesianPoint', Coordinates=coordinates)

# def create_local_placement(ifc_file, point, relative_to=None):
    # ifc_point = ifc_file.createIfcCartesianPoint(point)
    # axis2placement = ifc_file.createIfcAxis2Placement3D(ifc_point)
    
    # if relative_to:
        # local_placement = ifc_file.createIfcLocalPlacement(relative_to, axis2placement)
    # else:
        # local_placement = ifc_file.createIfcLocalPlacement(None, axis2placement)
    
    # return local_placement
    
def create_swept_disk_solid(ifc_file, polyline, radius):
    return ifc_file.create_entity('IfcSweptDiskSolid',
        Directrix=polyline,
        Radius=radius,
        InnerRadius=None,
        StartParam=None,
        EndParam=None
    )

def add_property_set(ifc_file, ifc_object, name):
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
