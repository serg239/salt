# =============================================================================
# Pillar:
#   //pillar/comp/module/init.sls
# Description:
#   MOD dynamically generated and component pillars
# =============================================================================

#######################################
# Dynamically generated pillars
#######################################
include:
  - {{ pillar.node.version }}.config.global
  - {{ pillar.node.version }}.config.region
  - {{ pillar.node.version }}.config.site
  - {{ pillar.node.version }}.config.pod
  - {{ pillar.node.version }}.config.node
  - {{ pillar.node.version }}.config.vmspec

#######################################
# Proxytype pillar
#######################################
proxy:
  proxytype: mod
