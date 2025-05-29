import argparse
import logging
import os
import time
from asyncio import run

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel, Field


# TODO: Remove this once we've published the Fern SDK
# For now, we:
# 1. mkdir src/modules
# 2. ln -s /path/to/external-sdks/build/fern/sdks/python/* src/modules
# 3. Add a few lines in the client.py and core/client_wrapper.py to propagate the sandboxes_token
#    See the modules in Armin's thumbnail example repo for what these should look like: 
#    https://ghe.anduril.dev/afard/lattice-thumbnail-sample-app/blob/main/modules/client.py 
from modules.client import Asyncanduril, anduril

from ais import AIS
from integration import AISLatticeIntegration

DATASET_PATH = "var/ais_vessels.csv"

class Config(BaseModel):
    lattice_ip: str = Field(alias="lattice-ip")
    lattice_bearer_token: str = Field(alias="lattice-bearer-token")
    sandboxes_token: str = Field(alias="sandboxes-token")
    entity_update_rate_seconds: int = Field(alias="entity-update-rate-seconds")
    vessel_mmsi: list[int] = Field(alias="vessel-mmsi")
    ais_generate_interval_seconds: int = Field(
        alias="ais-generate-interval-seconds"
    )


if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.info("starting ais-lattice-integration")

    parser = argparse.ArgumentParser(
        description="AIS Vessel to Lattice Mesh Integration"
    )
    parser.add_argument(
        "--config",
        action="store",
        dest="configpath",
        default="../var/config.yml",
    )
    args = parser.parse_args()

    logger.info(f"got config path {args.configpath}")

    with open(args.configpath) as config_file:
        cfg_dict = yaml.load(config_file, Loader=yaml.FullLoader)
        cfg = Config.model_validate(cfg_dict)

    # range check the ais dataset generation interval
    generate_interval = max(1, min(cfg.ais_generate_interval_seconds, 60))

    ais_data = AIS(logger, DATASET_PATH, cfg.vessel_mmsi)

    lattice_api = anduril(
        base_url=cfg.lattice_ip, 
        token=cfg.lattice_bearer_token, 
        sandboxes_token=cfg.sandboxes_token,
        )

    ais_lattice_integration_hook = AISLatticeIntegration(
        logger, lattice_api, ais_data
    )

    # Running the fetch job in the background, spin up a second job to periodically publish entities.
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        ais_data.refresh_ais, "interval", seconds=generate_interval
    )
    scheduler.add_job(
        lambda: run(
            ais_lattice_integration_hook.publish_vessels_as_entities()
        ),
        "interval",
        seconds=cfg.entity_update_rate_seconds,
    )
    scheduler.start()

    logger.info(
        "Press Ctrl+{0} to exit".format("Break" if os.name == "nt" else "C")
    )
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        logger.info("shutting down ais-lattice-integration")
        scheduler.shutdown()
