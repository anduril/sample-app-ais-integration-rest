import pandas as pd
from threading import Lock
from logging import Logger
from collections import namedtuple

VesselData = namedtuple('VesselData', ['MMSI', 'LAT', 'LON', 'VesselName'])

class AIS:
    def __init__(self, logger: Logger, csv_path: str, requested_mmsis: list[str]):
        """
        AIS class constructor

        Parameters:
            logger (Logger): The logger object to use for logging
            csv_path (str): The path to the CSV file containing the vessel traffic data.
            requested_mmsis (list[str]): A list of MMSI values for the vessels of interest.

        Attributes:
            logger (Logger): The logger object to use for logging
            requested_mmsis (list[str]): The list of MMSI values for the vessels of interest.
            cached_ais (dict[str, Optional[VesselData]]): A dictionary mapping MMSI values to cached AIS data.
            cached_ais_lock (Lock): A lock object to synchronize access to the cached AIS data.
            grouped_data (dict[str, Iterator[VesselData]]): A dictionary mapping each MMSI to an iterator over the corresponding group in the AIS data.

        """
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
        """
        Fetches the next entry from the grouped data for the given MMSI.

        Parameters:
            mmsi (str): The MMSI for which to fetch the next entry.

        Returns:
            VesselData or None: The next entry for the given MMSI, or None if there are no more entries.
        """
        try:
            return next(self.grouped_data[mmsi])
        except StopIteration:
            self.logger.info(f"MMSI {mmsi} data generation complete - no more incoming vessel data for this MMSI")
            return None

    def refresh_ais(self):
        """
        Refreshes the AIS data by fetching the next entry for each requested MMSI and updating the cached AIS data.
        
        Parameters:
            None

        Returns:
            None
        """
        with self.cached_ais_lock:
            for mmsi in self.requested_mmsis:
                next_entry = self.__fetch_next_entry(mmsi)
                if next_entry:
                    self.cached_ais[mmsi] = next_entry

    def get_all_data(self):
        with self.cached_ais_lock:
            return list(self.cached_ais.values())