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
module: nxos_ping
version_added: "2.1"
short_description: Tests reachability using ping from Nexus switch
description:
    - Tests reachability using ping from switch to a remote destination
author: Jason Edelman (@jedelman8), Gabriele Gerbino (@GGabriele)
requirements:
    - NX-API
extends_documentation_fragment: nxos
options:
    dest:
        description:
            - IP address or hostname (resolvable by switch) of remote node
        required: true
        default: null
        choices: []
        aliases: []
    count:
        description:
            - Number of packets to send
        required: false
        default: 4
        choices: []
        aliases: []
    source:
        description:
            - Source IP Address
        required: false
        default: null
        choices: []
        aliases: []
    vrf:
        description:
            - Outgoing VRF
        required: false
        default: null
        choices: []
        aliases: []
'''

EXAMPLES = '''
# test reachability to 8.8.8.8 using mgmt vrf
- nxos_ping: dest=8.8.8.8 vrf=management host={{ inventory_hostname }}
# Test reachability to a few different public IPs using mgmt vrf
- nxos_ping: dest={{ item }} vrf=management host={{ inventory_hostname }}
  with_items:
    - 8.8.8.8
    - 4.4.4.4
    - 198.6.1.4
'''

RETURN = '''
action:
    description:
        - Show what action has been performed
    returned: always
    type: string
    sample: "PING 8.8.8.8 (8.8.8.8): 56 data bytes"
command:
    description: Show the command sent
    returned: always
    type: string
    sample: "ping 8.8.8.8 count 8 vrf management"
count:
    description: Show amount of packets sent
    returned: always
    type: string
    sample: "8"
dest:
    description: Show the ping destination
    returned: always
    type: string
    sample: "8.8.8.8"
rtt:
    description: Show RTT stats
    returned: always
    type: dict
    sample: {"avg": "6.264","max":"6.564",
            "min": "5.978"}
packets_rx:
    description: Packets successfully received
    returned: always
    type: string
    sample: "8"
packets_tx:
    description: Packets successfully transmitted
    returned: always
    type: string
    sample: "8"
packet_loss:
    description: Percentage of packets lost
    returned: always
    type: string
    sample: "0.00%"
'''


import socket
import xmltodict


def get_summary(results_list, reference_point):
    summary_string = results_list[reference_point+1]
    summary_list = summary_string.split(',')
    pkts_tx = summary_list[0].split('packets')[0].strip()
    pkts_rx = summary_list[1].split('packets')[0].strip()
    pkt_loss = summary_list[2].split('packet')[0].strip()
    summary = dict(packets_tx=pkts_tx,
                   packets_rx=pkts_rx,
                   packet_loss=pkt_loss)

    return summary


def get_rtt(results_list, packet_loss, location):
    if packet_loss != '100.00%':
        rtt_string = results_list[location]
        base = rtt_string.split('=')[1]
        rtt_list = base.split('/')
        min_rtt = rtt_list[0].lstrip()
        avg_rtt = rtt_list[1]
        max_rtt = rtt_list[2][:-3]
        rtt = dict(min=min_rtt, avg=avg_rtt, max=max_rtt)
    else:
        rtt = dict(min=None, avg=None, max=None)

    return rtt


def get_statistics_summary_line(response_as_list):
    for each in response_as_list:
        if '---' in each:
            index = response_as_list.index(each)
    return index


def execute_show_command(command, module):
    cmds = [command]
    try:
        body = module.execute(cmds)
    except ShellError as clie:
        module.fail_json(msg='Error sending {0}'.format(command),
                         error=str(clie))
    return body[0]


def get_ping_results(command, module, transport):
    ping = execute_show_command(command, module)

    splitted_ping = ping.split('\n')
    reference_point = get_statistics_summary_line(splitted_ping)
    summary = get_summary(splitted_ping, reference_point)
    rtt = get_rtt(splitted_ping, summary['packet_loss'], reference_point+2)

    return (splitted_ping, summary, rtt)


def main():
    argument_spec = dict(
            dest=dict(required=True),
            count=dict(required=False, default=4),
            vrf=dict(required=False),
            source=dict(required=False),
    )
    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    destination = module.params['dest']
    count = module.params['count']
    vrf = module.params['vrf']
    source = module.params['source']

    OPTIONS = {
        'vrf': vrf,
        'count': count,
        'source': source
        }

    ping_command = 'ping {0}'.format(destination)
    for command, arg in OPTIONS.iteritems():
        if arg:
            ping_command += ' {0} {1}'.format(command, arg)

    ping_results, summary, rtt = get_ping_results(
                    ping_command, module, module.params['transport'])

    packet_loss = summary['packet_loss']
    packets_rx = summary['packets_rx']
    packets_tx = summary['packets_tx']

    results = {}

    results['command'] = ping_command
    results['action'] = ping_results[1]
    results['dest'] = destination
    results['count'] = count
    results['packets_tx'] = packets_tx
    results['packets_rx'] = packets_rx
    results['packet_loss'] = packet_loss
    results['rtt'] = rtt

    module.exit_json(**results)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
    main()