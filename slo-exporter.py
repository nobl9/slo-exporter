#! /usr/bin/env python3

import json
import yaml

from datadog import api
from datadog import initialize


def get_api_options():
    """Read and return the required api and application keys."""
    api_key = open('api.key').read().strip()
    application_key = open('application.key').read().strip()
    return {'api_key': api_key, 'application_key': application_key}


def get_slo_ids():
    """Read and return the slo_ids to be processed."""
    with open('slo_ids') as f:
        slo_ids = f.readlines()
    return slo_ids


def get_slo_configs(api_options, slo_ids):
    """Connect to Datadog and to extract and return SLO configurations."""
    initialize(**api_options)
    slo_configs = []

    for slo_id in slo_ids:
        config = api.ServiceLevelObjective.get(slo_id)
        slo_configs.append(config)
    return slo_configs


def extract_values(config):
    """Extract the data we care about and return as a dict."""
    config_values = {}
    config_values['name'] = config['data']['name'].lower()
    config_values['displayName'] = config['data']['name']
    config_values['description'] = config['data']['description']
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


def construct_yaml(config_values):
    """Construct a string of YAML from values and templates."""
    constructed_yaml = ''
    service_template = open('service.yaml').read()
    slo_template = open('slo.yaml').read()
    threshold_template = open('threshold.yaml').read()
    timewindow_template = open('timewindow.yaml').read()

    constructed_yaml += service_template.format(**config_values)
    constructed_yaml += '---\n'
    constructed_yaml += slo_template.format(**config_values)
    constructed_yaml += '    thresholds:\n'
    for threshold in config_values['thresholds']:
        threshold_values = construct_threshold(threshold, config_values)
        constructed_yaml += threshold_template.format(**threshold_values)
    constructed_yaml += timewindow_template.format(**config_values)

    return constructed_yaml


def convert_configs(slo_configs):
    """Convert and return the Datadog SLO configurations into Nobl9 YAML."""
    for config in slo_configs:
        config_values = extract_values(config)
        constructed_yaml = construct_yaml(config_values)
        print(constructed_yaml)


if __name__ == '__main__':
    api_options = get_api_options()
    slo_ids = get_slo_ids()
    slo_configs = get_slo_configs(api_options, slo_ids)
    yaml_config = convert_configs(slo_configs)
