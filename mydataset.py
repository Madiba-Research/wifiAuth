import os

import torch
from torch_geometric.data import Dataset, download_url

class MyWifiDataset(Dataset):
    def __init__(self, root, transform=None, pre_transform=None, pre_filter=None):
        super().__init__(root, transform, pre_transform, pre_filter)

    @property
    def raw_file_names(self):
        # List of raw JSON file names in the raw directory
        return [f for f in os.listdir(self.raw_dir) if f.endswith('.json')]
    
    @property
    def processed_file_names(self):
        # Name of the file to store processed data
        return [f for f in os.listdir(self.processed_dir) if f.endswith('.pt')]

    def download(self):
        # If you need to download the raw data, implement this method.
        # Otherwise, you can leave it empty.
        pass

    def process(self):
        pass