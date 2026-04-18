# DATAQ DI-808 to InfluxDB relay

A Python app to get the live streams of voltages from the DATAQ DI-808 and push them to an InfluxDB.

## Requirements

- [`uv`](`https://docs.astral.sh/uv/getting-started/installation/`) Python project manager
- DATAQ DI-808 and the the info
    - Model # and serial #
    - URL to the device
    - Login username & password
    - Channel configuration

## Installation & setup

1. Clone this repo:

```bash
git clone https://github.com/SinclairQuantumLab/dataq-to-influxdb.git
cd dataq-to-influxdb
```

2. Clone the private `imaq_config` repo into the project root:

```bash
git clone https://github.com/SinclairQuantumLab/imaq_config.git imaq_config
```

3. Install dependencies and sync with `uv`:

```bash
uv sync
```

4. Open `main.py` and set DI-808 values:
   - `SERVER_URL`
   - `USERNAME`
   - `PASSWORD`
   - `EQUIPMENT`
   - `CHANNEL_CONFIG`

## How to run

Start the app from the project root:

```bash
./Startup_bash
```

or with `uv`:

```bash
uv run main.py
```

## Setup notes


- `main.py` contains the DI-808 connection and channel settings.
- `Startup_bash` launches the app from the project directory and activates the virtual environment.
- `dataq-to-influxdb.conf` is an optional Supervisor config sample.
