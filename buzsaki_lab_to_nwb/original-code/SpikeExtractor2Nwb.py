from converter import NWBConverter
import spikesorters as ss
import spiketoolkit as st
import spikeextractors as se

import numpy as np


class SpikeExtractor2NWBConverter(NWBConverter):

    def __init__(self, nwbfile, metadata, source_paths, x_pitch=None, y_pitch=None):
        """
        Reads data using RecordingExtractor and/or SpikeExtractor
        from SpikeExtractors: https://github.com/SpikeInterface/spikeextractors

        Parameters
        ----------
        nwbfile: pynwb.NWBFile
        metadata: dict
        source_paths: {'npx_file': {'type': 'file', 'path': PATH_TO_FILE}}
            Dictionary with path to SpikeGLX file to be read.
        x_pitch : float
        y_pitch : float
        """
        super().__init__(nwbfile=nwbfile, metadata=metadata, source_paths=source_paths)

        self.RX = None
        self.SX = None

    def run_conversion(self):
        """
        Adds voltages traces in self.RX as ElectricalSeries at acquisition group
        of current NWBFile.
        """
        # Devices and ElectrodeGroups are automatically created at NWBConverter.__init__()
        # Add electrodes, use staticmethod from se.NwbRecordingExtractor
        if self.RX is not None:
            self.nwbfile = se.NwbRecordingExtractor.add_electrodes(
                recording=self.RX,
                nwbfile=self.nwbfile,
                metadata=self.metadata
            )

            self.nwbfile = se.NwbRecordingExtractor.add_electrical_series(
                recording=self.RX,
                nwbfile=self.nwbfile,
                metadata=self.metadata
            )

        if self.SX is not None:
            self.add_units()

    def add_units(self):
        """
        Adds Units group to current NWBFile.
        """
        if self.SX is None:
            print("There are no sorted units to be added. Please run "
                  "'run_spike_sorting' to get sorted units.")
            return None
        # Tests if Units already exists
        aux = [i.name == 'Units' for i in self.nwbfile.children]
        if any(aux):
            print('Units already exists in current NWBFile.')
            return
        else:
            ids = self.SX.get_unit_ids()
            fs = self.SX.get_sampling_frequency()
            # Stores spike times for each detected cell (unit)
            for id in ids:
                spkt = self.SX.get_unit_spike_train(unit_id=id) / fs
                if 'waveforms' in self.SX.get_unit_spike_feature_names(unit_id=id):
                    if 'electrode_group' in self.SX.get_unit_property_names(unit_id=id):
                        # Stores average and std of spike traces
                        wf = self.SX.get_unit_spike_features(unit_id=id,
                                                             feature_name='waveforms')
                        relevant_ch = most_relevant_ch(wf)
                        # Spike traces on the most relevant channel
                        traces = wf[:, relevant_ch, :]
                        traces_avg = np.mean(traces, axis=0)
                        traces_std = np.std(traces, axis=0)
                        self.nwbfile.add_unit(
                            id=id,
                            spike_times=spkt,
                            waveform_mean=traces_avg,
                            waveform_sd=traces_std,
                            electrode_group=self.SX.get_unit_property(id,'electrode_group')
                        )
                    else:
                        # Stores average and std of spike traces
                        wf = self.SX.get_unit_spike_features(unit_id=id,
                                                             feature_name='waveforms')
                        relevant_ch = most_relevant_ch(wf)
                        # Spike traces on the most relevant channel
                        traces = wf[:, relevant_ch, :]
                        traces_avg = np.mean(traces, axis=0)
                        traces_std = np.std(traces, axis=0)
                        self.nwbfile.add_unit(
                            id=id,
                            spike_times=spkt,
                            waveform_mean=traces_avg,
                            waveform_sd=traces_std
                        )
                else:
                    if 'electrode_group' in self.SX.get_unit_property_names(unit_id=id):
                        self.nwbfile.add_unit(id=id, spike_times=spkt, electrode_group=self.SX.get_unit_property(id,'electrode_group'))
                    else: 
                        self.nwbfile.add_unit(id=id, spike_times=spkt)
        # Extract and add custom column data from unit properties
        descriptions = [
            {
                'name': 'cell_type',
                'description': 'name of cell type'},
            {
                'name': 'global_id',
                'description': 'global id for cell for entire experiment'},
            {
                'name': 'shank_id',
                'description': '0-indexed id of cluster of shank'},
#             {
#                'name': 'electrode_group',
#                'description': 'the electrode group that each spike unit came from'},
            {
               'name': 'max_electrode',
               'description': 'electrode that has the maximum amplitude of the waveform'
            }
        ]
        property_names = self.SX.get_unit_property_names(0)
        if 'electrode_group' in property_names:
            property_names.remove('electrode_group')
        custom_unit_columns = []
        for unit_property in property_names: # Use ID zero as base case, and assume all other IDs have those same unit properties
            custom_unit_column = []
            for id in self.SX.get_unit_ids():
                custom_unit_column.append(self.SX.get_unit_property(id,unit_property))
        
            this_description = list(filter(lambda description: description['name'] == unit_property, descriptions))
            
            if unit_property=='max_electrode':
                custom_unit_columns.append({'name': unit_property,
                                            'description': this_description[0]['description'],
                                            'data': custom_unit_column,
                                            'table': self.nwbfile.electrodes})
            else:
                custom_unit_columns.append({'name': unit_property,
                                            'description': this_description[0]['description'],
                                            'data': custom_unit_column})
        
#         if not custom_unit_columns:
        [self.nwbfile.add_unit_column(**x) for x in custom_unit_columns]
            
            

    def run_spike_sorting(self, sorter_name='herdingspikes', add_to_nwb=True,
                          output_folder='my_sorter_output', delete_output_folder=True):
        """
        Performs spike sorting, using SpikeSorters:
        https://github.com/SpikeInterface/spikesorters

        Parameters
        ----------
        sorter_name : str
        add_to_nwb : boolean
            Whether to add the sorted units results to the NWB file or not. The
            results will still be available through the extractor attribute SX.
        output_folder : str or path
            Folder that is created to store the results from the spike sorting.
        delete_output_folder : boolean
            Whether to delete or not the content created in output_folder.
        """
        self.SX = ss.run_sorter(
            sorter_name_or_class=sorter_name,
            recording=self.RX,
            output_folder=output_folder,
            delete_output_folder=delete_output_folder
        )

        st.postprocessing.get_unit_waveforms(
            recording=self.RX,
            sorting=self.SX,
            ms_before=1,
            ms_after=2,
            save_as_features=True,
            verbose=False
        )

        if add_to_nwb:
            self.add_units()


def most_relevant_ch(traces):
    """
    Calculates the most relevant channel for an Unit.
    Estimates the channel where the max-min difference of the average traces is greatest.

    traces : ndarray
        ndarray of shape (nSpikes, nChannels, nSamples)
    """
    nChannels = traces.shape[1]
    avg = np.mean(traces, axis=0)

    max_min = np.zeros(nChannels)
    for ch in range(nChannels):
        max_min[ch] = avg[ch, :].max() - avg[ch, :].min()

    relevant_ch = np.argmax(max_min)
    return relevant_ch
