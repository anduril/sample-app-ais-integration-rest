from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Optional, Dict, Any

import aiohttp

from ais import VesselData

EXPIRY_OFFSET_SECONDS = 10

class Lattice:
    def __init__(self, logger: Logger, lattice_ip: str, bearer_token: str):
        self.logger = logger
        self.lattice_ip = lattice_ip if lattice_ip.startswith("https://") else f"https://{lattice_ip}"
        self.generated_metadata = {"authorization": "Bearer " + bearer_token}

    async def get_entity(self, entity_id) -> Optional[Dict[str, Any]]:
        """
        Asynchronously retrieves an entity from the Lattice API using the provided entity ID.
        Usable wrapper around the get_entity API.

        Args:
            entity_id (str): The ID of the entity to retrieve.
        Returns:
            Optional[Dict[str, Any]]: The retrieved encased, or None if an error occurred.
        Raises:
            None

        """
        try:
            async with aiohttp.ClientSession(headers=self.generated_metadata) as session:
                async with session.get(f"{self.lattice_ip}/api/v1/entities/{entity_id}") as response:
                    response.raise_for_status()
                    entity_data = await response.json()
                    return entity_data
        except Exception as error:
            self.logger.error(f"lattice api get entity error {error}")
            return None

    async def publish_entity(self, entity) -> Optional[Dict[str, Any]]:
        """
        Asynchronously publishes an entity to the Lattice API.
        Usable wrapper around the publish_entity API.
        For a cURL example of publishing an entity, please refer to https://docs.anduril.com/entity/publishing-your-first-entity

        Args:
            entity (Entity): The entity to be published.
        Returns:
            Optional[Dict[str, Any]]: The response from the Lattice API, or None if an error occurred.
        Raises:
            None
        """
        try:
            async with aiohttp.ClientSession(headers=self.generated_metadata) as session:
                async with session.put(f"{self.lattice_ip}/api/v1/entities", json=entity) as response:
                    response.raise_for_status()
                    entity_data = await response.json()
                    return entity_data
        except Exception as error:
            self.logger.error(
                f"lattice api publish entity error {error}\n\trequest={session.request}\n\tresponse={response.status}\n\t{entity}")
            return None

    @staticmethod
    def generate_new_entity(vessel_data: VesselData) -> Optional[Dict[str, Any]]:
        """
        Generates a new entity using the provided VesselData.

        For more information about these data fields, please refer to
        https://docs.anduril.com/reference/models/entitymanager/v1/entity

        Args:
            vessel_data (VesselData): The data containing relevant information about the vessel.
        Returns:
            Entity -> Dict: The generated entity with the basic attributes filled out:
                - entity_id: The vessel's MMSI.
                - description: A description of the vessel.
                - is_live: A boolean indicating whether the entity is live.
                - created_time: The time the entity was created.
                - expiry_time: The time the entity expires.
                - aliases: The aliases for the entity, including the vessel's MMSI.
                - mil_view: View of the entity.
                - location: The location of the entity, including latitude, longitude, and altitude.
                - ontology: The ontology for the entity, including the template, platform type, and specific type.
                - provenance: The provenance for the entity, including the data type, integration name, and source update time.
                - data_classification: The data classification for the entity, including the level of classification.
        """

        return {"entityId": str(vessel_data.MMSI),
            "description": "Generated by AIS Vessel Traffic Dataset",
            "isLive": True,
            "createdTime": (datetime.now(timezone.utc)).isoformat(),
            "expiryTime": (datetime.now(timezone.utc) + timedelta(seconds=EXPIRY_OFFSET_SECONDS)).isoformat(),
            "aliases": {
                "name": vessel_data.VesselName,
                "alternateIds": [
                    {
                        "id": str(vessel_data.MMSI),
                        "type": "ALT_ID_TYPE_MMSI_ID"
                    }
                ]
            },
            "milView": {
                "disposition": "DISPOSITION_NEUTRAL",
                "environment": "ENVIRONMENT_SURFACE"
            },
            "location": {
                "position": {
                    "latitudeDegrees": vessel_data.LAT,
                    "longitudeDegrees": vessel_data.LON,
                }
            },
            "ontology": {
                "template": "TEMPLATE_TRACK",
                # For more information, please refer to https://docs.anduril.com/entity/publishing-your-first-entity#assign-entity-icons
                "platformType": "Surface_Vessel",
            },
            "provenance": {
                "dataType": "vessel-data",
                "integrationName": "ais-sample-integration",
                "sourceUpdateTime": datetime.now(timezone.utc).isoformat()
            },
            "dataClassification": {
                "default": {
                    "level": "CLASSIFICATION_LEVELS_UNCLASSIFIED"
                }
            }
        }