"""
SPDX-License-Identifier: GPL-2.0

Copyright (c) 2020 Michał Kruszewski
"""

import argparse
import sre_yield
import copy
import sys
import pprint

import natsort
from ruamel.yaml import YAML


def error_and_exit(msg):
    print("\033[91mERROR\033[0m: " + msg)
    sys.exit(1)


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(
        prog="fp2p",
        description="Program for automatic assignment of ports to pins in FPGA designs. Especially useful when signals "
        "propagate through multiple PCBs. It is capable of simple regex expanding and applies natural "
        "(human) sort for pairing generated keys and values.",
    )

    subparsers = parser.add_subparsers()

    tree_help = "Yaml file describing mapping tree."

    resolve_parser = subparsers.add_parser(
        "resolve", help="Only resolve mapping tree and print the result."
    )
    resolve_parser.add_argument("tree_file", help=tree_help)
    resolve_parser.set_defaults(func=resolve)

    assign_parser = subparsers.add_parser("assign", help="Assign ports to pins.")
    assign_parser.add_argument(
        "assignment_file",
        help="YAML file describing assignment for ports and terminal pins defined in the mapping tree.",
    )
    assign_parser.add_argument("tree_file", help=tree_help)
    assign_parser.add_argument(
        "output_file", help="Output constraints file destination."
    )
    assign_parser.set_defaults(func=assign)

    return parser.parse_args()


def set_default_parameters(mapping):
    common_settings = mapping.pop("_default_", None)
    if common_settings is not None:
        for port in mapping:
            for k, v in common_settings.items():
                if k in mapping[port]:
                    if type(v) is dict:
                        aux = mapping[port][k]
                        mapping[port][k] = copy.deepcopy(v)
                        mapping[port][k].update(aux)
                else:
                    mapping[port][k] = v

    return mapping


def apply_prefix_parameter(mapping):
    new_mapping = {}

    for port in mapping:
        new_key = port
        if "prefix" in mapping[port]:
            new_key = mapping[port]["prefix"] + new_key
            _ = mapping[port].pop("prefix", None)

        new_mapping[new_key] = mapping[port]

    return new_mapping


def apply_suffix_parameter(mapping):
    new_mapping = {}

    for port in mapping:
        new_key = port
        if "suffix" in mapping[port]:
            new_key = new_key + mapping[port]["suffix"]
            _ = mapping[port].pop("suffix", None)

        new_mapping[new_key] = mapping[port]

    return new_mapping


def get_mapping_from_entry(key, value):
    if "regex" not in value or value["regex"] == False:
        return {key: value}

    keys = list(sre_yield.AllStrings(key))
    ends = list(sre_yield.AllStrings(value["end"]))

    if len(keys) != len(ends):
        error_and_exit(
            f"Different lengths of lists after regex expansion for key: {key} end: {value['end']}"
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

    yaml = YAML(typ="safe")

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
                f"Conflict in keys names after mapping entry: {k}, file: {file}"
            )

    return mapping


found_node_names = []


def map_tree_sanity_check(node):
    if "files" not in node:
        error_and_exit(f"Missing 'files' key in node {node['name']}")
    else:
        if not node["files"]:
            error_and_exit(f"Found empty files list in node: {node['name']}")

    for key, val in node.items():
        if key == "name":
            if val in found_node_names:
                error_and_exit(f"Duplicated node name: {val}")
            found_node_names.append(val)
        elif key == "nodes":
            if not val:
                error_and_exit(f"Found empty nodes list in node '{node['name']}'.")

            for node in val:
                map_tree_sanity_check(node)


mapping_files = set()


def get_mapping_files(node):
    for f in node["files"]:
        mapping_files.add(f)

    if "nodes" in node:
        if node["nodes"]:
            for node in node["nodes"]:
                get_mapping_files(node)
        else:
            error_and_exit(f"Found empty nodes list in node: {node['name']}")

    return mapping_files


files_mappings = {}


def get_file_mappings():
    for f in mapping_files:
        files_mappings[f] = get_mapping_from_file(f)


nodes_mappings = {}


def get_nodes_mappings(node):
    nm = {}

    for f in node["files"]:
        fm = files_mappings[f]
        for k, v in fm.items():
            if k not in nm:
                nm[k] = v
            else:
                error_and_exit(f"Conflicting key '{k}' in node {node['name']}")

    nodes_mappings[node["name"]] = nm

    if "nodes" in node:
        if node["nodes"]:
            for node in node["nodes"]:
                get_nodes_mappings(node)
        else:
            error_and_exit(f"Found empty nodes list in node: {node['name']}")

    return nodes_mappings


def nodes_mappings_sanity_check(node):
    """
    This function checks ensures that nodes having the same parent have unique keys.
    In such case the mapping would be ambiguous.
    It would be possible to explicitly define to which node the end should be connected, however this approach is rigid
    to specific design and any reuse of mapping files would be tedious and time consuming.
    """
    if "nodes" not in node:
        return

    nodes_to_check = []
    for node in node["nodes"]:
        nodes_to_check.append(node["name"])

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
                    f"key '{k}' found in 2 nodes: {unique_keys[k]} and {name} having the same parent."
                )


def detect_dangling_terminals():
    for k, v in nodes_mappings.items():
        for _, b in v.items():
            if "terminal" in b and b["terminal"] != False:
                if "_touched" not in b:
                    error_and_exit(
                        f"Terminal end '{b['end']}' within node '{k}' is not mapped to any pin!"
                    )


def resolve_single_mapping(mapping, node):
    end = mapping["end"]

    node_map = nodes_mappings[node["name"]]

    if end in node_map:
        if "terminal" in mapping:
            error_and_exit(
                f"Trying to map to the terminal end: '{mapping['end']}', file: {f}"
            )

        mapping["end"] = node_map[end]["end"]
        node_map[end]["_touched"] = True
        mapping["node_name"] = node["name"]

        if "terminal" in node_map[end]:
            mapping["terminal"] = None

        if "nodes" in node:
            for node in node["nodes"]:
                mapping = resolve_single_mapping(mapping, node)

    return mapping


def resolve_mapping_tree(map_tree):
    pins = []
    keys = nodes_mappings[map_tree["name"]].keys()
    for p in keys:
        pins.append(p)

    mapping = {}

    for pin in pins:
        m = {"pin": pin, "node_name": None, "end": pin}
        m = resolve_single_mapping(m, map_tree)

        key = m["node_name"]
        if key not in mapping:
            mapping[key] = {}

        del m["node_name"]

        end = m["end"]
        del m["end"]

        mapping[key][end] = m

    return mapping


def read_assignment_file(file):
    with open(file) as f:
        yaml = YAML(typ="safe")
        mapping = yaml.load(f)

    mapping = set_default_parameters(mapping)
    mapping = apply_prefix_parameter(mapping)
    mapping = apply_suffix_parameter(mapping)

    connection = {}
    for k, v in mapping.items():
        aux = get_mapping_from_entry(k, v)
        l1 = len(aux)
        l2 = len(connection)
        connection.update(aux)
        l3 = len(connection)
        if l1 + l2 != l3:
            error_and_exit(
                f"Conflict in keys names after mapping port: {k}, file: {file}"
            )

    return connection


def assign_ports_to_pins(connection, mapping):
    found_violation = False

    for k in connection:
        if "node" not in connection[k]:
            error_and_exit(f"Assignment {k} misses destination node!")

        node = connection[k]["node"]
        end = connection[k]["end"]

        try:
            m = mapping[node].pop(end, None)
        except KeyError:
            error_and_exit(f"Node with name '{node}' not found!")

        if m is None:
            error_and_exit(f"Port '{k}' assigned to missing end '{end}'!")
            found_violation = True
            continue

        connection[k]["fpga_pin"] = m["pin"]
        if "terminal" not in m:
            error_and_exit(
                f"Port '{k}' assigned to pin '{m['pin']}' mapped to non terminal end '{end}' within node '{node}'!"
            )

    if found_violation:
        sys.exit(1)

    # If there are any terminal ends left, report it as error and exit.
    for k, v in mapping.items():
        if "terminal" in v:
            print(
                f"ERROR: Terminal end '{k}', connected to pin '{v['pin']}' is not mapped to any port!"
            )
            found_violation = True

    if found_violation:
        sys.exit(1)

    return connection


def generate_constraint_file(connection, file):
    with open(file, "w") as f:
        f.write("# This file has been auto generated by the fp2p tool.\n")
        f.write("# Do not modify it by hand!\n")
        f.write("# More information on the website https://github.com/m-kru/fp2p.\n\n")

        for k, v in connection.items():
            pass
            f.write(
                "set_property PACKAGE_PIN %s [get_ports {%s}]\n" % (v["fpga_pin"], k)
            )
            if "set_property" in v:
                for k1, v1 in v["set_property"].items():
                    f.write("set_property %s %s [get_ports {%s}]\n" % (k1, v1, k))
            f.write("\n")


def resolve(mapping, args):
    pprint.pprint(mapping)


def assign(resolved_tree, args):
    connection = read_assignment_file(args.assignment_file)
    connection = assign_ports_to_pins(connection, resolved_tree)
    generate_constraint_file(connection, args.output_file)


def main():
    args = parse_command_line_arguments()

    with open(args.tree_file) as f:
        yaml = YAML(typ="safe")
        map_tree = yaml.load(f)

    map_tree_sanity_check(map_tree)

    get_mapping_files(map_tree)
    get_file_mappings()
    get_nodes_mappings(map_tree)
    nodes_mappings_sanity_check(map_tree)

    resolved_tree = resolve_mapping_tree(map_tree)
    detect_dangling_terminals()

    args.func(resolved_tree, args)


if __name__ == "__main__":
    main()
