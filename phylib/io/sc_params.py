from pathlib import Path
import numpy as np
import tomllib
import tomli_w

from dataclasses import dataclass
from typing import Optional, Union
import numpy as np

from phylib.utils._types import Bunch, _as_list
from phylib.io.sc_params_dialog import ScParamsDialog

@dataclass
class MainParams:
    # Frame and channel parameters
    ch_start: int = 1
    ch_window_width: int = 384
    frame_window_start: int = 1
    frame_batch_size: int = 15300
    n_tot_frames: int = -1

    # Input settings parameters
    script_path: str = ""
    raw_data_file: str = ""
    phy_cluster_file: str = ""
    n_threads: int = -1
    mute: bool = False
    detect_triggers: bool = False
    output_dir: str = "output/"
    spike_width: int = 32
    rematch_spikes: bool = False

    @property
    def frame_window_end(self):
        return -1 if self.n_tot_frames == -1 else self.n_tot_frames

    @property
    def spike_padding(self):
        return self.spike_width // 2

@dataclass
class Filter:
    mvg_avg_padding: int
    hlt_n: float
    hlt_zeta: float
    hlt_frange: np.ndarray
    
@dataclass
class Detection:
    mvg_avg_padding: int
    local_std_scaling: float
    global_std_scaling: float
    min_global_std_scaling: float
    expected_spikes_per_second: float
    max_spike_width_samples: int
    max_channel_width: int
    max_channel_diff: int

@dataclass
class Trigger:
    vertical_threshold: float
    min_width: int

@dataclass
class TempGen:
    frame_batch_size: float
    min_amp_thr: float
    max_amp_thr: float
    init_dist_thr: float
    dist_thr: float
    metric_thr: float
    min_channel_span: int
    min_clust_size: int
    
@dataclass
class TempClust:
    abs_dist_thr: float
    rel_dist_thr: float
    unit_thr: int
    height_thr: float
    batch_delay_thr: int

@dataclass
class Rematch:
    abs_dist_thr: float
    rel_dist_thr: float

class ScParams(Bunch):
    def __init__(self, dir_path, *args, **kwargs):
        super(ScParams, self).__init__(*args, **kwargs)
        self.output_dir = Path(dir_path).resolve()
        self.load_params()

    def _get_fpath(self):
        return self.output_dir / "sc_params.toml"
    
    def load_params(self):
        with open(self._get_fpath(), "rb") as file:
            data = tomllib.load(file)
            
        # Handle top-level parameters first
        main_params = {}
        for k, v in data.items():
            if k not in ['filter', 'detection', 'trigger', 'tempgen', 'tempclust', 'rematch']:
                main_params[k] = v
        self.main = MainParams(**main_params)

        # Convert LinRange back to numpy array
        filter_data = data['filter']
        frange_data = filter_data['hlt_frange']
        if frange_data['_type'] == 'LinRange':
            filter_data['hlt_frange'] = np.linspace(
                frange_data['start'],
                frange_data['stop'],
                frange_data['length']
            )
        
        # Create Filter instance
        filter_obj = Filter(
            mvg_avg_padding=filter_data['mvg_avg_padding'],
            hlt_n=filter_data['hlt_n'],
            hlt_zeta=filter_data['hlt_zeta'],
            hlt_frange=filter_data['hlt_frange']
        )
        
        # Create other component instances
        detection = Detection(**data['detection'])
        trigger = Trigger(**data['trigger'])
        tempgen = TempGen(**data['tempgen'])
        tempclust = TempClust(**data['tempclust'])
        rematch = Rematch(**data['rematch'])
        
        # Create main ScParams instance
        params_dict = {k: v for k, v in data.items() 
                    if k not in ['filter', 'detection', 'trigger', 'tempgen', 'tempclust', 'rematch']}
        params_dict.update({
            'filter': filter_obj,
            'detection': detection,
            'trigger': trigger,
            'tempgen': tempgen,
            'tempclust': tempclust,
            'rematch': rematch
        })
        for key in params_dict:
            self[key] = params_dict[key]

    def save_params(self):
        with open(self._get_fpath(), 'wb') as f:
            tomli_w.dump(_params_to_dict(self), f)

    def open_dialog(self):
        updated_params, accepted = ScParamsDialog.edit_params(self)
        if accepted:
            # Use the updated parameters
            for key in updated_params:
                self[key] = updated_params[key]        


def _params_to_dict(params: ScParams) -> dict:
    params_dict = {}
    
    # Add main parameters
    for k, v in params.main.__dict__.items():
        if k not in ['frame_window_end', 'spike_padding']:  # Skip computed properties
            params_dict[k] = v
    
    # Handle the filter specially due to numpy array
    filter_dict = params.filter.__dict__.copy()
    filter_dict['hlt_frange'] = {
        '_type': 'LinRange',
        'start': float(params.filter.hlt_frange[0]),
        'stop': float(params.filter.hlt_frange[-1]),
        'length': int(len(params.filter.hlt_frange))
    }
    params_dict['filter'] = filter_dict
    
    # Convert other nested objects to dictionaries
    params_dict['detection'] = params.detection.__dict__
    params_dict['trigger'] = params.trigger.__dict__
    params_dict['tempgen'] = params.tempgen.__dict__
    params_dict['tempclust'] = params.tempclust.__dict__
    params_dict['rematch'] = params.rematch.__dict__
    
    # Convert any numpy types to Python native types for TOML compatibility
    def convert_numpy(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        return obj
    
    return convert_numpy(params_dict)