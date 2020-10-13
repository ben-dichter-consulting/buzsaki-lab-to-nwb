"""Authors: Cody Baker and Ben Dichter."""
from buzsaki_lab_to_nwb import YutaNWBConverter

# TODO: add pathlib
import os
import pandas as pd

# List of folder paths to iterate over
base_path = "D:/BuzsakiData/SenzaiY"
paper_sessions = pd.read_excel(os.path.join(base_path, "DG_all_6_SessionShankList.xls"), header=None)[0]
sessions = dict()
for paper_session in paper_sessions:
    mouse_id = paper_session[9:11]  # could be generalized better
    if mouse_id in sessions:
        sessions[mouse_id].append(paper_session[11:])
    else:
        sessions.update({mouse_id: [paper_session[11:]]})

experimenter = "Yuta Senzai"
paper_descr = "mouse in open exploration and theta maze"
paper_info = "DOI:10.1016/j.neuron.2016.12.011"

for mouse_num, session_id in sessions.items():
    # TODO: replace with pathlib
    mouse_str = "YutaMouse" + str(mouse_num)
    session = os.path.join(base_path, mouse_str, mouse_str+session_id)
    session_name = os.path.split(session)[1]
    nwbfile_path = session + "_stub.nwb"

    # In case this has to be run multiple times due to random errors, don't overwrite the nwbfile
    if not os.path.isfile(nwbfile_path):
        input_file_schema = YutaNWBConverter.get_input_schema()

        # construct input_args dict according to input schema
        input_args = {
            'NeuroscopeRecording': {'file_path': os.path.join(session, session_name) + ".dat"},
            'NeuroscopeSorting': {'folder_path': session,
                                  'keep_mua_units': False},
            'YutaPosition': {'folder_path': session},
            'YutaLFP': {'folder_path': session},
            'YutaBehavior': {'folder_path': session}
        }

        yuta_converter = YutaNWBConverter(**input_args)

        expt_json_schema = yuta_converter.get_metadata_schema()

        # construct metadata_dict according to expt_json_schema
        metadata = yuta_converter.get_metadata()

        # Yuta specific info
        metadata['NWBFile'].update({'experimenter': experimenter})
        metadata['NWBFile'].update({'session_description': paper_descr})
        metadata['NWBFile'].update({'related_publications': paper_info})

        metadata['Subject'].update({'species': "Mus musculus"})
        #metadata['Subject'].update({'weight': '250-500g'})

        metadata[yuta_converter.get_recording_type()]['Ecephys']['Device'][0].update({'name': 'implant'})

        for electrode_group_metadata in metadata[yuta_converter.get_recording_type()]['Ecephys']['ElectrodeGroup']:
            electrode_group_metadata.update({'location': 'unknown'})
            electrode_group_metadata.update({'device_name': 'implant'})

        yuta_converter.run_conversion(nwbfile_path, metadata, stub_test=True)
