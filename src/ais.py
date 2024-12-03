import pandas as pd
from threading import Lock
from logging import Logger
from collections import namedtuple

VesselData = namedtuple('VesselData', ['MMSI', 'LAT', 'LON', 'VesselName'])

class AIS:
    def __init__(self, logger: Logger, csv_path: str, requested_mmsis: list[str]):
        self.logger = logger
        self.csv_path = csv_path
        self.requested_mmsis = requested_mmsis
        self.cached_ais = {mmsi: None for mmsi in requested_mmsis}
        self.cached_ais_lock = Lock()

        self.df = pd.read_csv(self.csv_path, usecols=['MMSI', 'LAT', 'LON', 'VesselName'])
        self.grouped_data = {
            mmsi: iter(group.apply(lambda row: VesselData(row.MMSI, row.LAT, row.LON, row.VesselName), axis=1))
            for mmsi, group in self.df.groupby('MMSI')
        }

    def __fetch_next_entry(self, mmsi):
        try:
            return next(self.grouped_data[mmsi])
        except StopIteration:
            print(f"MMSI {mmsi} data generation complete - no more incoming vessel data for this MMSI")
            return None

    def refresh_ais(self):
        with self.cached_ais_lock:
            for mmsi in self.requested_mmsis:
                next_entry = self.__fetch_next_entry(mmsi)
                if next_entry:
                    self.cached_ais[mmsi] = next_entry

    def get_all_data(self):
        with self.cached_ais_lock:
            return list(self.cached_ais.values())