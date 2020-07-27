from abc import abstractmethod
from copy import deepcopy

from nwb_conversion_tools.utils import get_schema_from_method_signature, get_schema_from_hdmf_class



base_schema = dict(
    required=[],
    properties=[],
    type='object',
    additionalProperties='false')

root_schema = deepcopy(base_schema)
root_schema.update({
    "$schema": "http://json-schema.org/draft-07/schema#",
})

class NWBConverter:
    
    data_interface_classes = None  # dict of all data interfaces
    
    @classmethod
    def get_input_schema(cls): # I'm thinking about making this a class attribute instead of a class method
        """Compile input schemas from each of the data interface classes"""
        input_schema = deepcopy(root_schema)
        for name, data_interface in cls.data_interface_classes.items():
            input_schema['properties'].append(data_interface.get_input_schema())
        return input_schema
    
    def __init__(self, **input_paths):
        """Initialize all of the underlying data interfaces"""
        self.data_interface_objects = {name: data_interface(**input_paths[name])
                                       for name, data_interface in self.data_interface_classes.items()}
        
    def get_metadata_schema(self):
        """Compile metadata schemas from each of the data interface objects"""
        
        metadata_schema = deepcopy(root_schema)
        default_metadata_schema['properties'] = dict(
            NWBFile=get_schema_from_hdmf_class(NWBFile),
            Subject=get_schema_from_hdmf_class(Subject)
        )
        for name, data_interface in self.data_interface_objects.items():
            metadata_schema['properties'].append(dict(name=data_interface.get_metadata_schema()))
            metadata_schema['required'].append(name)
            
        return metadata_schema

    def run_conversion(self, nwbfile_path, metadata_dict):
        """Run all of the data interfaces"""
        # default implementation will be to sequentially run each data interface, but this can be overridden as needed
        [data_interface.convert_data(nwbfile_path, metadata_dict[name])
         for name, data_interface in self.data_interface_objects.items()]