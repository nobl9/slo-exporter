# slo-exporter

This script will help you convert Datadog SLO configurations to Nobl9
YAML configurations.

If you opt to run this locally, you must install the [sloctl CLI tool.](https://docs.nobl9.com/sloctl-user-guide)

1. Update the auth.yaml and config.toml files with the required credentials.
2. Run `./slo_export.py > file.yaml` to dump the datadog SLOs into a n9 formatted yaml.
3. Run `sloctl apply -f file.yaml --config config.toml` to apply it to nobl9.

```shell script
./slo_export.py > file.yaml
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
Update the config.yaml and config.toml files with the required credentials.

Build the image

```shell script
docker build -t slo-exporter .
```

Run the build

```shell script
docker run slo-exporter
```
