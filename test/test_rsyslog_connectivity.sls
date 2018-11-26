# =====================================
#
# Description:
#   Run network.connect test to see if ops-node rsyslog is reachable
# Usage:
#  sudo salt 'mod.dpdev' state.apply current_dp.comp.test.test_rsyslog_connectivity
# Notes:
#  1. MOD can enter a bad state if it can't talk to the remote syslog service.
#     Add at the beginning of the MOD highstate a check to ensure that the remote syslog service is available and online
#  2. Host ops.mgmt.ip is also defined in: 
#     {{ path_to_json_files }}/{{ full_comp_name }}_{{ config_file_name }}.json
#
# =====================================

check-rsyslog-is-up-on-host-{{ pillar.pod.ops.mgmt.ip }}:
  cmd.run:
    - name: 'nc -w 1 -v -z -u {{ pillar.pod.ops.mgmt.ip }} 514'
    - shell: '/bin/bash'
    - failhard: False
    - retry:
        attempts: 20
        until: True
        interval: 15
        splay: 10
