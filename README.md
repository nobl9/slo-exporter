# slo-exporter

This script will help you convert Datadog SLO configurations to Nobl9
YAML configurations.

1. Copy a Datadog API Key into a file named `api.key`
2. Copy a Datadog Application Key into a file named `application.key`
3. Run `slo-exporter.py --datasource=your-dd-datasource --project=your-project`. This defaults output
   to STDOUT.
4. Alternately you can specify output to a file via
   `--output=file --filename=filename.yml` or simple shell redirection.
5. The output from slo-exporter.py can be input directly to the Nobl9 sloctl CLI. For example:
```shell script
./slo-exporter.py --datasource=your-dd-datasource --project=your-project > exported-datadog-slos.yaml
sloctl apply -f exported-datadog-slos.yaml
```
Or, if you want to import all of your Datadog SLOs, more simply run:   
```shell script
./slo-exporter.py --datasource=your-dd-datasource --project=your-project | sloctl apply -f -
```
Please note that sloctl's semantics are idempotent, like Kubernetes, so you can run this command repeatedly to keep the resulting Nobl9 SLOs in sync with the Datadog SLOs. (This accomplishes a one-way sync. Changes from Datadog will be synched to Nolb9. However, changes made in Nobl9 will not be synched back to Datadog.)

##Additional recommendations about the python environment

To create a python 3 virtual environment and install dependencies:
```shell script
python3 -m venv pyenv
source pyenv/bin/activate
pip install -r requirements.txt
```
