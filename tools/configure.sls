# =====================================
# State:
#   //comp/tools/configure.sls
# Description:
#   Configure MOD node
# Usage:
#   sudo salt 'mod.dpdev' state.sls current_dp.comp.tools.configure
# =====================================
{% set full_comp_name = pillar.node.component ~ '-' ~ pillar.node.pod %}
{% set path_to_json_file = "/tmp/mod"%}
{% set config_file_name  = "config" %}

# ===================================
# Configure MOD
configure-mod:
  mod.configured:
    - name: {{ path_to_json_file }}/{{ full_comp_name }}_{{ config_file_name }}.json
