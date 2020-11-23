"""Authors: Cody Baker and Ben Dichter."""
from buzsaki_lab_to_nwb import PeyracheNWBConverter
from nwb_conversion_tools import NeuroscopeRecording
from pathlib import Path
import os

base_path = Path("D:/BuzsakiData/PeyracheA")
mice_names = [f"Mouse{x}" for x in ["12", "16", "17", "18", "19", "20", "23", "24", "25", "27", "28", "32"]]

convert_sessions = [session for mouse_name in mice_names for session in (base_path / Path(mouse_name)).iterdir()]

experimenter = "Adrien Peyrache"
paper_descr = "The data set contains recordings made from multiple anterior thalamic nuclei, mainly "
"the antero-dorsal (AD) nucleus, and subicular areas, mainly the post-subiculum (PoS), in freely moving "
"mice. Thalamic and subicular electrodes yielding high number of the so-called Head-Direction (HD) cells were "
"likely to be located in the AD nucleus and the PoS, respectively. Electrode placement was confirmed by "
"histology. The data was obtained during 42 recording sessions and includes responses of 720 neurons in the "
"thalamus and 357 neurons in the PoS, in seven animals while they foraged for food in an open environment "
"(53- x 46-cm).  Three animals were recorded simultaneously in the thalamus and the PoS (21 sessions). In the "
"four other animals, electrodes were implanted in the anterior thalamus and in the pyramidal layer of the CA1 "
"area of the hippocampus but only to record Local field Potentials (LFPs). The raw (broadband) data was recorded "
"at 20KHz, simultaneously from 64 to 96 channels."
paper_info = [
    "Internally organized mechanisms of the head direction sense. "
    "Peyrache A, Lacroix MM, Petersen PC, Buzsaki G, Nature Neuroscience. 2015"
]

device_descr = "Silicon probes (Neuronexus Inc. Ann Arbor, MI) were mounted on movable drives for recording "
"of neuronal activity and local field potentials (LFP) in the anterior thalamus (n = 7 mice) and, in addition "
"in the post-subiculum (n = 3 out of 7 mice). In the four animals implanted only in the anterior thalamus, "
"electrodes were also implanted in the hippocampal CA1 pyramidal layer for accurate sleep scoring: three to six "
"50 μm tungsten wires (Tungsten 99.95%, California Wire Company) were inserted in silicate tubes and attached to "
"a micromanipulator. Thalamic probes were implanted in the left hemisphere, perpendicularly to the midline, "
"(AP: –0.6 mm; ML:–0.5 to –1.9 mm; DV: 2.2 mm), with a 10 – 15° angle, the shanks pointing toward midline "
"(see Supplementary Fig. 1a–f). Post-subicular probes were inserted at the following coordinates: AP: –4.25 mm: "
"ML: –1 to –2 mm; DV: 0.75 mm (Supplementary Fig. 1g,h). Hippocampal wire bundles were implanted above "
"CA1 (AP: –2.2 mm; –1 to –1.6 mm ML; 1 mm DV). The probes consisted of 4, 6 or 8 shanks "
"(200-μm shank separation) and each shank had 8 (4 or 8 shank probes; Buz32 or Buz64 Neuronexus) or 10 "
"recording (6-shank probes; Buz64s) sites (160 μm2 each site; 1–3 M impedance), staggered to provide a "
"two-dimensional arrangement (20 μm vertical separation)."
raw_sessions = []  # ["Mouse12-120806"]

for session_path in convert_sessions:
    folder_path = session_path.absolute()
    session_id = session_path.name
    print(f"Converting session {session_id}...")

    input_args = dict(
        NeuroscopeSorting=dict(
            folder_path=folder_path,
            keep_mua_units=False
        ),
        PeyracheLFP=dict(folder_path=folder_path),
        PeyracheBehavior=dict(folder_path=folder_path)
    )
    conversion_options = dict(
        NeuroscopeSorting=dict(stub_test=True),
        PeyracheLFP=dict(stub_test=True)
    )

    if session_path in raw_sessions:
        input_args.update(
            NeuroscopeRecording=dict(
                folder_path=folder_path
            )
        )
        conversion_options.update(
            NeuroscopeRecording=dict(
                stub_test=True
            )
        )
    else:
        conversion_options['NeuroscopeSorting'].update(write_ecephys_metadata=True)

    peyrache_converter = PeyracheNWBConverter(**input_args)
    metadata = peyrache_converter.get_metadata()

    # Specific info
    metadata['NWBFile'].update(
        experimenter=experimenter,
        session_description=paper_descr,
        related_publications=paper_info
    )
    metadata['Subject'].update(
        genotype="Wild type",
        weight="27-50g"
    )
    if session_path not in raw_sessions:
        metadata['Ecephys'].update(NeuroscopeRecording.get_metadata())
    metadata['Ecephys']['Device'][0].update(description=device_descr)

    nwbfile_path = os.path.join(folder_path, f"{session_id}_stub.nwb")
    peyrache_converter.run_conversion(
        nwbfile_path=nwbfile_path,
        metadata=metadata,
        conversion_options=conversion_options
    )
