#! /usr/bin/env python3

import argparse
import logging
import re
import sys

from datadog import api
from datadog import initialize


parser = argparse.ArgumentParser()
parser.add_argument('--output', type=str, default='stdout',
                    choices=['stdout', 'file'],
                    help='Choose your output desintion. One of '
                         '\'stdout\' or \'file\'')
parser.add_argument('--filename', type=str, required='--output' in sys.argv,
                    help='Filename for output. Must specify --output=file.')
parser.add_argument('--api_key', type=str, default='api.key',
                    help='Location of your datadog API key.')
parser.add_argument('--application_key', type=str, default='application.key',
                    help='Location of your datadog Application key.')
parser.add_argument('--slo_ids', type=str, default='slo_ids',
                    help='Location of your slo_ids file.')
parser.add_argument('--datasource', type=str, default='my-datadog',
                    help='Nobl9 datasource to use.')


def get_api_options(api_key, application_key):
    """Read and return the required api and application keys."""
    api_value = open(api_key).read().strip()
    application_value = open(application_key).read().strip()

    return {'api_key': api_value, 'application_key': application_value}


def get_slo_ids(slo_ids):
    """Read and return the slo_ids to be processed."""
    try:
        with open(slo_ids) as f:
            slo_ids = f.readlines()
    except FileNotFoundError as e:
        logging.error(e)
        sys.exit(1)

    return slo_ids


def get_templates():
    """Load the YAML templates needed to render the final configs."""
    templates = {}
    try:
        templates['service'] = open('service.yaml').read()
        templates['slo'] = open('slo.yaml').read()
        templates['thresholds'] = open('threshold.yaml').read()
        templates['timewindow'] = open('timewindow.yaml').read()
    except FileNotFoundError as e:
        logging.error(e)
        sys.exit(1)

    return templates


def get_slo_configs(api_options, slo_ids):
    """Connect to Datadog and to extract and return SLO configurations."""
    initialize(**api_options)
    slo_configs = []

    for slo_id in slo_ids:
        config = api.ServiceLevelObjective.get(slo_id)
        if 'errors' in config.keys():
            # The datadog api library will already log a meaningful message
            sys.exit(1)
        slo_configs.append(config)

    return slo_configs


def normalize_name(name):
    """Turn a displayname in a kubernetes-style name."""
    name = name.lower()
    name = re.sub('[^a-zA-Z0-9- ]', '', name)
    name = re.sub('\s+', '-', name)

    return name


def extract_values(config, datasource):
    """Extract the data we care about and return as a dict."""
    config_values = {}
    config_values['name'] = normalize_name(config['data']['name'])
    config_values['displayName'] = config['data']['name']
    config_values['description'] = config['data']['description']
    config_values['datasource'] = datasource
    config_values['thresholds'] = []

    num_thresholds = len(config['data']['thresholds'])
    for i in range(num_thresholds):
        target_dict = config['data']['thresholds'][i]
        target = target_dict['target']
        config_values['thresholds'].append({})
        config_values['thresholds'][i]['budgetTarget'] = target
        display_name = target_dict['target_display']
        config_values['thresholds'][i]['displayName'] = display_name
        config_values['good'] = config['data']['query']['numerator']
        config_values['total'] = config['data']['query']['denominator']
    config_values['count'] = config['data']['thresholds'][0]['timeframe'][:-1]

    return config_values


def construct_threshold(threshold, config_values):
    """Put together a dictionary for a specific threshold."""
    threshold_dict = {}
    threshold_dict['budgetTarget'] = threshold['budgetTarget']
    threshold_dict['good'] = config_values['good']
    threshold_dict['total'] = config_values ['total']
    threshold_dict['displayName'] = threshold['displayName']

    return threshold_dict


def construct_yaml(config_values, templates):
    """Construct a string of YAML from values and templates."""
    constructed_yaml = ''
    constructed_yaml += templates['service'].format(**config_values)
    constructed_yaml += '---\n'
    constructed_yaml += templates['slo'].format(**config_values)
    constructed_yaml += '  objectives:\n'

    for threshold in config_values['thresholds']:
        threshold_values = construct_threshold(threshold, config_values)
        constructed_yaml += templates['thresholds'].format(**threshold_values)
    constructed_yaml += templates['timewindow'].format(**config_values)

    return constructed_yaml


def convert_configs(slo_configs, templates, datasource):
    """Convert and return the Datadog SLO configurations into Nobl9 YAML."""
    nobl9_config = ''
    for config in slo_configs:
        config_values = extract_values(config, datasource)
        nobl9_config += construct_yaml(config_values, templates)

    return nobl9_config


def output_config(nolb9_config, output, filename):
    """Output the Nobl9 configuration to stdout or a specified filename"""
    if output == 'file':
        f = open(filename, 'w')
        f.write(nobl9_config)
    else:
        print(nobl9_config)

    return


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    args = vars(parser.parse_args())
    api_options = get_api_options(args['api_key'], args['application_key'])
    slo_ids = get_slo_ids(args['slo_ids'])
    templates = get_templates()

    slo_configs = get_slo_configs(api_options, slo_ids)
    nobl9_config = convert_configs(slo_configs, templates, args['datasource'])
    output_config(nobl9_config, args['output'], args['filename'])
    sys.exit(0)
