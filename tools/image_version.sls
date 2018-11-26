# =====================================
#
# Description:
#   Display current image/build version number
# Usage:
#   sudo salt 'mod.dpdev' state.sls current_dp.comp.tools.image_version
#
# =====================================

# ===================================
# Display version using _modules/mod.py
mod-version:
  module.run:
    - name: mod.version