# =====================================
# State:
#   //comp/tools/verify.sls
# Description:
#   Verify the results of the MOD configuration commands
# Usage:
#   sudo salt 'mod.dpdev' state.sls current_dp.comp.tools.verify -l debug
# =====================================
{% set full_comp_name = pillar.node.component ~ '-' ~ pillar.node.pod %}

{% set path_to_json_files = "/tmp/mod"%}
{% set config_file_name   = "config" %}

# ===================================
# Generate MOD configuration (commands) file
# in the /tmp directory from JINJA template
generate-json-config-file:
  file.managed:
    - source: salt://{{ pillar.node.version }}/comp/files/{{ config_file_name }}.json.jinja
    - name: {{ path_to_json_files }}/{{ full_comp_name }}_{{ config_file_name }}.json
    - template: jinja
    - user: root
    - group: root
    - mode: 644

# ===================================
# Verify the results of the MOD configuration commands
verify-mod:
  module.run:
    - name:  mod.verify
    - json_fname: {{ path_to_json_files }}/{{ full_comp_name }}_{{ config_file_name }}.json
    - require:
      - file: generate-json-config-file
