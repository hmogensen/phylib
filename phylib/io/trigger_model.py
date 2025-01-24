from pathlib import Path
import numpy as np
from h5py import File
import os

class TriggerModel(object):

    def __init__(self, dir_path):
        self.dir_path = Path(dir_path).resolve()
        assert isinstance(self.dir_path, Path)
        assert self.dir_path.exists()
        self._load_data()

    def _load_data(self):
        fpath = self.dir_path / "phy_triggers_onebased.jld2"
        if fpath.exists():
            with File(fpath, "r") as f:
                trigger_samples = np.array(f["trigger_samples"][()]) - 1
                trigger_indx = np.array(f["trigger_indx"][()]) - 1
                trigger_names = np.array(f["trigger_names"][()])
                sample_rate = f["sample_rate"][()]
        else:
            trigger_samples = np.array([])
            trigger_indx = np.array([])
            trigger_names = np.array([])
            sample_rate = 1.
        
        assert len(trigger_samples) == len(trigger_indx)
        assert len(trigger_indx) == 0 or (np.max(trigger_indx) < len(trigger_names))
        self.trigger_samples = trigger_samples
        self.trigger_indx = trigger_indx
        self.trigger_names = trigger_names

        self.trigger_times = trigger_samples / sample_rate

    def get_triggers(self):
        """Returns a dict with trigger id -> Dict"""
        unique_trigger_indx = np.unique(self.trigger_indx)
        triggers = {}
        for i in range(len(unique_trigger_indx)):
            triggers[i] = {"name": self.trigger_names[unique_trigger_indx[i]],
                           "times": self.trigger_times[self.trigger_indx == unique_trigger_indx[i]]}
        return triggers
        
        


