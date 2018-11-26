# =============================================================================
#
# Description:
#   Top "init" file for states
#
# =============================================================================
include:
  - {{ pillar.node.version }}.prepare
  - {{ pillar.node.version }}.config
  - {{ pillar.node.version }}.test_rsyslog_connectivity
  - {{ pillar.node.version }}.test_network_connectivity
  - {{ pillar.node.version }}.start
