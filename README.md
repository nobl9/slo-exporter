# slo-exporter

This script will help you convert Datadog SLO configurations to Nobl9
YAML configurations.


You can use the --validate flag to verify your datadog and nobl9 credentials are valid.

1. Update the auth.yaml and config.toml files with the required credentials.
2. By default the integration uses a Direct agent. If you are self-hosting the agent please update line 12 in slo.yaml accordingly.
3. Run `./export.py > file.yaml` to dump the datadog SLOs into a n9 formatted yaml.
4. Run `sloctl apply -f file.yaml --config config.toml` to apply it to nobl9.

```shell script
./export.py > file.yaml
sloctl apply -f file.yaml --config config.toml
```


Please note that sloctl's semantics are idempotent, like Kubernetes, so you can
run this command repeatedly to keep the resulting Nobl9 SLOs in sync with the
Datadog SLOs. (This accomplishes a one-way sync. Changes from Datadog will be
synched to Nolb9. However, changes made in Nobl9 will not be synched back to
Datadog.)

## Additional recommendations about the python environment

To create a python 3 virtual environment and install dependencies:

```shell script
python3 -m venv pyenv
source pyenv/bin/activate
pip install -r requirements.txt
```

## Using containerized slo-exporter
Update the auth.yaml and config.toml files with the required credentials.

Build the image

```shell script
docker build -t slo-exporter .
```

Run the build

```shell script
docker run slo-exporter
```