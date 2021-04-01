# slo-exporter

This script will help you convert Datadog SLO configurations to Nobl9
YAML configurations.

Keep in mind that environment variables have priority over flags.

There are additional optional flag options discoverable via `--help`.

1. Copy a Datadog API Key into a file named `api.key` or into a environment variable named `DD_API_KEY`
2. Copy a Datadog Application Key into a file named `application.key` or into a environment variable named `DD_APPLICATION_KEY`
3. Run `slo-exporter.py --datasource=your-dd-datasource` or set environment variable named `N9_DATASOURCE`. This defaults output
   to STDOUT and datasource project to default.
4. Alternately you can specify output to a file via
   `--output=file --filename=filename.yml` or setting `DD_OUTPUT` and `DD_FILENAME` (simple shell redirectionalso works).
5. You can specify a custom project via `--project` or `N9_PROJECT`.
6. You can specify a project to be populated via a tag via `--project_tag` or `N9_PROJECT_TAG`.
7. The output from `slo-exporter.py` can be input directly to the Nobl9 sloctl
   CLI. For example:

```shell script
./slo-exporter.py --datasource=your-dd-datasource \
--datasource_project=your-dd-datasource-project \
--project=your-dd-project > exported-datadog-slos.yaml

sloctl apply -f exported-datadog-slos.yaml
```

Or, if you want to import all of your Datadog SLOs, more simply with `default` projects run:

```shell script
./slo-exporter.py --datasource=your-dd-datasource | sloctl apply -f -
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
docker run \
-e "N9_PROJECT=" \
-e "N9_CLIENT_ID=" \
-e "N9_CLIENT_SECRET=" \
-e "DD_API_KEY=" \
-e "DD_APLICATION_KEY=" \
-e "N9_DATASOURCE=" \
slo-exporter 
```

or providing env file with choosen variables

```shell script
docker run --env-file={your_env_file_name} slo-exporter 
```

## Environment variables

For sloctl to work in a container set following environment variables:

`N9_PROJECT`

`N9_CLIENT_ID`

`N9_CLIENT_SECRET`

### Full list of environment variables to may set for the exporter

`DD_API_KEY` - API Key for your DataDog service

`DD_APPLICATION_KEY` - Application Key for your Datadog service

`DD_FILENAME` - You may specify the filename to which SLO form Datadog will be exported

`DD_OUTPUT` - You may choose the output type of the export like stdout (default), yaml or json.

`N9_DATASOURCE`- DataDog Datasource in your Nobl9

`N9_DATASOURCE_PROJECT` - DataDog Datasource Project in your Nobl9

`N9_PROJECT` - Project in Nobl9

`N9_PROJECT_TAG` - Project tag in Nobl9
