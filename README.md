Examples
========

Proxy-minion
------------
The proxy minion states are defined in: 

* __proxy_module.sls__ - proxy module (//_proxy dir)
* __execution_module.sls__  - execution module (//_modules dir)
* __state_module.sls__ - state module (//_states dir)
* __grains_module.sls__ - grains module (//_grains dir)

and top.sls of the component's Pillars.

Dynamically generated top.sls for Salt States and Pillars
---------------------------------------------------------

* __states_init.sls__ - top.sls for dynamically generated Salt States (//states/init.sls)
* __pillar_init.sls__ - top.sls for dynamically generated Pillars (//pillars/init.sls)

Tools States
------------
The tools states are to modify, reconfigure, verify, etc. a different services on the node.

* __restart.sls__ - to restart/reboot node

*Usage:*
```bash
$ sudo salt 'mod.dpdev' state.sls comp.mod.tools.restart
```  

* __gen_config_file.sls__ - to generate configuration file with commands

*Usage:*
```bash
$ sudo salt 'mod.dpdev' state.sls comp.mod.tools.gen_config_file
```  

* __image_version.sls__ - to display current image/build version number

*Usage:*
```bash
$ sudo salt 'mod.dpdev' state.sls comp.mod.tools.image_version
```

* __image_upgrade.sls___ - to update node from the image located on the ops node

*Usage:*
```bash
$ sudo salt 'mod.dpdev' state.sls comp.mod.tools.image_upgrade
```

* __configure.sls__ - to configure node from JSON file

*Usage:*
```bash
$ sudo salt 'mod.dpdev' state.sls comp.mod.tools.configure
```

* __assign_host_name.sls__ - to assign host name

*Usage:*
```bash
$ sudo salt 'mod.dpdev' state.sls comp.mod.tools.assign_host_name
```

* __verify.sls__ - to Generate MOD configuration (commands) file and
                   verify the results of the commands' execution

*Usage:*
```bash
$ sudo salt 'mod.dpdev' state.sls comp.mod.tools.verify
```  


Test States
-----------
The test states allows to run specific commands on MOD node:

* __test_rsyslog_connectivity.sls__ - to run network.connect test and see if ops node's rsyslog is reachable

*Usage:*
```bash
$ sudo salt 'mod.dpdev' state.sls comp.mod.test.test_rsyslog_connectivity
```

* __ping_loop.sls__ - to run test.ping command in the loop with delay

*Usage:*
```bash
$ sudo salt 'mod.dpdev' state.sls comp.mod.test.ping_loop
```


