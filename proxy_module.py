# -*- coding: utf-8 -*-
"""
Proxymodule for MOD devices.
Provides an Interface with MOD device via proxy-minion.

Script: //_proxy/mod.py

.. versionadded:: 2017.7.0

:maintainer:    Sergei Zaytsev <Sergei_Zaytsev@comp.com>
:maturity:      new
:depends:       cli_helper, paramiko v2.2.1 - NOT PROVIDED IN THIS EXAMPLE
:platform:      all

Define the pillars to configure the proxy-minion:

.. code-block:: yaml

  proxy:
    proxytype: mod

  Other connection parameters are defined from pillars through __pillar__ dunder:
    comp_name = __pillar__['node']['component']
    ipaddr:         __pillar__['pod']['mod'][comp_name]['mgmt']['ip']
    username:       __pillar__['pod']['mod'][comp_name]['deploy']['userName']
    password:       __pillar__['pod']['mod'][comp_name]['deploy']['consolePassword']

proxytype
    (REQUIRED) Use this proxy minion `mod`
host
    (REQUIRED) IP address or hostname to connect to
username
    (REQUIRED) username to login with
password
    (REQUIRED) console password to use to login with

.. note::
   Dependencies:
     cli_helper Python module is in the local directory

"""

# Import Python libs
from __future__ import absolute_import
from __future__ import print_function

# Import Salt libs
import salt
from salt.utils.decorators import depends

# Logging
import logging

# Import cli_helper
try:
    import cli_helper  # library

    HAS_HELPER = True
except ImportError:
    HAS_HELPER = False

# This must be present or the Salt loader won't load this module
__proxyenabled__ = ['mod']

# Variable is scoped to this module
# so we can have persistent data across calls
thisproxy = {}

# Set up logging
log = logging.getLogger(__file__)

# Define the module's virtual name
__virtualname__ = 'mod'

__version__ = "2.0.0"


# =====================================
# This does nothing, it's here just as an example and to provide a log
# entry when the module is loaded.
def __virtual__():
    """
    Mandatory function.
    Only return if all the modules are available
    """
    log.debug('mod_proxy__virtual__called')
    if not HAS_HELPER:
        log.debug('missing HAS_HELPER')
        return False, 'Missing dependency:\n The MOD proxy minion requires the \'cli_helper\' Python module.'

    return __virtualname__


# =====================================
# init(opts)
# ----------------------------------------
# Every proxy module needs an 'init',
# though we can just put thisproxy['initialized'] = True here
# if nothing else needs to be done.
@depends(HAS_HELPER)
def init(opts=None):
    """
    Mandatory function.
    Open connection to the MOD device, login, and bind to the Resource class
    The default values of the timeout attributes:
      login_timeout   = 10
      promptTimeout  = 10
      commandTimeout = 120
    """
    log.debug('init called, len(thisproxy): ' + str(len(thisproxy)))

    if 'initialized' in thisproxy and thisproxy['initialized'] is True:
        log.debug('already initialized')
        return True

    thisproxy['comp_name'] = __pillar__['node']['component']
    thisproxy['comp_pillar'] = __pillar__['pod']['mod'][thisproxy['comp_name']]
    log.info('Proxy.mod.init(): Running cli_helper.CLI for "{0}"'.format(thisproxy['comp_name']))

    thisproxy['connection_kwargs'] = {
        'ipaddr': thisproxy['comp_pillar']['mgmt']['ip'],
        'username': thisproxy['comp_pillar']['deploy']['userName'],
        'password': thisproxy['comp_pillar']['deploy']['consolePassword']
    }

    thisproxy['initialized'] = True
    return True


def create_persistent_connection():
    """
    Create a PersistentConnection object in order to exec commands

    :return:
    """
    return PersistentConnection(thisproxy)


class PersistentConnection(object):
    """

    """
    def __init__(self, proxy_cfg):
        self.proxy_cfg = proxy_cfg

    def __enter__(self):
        try:
            self.mod_connection = cli_helper.CLI(**self.proxy_cfg['connection_kwargs'])
            return self
        except Exception as e:
            log.exception('PersistentConnection create connection failed: Exception constructing cli_helper.CLI due to "{}"'.format(e))
            raise salt.exceptions.SaltException(e.msg)

    def exec_cmd(self, command, context):
        """
        Execute command on the device in a given context
        """
        try:
            return self.mod_connection.command(command, context)
        except Exception as e:
            raise e

    def __exit__(self, exc_type, exc_value, traceback):
        log.debug('closing mod_connection')
        try:
            self.mod_connection.command('', context='CLI_EXIT')
            self.mod_connection.close()
        except Exception as e:
            # log it, but ok to kepp going
            log.exception('PersistentConnection close connection failed: exception "{}"'.format(e))


# =====================================
# Check the connection status
def alive(opts=None):
    """
    Mandatory function.
    Return the connection status with the MOD device.

    .. versionadded:: 2017.7.1

    Set always_alive = False in the proxy configuration file
    to initialize the connection only when needed
    See: proxy_reconnect() function in salt/modules/status.py
    """

    # since we use on-demand connections, we don't need the minion to be restarted (shutdown, then init)
    return True


# =====================================
# Check if init() function has been called
def initialized():
    """
    Mandatory function.
    Since grains are loaded in many different places and some of those
    places occur before the proxy can be initialized, return whether
    our init() function has been called
    """
    return thisproxy.get('initialized', False)


# =====================================
# Get proxy type
def proxytype():
    """
    Returns the name of this proxy
    """
    return 'mod'


# =====================================
# Test connection
def ping():
    """
    Mandatory function.
    Ping?  Pong!
    """
    log.debug('mod proxy ping called')

    try:
        with create_persistent_connection() as conn:
            ret = conn.exec_cmd('show version', context='CLI')
            return ret and "Serial number" in ret.replace('\n', ' ')
    except Exception as e:
        # log it, but don't throw the exception
        log.exception('proxy.mod.ping: exception "{}"'.format(e))
        return False


# =====================================
# Get MOD version
def version():
    """
    Get MOD version
    This key is here because a function in '_grains/mod.py
    called version() here in the proxymodule
    """

    log.debug('mod proxy version called')
    with create_persistent_connection() as conn:
        return {'version': conn.exec_cmd('show version', context='CLI')}


# =====================================
# Get IP address of management interface
def mgmt_ip():
    """
    Get MOD management IP address
    """

    log.debug('mod proxy mgmt_ip called')
    with create_persistent_connection() as conn:
        res = conn.exec_cmd('show running-config ip-address', context='CLI')
        # expected result:
        # interface 1:0
        #  ip-address 172.27.178.85 255.255.255.0
        # !

        for line in res.splitlines():
            if "ip-address" in line:
                return line.lstrip().split(' ')[1]

        log.debug('ip-address not found, result: ' + str(res))
        return "N/A"


# =====================================
# Close MOD connection
def shutdown(opts=None):
    """
    Mandatory function.
    This is called when the proxy-minion is exiting to make sure the
    connection to the device is closed cleanly.
    """

    log.info('Proxy.mod.shutdown(): Proxy module {0} shutting down!'.format(opts['id']))

    # all connections use PersistentConnection which guarantees connection all closed on class exit
    return True
