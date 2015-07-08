#!/usr/bin/env python
#
#
#    NEPI, a framework to manage network experiments
#    Copyright (C) 2015 INRIA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 2 as
#    published by the Free Software Foundation;
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Alina Quereilhac <alina.quereilhac@inria.fr>
#         Maksym Gabielkov <maksym.gabielkovc@inria.fr>
#
# Author file: Mario Zancanaro <mario.zancanaro@inria.fr>
#
# This is a maintenance functions used to make group operations at the nodes from
# INRIA testbed (R2Lab) before running a OMF experiment using Nitos nodes.
#

from nepi.execution.ec import ExperimentController
from nepi.execution.resource import ResourceAction, ResourceState
import os
from nepi.util.sshfuncs import logger
import time
import sys
import re


def load(nodes, version, connection_info, show_results=True):
    """ Load a new image to the nodes from the list """
    valid_version(version)
    ec    = ExperimentController(exp_id="load-{}".format(version))
    nodes = check_node_name(nodes)

    gw_node = ec.register_resource("linux::Node")
    ec.set(gw_node, "hostname", connection_info['gateway'])
    ec.set(gw_node, "username", connection_info['gateway_username'])
    ec.set(gw_node, "identity", connection_info['identity'])
    ec.set(gw_node, "cleanExperiment", True)
    ec.set(gw_node, "cleanProcesses", False)
    ec.set(gw_node, "cleanProcessesAfter", False)

    node_appname = {}
    node_appid   = {}
    apps         = []

    for node in nodes:
        on_cmd_a = "nodes {}; load-{}".format(node, version) 
        node_appname.update({node : 'app_{}'.format(node)}) 
        node_appname[node] = ec.register_resource("linux::Application")
        ec.set(node_appname[node], "command", on_cmd_a)
        ec.register_connection(node_appname[node], gw_node)
        # contains the app id given when register the app by EC
        node_appid.update({node_appname[node] : node})
        apps.append(node_appname[node])

    ec.deploy(gw_node)

    results = {}
    for app in apps:
        print "-- loading image at node {}".format(node_appid[app])
        ec.deploy(app)
        ec.wait_finished(app)
        
    results = {}
    for app in apps:
        stdout    = remove_special(ec.trace(app, "stdout"))
        exitcode  = remove_special(ec.trace(app, 'exitcode'))
        results.update({ node_appid[app] : {'exit' : exitcode, 'stdout' : stdout}})
    
    ec.shutdown()

    for key_node in sorted(results):
        if '0' in results[key_node]['exit']:
            # imprement thread for improvements and check in parallel
            ans = check_if_node_answer(key_node, connection_info, 2, 30)
            results.update(ans)

    if show_results:
        print_results(results, 'loaded')

    return results


def reset(nodes, connection_info, show_results=True):
    """ Reset all nodes from the list """
    ec    = ExperimentController(exp_id="reset")
    nodes = check_node_name(nodes)
    
    gw_node = ec.register_resource("linux::Node")
    ec.set(gw_node, "hostname", connection_info['gateway'])
    ec.set(gw_node, "username", connection_info['gateway_username'])
    ec.set(gw_node, "identity", connection_info['identity'])
    ec.set(gw_node, "cleanExperiment", True)
    ec.set(gw_node, "cleanProcesses", False)
    ec.set(gw_node, "cleanProcessesAfter", False)

    node_appname = {}
    node_appid   = {}
    apps         = []

    for node in nodes:
        on_cmd_a = "curl 192.168.1.{}/reset".format(node) 
        node_appname.update({node : 'app_{}'.format(node)}) 
        node_appname[node] = ec.register_resource("linux::Application")
        ec.set(node_appname[node], "command", on_cmd_a)
        ec.register_connection(node_appname[node], gw_node)
        # contains the app id given when register the app by EC
        node_appid.update({node_appname[node] : node})
        apps.append(node_appname[node])

    ec.deploy(gw_node)

    results = {}
    for app in apps:
        print "-- restarting node {}".format(node_appid[app])
        ec.deploy(app)
        ec.wait_finished(app)
        
        stdout    = remove_special(ec.trace(app, "stdout"))
        exitcode  = remove_special(ec.trace(app, 'exitcode'))
        results.update({ node_appid[app] : {'exit' : exitcode, 'stdout' : stdout}})

    ec.shutdown()
    
    for key_node in sorted(results):
        if '0' in results[key_node]['exit']:
            ans = check_if_node_answer(key_node, connection_info)
            results.update(ans)

    if show_results:
        print_results(results, 'reset')

    return results


def alive(nodes, connection_info, show_results=True):
    """ Check if a node answer a ping command """
    ec    = ExperimentController(exp_id="alive")
    nodes = check_node_name(nodes)

    gw_node = ec.register_resource("linux::Node")
    ec.set(gw_node, "hostname", connection_info['gateway'])
    ec.set(gw_node, "username", connection_info['gateway_username'])
    ec.set(gw_node, "identity", connection_info['identity'])
    ec.set(gw_node, "cleanExperiment", True)
    ec.set(gw_node, "cleanProcesses", False)
    ec.set(gw_node, "cleanProcessesAfter", False)

    node_appname = {}
    node_appid   = {}
    apps         = []

    for node in nodes:
        on_cmd_a = "ping -c1 192.168.1.{}".format(node) 
        node_appname.update({node : 'app_{}'.format(node)}) 
        node_appname[node] = ec.register_resource("linux::Application")
        ec.set(node_appname[node], "command", on_cmd_a)
        ec.register_connection(node_appname[node], gw_node)
        # contains the app id given when register the app by EC
        node_appid.update({node_appname[node] : node})
        apps.append(node_appname[node])

    ec.deploy(gw_node)

    ec.deploy(apps)
    ec.wait_finished(apps) 

    #ec.register_condition(sender_app, ResourceAction.START, receiver_app, ResourceState.STARTED) 

    results = {}
    for app in apps:
        stdout    = remove_special(ec.trace(app, "stdout"))
        exitcode  = remove_special(ec.trace(app, 'exitcode'))
        results.update({ node_appid[app] : {'exit' : exitcode, 'stdout' : stdout}})

    ec.shutdown()

    if show_results:
        print_results(results, 'alive')

    return results


def status(nodes, connection_info, show_results=True):
    """ Check the status of all nodes from the list """
    return multiple_action(nodes, connection_info, 'status')


def on(nodes, connection_info, show_results=True):
    """ Turn on all nodes from the list """
    return multiple_action(nodes, connection_info, 'on')


def off(nodes, connection_info, show_results=True):
    """ Turn off all nodes from the list """
    return multiple_action(nodes, connection_info, 'off')


def multiple_action(nodes, connection_info, action, show_results=True):
    """ Execute the command in all nodes from the list """
    ec    = ExperimentController(exp_id=action)
    nodes = check_node_name(nodes)

    gw_node = ec.register_resource("linux::Node")
    ec.set(gw_node, "hostname", connection_info['gateway'])
    ec.set(gw_node, "username", connection_info['gateway_username'])
    ec.set(gw_node, "identity", connection_info['identity'])
    ec.set(gw_node, "cleanExperiment", True)
    ec.set(gw_node, "cleanProcesses", False)
    ec.set(gw_node, "cleanProcessesAfter", False)

    node_appname = {}
    node_appid   = {}
    apps         = []

    for node in nodes:
        on_cmd_a = "curl 192.168.1.{}/{}".format(node, action) 
        node_appname.update({node : 'app_{}'.format(node)}) 
        node_appname[node] = ec.register_resource("linux::Application")
        ec.set(node_appname[node], "command", on_cmd_a)
        ec.register_connection(node_appname[node], gw_node)
        # contains the app id given when register the app by EC
        node_appid.update({node_appname[node] : node})
        apps.append(node_appname[node])

    ec.deploy(gw_node)

    ec.deploy(apps)
    ec.wait_finished(apps) 

    results = {}
    for app in apps:
        stdout    = remove_special(ec.trace(app, "stdout"))
        exitcode  = remove_special(ec.trace(app, 'exitcode'))
        results.update({ node_appid[app] : {'exit' : exitcode, 'stdout' : stdout}})

    ec.shutdown()
    
    if show_results:
        print_results(results, action, True)

    return results

def remove_special(str):
    """ Remove special caracters from a string """
    if str is not None:
        new_str = str.replace('\n', '').replace('\r', '').lower()
        #new_str = re.sub('[^A-Za-z0-9]+', ' ', str)
    else:
        new_str = ''

    return new_str


def ip_node(alias):
    """ Returns the ip from the node alias [fitXX] """
    prefix = '192.168.1.xx'
    alias = alias.lower().replace('fit', '')

    try:
        int(alias)
    except Exception, e:
        raise Exception("error in ip convertion")
    
    ip = prefix.replace('xx', alias)
    return ip


def check_node_name(nodes):
    """ Returns the node without alias format """
    new_nodes = []
    nodes = (map(str,nodes))

    if not type(nodes) is list:
        raise Exception("invalid paramenter: {}, must be a list".format(nodes))
        return False
    for node in nodes:
        if "fit" in node:
            new_nodes.append(number_node(node))
        else:
            new_nodes.append(int(node))

    return new_nodes


def number_node(alias):
    """ Returns the number from the node alias [fitXX] """
    node = alias.lower().replace('fit', '')
    
    return int(node)

def valid_version(version):
    """ Check if the version to load """
    versions = ['u1410', 'u1504', 'f21']
    if version not in versions:
        raise Exception("invalid version, must be {}".format(versions))
        return False
    else:
        return version

def print_results(results, action=None, stdout=False):
    """ Print the results in a summary way"""
    print "+ + + + + + + + + "
    if results:
        for key in sorted(results):
            if not results[key]['exit']:
                new_result = 'fail'
            elif int(results[key]['exit']) > 0:
                new_result = 'fail'
            else:
                if stdout:
                    new_result = results[key]['stdout']
                else:
                    new_result = action
            print "node {:02}: {}".format(key, new_result)
    else:
        print "-- no results to show"
    print "+ + + + + + + + +"


def check_if_node_answer(node, connection_info, times=2, wait_for=10):
    results = {}
    turn = 0
    for n in range(times):
        turn += 1
        print "-- attempt #{} for node {}".format(n+1, node)
                
        ans = alive([node], connection_info, False)
        if '0' in ans[node]['exit']:
            results.update(ans)
            break
        else:
            if times > turn:
                print "-- waiting for a while for new attempt"
                wait_and_update_progress_bar(wait_for)

    return results


def wait_and_update_progress_bar(wait_for):
    for n in range(wait_for):
        time.sleep(1)
        print '\b.',
        sys.stdout.flush()
    print ""
