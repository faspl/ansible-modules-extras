#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

DOCUMENTATION = '''
---
module: nxos_save_config
version_added: "2.1"
short_description: Saves running configuration
description:
    - Saves running config to startup-config or file of your choice
author: Jason Edelman (@jedelman8), Gabriele Gerbino (@GGabriele)
requirements:
    - NX-API
options:
    path:
        description:
            - Path including filename on target device to save running config
        required: false
        default: null
        choices: []
        aliases: []
'''

EXAMPLES = '''
# save running config to startup-config
- nxos_save_config: host={{ inventory_hostname }}
# save running config to dir in bootflash
- nxos_save_config: path='bootflash:configs/my_config.cfg' host={{ inventory_hostname }}
'''

RETURN = '''
path:
    description: Describes where the running config will be saved
    returned: always
    type: string
    sample: 'startup-config'
status:
    description: Shows whether the save's been successful or not
    returned: always
    type: string
    sample: 'successful'
changed:
    description: Checks to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


import socket
import xmltodict


def execute_show_command(command, module):
    cmds = [command]
    try:
        body = module.execute(cmds)
    except ShellError, clie:
        module.fail_json(msg='Error sending {0}'.format(command),
                         error=str(clie))
    return body[0]


def save_config(path, module, transport):
    command = 'copy run {0}'.format(path)
    error = None
    changed = False
    complete = False

    save_response = execute_show_command(command, module)

    if '100%' in save_response or 'copy complete' in save_response.lower():
        complete = True
        changed = True

    if complete:
        result = 'successful'
        return (result, changed)
    else:
        error = 'error: could not validate save'
        module.fail_json(msg=error, response=save_response)


def main():
    argument_spec = dict(
            path=dict(default='startup-config')
    )
    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    path = module.params['path']

    if path != 'startup-config':
        if ':' not in path:
            msg = ('''invalid format for path.  Requires ":" '''
                   '''Example- bootflash:config.cfg'''
                   '''or bootflash:configs/test.cfg''')
            module.fail_json(msg=msg)

    complete_save, changed = save_config(path, module,
                                         module.params['transport'])

    results = {}
    results['path'] = path
    results['status'] = complete_save
    results['changed'] = changed

    module.exit_json(**results)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
    main()
