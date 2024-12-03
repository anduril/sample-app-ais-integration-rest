import argparse
import logging
import os
import time
from asyncio import run
from datetime import timedelta

import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from integration import AISLatticeIntegration
from lattice import Lattice
from ais import AIS

DATASET_PATH = "var/ais_vessels.csv"

def validate_config(cfg):
    if "lattice-ip" not in cfg:
        raise ValueError("missing lattice-ip")
    if "lattice-bearer-token" not in cfg:
        raise ValueError("missing lattice-bearer-token")
    if "entity-update-rate-seconds" not in cfg:
        raise ValueError("missing entity-update-rate-seconds")
    if "vessel-mmsi" not in cfg:
        raise ValueError("missing vessel-mmsi")
    if "ais-generate-interval-seconds" not in cfg:
        raise ValueError("missing ais-generate-interval-seconds")


if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.info("starting ais-lattice-integration")

    parser = argparse.ArgumentParser(description="AIS Vessel to Lattice Mesh Integration")
    parser.add_argument(
        "--config", action="store", dest="configpath", default="../var/config.yml"
    )
    args = parser.parse_args()

    logger.info(f"got config path {args.configpath}")

    with open(args.configpath) as config_file:
        cfg = yaml.load(config_file, Loader=yaml.FullLoader)
        logger.debug(f"provided config {cfg}")
        validate_config(cfg)

    # range check the ais dataset generation interval
    generate_interval = max(1, min(cfg["ais-generate-interval-seconds"], 60))

    ais_data = AIS(
        logger,
        DATASET_PATH,
        cfg["vessel-mmsi"]
    )

    lattice_api = Lattice(logger, cfg["lattice-ip"], cfg["lattice-bearer-token"])

    ais_lattice_integration_hook = AISLatticeIntegration(
        logger, lattice_api, ais_data
    )

    # Running the fetch job in the background, spin up a second job to periodically publish entities.
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        ais_data.refresh_ais, "interval", seconds=generate_interval
    )
    scheduler.add_job(
        lambda: run(ais_lattice_integration_hook.publish_vessels_as_entities()),
        "interval",
        seconds=cfg["entity-update-rate-seconds"],
    )
    scheduler.start()

    logger.info("Press Ctrl+{0} to exit".format("Break" if os.name == "nt" else "C"))
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        logger.info("shutting down ais-lattice-integration")
        scheduler.shutdown()
