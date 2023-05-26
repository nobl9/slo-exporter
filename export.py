#! /usr/bin/env python3

from datadog import initialize, api
from envyaml import EnvYAML
import sys
import argparse
import re
import logging
import subprocess

env = EnvYAML('auth.yaml')

# pull datadog credentials
DD_APP_KEY = env['datadog']['DD_APPLICATION_KEY']
DD_API_KEY = env['datadog']['DD_API_KEY']
DD_SITE = env['datadog']['DD_SITE']
try:
    DD_TAG = env['datadog']['DD_TAG']
except:
    pass

# pull nobl9 prohect seting
N9_PROJECT= env['nobl9']['N9_PROJECT']
N9_DATASOURCE= env['nobl9']['N9_DATASOURCE']
N9_DS_PROJECT=env['nobl9']['N9_DS_PROJECT']
N9_DS_KIND=env['nobl9']['N9_DS_KIND']

def get_api_options_from_env():
    return {'api_key': DD_API_KEY, 'application_key': DD_APP_KEY}

def validation_options():
    """Check if Datadog Authentication is Valid"""
    options = get_api_options_from_env()
    print("\033[1m" + "AUTH VALIDATION" + "\033[1m")
    for k in options:
        if options[k] == None:
            print(k, ": invalid or not found")
        else:
            print(k,": valid")

def get_slo_configs(options):
    """Connect to Datadog and extract and return SLO configurations."""
    initialize(**options)
    slo_configs = api.ServiceLevelObjective.get_all(limit=20000)
    if 'errors' in slo_configs.keys():
        print("\n", slo_configs)
        sys.exit(1)
    return slo_configs

def get_templates():
    """Load the YAML templates needed to render the final configs."""
    templates = {}
    try:
        templates['service'] = open('service.yaml').read()
        templates['slo'] = open('slo.yaml').read()
        templates['objective'] = open('objective.yaml').read()
        templates['timewindow'] = open('timewindow.yaml').read()
    except FileNotFoundError as e:
        logging.error(e)
        sys.exit(1)

    return templates

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
    if tag_name:
        for tag in config['tags']:
            if tag.startswith(tag_name):
                return normalize_name(tag.split(':')[1])
    return default

def extract_values(config, datasource, datasource_project, project):
    """Extract the data we care about and return as a dict."""
    config_values = {}
    for x in config:
        config_values = {}
        config_values['name'] = normalize_name(config['name'])
        config_values['displayName'] = config['name'][:63]
        config_values['description'] = escape_chars(config['description'])
        config_values['datasource'] = datasource
        config_values['datasource_project'] = datasource_project
        config_values['project'] = project
        config_values['kind'] = N9_DS_KIND
        SERVICE_NAME = extract_tag(tag_name='service',config=config,
                                default=config_values['name'])
        config_values['service_name'] = SERVICE_NAME
        config_values['thresholds'] = []

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
    constructed_yaml += templates['service'].format(**config_values)
    
    constructed_yaml += '---\n'
    constructed_yaml += templates['slo'].format(**config_values)
    constructed_yaml += '  objectives:\n'

    for threshold in config_values['thresholds']:
        threshold_values, value_counter = construct_threshold(threshold,
                                                              config_values,
                                                              value_counter)
        constructed_yaml += templates['objective'].format(**threshold_values)
    constructed_yaml += templates['timewindow'].format(**config_values)
    constructed_yaml += '---\n'

    return constructed_yaml


def convert_configs(slo_configs, templates, datasource, datasource_project, project):
    """Convert and return the Datadog SLO configurations into Nobl9 YAML."""
    nobl9_config = ''
    for config in slo_configs['data']:
        if 'query' in config.keys():
            if DD_TAG and DD_TAG in config['tags']:
                config_values = extract_values(config, N9_DATASOURCE, N9_DS_PROJECT, N9_PROJECT)
                nobl9_config += construct_yaml(config_values, templates)
            if DD_TAG is None:
                config_values = extract_values(config, N9_DATASOURCE, N9_DS_PROJECT, N9_PROJECT)
                nobl9_config += construct_yaml(config_values, templates)
    if len(nobl9_config) < 1:
        print("Please check your datadog configuration. No matching labels or SLOs were found.")
    return nobl9_config

def dedupe(contents):
    contents = contents.split('---\n')
    unique_chunks = ''
    for i in contents:
        if i not in unique_chunks:
            unique_chunks += i + '---\n'
    return unique_chunks

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true", 
                    help="Check if your credentials are valid")
    
    args, unknown_args = parser.parse_known_args()

    if args.validate:
        validation_options()
    else:
        templates = get_templates()
        slo_configs = get_slo_configs(get_api_options_from_env())

        nobl9_config = convert_configs(slo_configs, templates,
                                    N9_DATASOURCE, N9_DS_PROJECT, N9_PROJECT)
        print(dedupe(nobl9_config))
        sys.exit(0)
