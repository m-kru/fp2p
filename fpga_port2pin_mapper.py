import argparse
import sre_yield
import copy
import sys
import pprint

import natsort
from ruamel.yaml import YAML


def print_and_exit(msg):
    print(msg)
    sys.exit(1)


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(
        prog='fpga_port2pin_mapper',
        description="Program for automatic mapping of ports to pins in FPGA designs. Especially useful when signals "
                    "propagate through multiple PCBs. It is capable of simple regex expanding and applies natural "
                    "(human) sort for pairing generated keys and values."
    )

    subparsers = parser.add_subparsers()

    map_chain_help = """Chain (list) of yaml files describing mappings. Different nodes of
                        mapping are separated by commas ','. Each node can consist of multiple
                        files. In such case use square brackets '[]' to group them. Lists can be
                        nested. Example: 'node_1,[node_2_1,[node_2_2_1,node_2_2_2]],node_3'.
                        The chain must start with mapping of FPGA pins and should end with mapping
                        of terminal pins (in short, it is user responsibility to preserve
                        the correct order of mappings when invoking the program."""

    map_tree_help = "Yaml file describing mapping tree."

    resolve_parser = subparsers.add_parser("resolve", help="Only resolve mapping and print the result.")
    resolve_parser.add_argument('map_tree', help=map_tree_help)
    resolve_parser.set_defaults(func=resolve)

    map_parser = subparsers.add_parser("map", help="Map ports to pins.")
    map_parser.add_argument('connection', help="File describing connection between ports and terminal pins defined in the map chain.")
    map_parser.add_argument('map_tree', help=map_chain_help)
    map_parser.add_argument('output_file', help="Output constraints file destination.")
    map_parser.set_defaults(func=map)

    return parser.parse_args()


def set_default_parameters(mapping):
    common_settings = mapping.pop('default', None)
    if common_settings is not None:
        for port in mapping:
            for k, v in common_settings.items():
                if k in mapping[port]:
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
        if 'prefix' in mapping[port]:
            new_key = mapping[port]['prefix'] + new_key
            _ = mapping[port].pop('prefix', None)

        new_mapping[new_key] = mapping[port]

    return new_mapping


def get_mapping_from_entry(key, value):
    if 'regex' not in value:
        return {key: value}

    keys = list(sre_yield.AllStrings(key))
    ends = list(sre_yield.AllStrings(value['end']))

    if len(keys) != len(ends):
        raise BaseException("Different lengths of lists after regex expansion for key: " + key + " end: " + value['end'])

    keys = natsort.natsorted(keys)
    ends = natsort.natsorted(ends)

    mapping = {}
    for k, e in zip(keys, ends):
        aux = copy.deepcopy(value)
        aux['end'] = e
        mapping[k] = aux

    return mapping


def get_mapping_from_file(file):
    mapping = {}

    yaml = YAML(typ='safe')

    with open(file) as f:
        map_dict = yaml.load(f)

    map_dict = set_default_parameters(map_dict)
    map_dict = apply_prefix_parameter(map_dict)

    for k, v in map_dict.items():
        aux = get_mapping_from_entry(k, v)
        l1 = len(aux)
        l2 = len(mapping)
        mapping.update(aux)
        l3 = len(mapping)
        if l1 + l2 != l3:
            print_and_exit(f"ERROR: Conflict in keys names after mapping entry: {k}, file: {file}")

    return mapping


def prepare_chain_link(files):
    link = {}

    for file in files:
        if type(file) is list:
            link.update(prepare_chain_link(file))
        else:
            aux = get_mapping_from_file(file)

            for k in aux:
                if k in link:
                    print_and_exit(f"ERROR: Conflict in keys names after mapping entry: {k}, file: {file}")

            link.update(aux)

    return link


def parse_chain_list_string(chain_string):
    list = []

    file = ''
    while True:
        if not chain_string:
            if file:
                list.append(file)
            break

        c = chain_string[0]
        chain_string = chain_string[1:]

        if c == ',':
            if file:
                list.append(file)
            file = ''
        elif c == '[':
            l, chain_string = parse_chain_list_string(chain_string)
            list.append(l)
        elif c == ']':
            if file:
                list.append(file)
            break
        else:
            file += c

    return list, chain_string


found_node_names = []


def map_tree_sanity_check(node):
    if 'files' not in node:
        raise BaseException(f"Missing 'files' key in node : {node['name']}")
    else:
        if not node['files']:
            raise BaseException(f"Found empty files list in node: {node['name']}")

    for key, val in node.items():
        if key == 'name':
            if val in found_node_names:
                raise BaseException(f"Duplicated node name: {val}")
            found_node_names.append(val)
        elif key == 'nodes':
            if not val:
                print_and_exit(f"ERROR: Found empty nodes list in node '{node['name']}'.")

            for node in val:
                map_tree_sanity_check(node)


mapping_files = set()


def get_mapping_files(node):
    for f in node['files']:
        mapping_files.add(f)

    if 'nodes' in node:
        if node['nodes']:
            for node in node['nodes']:
                get_mapping_files(node)
        else:
            raise BaseException(f"Found empty nodes list in node: {node['name']}")

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
                print_and_exit(f"ERROR: Conflicting key '{k}' in node {node['name']}")

    nodes_mappings[node['name']] = nm

    if 'nodes' in node:
        if node['nodes']:
            for node in node['nodes']:
                get_nodes_mappings(node)
        else:
            raise BaseException(f"Found empty nodes list in node: {node['name']}")

    return nodes_mappings


def nodes_mappings_sanity_check(node):
    """
    This function checks ensures that nodes having the same parent have unique keys.
    In such case the mapping would be ambiguous.
    It would be possible to explicitly define to which node the end should be connected, however this approach is rigid
    to specific design and any reuse of mapping files would be tedious and time consuming.
    """
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
                print_and_exit(f"ERROR: key '{k}' found in 2 nodes: {unique_keys[k]} and {name} having the same parent.")


def prepare_map_chain(chain_string):

    chain_list, _ = parse_chain_list_string(chain_string)

    map_chain = []
    for link in chain_list:
        if type(link) is not list:
            link = [link]
        map_chain.append(prepare_chain_link(link))

    pass
    return map_chain


def detect_dangling_terminals(map_chain):
    violations_found = False

    for i in range(0, len(map_chain)):
        for k in map_chain[i]:
            if 'terminal' in map_chain[i][k]:
                print(f"ERROR: Dangling terminal, key: {k}, map chain node: {i}")
                violations_found = True
        pass

    if violations_found:
        sys.exit(1)


def resolve_single_mapping(mapping, node):
    end = mapping['end']

    node_map = nodes_mappings[node['name']]

    if end in node_map:
        if 'terminal' in mapping:
            print_and_exit(f"ERROR: Trying to map to the terminal end: '{mapping['end']}', file: {f}")
            sys.exit(1)

        mapping['end'] = node_map[end]['end']
        mapping['node_name'] = node['name']

        if 'terminal' in node_map[end]:
            mapping['terminal'] = None

        if 'nodes' in node:
            for node in node['nodes']:
                mapping = resolve_single_mapping(mapping, node)

    return mapping


def resolve_map_tree(map_tree):
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
#    detect_dangling_terminals(map_chain)

    return mapping


def read_connection_file(file):
    with open(file) as f:
        yaml = YAML(typ='safe')
        mapping = yaml.load(f)

    mapping = set_default_parameters(mapping)

    connection = {}
    for k, v in mapping.items():
        aux = get_mapping_from_entry(k, v)
        l1 = len(aux)
        l2 = len(connection)
        connection.update(aux)
        l3 = len(connection)
        if l1 + l2 != l3:
            print_and_exit(f"ERROR: Conflict in keys names after mapping port: {k}, file: {file}")

    return connection


def map_ports_to_pins(connection, mapping):
    found_violation = False

    for k in connection:

        node = connection[k]['node']
        end = connection[k]['end']

        try:
            m = mapping[node].pop(end, None)
        except KeyError:
            print_and_exit(f"ERROR: Node with name '{node}' not found!")

        if m is None:
            print(f"ERROR: Port '{k}' connected to missing end '{end}'!")
            found_violation = True
            continue

        connection[k]['fpga_pin'] = m['pin']
        if 'terminal' not in m:
            print(f"WARNING: Port '{k}' mapped to pin '{m['pin']}' connected to non terminal end '{end}'!")

    if found_violation:
        sys.exit(1)

    # If there are any terminal ends left, report it as error and exit.
    for k, v in mapping.items():
        if 'terminal' in v:
            print(f"ERROR: Terminal end '{k}', connected to pin '{v['pin']}' is not mapped to any port!")
            found_violation = True

    if found_violation:
        sys.exit(1)

    return connection


def generate_constraint_file(connection, file):
    with open(file, 'w') as f:
        for k, v in connection.items():
            pass
            f.write("set_property PACKAGE_PIN %s [get_ports {%s}]\n" % (v['fpga_pin'], k))
            if 'set_property' in v:
                for k1, v1 in v['set_property'].items():
                    f.write("set_property %s %s [get_ports {%s}]\n" % (k1, v1, k))
            f.write("\n")


def resolve(mapping, args):
    pprint.pprint(mapping)


def map(mapping, args):
    connection = read_connection_file(args.connection)
    connection = map_ports_to_pins(connection, mapping)
    generate_constraint_file(connection, args.output_file)


def main():
    args = parse_command_line_arguments()

    with open(args.map_tree) as f:
        yaml = YAML(typ='safe')
        map_tree = yaml.load(f)

    map_tree_sanity_check(map_tree)

    get_mapping_files(map_tree)
    get_file_mappings()
    get_nodes_mappings(map_tree)
    nodes_mappings_sanity_check(map_tree)

#    map_chain = prepare_map_chain(args.map_chain) to omijam bo jest w pliku teraz zdefiniowane

    mapping = resolve_map_tree(map_tree)

    args.func(mapping, args)
    pass


if __name__ == '__main__':
    main()
