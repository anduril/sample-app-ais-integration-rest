from anduril import Lattice

import argparse, logging, os, time, yaml
from asyncio import run
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel, Field

from ais import AIS
from integration import AISLatticeIntegration

DATASET_PATH = "var/ais_vessels.csv"


class Config(BaseModel):
    lattice_endpoint: str = Field(alias="lattice-endpoint")
    environment_token: str = Field(alias="environment-token")
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

    # Remove the header if you are not developing on Sandboxes.
    client = Lattice(
                    base_url=f"https://{cfg.lattice_endpoint}",
                    token=cfg.environment_token, 
                    headers={ "anduril-sandbox-authorization": f"Bearer {cfg.sandboxes_token}" }
                )
    
    ais_lattice_integration_hook = AISLatticeIntegration(
        logger, client, ais_data
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
