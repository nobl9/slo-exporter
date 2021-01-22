#! /usr/bin/env python3

import argparse
import json
import logging
import re
import sys

from datadog import api
from datadog import initialize


parser = argparse.ArgumentParser()
parser.add_argument('--output', type=str, default='stdout',
                    choices=['stdout', 'file', 'json'],
                    help='Choose your output desintion. One of '
                         '\'stdout\', \'file\', or \'json\'.')
parser.add_argument('--filename', type=str, required='--output' in sys.argv,
                    help='Filename for output. Must specify --output=file.')
parser.add_argument('--api_key', type=str, default='api.key',
                    help='Location of your datadog API key.')
parser.add_argument('--application_key', type=str, default='application.key',
                    help='Location of your datadog Application key.')
parser.add_argument('--datasource', type=str, default='my-datadog',
                    help='Nobl9 datasource to use.')
parser.add_argument('--namespace', type=str, default='default',
                    help='Specify a target namespace.')


def get_api_options(api_key, application_key):
    """Read and return the required api and application keys."""
    api_value = open(api_key).read().strip()
    application_value = open(application_key).read().strip()

    return {'api_key': api_value, 'application_key': application_value}


def get_templates():
    """Load the YAML templates needed to render the final configs."""
    templates = {}
    try:
        templates['service'] = open('service.yaml').read()
        templates['unique_service'] = open('unique_service.yaml').read()
        templates['slo'] = open('slo.yaml').read()
        templates['thresholds'] = open('threshold.yaml').read()
        templates['timewindow'] = open('timewindow.yaml').read()
    except FileNotFoundError as e:
        logging.error(e)
        sys.exit(1)

    return templates


def get_slo_configs(api_options):
    """Connect to Datadog and extract and return SLO configurations."""
    initialize(**api_options)
    slo_configs = api.ServiceLevelObjective.get_all(limit=5000)
    if 'errors' in slo_configs.keys():
        # The datadog api library will already log a meaningful message
        sys.exit(1)

    return slo_configs


def normalize_name(name):
    """Turn a displayname in a kubernetes-style name."""
    name = name.lower()
    name = re.sub('[^a-zA-Z0-9- ]', '', name)
    name = re.sub('\s+', '-', name)
    name = re.sub(r'(-)+', r'\1', name)
    name = name[:63]
    name = name.strip('-')

    return name


def escape_chars(description):
    """Datadog description strings might contain quotes or newlines."""
    description = re.sub('\n', ' ', description)
    description = re.sub('\"', '\\\"', description)

    return description


def extract_tag(tag_name, config, default):
    """Extract a tag if it is present in a config or fallback to a default."""
    for tag in config['tags']:
        if tag.startswith(tag_name):
            return normalize_name(tag.split(':')[1])
    return default


def extract_values(config, datasource, namespace):
    """Extract the data we care about and return as a dict."""
    config_values = {}
    config_values['unique_service'] = False
    config_values['name'] = normalize_name(config['name'])
    config_values['displayName'] = config['name'][:63]
    config_values['description'] = escape_chars(config['description'])
    config_values['datasource'] = datasource
    config_values['namespace'] = namespace
    config_values['thresholds'] = []
    config_values['service_name'] = extract_tag(tag_name='service',
                                                config=config,
                                                default=config_values['name'])
    if config_values['service_name'] != config_values['name']:
        config_values['unique_service'] = True

    num_thresholds = len(config['thresholds'])
    for i in range(num_thresholds):
        target_dict = config['thresholds'][i]
        target = target_dict['target']
        config_values['thresholds'].append({})
        config_values['thresholds'][i]['budgetTarget'] = target
        display_name = target_dict['target_display']
        config_values['thresholds'][i]['displayName'] = display_name
        config_values['good'] = config['query']['numerator']
        config_values['total'] = config['query']['denominator']
    config_values['count'] = config['thresholds'][0]['timeframe'][:-1]

    return config_values


def construct_threshold(threshold, config_values, value_counter):
    """Put together a dictionary for a specific threshold."""
    threshold_dict = {}
    threshold_dict['budgetTarget'] = float(threshold['budgetTarget'])/100
    threshold_dict['good'] = config_values['good']
    threshold_dict['total'] = config_values ['total']
    threshold_dict['displayName'] = threshold['displayName']
    threshold_dict['value_counter'] = value_counter
    value_counter += 1

    return threshold_dict, value_counter


def construct_yaml(config_values, templates):
    """Construct a string of YAML from values and templates."""
    # In case there are multiple thresholds per ratio SLO we will need
    # a unique value for each, so this variable gets passed around and
    # updated as needed.
    value_counter = 0
    constructed_yaml = ''
    if config_values['unique_service'] == False:
        constructed_yaml += templates['service'].format(**config_values)
        constructed_yaml += '---\n'
    else:
        constructed_yaml += templates['unique_service'].format(**config_values)
        constructed_yaml += '---\n'
    constructed_yaml += templates['slo'].format(**config_values)
    constructed_yaml += '  thresholds:\n'

    for threshold in config_values['thresholds']:
        threshold_values, value_counter = construct_threshold(threshold,
                                                              config_values,
                                                              value_counter)
        constructed_yaml += templates['thresholds'].format(**threshold_values)
    constructed_yaml += templates['timewindow'].format(**config_values)
    constructed_yaml += '---\n'

    return constructed_yaml


def convert_configs(slo_configs, templates, datasource, namespace):
    """Convert and return the Datadog SLO configurations into Nobl9 YAML."""
    nobl9_config = ''
    for config in slo_configs['data']:
        if 'query' in config.keys():
            config_values = extract_values(config, datasource, namespace)
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
    templates = get_templates()

    slo_configs = get_slo_configs(api_options)
    if args['output'] == 'json':
        print(json.dumps(slo_configs, indent=2))
        sys.exit(0)
    nobl9_config = convert_configs(slo_configs, templates,
                                   args['datasource'], args['namespace'])
    output_config(nobl9_config, args['output'], args['filename'])
    sys.exit(0)
