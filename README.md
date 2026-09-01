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

4. Copy the settings template and edit the local settings:

    ```bash
    cp settings.toml.template settings.toml
    ```

   Set the DATAQ equipment, server, and channel map in `settings.toml`.
   Channels omitted from `[dataq.channels]` are not uploaded. DATAQ credentials
   are read from `[dataq]` in the private `imaq-secret/auth.toml` file.
   Root settings control the exception threshold and reconnection delays.
   The local `settings.toml` file is ignored by Git.

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


- `settings.toml` contains the DI-808 connection, channel, exception threshold,
  and reconnection settings.
- `Startup_bash` launches the app from the project directory and activates the virtual environment.
- `dataq-to-influxdb.conf` is an optional Supervisor config sample.
