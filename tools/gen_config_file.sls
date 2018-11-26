# =====================================
#
# Description:
#   Generate MOD configuration (command) file
# Usage:
#   sudo salt 'mod.dpdev' state.sls current_dp.comp.tools.gen_config_file
#
# =====================================
{% set full_comp_name = pillar.node.component ~ '-' ~ pillar.node.pod %}

{% set path_to_json_file = "/tmp/mod" %}
{% set config_file_name  = "config" %}

# ===================================
# Check "configured" function in MOD state module
configure-mod:
  mod.configured:
    - name: {{ path_to_json_file }}/{{ full_comp_name }}_{{ config_file_name }}.json

# ===================================
# Generate MOD configuration JSON (commands) file from JINJA template
generate-json-config-file:
  file.managed:
    - source: salt://{{ pillar.node.version }}/comp/files{{ config_file_name }}.json.jinja
    - name: {{ path_to_json_file }}/{{ full_comp_name }}_{{ config_file_name }}.json
    - template: jinja
    - user: root
    - group: root
    - mode: 644
