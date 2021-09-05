#!/bin/python3
"""
SPDX-License-Identifier: GPL-2.0

Copyright (c) 2020 Michał Kruszewski
"""

import argparse
import copy
import logging as log
import pprint
import sre_yield
import sys

import natsort
from ruamel.yaml import YAML


def error_and_exit(msg):
    log.error(msg + "!")
    sys.exit(1)


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(
        prog="fp2p",
        description="Program for automatic assignment of ports to pins in FPGA designs. Especially useful when signals "
        "propagate through multiple PCBs. It is capable of simple regex expanding and applies natural "
        "(human) sort for pairing generated keys and values.",
    )

    subparsers = parser.add_subparsers()

    tree_help = "YAML file describing mapping tree."

    assign_parser = subparsers.add_parser("assign", help="Assign ports to pins.")
    assign_parser.add_argument("tree_file", help=tree_help)
    assign_parser.add_argument(
        "assignment_file",
        help="YAML file describing assignment for ports and terminal pins defined in the mapping tree.",
    )
    assign_parser.add_argument(
        "eda_tool", choices=["vivado", "quartus"], help="Target EDA tool."
    )
    assign_parser.set_defaults(func=assign)

    graph_parser = subparsers.add_parser(
        "graph", help="Render graph for tree file. Useful for debugging tree files."
    )
    graph_parser.add_argument("tree_file", help=tree_help)
    graph_parser.set_defaults(func=graph)

    resolve_parser = subparsers.add_parser(
        "resolve", help="Only resolve mapping tree and print the result."
    )
    resolve_parser.add_argument("tree_file", help=tree_help)
    resolve_parser.set_defaults(func=resolve)

    return parser.parse_args()


def set_default_parameters(dict_):
    common_settings = dict_.pop("_default_", None)
    if common_settings is not None:
        for port in dict_:
            for k, v in common_settings.items():
                if k in dict_[port]:
                    if type(v) is dict:
                        aux = dict_[port][k]
                        dict_[port][k] = copy.deepcopy(v)
                        dict_[port][k].update(aux)
                else:
                    dict_[port][k] = v

    return dict_


def apply_prefix_parameter(mapping):
    new_mapping = {}

    for port in mapping:
        new_key = port
        if 'prefix' in mapping[port]:
            new_key = mapping[port]['prefix'] + new_key
            _ = mapping[port].pop('prefix', None)

        new_mapping[new_key] = mapping[port]

    return new_mapping


def apply_suffix_parameter(mapping):
    new_mapping = {}

    for port in mapping:
        new_key = port
        if 'suffix' in mapping[port]:
            new_key = new_key + mapping[port]['suffix']
            _ = mapping[port].pop('suffix', None)

        new_mapping[new_key] = mapping[port]

    return new_mapping


def get_mapping_from_entry(key, value):
    if 'regex' not in value or value['regex'] == False:
        return {key: value}

    keys = list(sre_yield.AllStrings(key))
    ends = list(sre_yield.AllStrings(value['end']))

    if len(keys) != len(ends):
        error_and_exit(
            f"Different lengths of lists after regex expansion for key '{key}' end '{value['end']}'"
        )

    keys = natsort.natsorted(keys)
    ends = natsort.natsorted(ends)

    mapping = {}
    for k, e in zip(keys, ends):
        aux = copy.deepcopy(value)
        aux["end"] = e
        mapping[k] = aux

    return mapping


def get_mapping_from_file(file):
    mapping = {}

    yaml = YAML(typ='safe')

    with open(file) as f:
        map_dict = yaml.load(f)

    map_dict = set_default_parameters(map_dict)
    map_dict = apply_prefix_parameter(map_dict)
    map_dict = apply_suffix_parameter(map_dict)

    for k, v in map_dict.items():
        aux = get_mapping_from_entry(k, v)
        l1 = len(aux)
        l2 = len(mapping)
        mapping.update(aux)
        l3 = len(mapping)
        if l1 + l2 != l3:
            error_and_exit(
                f"Conflict in keys names after mapping entry '{k}', file '{file}'"
            )

    return mapping


found_node_names = []


def tree_sanity_check(node):
    if 'files' not in node:
        error_and_exit(f"Missing 'files' key in node '{node['name']}'")
    else:
        if not node["files"]:
            error_and_exit(f"Found empty files list in node '{node['name']}'")

    for key, val in node.items():
        if key == 'name':
            if val in found_node_names:
                error_and_exit(f"Duplicated node name '{val}'")
            found_node_names.append(val)
        elif key == 'nodes':
            if not val:
                error_and_exit(f"Found empty nodes list in node '{node['name']}'")

            for node in val:
                tree_sanity_check(node)


mapping_files = set()


def get_mapping_files(node):
    if type(node['files']) == str:
        error_and_exit(
            f"Node '{node['name']}' 'files' key value is a string '{node['files']}', expecting list of strings"
        )

    for f in node['files']:
        mapping_files.add(f)

    if 'nodes' in node:
        if node['nodes']:
            for node in node['nodes']:
                get_mapping_files(node)
        else:
            error_and_exit(f"Found empty nodes list in node '{node['name']}'")

    return mapping_files


files_mappings = {}


def get_file_mappings():
    for f in mapping_files:
        files_mappings[f] = get_mapping_from_file(f)


nodes_mappings = {}


def get_nodes_mappings(node):
    nm = {}

    for f in node['files']:
        fm = files_mappings[f]
        for k, v in fm.items():
            if k not in nm:
                nm[k] = v
            else:
                error_and_exit(f"Conflicting key '{k}' within node '{node['name']}'")

    nodes_mappings[node['name']] = nm

    if 'nodes' in node:
        if node['nodes']:
            for node in node['nodes']:
                get_nodes_mappings(node)
        else:
            error_and_exit(f"Found empty nodes list in node '{node['name']}'")

    return nodes_mappings


def nodes_mappings_sanity_check(node):
    """
    This function checks ensures that nodes having the same parent have unique keys.
    In such case the mapping would be ambiguous.
    It would be possible to explicitly define to which node the end should be connected, however this approach is rigid
    to specific design and any reuse of mapping files would be tedious and time consuming.
    """
    if 'nodes' not in node:
        return

    nodes_to_check = []
    for node in node['nodes']:
        nodes_to_check.append(node['name'])

    # Do not check in case of single node as such scenario is checked when node mapping is created.
    if len(nodes_to_check) == 1:
        return

    unique_keys = {}

    for name in nodes_to_check:
        for k in nodes_mappings[name]:
            if k not in unique_keys:
                unique_keys[k] = name
            else:
                error_and_exit(
                    f"key '{k}' found in 2 nodes '{unique_keys[k]}' and '{name}' having the same parent"
                )


def detect_dangling_terminals():
    for k, v in nodes_mappings.items():
        for _, b in v.items():
            if 'terminal' in b and b['terminal'] != False:
                if "_touched" not in b:
                    error_and_exit(
                        f"Terminal end '{b['end']}' within node '{k}' not mapped to any pin"
                    )


def resolve_single_mapping(mapping, node):
    end = mapping['end']

    node_map = nodes_mappings[node['name']]

    if end in node_map:
        if 'terminal' in mapping:
            error_and_exit(
                f"Trying to map to the terminal end '{mapping['end']}' within node '{node['name']}'"
            )

        mapping['end'] = node_map[end]['end']
        node_map[end]['_touched'] = True
        mapping['node_name'] = node['name']

        if 'terminal' in node_map[end]:
            mapping['terminal'] = None

        if 'nodes' in node:
            for node in node['nodes']:
                mapping = resolve_single_mapping(mapping, node)

    return mapping


def resolve_mapping_tree(map_tree):
    pins = []
    keys = nodes_mappings[map_tree['name']].keys()
    for p in keys:
        pins.append(p)

    mapping = {}

    for pin in pins:
        m = {'pin': pin, 'node_name': None, 'end': pin}
        m = resolve_single_mapping(m, map_tree)

        key = m['node_name']
        if key not in mapping:
            mapping[key] = {}

        del m['node_name']

        end = m['end']
        del m['end']

        mapping[key][end] = m

    return mapping


def flatten_assignment_dictionary(assignment):
    flattened = {}

    for node, assignments in assignment.items():
        # Propagate global defaults. They are applied later.
        if node == '_default_':
            flattened[node] = assignments
            continue

        # Set node specific defaults.
        assignments = set_default_parameters(assignments)
        for k, v in assignments.items():
            v['node'] = node
            flattened[k] = v

    return flattened


def read_assignment_file(file_):
    with open(file_) as f:
        yaml = YAML(typ='safe')
        assignment = yaml.load(f)

    assignment = flatten_assignment_dictionary(assignment)
    assignment = set_default_parameters(assignment)
    assignment = apply_prefix_parameter(assignment)
    assignment = apply_suffix_parameter(assignment)

    connection = {}
    for k, v in assignment.items():
        aux = get_mapping_from_entry(k, v)
        l1 = len(aux)
        l2 = len(connection)
        connection.update(aux)
        l3 = len(connection)
        if l1 + l2 != l3:
            error_and_exit(
                f"Conflict in keys names in the assignment file after adding assignment '{k}'"
            )

    return connection


def assign_ports_to_pins(connection, mapping):
    for k in connection:
        try:
            node = connection[k]['node']
        except KeyError:
            error_and_exit(f"Port '{k}' misses destination node")

        try:
            end = connection[k]['end']
        except KeyError:
            error_and_exit(f"Port '{k}' misses destination end")

        try:
            try:
                n = mapping[node]
            except KeyError:
                error_and_exit(f"Node '{node}' not found in the resolved tree")

            m = n[end]
            if '_assigned_to' in m:
                error_and_exit(
                    f"Trying to assign port '{k}' to pin '{m['pin']}' which is already assigned to port '{m['_assigned_to']}'"
                )
            m['_assigned_to'] = k
        except KeyError:
            error_and_exit(
                f"Port '{k}', end '{end}' not found in the resolved tree within node '{node}'"
            )

        if m is None:
            error_and_exit(f"Port '{k}' assigned to missing end '{end}'")

        connection[k]['fpga_pin'] = m['pin']
        if 'terminal' not in m:
            error_and_exit(
                f"Port '{k}' assigned to pin '{m['pin']}' mapped to non terminal end '{end}' within node '{node}'"
            )

    # If there are any terminal ends left, report it as error and exit.
    for k, v in mapping.items():
        if 'terminal' in v:
            error_and_exit(
                f"Terminal end '{k}' connected to pin '{v['pin']}' not mapped to any port"
            )

    return connection


def print_constraint_header(args):
    print("# This file has been auto generated by the fp2p tool.")
    print("# Do not modify it by hand!")
    print("# Files used for generation:")
    print("#   Tree file: {}".format(args.tree_file))
    print("#   Assignment file: {}".format(args.assignment_file))
    print("# More information on the website https://github.com/m-kru/fp2p.")


def vivado_print_constraint_file(connection, args):
    print_constraint_header(args)

    for k, v in connection.items():
        print()
        print("set_property PACKAGE_PIN %s [get_ports {%s}]" % (v["fpga_pin"], k))
        if 'set_property' in v:
            for k1, v1 in v['set_property'].items():
                print("set_property %s %s [get_ports {%s}]" % (k1, v1, k))


def quartus_print_constraint_file(connection, args):
    print_constraint_header(args)

    for k, v in connection.items():
        print()
        print("set_location_assignment %s -to %s" % (v["fpga_pin"], k))
        if 'set_instance_assignment' in v:
            for k1, v1 in v['set_instance_assignment'].items():
                print("set_instance_assignment -name %s %s -to %s" % (k1, v1, k))


def resolve(tree, resolved_tree, args):
    pprint.pprint(resolved_tree)


def add_graph_nodes(dot, node):
    node_label = "<<B>" + node['name'] + "</B><br />"
    for f in node['files']:
        node_label += f + "<br />"
    node_label += ">"
    dot.node(node['name'], label=node_label)

    if 'nodes' in node:
        for n in node['nodes']:
            add_graph_nodes(dot, n)


def add_graph_edges(dot, node):
    if 'nodes' in node:
        for n in node['nodes']:
            dot.edge(node['name'], n['name'])
            add_graph_edges(dot, n)


def graph(tree, resolved_tree, args):
    from graphviz import Digraph

    dot = Digraph(name=args.tree_file.split(".")[0] + ".fp2p")

    add_graph_nodes(dot, tree)
    add_graph_edges(dot, tree)
    dot.render(view=True, cleanup=True)


def detect_unassigned_terminals(mapping):
    for node, aux in mapping.items():
        for end, v in aux.items():
            if 'terminal' in v and v['terminal'] != False:
                if '_assigned_to' not in v:
                    error_and_exit(
                        f"Terminal end '{end}' within node '{node}' not assigned to any port"
                    )


def assign(tree, resolved_tree, args):
    connection = read_assignment_file(args.assignment_file)
    connection = assign_ports_to_pins(connection, resolved_tree)
    detect_unassigned_terminals(resolved_tree)

    if args.eda_tool == 'vivado':
        vivado_print_constraint_file(connection, args)
    elif args.eda_tool == 'quartus':
        quartus_print_constraint_file(connection, args)


def main():
    log.basicConfig(
        level=log.ERROR, format="%(levelname)s: %(message)s", stream=sys.stderr
    )

    args = parse_command_line_arguments()

    with open(args.tree_file) as f:
        yaml = YAML(typ='safe')
        tree = yaml.load(f)

    tree_sanity_check(tree)

    get_mapping_files(tree)
    get_file_mappings()
    get_nodes_mappings(tree)
    nodes_mappings_sanity_check(tree)

    resolved_tree = resolve_mapping_tree(tree)
    detect_dangling_terminals()

    args.func(tree, resolved_tree, args)


if __name__ == "__main__":
    main()
