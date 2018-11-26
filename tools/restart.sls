# =====================================
#
# Description:
#   Restart MOD node and wait 120 sec
# Usage:
#   sudo salt 'mod.dpdev' state.sls current_dp.comp.tools.restart -t 180
#
# =====================================

# ===================================
# Reboot/Restart MOD node
restart-mod:
  module.run:
    - name: mod.restart

# ===================================
# Sleep 'till booted - MOD rarely takes more than 2 min. to boot
# still need to wait an extra minute for Tomcat to initialize the
# REST interface
sleep-till-booted:
  module.run:
    - name: test.sleep
    - length: 180
    - require:
      - module: restart-mod
