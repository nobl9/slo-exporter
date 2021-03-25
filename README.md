# slo-exporter

This script will help you convert Datadog SLO configurations to Nobl9
YAML configurations.

1. Copy a Datadog API Key into a environment variable named `DD_API_KEY`
2. Copy a Datadog Application Key into a environment variable named `DD_APPLICATION_KEY`
3. Copy a Datadog Data Source into a environment variable named `DD_DS`
4. Run `slo-exporter.py`. This defaults output to STDOUT.
5. Alternately you can specify output to a file via
   `DD_OUTPUT=file DD_FILENAME=filename.yml` or simple shell redirection.
6. You can specify a custom project via `DD_PROJECT`.
7. You can specify a project to be populated via a tag via `DD_PROJECT_TAG`.
8. The output from slo-exporter.py can be input directly to the Nobl9 sloctl
   CLI. For example:

```shell script
./slo-exporter --datasource=your-dd-datasource > exported-datadog-slos.yaml
sloctl apply -f exported-datadog-slos.yaml
```

Or, if you want to import all of your Datadog SLOs, more simply run:

```shell script
./slo-exporter --datasource=your-dd-datasource | sloctl apply -f -
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

Build the image

```shell script
docker build -t slo-exporter
```

Add environment variables manually on docker run

```shell script
docker run -e "N9_PROJECT=" -e "N9_CLIENT_ID=" -e "N9_CLIENT_SECRET=" -e "DD_API_KEY=" -e "DD_APLICATION_KEY=" -e "DD_DS=" -e "DD_DS_PROJECT=" -e "DD_PROJECT=" -e "DD_PROJECT_TAG=" -e "DD_FILENAME=" -e "DD_OUTPUT=" slo-exporter 
```

or providing env file with choosen variables

```shell script
docker run --env-file={your_env_file_name} slo-exporter 
```

## Environment variables for sloctl

For sloctl to wotk in an container set following environment variables:
N9_PROJECT
N9_CLIENT_ID
N9_CLIENT_SECRET

For specific Datasource in DataDog
DD_DS_PROJECT - DataDog Datasource Project
