from pathlib import Path
import numpy as np
from h5py import File

# FILENAMES
_FNAME_TEMPLATE_CLUSTERS = "template_clusters.npy"
class GraphModel(object):
    
    def __init__(self, dir_path):
        self.dir_path = Path(dir_path).resolve()
        assert isinstance(self.dir_path, Path)
        assert self.dir_path.exists()
        self._load_data()

    def _load_data(self):
        # TODO: Use filenames from sc_params.const.
        self.template_amp_channels = self._load_npy("template_amp_channels.npy")
        self.template_units = self._load_npy("template_units.npy")
        self.template_batch_nr = self._load_npy("template_batch_nr.npy")
        self.template_amplitudes = self._load_npy("template_amplitudes.npy")
        self.template_clusters = self._load_npy(_FNAME_TEMPLATE_CLUSTERS)
        self.abs_dist_sparse = self._load_npy("abs_dist_sparse.npy")
        self.rel_dist_sparse = self._load_npy("rel_dist_sparse.npy")
        self.row_dist_indx = self._load_npy("row_dist_indx.npy")
        self.col_dist_indx = self._load_npy("col_dist_indx.npy")
        self.template_channel_ranges=self._load_npy("template_channel_ranges.npy")

    def set_template_clusters(self, template_clusters):
        assert len(template_clusters) == len(self.template_clusters)
        self._save_npy(_FNAME_TEMPLATE_CLUSTERS, template_clusters)
        # Reload to allow for optimizations (e.g. caching / sparse memory management)
        self.template_clusters = self._load_npy(_FNAME_TEMPLATE_CLUSTERS)
        assert np.array_equal(self.template_clusters, template_clusters)

    def _load_npy(self, fname: str):
        fpath = self.dir_path / Path(fname)
        x = np.load(fpath)
        return x
    
    def _save_npy(self, fname: str, x,):
        fpath = self.dir_path / Path(fname)
        np.save(fpath, x)
    
    