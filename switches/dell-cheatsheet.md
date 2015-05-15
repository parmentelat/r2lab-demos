# hostnames

From faraday's `/etc/hosts` through `ssh` (usual credentials)

* `ssh switch-data`  (62xx)
* `ssh switch-control` (55xx)
* `ssh switch-reboot` (55xx)
* `ssh switch-c007` (????)

# Stacking & general

* look at the current config

#
    show running-config

* Baudrates
<table>
<tr><th>Type</th><th>Where</th><th>speed</th></tr>
<tr><td>Linksys SRW0248</td><td>bemol</td><td>38400 8N1</td></tr>
<tr><td>PowerConnect 62xx</td><td>faraday - data</td><td> 9600 8N1 </td></tr>
<tr><td>PowerConnect 55xx</td><td>faraday - others</td><td> 9600 8N1 </td></tr>
</table>

  * can be changed (on both types) using
 e.g. `speed 38400` but we don't want to do that


* Stacking
  * It feels like the 2 models we have cannot be stacked together in any case
  * We could still stack the 2 55xx boxes but what sense would that make ?
* Paging
  * the 55xx can use `terminal datadump` to turn off paging (i.e. displaying a `-more-` prompt); 
  * could not find the same on 62.xx

* ssh
  * all 4 switches run an ssh server; enter with user `root` and usual password
  * preparation for SSH	 server: not appearing in either config are the following 2 commands that I ran once to create keypairs attached to host identification of the switch itself. ssh server won't start - even after `ip ssh server` if any of both keys is missing


###
    crypto key generate rsa
    crypto key generate dsa
    
# Workflow
* All 4 config files are managed under git in the `switches/` subdir
* running make install pushes this onto the tftp server on faraday
* then use one of these commands to fetch that config from the switch

###
    copy tftp://192.168.3.100/switch-data.conf startup-config
    copy tftp://192.168.3.100/switch-control.conf startup-config
    copy tftp://192.168.3.100/switch-reboot.conf startup-config
    copy tftp://192.168.3.100/switch-c007.conf startup-config
    
* and then 

###
    reload

# Data Switch - 6248

## config management

* For resetting to factory defaults, I found only one method for now, which is to reboot the box, and from the console you first hit a menu that lets you restore the factory defaults

* it could be that deleting the startup-config would do the trick as well but I have not tried that at this point.

* for saving to save the running config for next reboot (on the 55xx boxes, use instead `write memory`)

### 
    copy running-config startup-config
    
## Addressing

* interfaces get addressed by strings like

###
    interface ethernet 1/g44	
    
* example, inspecting

###

    switch-data#show interfaces status ethernet 1/g4
    Port   Type                            Duplex  Speed    Neg  Link  Flow Control
                                                                 State Status
    -----  ------------------------------  ------  -------  ---- --------- ------------
    1/g4   Gigabit - Level                 Full    1000     Auto Up        Active
    
    Flow Control:Enabled


## Mirroring/monitoring   

    monitor session 1 source interface 1/g<x>
    monitor session 1 destination interface 1/g<z>

At that point the session is not active; you can check this with (exit config mode of course)

    show monitor session 1
    
Turn on

    monitor session 1 mode
    
Turn off

    no monitor session 1 mode

## IGMP

    ip igmp snooping
    
# Reboot and Control switches - 5548

## config management

* reset to factory defaults (do not save when prompted)

###
    delete startup-config
    reload

* save current config

###
    write memory

## Addressing

* interfaces get addressed by strings like

###
    interface gigabitethernet 1/0/4	
    
* example, inspecting

###
    switch-reboot# show interfaces status gigabitethernet 1/0/4
                                                 Flow Link          Back   Mdix
    Port     Type         Duplex  Speed Neg      ctrl State       Pressure Mode
    -------- ------------ ------  ----- -------- ---- ----------- -------- -------
    gi1/0/4  1G-Copper    Full    100   Enabled  On   Up          Disabled Off

## Mirroring/monitoring   

* not tried but I expect the same `monitoring` commands to work identically

## IGMP

    ip igmp snooping