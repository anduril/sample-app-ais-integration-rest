# AIS to Lattice Integration

## Description
This is a sample application showcasing an integration between AIS vessel traffic data and Lattice.

This sample application uses json to initialize the entity.
Showcasing here is the HTTP publish_entity endpoint to publish an entity to the Lattice API.

The AIS (Automatic Identification System) vessel traffic dataset is a repository of vessel identification and positioning data. The data is collected by the U.S. Coast Guard through an onboard navigation safety device that transmits and monitors the location and characteristics of vessels in U.S. and international waters in real time. For this sample demonstration, the only 4 fields in the dataset that we are interested in are the MMSI, latitude, longitude, and vessel name.

We will use these data fields to simulate the position of a vessel at the user's current time, and publish their current location to Lattice continuously.

We retrieve the vessel data from the `var/ais_vessels.csv` file in the directory. We publish the entity json data as an HTTP request to Lattice.

## How to run locally

#### Before you begin
Ensure you have [set up your development environment](https://docs.anduril.com/get-started)

#### Clone the repository

```bash
git clone https://github.com/anduril/sample-app-ais-integration-rest.git sample-app-ais-integration-rest
cd sample-app-ais-integration-rest
```

A prerequisite to run this program is a Python version greater than or equal to 3.9

> Optional: Initialize a virtual environment
> ```bash
> python -m venv .venv
> source .venv/bin/activate
> ```

#### Install dependencies

Install the dependencies used for this project:
```bash
pip install -r requirements.txt
```

#### Run the program

Modify the configuration file in `var/config.yml`, add your Lattice IP and Lattice Bearer Token. If you would like, you can modify:
- `entity-update-rate-seconds`: to change the interval between publishing vessel entities
- `vessel-mmsi`: to change the vessels to track
- `ais-generate-interval-seconds`: to change the interval between generating vessel data

Run the following command to start the program
```bash
python src/main.py --config var/config.yml
```

#### Verify your output
Navigate to your Lattice UI and verify that the vessel entities are displayed.

Congrats! You've successfully created and published entities to Lattice!
