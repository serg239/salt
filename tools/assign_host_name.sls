# =====================================
# State:
#   //comp/tools/assign_host_name.sls
# Description:
#   Assign host name
# Usage:
#   sudo salt 'mod.dpdev' state.sls current_dp.comp.tools.assign_host_name
# =====================================
{% set full_comp_name = pillar.node.component ~ '-' ~ pillar.node.pod %}

# ===================================
# Assign the host (appliance) name
assign-host-name:
  module.run:
    - name: mod.set
    - kwargs:
      config_command: appliance-name {{ full_comp_name }}
      check: ""
