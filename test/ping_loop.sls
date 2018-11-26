# =====================================
#
# Description:
#   Run test.ping command in the loop with delay
# Usage:
#  sudo salt 'mod.dpdev' salt.state current_dp.comp.test.ping_loop
#
# =====================================
{% set num_loops = 20 %}
{% set sleep_time = 5 %}

{% for idx in range(num_loops) %}

# =====================================
# test.ping
test-ping-{{ loop.index }}:
  module.run:
    - name: test.ping

# =====================================
# delay
delay-{{ loop.index }}:
  module.run:
    - name: test.sleep
    - kwargs:
      length: {{ sleep_time }}
    - require:
      - module: test-ping-{{ loop.index }}

{% endfor %}
