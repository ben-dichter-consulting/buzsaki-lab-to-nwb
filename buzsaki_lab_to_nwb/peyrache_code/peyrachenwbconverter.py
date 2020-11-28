"""Authors: Cody Baker and Ben Dichter."""
from nwb_conversion_tools import NWBConverter, neuroscopedatainterface, cellexplorerdatainterface
# from .peyrachebehaviordatainterface import PeyracheBehaviorInterface
from pathlib import Path
from dateutil.parser import parse as dateparse


class PeyracheNWBConverter(NWBConverter):
    """Primary conversion class for the GrosmarkAD dataset."""

    data_interface_classes = dict(
        #NeuroscopeRecording=neuroscopedatainterface.NeuroscopeRecordingInterface,
        CellExplorerSorting=cellexplorerdatainterface.CellExplorerSortingInterface,
        # NeuroscopeLFP=neuroscopedatainterface.NeuroscopeLFPInterface,
        # PeyracheBehavior=PeyracheBehaviorInterface
    )

    def get_metadata(self):
        """Auto-fill all relevant metadata used in run_conversion."""
        #session_id = Path(self.data_interface_objects['NeuroscopeLFP'].source_data['file_path']).stem
        session_id = "Mouse12-120806"
        if '-' in session_id:
            subject_id, date_text = session_id.split('-')
        session_start = dateparse(date_text[-4:] + date_text[:-4])

        metadata = super().get_metadata()
        metadata['NWBFile'].update(
                session_start_time=session_start.astimezone(),
                session_id=session_id,
                institution="NYU",
                lab="Buzsaki"
        )
        metadata.update(
            Subject=dict(
                species="Mus musculus"
            )
        )
        return metadata
