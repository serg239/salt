# -*- coding: utf-8 -*-
"""
MOD state module to interact with MOD devices
=============================================

Script: //_states/mod.py

.. versionadded:: 2016.11.6

:maturity:      new
:depends:       mod.py execution module
:platform:      all

"""
from __future__ import absolute_import
import logging
import time

log = logging.getLogger()


# =========================================================
# Verify, load licenses, and verify again
#
def licenses_loaded(name,host='127.0.0.1',usr='super',passwd='12345'):
    """
    Enforce that the MOD licenses will be loaded

    name
      The JSON file with MOD commands

    Example:

    .. code-block:: bash

       load-licenses:
         mod.licenses_loaded:
           - name: /path/to/json/file with "load-licenses" command

    .. note::
       Example of JSON file:
       * /tmp/mod/mod-dpdev_load-licenses.json

    """
    log.debug('licenses_loaded called name: {}'.format(name))

    # Prepare
    ret = {'name': name,
           'result': False,
           'changes': {},
           'comment': ''}

    # -------------------------
    # Verifying if Licenses have been already loaded
    res = __salt__['mod.check_licenses'](host, usr, passwd)
    log.debug('result of _state.mod.{} is: "{}:'.format(name,res))

    # Check if we're running in test=True mode
    if __opts__['test']:
        log.debug('running in test mode')
        # return the result
        ret['result'] = None
        if 'True' in res:
        #if 'already loaded' in res['message']:
            ret['comment'] = res['message']
        else:
            ret['comment'] = "Licenses will be loaded from {0} file".format(name)
        return ret

    # Generating the name of the status file. Ex.: /tmp/mod1-dp2-dev4-lic-status
    comp_name = __pillar__['node']['component']
    pod_name  = __pillar__['node']['pod']
    tmp_lic_status_fname = "/tmp/{}-{}-lic-status".format(comp_name, pod_name)

    with open(tmp_lic_status_fname, "w") as lic_status_file:
        if 'already loaded' in res['message']:
            log.debug('already loaded')
            # we will check the status file during the running the highstate next time
            lic_status_file.write("True")
            ret['result'] = True
            ret['comment'] = res['message']
        else:
            log.debug('not loaded, starting load...')
            # it's important to save False here, before the following attempts to load licenses;
            # it looks like we save "at that time the license was not loaded" status
            lic_status_file.write("False")
            # -------------------------
            # prepare output as a result of the first verification
            res = __salt__['mod.get_license_dates']()
            ret['changes'].setdefault('old', None)
            ret['changes'].setdefault('new', res['message'])

            # Loop - trying to load the licenses
            for iter in range(3):
                # -------------------------
                # load licenses
                log.debug('attempt: ' + str(iter) + '; name: ' + str(name))
                res = __salt__['mod.exec_commands_from_file'](name)
                
                #Sleep 60 seconds before checking again, and attempting re-load.
                #Rapid succession of downloading license may cause instability
                time.sleep(60)
                
                if res['out'] is True:
                    # check if licenses just loaded
                    res = __salt__['mod.check_licenses'](host, usr, passwd)
                    if 'already loaded' in res['message']:
                        log.debug('now loaded')
                        ret['result'] = True
                        ret['changes']['new'] = "Success"
                        ret['comment'] = "Licenses loaded successfully"
                        #write true..but already opened file needs to be truncated so you don't end up with "FalseTrue"
                        lic_status_file.truncate()
                        lic_status_file.write("True")
                        break
                else:
                    log.info("licenses_loaded error: " + str(res))
                    ret['result'] = False
                    ret['comment'] += "Failed attempt: {}, Result: {}. ".format(iter, str(res))

                # end if-else
            # end for
        # end if-else
    # end with
    return ret

# =========================================================
# Verify if DB is downloaded, using execution module function: system_db_downloaded
#
def system_db_downloaded(name, targeted_av_vendor='company'):
    """
    Enforce that the MOD licenses will be loaded

    name
      The name of this function (not relevant)
    targeted_av_vendor ['company']
      message:
          services company status pattern-status pattern-date 2017-10-23T00:00:00-00:00
      out:
          True

    Example:

    .. code-block:: bash

       load-licenses-check:
         mod.system_db_downloaded:
           - name: system_db_downloaded
           - kwargs:
             targeted_av_vendor: 'company'


    """
    log.debug('system_db_downloaded called name: {}; targeted_av_vendor: {}'.format(name, targeted_av_vendor))

    # Prepare
    ret = {'name': name,
           'result': False,
           'changes': {},
           'comment': ''}

    # -------------------------
    # Verifying if Licenses have been already loaded
    res = __salt__['mod.system_db_downloaded'](targeted_av_vendor)

    # Check if we're running in test=True mode
    if __opts__['test']:
        log.debug('running in test mode')
        # return the result
        ret['result'] = None
        if res['out']:
            ret['comment'] = res['message']
        else:
            ret['comment'] = "services {0} status pattern-status pattern-date NOT READY/No entries found".format(targeted_av_vendor)
        return ret

    if res['out']:
        ret['result'] = True

    ret['comment'] = res['message']

    return ret


# =========================================================
# Verify DB is downloaded, using execution module function: system_db_expiry
#
def system_db_expiry(name, targeted_av_vendor_list=None, days_from_now=0):
    """
    Check if an AV Pattern DB has been downloaded, and if it will expire within <n> days

    name
      The name of this function (not relevant)
    targeted_av_vendor_list :
        Targeted vendor to check (defaults to 'BASE')
        Vendor names: ['BASE','Vendor']
        or 'ALL' checks all valid vendor names
    days_from_now :
        checks if "days remaining" from license is greater than the value passed.  (defaults to 0)
        Returns False if the days remaining in the license is less than or equal to the days_from_now parameter

      message:
          Vendor: Vendor Database "Vendor" days_remaining is: 10, which is greater than 0 days from now
      out:
          True

    Example:

    .. code-block:: bash

       load-licenses-check:
         mod.system_db_expiry:
           - name: system_db_expiry
           - kwargs:
             targeted_av_vendor_list: ['Vendor']
             days_from_now: 90

    """
    if targeted_av_vendor_list is None:
        targeted_av_vendor_list = ['BASE']

    log.debug('system_db_downloaded called name: {}; targeted_vendor_list: {}; days_from_now: {}'.format(name, targeted_vendor_list, days_from_now))

    # Prepare
    ret = {'name': name,
           'result': False,
           'changes': {},
           'comment': ''}

    # -------------------------
    # Verifying if Licenses have been already loaded
    res = __salt__['mod.system_db_expiry'](targeted_vendor_list, days_from_now)

    # Check if we're running in test=True mode
    if __opts__['test']:
        log.debug('running in test mode')
        # return the result
        ret = res
        return ret

    if res['out']:
        ret['result'] = True

    ret['comment'] = res['message']

    return ret

# =========================================================
# Image_upgrade
#
def image_upgrade(name, imageUrl = None, buildNum = 0, forceImage = False):
    """
        Retrieve a MOD image (.img) and load it, with optional reboot

    Parameters
    ----------
    imageUrl :  The full URL to the .img image. (default: None)
    buildNum :  The build number to boot to (default: 0)
    
    Returns
    -------
    If image is downloaded successfully, the new image ReleaseID is returned

    Usage
    -----

    .. code-block:: bash

        sudo salt 'mod.dpdev' state.sls current_dp.comp.tools.image_upgrade pillar='{"imageUrl": "http://10.10.1.12/mod-1234567", "buildNum": 1234567}' -l debug
      - will first check to see if the currently running image is less than or equal to the requested image build-number, (test is ignored if forceImage=True)
      - if greater, a download will be attempted
      - if successful, the newly downloaded build number is returned as 'message', and 'out' is True
      - if un-successful, 'out' is False

    """

    log.debug('mod image_upgrade called imageUrl: {}; buildNum: {}, forceImage: {}'.format(imageUrl, buildNum, forceImage))

    # Prepare
    ret = {'name': name,
           'result': False,
           'changes': {},
           'comment': ''}

    res = __salt__['mod.image_upgrade'](imageUrl, buildNum, forceImage)

    # Check if we're running in test=True mode
    if __opts__['test']:
        log.debug('running in test mode')
        # return the result
        ret = res
        return ret

    if res['out']:
        ret['result'] = True

    ret['comment'] = res['message']

    return ret


# =========================================================
# Verify, add MOD and verify again
#
def mod_added(name):
    """
    Enforce that the MOD will be added
    name
        The JSON file with MOD commands

    Example:

      .. code-block:: bash

        add-mod:
           mod.mod_added:
             - name: /path/to/json/file with "add mod" commands

      .. note::
        Example of JSON file:
        * /tmp/mod/mod-dpdev4_add-mod-appliances.json
    """
    log.debug('mod_added called name: {}'.format(name))

    # Prepare
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}

    mod_command = "check mod"

    # -------------------------
    # Verifying if MOD appliances have been already added
    #
    res = __salt__['mod.check_mod']()

    # Check if we're running in test=True mode
    if __opts__['test']:
        log.debug('running in test mode')
        # return the result
        ret['result'] = None
        if 'already added' in res['message']:
            ret['comment'] = res['message']
        else:
            ret['comment'] = "MA info will be added from {0} file".format(name)
        return ret

    if 'already added' in res['message']:
        log.debug('already added')
        ret['result'] = True
        ret['comment'] = res['message']
    else:
        # -------------------------
        # prepare the output as a result of the first verification
        #
        res = __salt__['mod.get'](ma_command)
        ret['changes'].setdefault('old', None)
        ret['changes'].setdefault('new', res['message'])

        # Loop - trying to load the licenses
        for iter in range(3):
            # -------------------------
            # add MA appliances
            log.debug('attempt: ' + str(iter) + '; name: ' + str(name))
            res = __salt__['mod.exec_commands_from_file'](name)
            if res['out'] is True:
                # -------------------------
                # check if MA appliances just loaded
                res = __salt__['mod.check_mod']()
                if 'already added' in res['message']:
                    log.debug('now added')
                    ret['result'] = True
                    ret['changes']['new'] = "Success"
                    ret['comment'] = "MA appliances added successfully"
                    break
            else:
                log.info("ma_added error: " + str(res))
                ret['result'] = False
                ret['comment'] += "Failed attempt: {}, Result: {}. ".format(iter, str(res))

        # end for
    return ret


# =====================================
# Configure MOD by using commands from JSON file
#
def configured(name):
    """
    Enforce that the MOD node will be configured

    name
        The JSON file with MOD configuration commands

    Example:

    .. code-block:: yaml

       config-mod:
         mod.configured:
           - name: /path/to/json/file with MOD configuration commands

    .. note::
       Example of JSON file:
       * '/tmp/mod/mv1-dp1-mod2_config.json'
    """
    log.debug('configured called name: {}; '.format(name))

    # Prepare
    ret = {'name': name,
           'result': False,
           'changes': {},
           'comment': ''
           }

    # -------------------------
    # Verifying MOD configuration
    #
    res = __salt__['mod.verify'](name)

    # Check if we're running in test=True mode
    if __opts__['test']:
        log.debug('running in test mode')
        # return the result
        ret['result'] = None
        if 'Success' in res['message']:
            ret['comment'] = "MOD already configured"
        else:
            ret['comment'] = "MOD will be configured from {0} file".format(name)
        return ret

    if 'Success' in res['message']:
        log.debug('already configured')
        ret['result'] = True
        ret['comment'] = res['message']
    else:
        # prepare the output as a result of the first verification
        # old: "No entries found" or default values
        if 'old' in res.keys():
            ret['changes'].setdefault('old', res['old'])

        # new: Values from JSON configuration file
        if 'new' in res.keys():
            ret['changes'].setdefault('new', res['new'])

        # Loop - trying to configure MOD
        for iter in range(3):
            # -------------------------
            # configure MOD from json file
            log.debug('attempt: ' + str(iter) + '; name: ' + str(name))
            res = __salt__['mod.exec_commands_from_file'](name)
            if res['out'] is True:
                # -------------------------
                # verifying MOD again
                res = __salt__['mod.verify'](name)
                if 'Success' in res['message']:
                    log.debug('now configured')
                    ret['result'] = True
                    # we do not update the ret['changes']['new'] here
                    # to see the values from JSON file
                    ret['comment'] = "MOD node configured successfully"
                    break
            else:
                log.info("configured error: " + str(res))
                ret['result'] = False
                ret['comment'] += "Failed attempt: {}, Result: {}. ".format(iter, str(res))

        # end for
    return ret
