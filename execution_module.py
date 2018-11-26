# -*- coding: utf-8 -*-
"""
MOD execution module.
Provides Proxy Minion interface for managing MOD devices.

Script: //_modules/mod.py

.. versionadded:: 2016.11.6

:maturity:      new
:depends:       json, re
:platform:      all

This proxy minion enables a consistent interface to fetch, control and maintain
the configuration of MOD devices.

More in-depth conceptual reading on Proxy Minions can be found in the
Proxy Minion section of Salt's documentation.
"""

# Import Python Libs
from __future__ import absolute_import
import logging
import json
import re
import time
import subprocess

# Import Salt Libs
from salt.exceptions import SaltSystemExit

# import http_session class from mod-rest-helper.py, for making REST calls to mod devices
import sys
import os

# relative include of _utils directory- to find rest_helper
sys.path.append(os.path.dirname(__file__))
import rest_helper

# This must be present or the Salt loader won't load this module.
__proxyenabled__ = ['mod']

# Logging
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'mod'


def __virtual__():
    """
    We need a proxymodule entry in __opts__ in the opts dictionary
    """
    log.debug('mod_module__virtual__called')

    if 'proxy' in __opts__:
        log.debug('ok to create mod module')
        return __virtualname__
    else:
        msg = 'The MOD module could not be loaded: "proxy" is not defined in pillars.'
        log.debug(msg)
        return False, msg


# ========================================================
# Check the connection to the host
def ping():
    """
    To check the connection with the device

    Usage:

    .. code-block:: bash

        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.ping

    """
    log.debug('mod.ping called')
    ret = dict()

    try:
        comp_name = __pillar__['node']['component']
        with __proxy__['mod.create_persistent_connection']() as mod_connection:
            ret['message'] = mod_connection.exec_cmd('ping repeat 1 ' + __pillar__['pod']['mod'][comp_name]['mgmt']['ip'], context='ENABLE')
        log.debug('ping result: ' + str(ret['message']))

        comp_str = '108 bytes from ' + __pillar__['pod']['mod'][comp_name]['mgmt']['ip'] + ':'

        if comp_str in ret['message']:
            ret['out'] = True
            log.debug('good ping result found')
        else:
            ret['out'] = False
            log.debug('good ping result not found')
    except Exception as exception:
        ret['message'] = '*** modules.mod.ping(): execution failed due to "{0}"'.format(exception)
        log.warn(ret['message'])

    return ret


# ========================================================
# Restart the MOD
def restart(sleep_time=40):
    """
    To restart the device

    Usage:

    .. code-block:: bash

        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.restart

    """
    log.debug('mod.restart called')
    ret = dict()
    ret['out'] = False
    ret['result'] = False

    try:
        with __proxy__['mod.create_persistent_connection']() as mod_connection:
            ret['message'] = mod_connection.exec_cmd('restart', context='ENABLE')
        log.debug('mod.restart result: ' + str(ret['message']))
        ret['out'] = True
        ret['result'] = True
        log.debug('sleeping for {} seconds'.format(sleep_time))
        time.sleep(sleep_time)
    except Exception as exception:
        ret['message'] = '*** modules.mod.restart(): execution failed due to "{0}"'.format(exception)

    return ret


# =====================================
# Run MOD CLI "show config" command
def get(show_command):
    """
    Executes the CLI "show config" command and returns the text output

    Usage:

    .. code-block:: bash

        sudo salt 'mod_zone1.us-central1.amazonaws.com' mod.get 'alerts'
        sudo salt 'mod_zone1.us-central1.amazonaws.com' mod.get 'snmp'
        sudo salt 'mod_zone1.us-central1.amazonaws.com' mod.get 'services vendor active'
        sudo salt 'mod_zone1.us-central1.amazonaws.com' mod.get 'licences'

    .. note::
      * The show command is executed in ENABLE context

    """
    log.debug('mod.get called, show_command: ' + str(show_command))

    ret = dict()

    cmd_prefix = "show "
    if show_command != "licenses":
        cmd_prefix = cmd_prefix + "config "

    log.debug('cmd_prefix: ' + str(cmd_prefix))

    try:
        cmd = cmd_prefix + show_command
        log.debug('modules.mod.get(): Command: {0}'.format(cmd))
        # The output if license is not installed:
        # %  failed
        # %  ErrorCode : -14203
        # %  ErrorMessage : license is not installed
        with __proxy__['mod.create_persistent_connection']() as mod_connection:
            ret['message'] = mod_connection.exec_cmd(cmd, context='ENABLE')
        if show_command == "licenses":
            if "failed" in ret['message'].split('\n')[0]:
                error_msg = ret['message'].split('\n')[2].split(':')[1]
                ret['message'] = error_msg
                log.debug('licenses cmd failed: ' + str(ret['message']))
                ret['out'] = False
            else:
                ret['out'] = True
                log.debug('licenses cmd succeeded')
        else:
            if "-----" in ret['message'].split('\n')[0]:
                error_msg = ret['message'].split('\n')[1]
                ret['message'] = error_msg
                log.debug('cmd failed: ' + str(ret['message']))
                ret['out'] = False
            else:
                ret['out'] = True
                log.debug('cmd succeeded')
    except Exception as exception:
        ret['message'] = '*** modules.mod.get(): execution failed due to "{0}"'.format(exception)
        ret['out'] = False
        # log.debug('*** modules.mod.get(): Return: {0}'.format(ret['message']))

    return ret


# =====================================
# Run MOD CLI configuration command
def set(config_command, check=""):
    """
    Executes the CLI configuration command

    Usage:

    .. code-block:: bash

        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.set 'alerts destinations snmp [ ]'
        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.set 'services clam active true'
        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.set 'ntp update-now'

    Options:
      * config_command: The command that need to be executed in MOD CLI

    .. note::
        The configuration command is executed in CLI_CONFIG context

    """
    log.debug('mod.set called config_command: {}; check: {}'.format(config_command, check))
    ret = dict()

    try:
        with __proxy__['mod.create_persistent_connection']() as mod_connection:
            res = mod_connection.exec_cmd(config_command, context='CLI_CONFIG')
            log.debug('mod.set result: ' + str(res))
            if check != "" and not check.lower() in res.lower():
                ret['message'] = "'{}' resulted in '{}' and did not match check: '{}'".format(config_command, res, check)
                log.debug('mismatch: ' + str(ret['message']))
                ret['out'] = False
            else:
                log.debug('mod.set success')
                ret['message'] = res
                ret['out'] = True
    except Exception as exception:
        ret['message'] = '*** modules.mod.set(): execution failed due to "{0}"'.format(exception)
        log.debug('mod.set error: ' + str(ret['message']))
        ret['out'] = False

    return ret


# ========================================================
# Set the name of the device
def set_hostname(hostname=None):
    """
    Set the name of the MOD device

    Usage:

    .. code-block:: bash

        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.set_hostname hostname='mod1_zone1.us-central1.amazonaws.com'

    Options:
      * hostname: The name to be set.
      * verify_change: Whether the host name has changed.(default=True)
    """
    log.debug('mod.set_hostname called; hostname: ' + str(hostname))
    ret = dict()

    if hostname is None:
        log.debug('hostname cannot be None')
        ret['message'] = "Please, use a host name as parameter"
        ret['out'] = False
        return ret

    set_command = 'appliance-name {0}'.format(hostname)
    log.debug('set_command: ' + str(set_command))

    try:
        with __proxy__['mod.create_persistent_connection']() as mod_connection:
            response = mod_connection.exec_cmd(set_command, context='CLI_CONFIG')
            log.debug('response: ' + str(response))
            ret['message'] = response
            ret['out'] = True
    except Exception as exception:
        ret['message'] = '*** modules.mod.set_hostname(): execution failed due to "{0}"'.format(exception)
        log.debug(str(ret['message']))
        ret['out'] = False

    return ret


# ========================================================
# Execute commands from .json file
def exec_commands_from_file(json_fname):
    """
    Execute commands from .json file

    Usage:

    .. code-block:: bash

       sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.exec_commands_from_file '/tmp/mod/mod-dpdev_load-licenses.json'
       sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.exec_commands_from_file '/tmp/mod/mod-dpdev_add-mod.json'
       sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.exec_commands_from_file '/tmp/mod/mod-dpdev_mod_config.json'

    """
    log.debug('mod.exec_commands_from_file called json_fname: {}'.format(json_fname))
    ret = dict()
    error_nums = 0

    # Open config.json file:
    # {"Comment": "This configuration should match <URL>DOC-123456",
    #   "config": {
    #     "CLI_CONFIG":[
    #       {"cmd":"syslog [ UPDATE_OK UPDATE_ERROR REBOOT ]","chk":""},
    #       . . .
    # Bug fixing:
    # with open(json_fname, "r") as in_file, __proxy__['mod.create_persistent_connection']() as mod_connection:
    #   SyntaxError: invalid syntax
    # Reason: we load the module on Node which works on Python 2.6 only
    #         but Python 2.6 does not support multiple context expressions
    # Workaround: use nested statements

    with open(json_fname, "r") as in_file:
        with __proxy__['mod.create_persistent_connection']() as mod_connection:
            conf = json.load(in_file)
            # find the context in the "config" key
            for context in conf['config']:
                # loop for the list of commands (records) in the contex
                for record in conf['config'][context]:
                    # Get "chk:" value
                    check = str(record['chk'])
                    log.debug('chk value: ' + str(check))
                    try:
                        # execute the command in a given context
                        log.debug('exec_cmd: ' + str(record['cmd']))
                        res = mod_connection.exec_cmd(record['cmd'], context=context)
                        log.debug('cmd result: ' + str(res))
                        # check
                        if check != "" and not check.lower() in res.lower():
                            log.error("'{}' resulted in '{}' and did not match check: '{}'".format(record['cmd'], res, check))
                            error_nums += 1
                    except Exception as exception:
                        log.error('{0}'.format(exception))
                        ret['message'] = '*** modules.mod.exec_commands_from_file(): execution failed due to "{0}"'.format(exception)
                        # log.debug(str(ret['message']))
                        ret['out'] = False
                        break

    log.debug('error_nums: ' + str(error_nums))
    if error_nums == 0:
        ret['message'] = "Success"
        ret['out'] = True
    else:
        ret['message'] = "Error in check of the results. Please, read the log file."
        ret['out'] = False

    log.debug('return msg: ' + str(ret['message']))
    return ret

# =========================================================
#                    L I C E N S E S
# =========================================================

# =========================================================
# Check if licenses was already loaded via REST call
def check_licenses(host='127.0.0.1',username='super',password='12345'):
    """
    Check if licenses was already loaded

    Usage:

    .. code-block:: bash

       sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.check_licenses

    """
    log.debug('mod.check_licenses called')
    ret = dict()
    err = ""
    
    #check via REST call, instead of ConfD/SSH, APDS-509
    #theory being that issuing the command "show licenses" is causing stability problems with ConfD and back-end services
    #res = get_license_dates()
    cmd = "/opt/mod-utils/mod-licensing-rest.py -u {0} -p {1} -i {2} -a check".format(username, password, host)
    #cmd contains passwords
    #log.debug('subprocess: "{}"'.format(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (res, err) = proc.communicate()
    
    log.debug('result: ' + str(res))
    #if res['message']:
    if "\"valid\": true" in res:
        #if "license is not installed" not in res['message']:
        if "\"valid\": true" in res:
            ret['message'] = "Licenses already loaded"
            ret['out'] = True
        else:
            ret['message'] = "License is not installed"
            ret['out'] = False
    else:
        log.debug('message not present')
        ret['message'] = "Licenses was not loaded"
        ret['out'] = True

    log.debug('result: ' + str(ret['message']))
    return ret


# =========================================================
# Verify, load licenses, and verify again
def load_licenses(json_fname,host='127.0.0.1',username='admin',password='admin'):
    """
    Load licenses with pre and post verification

    Usage:

    .. code-block:: bash

       sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.load_licenses '/tmp/mod/mod-dpdev_load-licenses.json'

    """
    log.debug('mod.load_licenses json_fname: {}'.format(json_fname))
    ret = dict()

    ret['message'] = ""
    ret['out'] = False

    # check if licenses has been already loaded
    res = check_licenses(host,username,password)
    log.debug('result: ' + str(res))

    #if 'not loaded' in res['message'] or 'not installed' in res['message']:
    if 'True' not in res:
        log.debug('license not loaded or not installed')
        # Loop - trying to load the licenses
        for iter in range(3):
            # load license
            log.debug('running cmds: ' + str(json_fname))
            res = exec_commands_from_file(json_fname)
            if res['out'] is True:
                # check if licenses just loaded
                res = check_licenses(host,username,password)
                log.debug('result: ' + str(res))
                if 'True' in res:
                #if 'already loaded' in res['message']:
                    ret['message'] = "Licenses loaded successfully"
                    ret['out'] = True
                    break
            else:
                ret['message'] = ret['message'] + "\n" + "Iter:{}".format(iter) + " ==> " + res['message']
                log.debug("{}".format(ret['message']))
                # end for
    else:
        log.debug('licenses are loaded and installed')
        ret['message'] = res['message']
        ret['out'] = True

    return ret


# =========================================================
#                       M O D
# =========================================================

# =========================================================
# Check if MOD already added
def check_mod():
    """
    Check if MOD already added

    Usage:

    .. code-block:: bash

      sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.check_mod

    """
    log.debug('mod.check_mod called')
    ret = dict()

    check_command = "check mod"

    res = get(check_command)
    log.debug('result: ' + str(res))

    if "No entries found" in res['message']:
        ret['message'] = "MOD was not added"
    else:
        ret['message'] = "MOD already added"
    ret['out'] = True

    return ret


# =========================================================
# Verify, add MOD, and verify again
def add_mod(json_fname):
    """
    Add MOD with pre and post verification

    Usage:

    .. code-block:: bash

       sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.add_ma '/tmp/mod/mod-dpdev_add-mod.json'

    """
    log.debug('mod.add_mod json_fname: {}'.format(json_fname))
    ret = dict()

    ret['message'] = ""
    ret['out'] = False

    # check if MOD has been already added
    res = check_mod()
    if 'not added' in res['message']:
        # Loop - trying to add MOD
        for iter in range(3):
            # load MOD
            log.debug('running cmds: ' + str(json_fname))
            res = exec_commands_from_file(json_fname)
            if res['out'] is True:
                # check if MOD just added
                res = check_ma()
                if 'already added' in res['message']:
                    ret['message'] = "MOD added successfully"
                    ret['out'] = True
                    break
            else:
                ret['message'] = ret['message'] + "\n" + "Iter:{}".format(iter) + " ==> " + res['message']
                # end for iter
    else:
        ret['message'] = res['message']
        ret['out'] = True

    return ret


# =========================================================
#            C O N F I G   C O M M A N D S
# =========================================================

# =====================================
# Extract mod commands and values from .json file
def _get_commands_and_values(json_fname, cmd_types):
    """
    Private function to get "key:value" pairs of the mod commands from JSON file
      key:   full command or part of the command which will be used for verification
      value: passed value which is an expected verified value

    Input:
      * json_fname - full path to the .json file with mod commands
      * cmd_types  - list of verified command types
    Output:
      * dictionary (key:value) of mod commands and expected results

    """
    log.debug('mod._get_commands_and_values called json_fname: {}; cmd_types: {}'.format(json_fname, cmd_types))
    cmd_dict = {}

    pass

    return cmd_dict

# =====================================
# Verify the results of the extracted mod commands
def _verify_commands(**cmd_dict):
    """
    Private function to verify the results of the extracted mod commands
    Input:
      * cmd_dict - (key:value) of mod ConfD commands and expected results
    Output:
      * Result of the verification
        ret[cmd]['old']
        ret[cmd]['new']
        or
        empty dictionary if no changes needed
    """
    ret = dict()
    ret['old'] = {}
    ret['new'] = {}

    log.debug("*** modules.mod _verify_commands():Commands and Values: \n{}".format(cmd_dict))

    # Get command and expected result (as new_record) for all commands
    for cmd, new_record in cmd_dict.iteritems():
        # http specific
        if 'http' not in new_record:
            new_record = new_record.replace('/', ' ')
        else:
            first_subs = new_record.split('http')[0].replace('/', ' ')
            second_subs = new_record.split('http')[1]
            new_record = first_subs + 'http' + second_subs
        # remove double spaces
        new_record = ' '.join(new_record.split())
        # ===============================
        # Execute the "<cmd>" command on mod node
        cmd_result = get(cmd)
        #       if cmd_result['out'] is True:
        if "syntax error" in cmd_result['message']:
            old_record = cmd + " " + "Element does not exist"
        elif "No entries found" in cmd_result['message']:
            old_record = cmd + " " + "No entries found"
        else:
            # Format the output - remove the new line chars
            out_list = cmd_result['message'].split('\r\n')
            out_str = ''.join(out_list)
            # remove special chars
            old_record = re.sub('[\[,\],!]', '', out_str)
            old_record = re.sub('\s\s+', ' ', old_record)
            # formatted result of the command
            old_record = ' '.join(old_record.split())

        # Compare the result (output) with expected result
        if new_record != old_record:
            # Check if all words of the expected result are in the command's output
            new_record_list = new_record.split(' ')
            for item in new_record_list:
                if item not in old_record:
                    # get the value which is not part of the command
                    old_record = old_record.split(cmd)[1].strip()
                    # Save the error
                    # key = command, value = expected and real results
                    ret['old'][cmd] = old_record
                    ret['new'][cmd] = new_record
                    break
    # end for
    return ret


# ========================================================
# Verify the results of the mod commands (.json file)
def verify(json_fname):
    """
    Verify the expected and real values configured by the commands in JSON file

    Usage:

    .. code-block:: bash

        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.verify '/tmp/mod/mod-dpdev_config.json'

    """
    log.debug('mod.verify called, json_fname: ' + str(json_fname))

    # mod command types
    cmd_types = ["alerts", "services", "snmp"]

    ret = dict()

    # ===================================
    # Get {K:V} pairs of the mod commands (K) and expected results (V)
    #
    cmd_dict = dict()
    try:
        cmd_dict = _get_commands_and_values(json_fname, cmd_types)
        if len(cmd_dict) == 0:
            ret['message'] = '*** modules.mod verify()._get_commands_and_values: empty list of commands'
            log.debug(str(ret['message']))
            ret['out'] = False
            return ret
    except Exception as exception:
        ret['message'] = '*** modules.mod verify()._get_commands_and_values: execution failed due to "{0}"'.format(exception)
        log.debug(str(ret['message']))
        ret['out'] = False
        return ret

    # The cmd_dict is a dictionary of commands and results
    # Examples:
    #   alerts destinations email: RESULT
    #   enabled: true
    
    # ===================================
    # Verify the results of the commands
    #
    try:
        ret = _verify_commands(**cmd_dict)
        log.debug('VERIFY: Old: {}, New: {}'.format(ret['old'], ret['new']))
        if ret['old'] or ret['new']:
            ret['message'] = "Failure"
            ret['out'] = False
        else:
            # clear old and new dicts
            ret.clear()
            ret['message'] = "Success"
            ret['out'] = True
    except Exception as exception:
        ret['message'] = '*** modules.mod verify()._verify_commands: execution failed due to "{0}"'.format(exception)
        log.debug(str(ret['message']))
        ret['out'] = False

    return ret


# =========================================================
# Configure mod with pre and post verification
def config(json_fname):
    """
    Configure mod with pre and post verification

    Usage:

    .. code-block:: bash

       sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.config '/tmp/mod/mod-dpdev_add-mod.json'

    """
    log.debug('mod.config json_fname: {}'.format(json_fname))
    ret = dict()

    ret['message'] = ""
    ret['out'] = False

    # verify mod configuration
    res = verify(json_fname)

    if 'Success' not in res['message']:
        # Loop - trying to configure mod
        for iter in range(3):
            # Configure mod from .json file
            res = exec_commands_from_file(json_fname)
            if res['out'] is True:
                # verify mod again
                res = verify(json_fname)
                if 'Success' in res['message']:
                    ret['message'] = "mod node configured successfully"
                    ret['out'] = True
                    break
    else:
        ret['message'] = res['message']
        ret['out'] = True

    return ret


# =====================================
# Shutdown the connection
def shutdown():
    """
    Shutdown the connection to the mod proxy-minion.
    For this proxy, shutdown is a no-op.
    """
    log.debug('mod proxy shutdown() called...')


# =========================================================
#                   D B   C O M M A N D S
# =========================================================

# =====================================
# Check if DB has been downloaded
def db_downloaded(targeted_vendor):
    """
    Check if DB has been downloaded

    Parameters
    ----------
    targeted_vendor :
        Targeted vendor to check
        Vendor names: vendor

    Returns
    -------
    If service downloaded successfully
        ['out'] = True
        ['massage'] = 'service <name> status ...' or 'Vendor ...'
    If DB was not downloaded:
        ['out'] = False
        ['massage'] = ' No entries found'

    Usage
    -----

    .. code-block:: bash

        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.db_downloaded 'vendor'

    """
    log.debug('mod.db_downloaded called; targeted_vendor: ' + str(targeted_vendor))
    ret = dict()

    ret['message'] = ""
    ret['out'] = False

    if targeted_vendor not in ['vendor']:
        ret['message'] = "Please, use one of the following vendor names as parameter:\n" + "[vendor]"
        log.debug('targeted_vendor not in approved list')
        return ret

    vendor_name = targeted_vendor.lower()

    check_not_found = 'No entries found'
    check_service_ok = 'services ' + vendor_name + ' status'
    check_clam_ok = 'Vendor'

    if vendor_name == 'vendor':
        cmd = vendor_name + ' status'
    else:
        cmd = 'show services ' + vendor_name + ' status'

    log.debug('cmd: ' + str(cmd))
    try:
        # execute the command in ENABLE context
        with __proxy__['mod.create_persistent_connection']() as mod_connection:
            res = mod_connection.exec_cmd(cmd, context='ENABLE')
            log.debug('cmd result: ' + str(res))
    except Exception as exception:
        ret['message'] = '*** modules.mod.db_downloaded(): execution failed due to "{0}"'.format(exception)
        log.error(str(ret['message']))
        return ret

    ret['message'] = res

    # check the result
    if check_not_found in res:
        ret['out'] = False
    elif check_service_ok in res or check_vendor in res:
        ret['out'] = True
    else:
        log.error("'{}' resulted in '{}' and did not match known checks".format(cmd, res))
    return ret


# =====================================
# Check if DB is actively being downloaded
def db_downloading(targeted_vendor):
    """
    Check if DB is actively being downloaded

    Parameters
    ----------
    targeted_vendor :
        Targeted vendor to check
        Vendor names: vendor

    Returns
    -------
    If download is in progress
        ['out'] = True
        ['massage'] = 'service <name> status ... downloading true'
    If download is NOT in progress
        ['out'] = False
        ['massage'] = 'service <name> status ... downloading false'

    Usage
    -----

    .. code-block:: bash

        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.db_downloading 'vendor'

    """
    log.debug('mod.db_downloading called; targeted_vendor: ' + str(targeted_vendor))
    ret = dict()

    ret['message'] = ""
    ret['out'] = False

    if targeted_vendor not in ['vendor]:
        ret['message'] = "Please, use one of the following vendor names as parameter:\n" \
                         + "[vendor]"
        log.debug('targeted_vendor not in approved list')
        return ret

    vendor_name = targeted_vendor.lower()

    check_downloading = 'downloading true'
    check_not_downloading = 'downloading false'
    cmd = 'show services ' + vendor_name + ' status'

    try:
        # execute the command in ENABLE context
        with __proxy__['mod.create_persistent_connection']() as mod_connection:
            res = mod_connection.exec_cmd(cmd, context='ENABLE')
            log.debug('cmd result: ' + str(res))
    except Exception as exception:
        log.error('{0}'.format(exception))
        ret['message'] = '*** modules.mod.db_downloading(): execution failed due to "{0}"'. \
            format(exception)
        return ret

    ret['message'] = res

    # check the result
    if check_downloading in res:
        ret['out'] = True
    elif check_not_downloading in res:
        ret['out'] = False
    else:
        log.error("'{}' resulted in '{}' and did not match known checks".format(cmd, res))
    return ret


# =====================================
# Check if an AV Pattern DB has been downloaded, and if it will expire within <n> days
#
def db_expiry(targeted_vendor_list=None, days_from_now=0):
    """
    Check if DB has been downloaded, and if it will expire within <n> days

    Parameters
    ----------
    targeted_vendor_list :
        Targeted vendor to check (defaults to 'BASE')
        Vendor names: ['BASE', 'Vendor']
        or 'ALL' checks all valid vendor names
    days_from_now :
        checks if "days remaining" from license is greater than the value passed.  (defaults to 0)
        Returns False if the days remaining in the license is less than or equal to the days_from_now parameter

    Returns
    -------
    If service downloaded successfully, is "valid", and will not expire within "days_from_now"
        ['out'] = True
        ['massage'] = 'Vendor: Vendor
                       Database "Vendor" days_remaining is: 10, which is greater than 0 days from now'

    If DB was not downloaded, and therefore is invalid:
        ['out'] = False
        ['massage'] = 'Vendor: Vendor
                       Not Valid'

    Usage
    -----

    .. code-block:: bash

        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.db_expiry ['BASE'] days_from_now='10'
        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.db_expiry ['Vendor'] days_from_now='90'
        sudo salt 'mod1_zone1.us-central1.amazonaws.com' mod.db_expiry ['ALL'] days_from_now='90'

    """
    if targeted_vendor_list is None:
        targeted_vendor_list = ['BASE']

    log.debug('mod.db_expiry called; targeted_vendor_list: ' + str(targeted_vendor_list) + '; days_from_now: ' + str(days_from_now))
    ret = dict()

    ret['message'] = ""
    ret['out'] = None  # None, not False

    # create an object to interact with mod device
    comp_name = __pillar__['node']['component']

    try:
        mod = rest_helper.HttpSession(ip=__pillar__['pod']['mod'][comp_name]['mgmt']['ip'],
                                       admin_password=__pillar__['pod']['mod'][comp_name]['deploy']['enablePassword'],
                                       user=__pillar__['pod']['mod'][comp_name]['deploy']['userName'])
    except Exception as exception:
        log.error('{0}'.format(exception))
        ret['message'] = '*** modules.mod.db_expiry(): execution failed instantiating rest_helper.HttpSession'
        ret['out'] = False
        return ret

    mod.login()

    # from the mod sys_info, extract the 'licenses' LIST
    try:
        output = mod.sys_info()['licenses']
        log.debug('output: ' + str(output))
    except Exception as exception:
        log.error('{0} ERROR retrieving licensing information via REST'.format(exception))
        return {'message': '*** modules.mod.db_expiry(): execution failed retrieving JSON licensing-object, is mod fully booted?', 'out': False}

    my_vendors = []
    valid_vendors = ['BASE', 'Vendor',]

    # collect passed-in vendor names and build our own list of valid names
    for my_vend in targeted_vendor_list:
        if my_vend in valid_vendors:
            my_vendors.append(my_vend)
        if my_vend.lower() in ['all']:
            my_vendors = valid_vendors
            break

    log.debug('my_vendors: ' + str(my_vendors))
    if not my_vendors:
        ret['message'] = 'No valid vendor names were selected'
        return ret

    pod_name = __pillar__['node']['pod']
    tmp_db_status_fname = "/tmp/{}-{}-db-status".format(comp_name, pod_name)

    with open(tmp_db_status_fname, "w") as db_status_file:
        for license_dict in output:
            for k, v in license_dict.items():
                if k == 'vendor' and v in my_vendors:
                    ret['message'] += '\nVendor: {}'.format(v)
                    if license_dict['valid']:
                        if int(license_dict['days_remaining']) > int(days_from_now):
                            ret['message'] += ' Database "{}" days_remaining is: {}, which is greater than {} days from now'.format(v, int(
                                license_dict['days_remaining']), days_from_now)
                            if ret['out'] is None:
                                ret['out'] = True
                        else:
                            ret['message'] += ' WARNING DATABASE "{}" LICENSE WILL EXPIRE WITHIN {} DAYS'.format(v, days_from_now)
                            ret['out'] = False
                    else:
                        ret['message'] += ' Not Valid'
                        ret['out'] = False
        # Save the final status of loading of the DB
        db_status_file.write(str(ret['out']))

    return ret

# =====================================
# Image Upgrade
#
def image_upgrade(imageUrl = None, buildNum = 0, forceImage = False):
    """
    Retrieve a mod image (.bcsi) and load it, with optional reboot

    Parameters
    ----------
    imageUrl :  The full URL to the .bcsi image. (default: None)
    buildNum :  The build number to boot to (default: 0)

    Returns
    -------
    If image is downloaded successfully, the new image ReleaseID is returned

    Usage
    -----

    .. code-block:: bash

        sudo salt 'mod1_zone1.us-central1.amazonaws.com' state.sls current_dp.comp.mod.tools.image_upgrade pillar='{"imageUrl": "http://10.10.1.12/mod/mod-1234567"}' -l debug
      - will first check to see if the currently running image is less than or equal to the requested image build-number,
      - if greater, a download will be attempted
      - if successful, the newly downloaded build number is returned as 'message', and 'out' is True
      - if un-successful, 'out' is False

    """

    log.debug('mod.image_upgrade called; imageUrl passed: {0}'.format(imageUrl))
    ret = dict()

    # create an object to interact with mod device
    comp_name = __pillar__['node']['component']

    try:
        mod = rest_helper.HttpSession(ip=__pillar__['pod']['mod'][comp_name]['mgmt']['ip'],
                                       admin_password=__pillar__['pod']['mod'][comp_name]['deploy']['enable'],
                                       user=__pillar__['pod']['mod'][comp_name]['deploy']['userName'])
    except Exception as exception:
        log.error('{0}'.format(exception))
        ret['message'] = '*** modules.mod.image_upgrade(): execution failed instantiating rest_helper.HttpSession'
        ret['out'] = False
        return ret

    mod.login()

    # from the mod system-images, iiterate over image-list, find which one is booted, extract releaseID
    try:
        ver = mod.version()
        log.debug('mod version: ' + str(ver))
    except Exception as exception:
        log.error('{0} ERROR retrieving system version via REST'.format(exception))
        return {'message': '*** modules.mod.image_upgrade(): execution failed retrieving system version', 'out': False}

    currentlyBooted = ver['build']
    if int(currentlyBooted) >= int(buildNum) and not forceImage:
        message = 'new build image [{0}] should be greater-than the currently-running system image [{1}]'.format(buildNum,currentlyBooted)
        log.debug(message)
        return {'message': '*** modules.mod.image_upgrade(): {0}'.format(message), 'out': False}

    #send URL for mod to fetch
    mod.retrieve_image(imageUrl)

    #loop until image is retrieved, or timeout
    stopLoop=False
    count = 1
    while not stopLoop and count < 10:
        count += 1
        time.sleep(10)
        check = mod.retrieve_image_status()
        if check['currentlyDownloading'] == False:
            stopLoop = True

    #did we time-out?
    if not stopLoop:
        message = 'Image fetch timed-out.  [{0}]'.format(check['downloadStatusMessage'])
        log.debug(message)
        return {'message': '*** modules.mod.image_upgrade(): {0}'.format(message), 'out': False}

    sysImages = mod.system_images()
    log.debug('all mod images: ' + str(sysImages))
    #find the image that's now the default - releaseId should = buildNum
    for sysImage in sysImages:
        if sysImage['defaultImage']:
           break

    if int(sysImage['releaseId']) == int(buildNum):
        return {'message': '{0}'.format(sysImage['releaseId']), 'out': True }
    else:
        return {'message': 'ERROR *** modules.mod.image_upgrade(): [{0}] The default image is still {1}'.format(check['reason'], sysImage['releaseId']), 'out': False }

# ========================================================
# Extract the image build number
#
def version():
    """
    Extract the MOD image build number

    Usage:

    .. code-block:: bash

        salt 'mod1_zone1.us-central1.amazonaws.com' mod.version

    """
    log.debug('mod.version called')
    ret = dict()

    # create an object to interact with mod device
    comp_name = __pillar__['node']['component']

    try:
        mod = rest_helper.HttpSession(ip=__pillar__['pod']['mod'][comp_name]['mgmt']['ip'],
                                       admin_password=__pillar__['pod']['mod'][comp_name]['deploy']['enablePassword'],
                                       user=__pillar__['pod']['mod'][comp_name]['deploy']['userName'])
    except Exception as exception:
        log.error('{0}'.format(exception))
        ret['message'] = '*** modules.mod.version(): execution failed instantiating rest_helper.HttpSession'
        ret['out'] = False
        return ret

    mod.login()

    # extract build from version object
    try:
        ver = mod.version()
        log.debug('mod version-object: ' + str(ver))
    except Exception as exception:
        log.error('{0} ERROR retrieving system images via REST'.format(exception))
        return {'message': '*** modules.mod.version(): execution failed retrieving JSON system_image list?', 'out': False}

    currentlyBooted = ver['build']
    if currentlyBooted:
        return {'message': '{0}'.format(currentlyBooted), 'out': True}
    else:
        return {'message': '*** modules.mod.version(): execution failed', 'out': False}

# =========================================================
