from logging import Logger

from lattice import Lattice
from ais import AIS


class AISLatticeIntegration:
    def __init__(
        self,
        logger: Logger,
        lattice_api: Lattice,
        ais: AIS,
    ):
        self.logger = logger
        self.lattice_api = lattice_api
        self.ais = ais

    async def publish_vessels_as_entities(self):
        """
        Asynchronously publishes vessel data as entities to the Lattice API.
        Bridges the AIS vessel data and the Lattice API

        Parameters:
            None

        Returns:
            None
        """
        for vessel_data in self.ais.get_all_data():
            entity = Lattice.generate_new_entity(vessel_data)

            self.logger.debug(
                f"MMSI={vessel_data.MMSI} VESSEL NAME={vessel_data.VesselName}\n\t{entity}"
            )

            await self.lattice_api.publish_entity(entity)
