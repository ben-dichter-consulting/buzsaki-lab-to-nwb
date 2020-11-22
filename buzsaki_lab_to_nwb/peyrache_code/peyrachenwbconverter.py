"""Authors: Cody Baker and Ben Dichter."""
from nwb_conversion_tools import NWBConverter, neuroscopedatainterface
from .peyrachelfpdatainterface import PeyracheLFPInterface
from .peyrachebehaviordatainterface import PeyracheBehaviorInterface
import numpy as np
from scipy.io import loadmat
import os
from lxml import etree as et
from datetime import datetime
from dateutil.parser import parse as dateparse


class GrosmarkNWBConverter(NWBConverter):
    """Primary conversion class for the GrosmarkAD dataset."""

    data_interface_classes = dict(
        NeuroscopeRecording=neuroscopedatainterface.NeuroscopeMultiRecordingInterface,
        NeuroscopeSorting=neuroscopedatainterface.NeuroscopeSortingInterface,
        PeyracheLFP=PeyracheLFPInterface,
        # PeyracheBehavior=PeyracheBehaviorInterface
    )

    def get_metadata(self):
        """Auto-fill all relevant metadata used in run_conversion."""
        session_path = self.data_interface_objects['GrosmarkLFP'].input_args['folder_path']
        subject_path, session_id = os.path.split(session_path)
        if '_' in session_id:
            subject_id, date_text = session_id.split('_')
        session_start = dateparse(date_text[-4:] + date_text[:-4])

        xml_filepath = os.path.join(session_path, "{}.xml".format(session_id))
        root = et.parse(xml_filepath).getroot()

        shank_channels = [[int(channel.text)
                          for channel in group.find('channels')]
                          for group in root.find('spikeDetection').find('channelGroups').findall('group')]
        all_shank_channels = np.concatenate(shank_channels)
        all_shank_channels.sort()

        shank_electrode_number = [x for channels in shank_channels for x, _ in enumerate(channels)]
        shank_group_name = ["shank{}".format(n+1) for n, channels in enumerate(shank_channels) for _ in channels]

        cell_filepath = os.path.join(session_path, "{}.spikes.cellinfo.mat".format(session_id))
        if os.path.isfile(cell_filepath):
            cell_info = loadmat(cell_filepath)['spikes']

        celltype_mapping = {'pE': "excitatory", 'pI': "inhibitory"}
        celltype_filepath = os.path.join(session_path, "{}.CellClass.cellinfo.mat".format(session_id))
        if os.path.isfile(celltype_filepath):
            celltype_info = [str(celltype_mapping[x[0]])
                             for x in loadmat(celltype_filepath)['CellClass']['label'][0][0][0]]
        metadata = super().get_metadata()
        return metadata
