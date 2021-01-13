# slo-exporter

This script will help you convert Datadog SLO configurations to Nobl9
YAML configurations.

1. Copy a Datadog API Key into a file named `api.key`
2. Copy a Datadog Application Key into a file named `application.key`
3. Run `slo-exporter.py --datasource=your-dd-datasource`. This defaults output
   to STDOUT.
4. Alternately you can specify output to a file via
   `--output=file --filename=filename.yml` or simple shell redirection.
