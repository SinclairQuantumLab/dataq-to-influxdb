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

1. `git clone` this repo to `~/Projects/`:
  
    ```bash
    cd ~/Projects/
    git clone --recurse-submodules https://github.com/SinclairQuantumLab/dataq-to-influxdb.git 
    ```

    > **NOTE**: the `--recurse-submodules` option clones [`imaq-secret`](https://github.com/SinclairQuantumLab/imaq-secret.git) repo for the credential to access to our InfluxDB together at the right location in this repo.

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
