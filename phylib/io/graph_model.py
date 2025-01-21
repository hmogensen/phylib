from pathlib import Path
import numpy as np
from h5py import File

def onebased_to_zerobased(x):
    if not np.all(x != 0):
        raise ValueError("Zero values found in input. Input must be one-based indexing.")
    return x - 1

def zerobased_to_onebased(x):
    return x + 1


class GraphModel(object):
    
    def __init__(self, dir_path):
        self.dir_path = Path(dir_path).resolve()
        assert isinstance(self.dir_path, Path)
        assert self.dir_path.exists()
        self._load_params()
        self._load_data()

    def _load_params(self):
        with File(self.dir_path / "phy_graph_params.jld2", "r") as f:
            self.params = {key: f[key][()] for key in f.keys()}
        print(f"self.params = {self.params}")

    def _load_data(self):
        self.abs_dist_mat = self._load_npy("abs_dist_mat.npy", False)
        self.rel_dist_mat = self._load_npy("rel_dist_mat.npy", False)
        self.template_amp_channels = self._load_npy("template_amp_channels.npy", True)
        self.template_units = self._load_npy("template_units.npy", True)
        self.template_batch_nr = self._load_npy("template_batch_nr.npy", True)
        self.template_amplitudes = self._load_npy("template_amplitudes.npy", False)
        self.template_clusters = self._load_npy("template_clusters.npy", True)

    def _load_npy(self, fname: str, convert_to_zerobased: bool):
        fpath = self.dir_path / Path(fname)
        x = np.load(fpath)
        if convert_to_zerobased:
            x = zerobased_to_onebased(x)
        return x
    
    def _save_npy(self, fname: str, x, convert_to_onebased: bool):
        fpath = self.dir_path / Path(fname)
        if convert_to_onebased:
            x = onebased_to_zerobased(x)
        np.save(fpath, x)
    
    