#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tool to export SLO configurations from Datadog

This command-line tool accepts basic Datadog authentication information and uses
it to export all service level objectives (SLOs) configuration that token has
acccess to. It then translates these configurations into the Nobl9 YAML format,
and displays this on stdout.
"""

import logging
import os
import re
import sys
import yaml

from datadog_api_client import ApiClient
from datadog_api_client import Configuration
from datadog_api_client.exceptions import ApiException
from datadog_api_client.v1.api.service_level_objectives_api import (
        ServiceLevelObjectivesApi
        )

__author__ = 'Nobl9, Inc.'
__version__ = '0.1.0'
__status__ = 'Development'


def get_templates():
    """Load template files required for configuring Nobl9 YAML.

    Arguments:
        None

    Returns:
        templates (dict): A dictionary containing Nobl9 YAML templates.
    """
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


def get_config(env_values=False, filename='config.yaml'):
    """Load program configuration from the environment or a configuration file.

    Arguments:
        env_values (bool): Set to true in order to use environment variables.
        filename (string): The location of the file containing program
            configuration.

    Returns:
        config (dict): A dictionary containing program configuration.
    """
    config = {}
    required_conf = ['DD_API_KEY', 'DD_APP_KEY', 'DD_SITE', 'N9_PROJECT',
                     'N9_DS', 'N9_DS_PROJECT', 'N9_DS_KIND']
    if env_values:
        for item in required_conf:
            try:
                config[item] = os.environ[item]
            except KeyError:
                logging.error('Env variable {} not found.'.format(item))
                sys.exit(1)
    else:
        config_yaml = yaml.safe_load(open(filename, 'r'))
        for item in required_conf:
            try:
                config[item] = config_yaml[item]
            except KeyError:
                logging.error('Config value {} not found.'.format(item))
                sys.exit(1)
    return config


def get_slo_configs(config):
    """Connect to Datadog using our configuration and retrieve all SLO configs.

    Arguments:
        config (dict): A dictionary containing all required program
            configuration options.

    Returns:
        slo_configs (dict): A dictionary containing all retrieved SLO configs.
    """
    api_config = Configuration()
    api_config.api_key['apiKeyAuth'] = config['DD_API_KEY']
    api_config.api_key['appKeyAuth'] = config['DD_APP_KEY']
    api_config.server_variables['site'] = config['DD_SITE']
    try:
        with ApiClient(api_config) as api_client:
            api_instance = ServiceLevelObjectivesApi(api_client)
            response = api_instance.list_slos()
        slo_configs = response.to_dict()
    except ApiException as e:
        logging.error(e)
        sys.exit(1)
    return slo_configs


def normalize_name(name):
    """Turn a displayname in a kubernetes-stylei/RFC 1123-compliant name."""
    name = name.lower()
    name = re.sub('[^a-zA-Z0-9- ]', '', name)
    name = re.sub('\\s+', '-', name)
    name = re.sub(r'(-)+', r'\1', name)
    name = name[:63]
    name = name.strip('-')
    return name


def escape_chars(description):
    """Datadog description strings might contain quotes or newlines."""
    description = re.sub('\n', ' ', description)
    description = re.sub('\"', '\\\"', description)
    return description


def extract_values(slo, config):
    """Construct a dictionary containing relevant values from a single DD SLO.

    For a better understanding of the complexity of the values being extracted,
    please see the definition of the SLOResponse class in datadog_api_client.v1.

    Arguments:
        slos (dict): A dictonary containing an entire DD SLO config and
            metadata.
        config (dict): Additional configuration specifying Nobl9-specific
            values.

    Returns:
        slos_values (dict): A dictionary with values ready to populate Nobl9
            YAML templates.
    """
    slo_values = {}
    slo_values['name'] = normalize_name(slo['name'])
    slo_values['displayName'] = slo['name'][:63]
    slo_values['description'] = escape_chars(slo['description'])
    slo_values['datasource'] = config['N9_DS']
    slo_values['datasource_project'] = config['N9_DS_PROJECT']
    slo_values['kind'] = config['N9_DS_KIND']
    slo_values['project'] = config['N9_PROJECT']
    slo_values['service_name'] = slo_values['name']
    slo_values['good'] = slo['query']['numerator']
    slo_values['total'] = slo['query']['denominator']
    slo_values['thresholds'] = []

    num_thresholds = len(slo['thresholds'])
    for threshold in range(num_thresholds):
        target = slo['thresholds'][threshold]['target']
        slo_values['thresholds'].append({})
        slo_values['thresholds'][threshold]['budgetTarget'] = target
        display_name = slo['thresholds'][threshold]['target_display']
        slo_values['thresholds'][threshold]['displayName'] = display_name
    slo_values['count'] = slo['thresholds'][0]['timeframe'][:-1]
    return slo_values


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


def construct_yaml(slo_values, templates):
    """Construct a string of YAML from values and templates.

    Arguments:
        slo_values (dict): A dictionary containing the extracted DD configs.
        templates (dict): All Nobl9 YAML templates in dictionary form.

    Returns:
        constructed_yaml (str): Nobl9 compliant YAML for a single SLO.
    """
    # In case there are multiple thresholds per ratio SLO we will need
    # a unique value for each, so this variable gets passed around and
    # updated as needed.
    value_counter = 0
    constructed_yaml = ''
    constructed_yaml += templates['service'].format(**slo_values)
    constructed_yaml += '---\n'
    constructed_yaml += templates['slo'].format(**slo_values)
    constructed_yaml += '  objectives:\n'
    for threshold in slo_values['thresholds']:
        threshold_values, value_counter = construct_threshold(threshold,
                                                              slo_values,
                                                              value_counter)
        constructed_yaml += templates['objective'].format(**threshold_values)
    constructed_yaml += templates['timewindow'].format(**slo_values)
    constructed_yaml += '---\n'
    return constructed_yaml


def convert_configs(templates, config, slo_configs):
    """Take SLO configs exported from DD and export into Nobl9 YAML.

    Arguments:
        templates (dict): All N9 YAML templates in dictionary form.
        config (dict): Dictionary containing all program configuration.
        slo_configs (list): Exported DD SLO configuration details.

    Returns:
        nobl9_config (str): Nobl9 YAML as a string ready to be written to a
            file and applied via sloctl.
    """
    nobl9_config = ''
    for slo in slo_configs['data']:
        if 'query' in slo.keys():
            slo_values = extract_values(slo, config)
            nobl9_config += construct_yaml(slo_values, templates)
    if len(nobl9_config) < 1:
        logging.error('No valid SLO data found in response from Datadog.')
        sys.exit(1)
    return nobl9_config


if __name__ == '__main__':
    """Tool to export SLO configurations from Datadog."""

    templates = get_templates()
    config = get_config()
    slo_configs = get_slo_configs(config)
    nobl9_config = convert_configs(templates, config, slo_configs)
    print(nobl9_config)
