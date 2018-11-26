# -*- coding: utf-8 -*-
"""
Grains for MOD component.
NOTE this is a little complicated - MOD can only be accessed
via salt proxy-minion. Thus, some grains make sense to get them
from the minion (PYTHONPATH), but others don't (ip_interfaces)
"""

# Import Python libs
from __future__ import absolute_import
import salt.utils
import logging

__proxyenabled__ = ['mod']
__virtualname__ = 'mod'

# Get looging started
log = logging.getLogger(__file__)


def __virtual__():
    log.info('mod_grains__virtual__called')
    try:
        if salt.utils.is_proxy() and __opts__['proxy']['proxytype'] == 'mod':
            log.debug('OK to create mod proxy')
            return __virtualname__
    except KeyError:
        log.info('mod_grains__key_error')
        pass

    log.info('NOT OK to create mod proxy')
    return False


def defaults():
    return {'os': 'proxy', 'kernel': 'unknown', 'osrelease': 'proxy'}


def os_family():
    return {'os_family': 'UNKNOWN'}


def region():
    region_name = __pillar__['node']['region']
    return {'region': region_name}


def zone():
    zone_name = __pillar__['node']['zone']
    return {'zone': zone_name}


def dc():
    dc_name = __pillar__['node']['dc']
    return {'dc': dc_name}


def env():
    env_name = __pillar__['node']['version']
    return {'env': env_name}


def role():
    role_name = __pillar__['node']['component_type']
    return {'role': role_name}


# =====================================
# Define grains by using functions from proxymodule
def proxy_functions(proxy):
    """
    The loader will execute functions with one argument and pass
    a reference to the proxymodules LazyLoader object.  However,
    grains sometimes get called before the LazyLoader object is setup
    so `proxy` might be None.
    """
    if proxy is None:
        log.warn('proxy is None')
        return {}

    if proxy['mod.initialized']() is False:
        log.warn('mod.initialized is False')
        return {}

    res = dict()

    # get MOD version info from proxymodule
    res['mod'] = proxy['mod.version']()
    log.debug('mod.version: ' + str(res['mod']))

    # Bug fixing:
    # Grains are loaded so early in startup that no dunder dictionaries
    # are present, so __proxy__, __salt__, etc. are not available.

    # get MOD mgmt IP from proxy module
    ip_dict = {'ens32': []}
    ip_dict['ens32'] = proxy['mod.mgmt_ip']()
    res['ip_interfaces'] = ip_dict
    log.debug('ip_interfaces: ' + str(res['ip_interfaces']))

    ip4_dict = {'ens32': []}
    ip4_dict['ens32'] = proxy['mod.mgmt_ip']()
    res['ip4_interfaces'] = ip4_dict
    log.debug('ip4_interfaces: ' + str(res['ip4_interfaces']))

    return res

#    return {'mod': proxy['mod.grains']()}
#   def facts(proxy=None):
#     if proxy is None or proxy['mod.initialized']() is False:
#       return {}
#     return {'mod_grains': proxy['mod.grains']()}
