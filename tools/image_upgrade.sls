# =============================================================================
#
# Description:
#   Update MOD from the image located on the ops node
# Usage:
#   sudo salt 'mod.dpdev' state.sls current_dp.comp.tools.image_upgrade pillar='{"build_num": "1234567"}' -l debug
#   sudo salt 'mod.dpdev' state.sls current_dp.comp.tools.image_upgrade pillar='{"build_num": "1234565", debug="true"}' -l debug
# Notes:
#   External pillar values:
#     build_num - build number string. Values: ["1234567"|"debug-1234567"]
#     debug     - debug build. boolean Values: ["true"|"false"]. Defalut: "false".
#
# =============================================================================
{% set comp_name = 'mod' %}

# 1234567 - getting the current build number from component, not from pillars!
{% set current_build_num = salt['mod.version']()['message'] %}

# Get new build number from command-line pillar, or default to the existing current_build_num
{% set new_build_num = salt['pillar.get']('build_num', current_build_num) %}

# Check if it's upgrade
{% if new_build_num | int > current_build_num | int %}

  # Check if the debug version should be installed (debug=True from pillar)
  {% set is_debug = salt['pillar.get']('debug', 'false') %}
  {% if is_debug|lower == 'false' %}
    {% set new_build_name = new_build_num %}
  {% else %}
    {% set new_build_name = 'debug-' ~ new_build_num %}
  {% endif %}

  # Example: http://<ops-node>/mod-210186.img
  # Example: http://<ops-node>/mod-debug-210186.img
  {% set img_url = 'http://'~pillar.pod.ops.mgmt.ip~'/'~comp_name~'/'~comp_name~'-'~new_build_name~'.img' %}

  # Check if URL-file exists
  {% set urlFileStatus = salt['http.query'](url=img_url, method='HEAD', status=True) %}
  
  {% if urlFileStatus['status'] == 200 %}

    # ===================================
    # Show the from-to build numbers
    show-build-numbers:
      module.run:
        - name: test.echo
        - text: "Upgrading MOD from build={{ current_build_num }} to build={{ new_build_name }}"

    # ===================================
    # Show the image source URL
    show-url:
      module.run:
        - name: test.echo
        - text: "Source URL={{ img_url }}"

    # =====================================
    # Load upgrade file from build server
    #
    load-upgrade:
      mod.image_upgrade:
        - name: mod.image_upgrade
        - kwargs:
          imageUrl: {{ img_url }}
          buildNum: {{ new_build_num }}

    # ===================================
    # Reboot to run the newly installed image
    #
    restart-mod:
      module.run:
        - name: mod.restart
        - require:
          - mod: load-upgrade

    # ===================================
    # Sleep 300 sec
    # wait for MOD to restart
    reboot-sleep-300sec:
      module.run:
        - name: test.sleep
        - length: 300
        - require:
          - module: restart-mod

    # ===================================
    # Display the new build number for human validation
    show-new-build-number:
      module.run:
        - name: mod.version
        - require:
          - module: reboot-sleep-300sec
          
  {% else %}
  
    # ===================================
    # Show message about build URL error
    build-url-error:
      module.run:
        - name: test.echo
        - text: echo "Unable to access {{ img_url }}  Perhaps it's missing/unavailable"
    fail-state:
      test.fail_without_changes:
        - name: 'Try again'

  {% endif %}
  
{% else %}

  # ===================================
  # Show message about the wrong build number
  wrong-build-number:
    module.run:
      - name: test.echo
      - text: echo "The new build number {{ new_build_num }} should be greater than the current build number {{ current_build_num }}"
  fail-state:
    test.fail_without_changes:
      - name: 'Try again'

{% endif %}