#! /usr/bin/env python3

from datadog import api
from datadog import initialize


def get_api_options():
    api_key = open('api.key').read().strip()
    application_key = open('application.key').read().strip()
    return {'api_key': api_key, 'application_key': application_key}


def get_slo_ids():
    with open('slo_ids') as f:
        slo_ids = f.readlines()
    return slo_ids


def get_slo_configs(api_options, slo_ids):
    initialize(**api_options)
    slo_configs = []

    for slo_id in slo_ids:
        config = api.ServiceLevelObjective.get(slo_id)
        slo_configs.append(config)
    return slo_configs


if __name__ == '__main__':
    api_options = get_api_options()
    slo_ids = get_slo_ids()
    slo_configs = get_slo_configs(api_options, slo_ids)
    print(slo_configs)
