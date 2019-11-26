import argparse
import sre_yield
import natsort
from ruamel.yaml import YAML
import copy
import sys


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(
        prog='fpga_port2pin_mapper',
        description="Program for automatic mapping of ports to pins in FPGA designs. Especially useful when signals "
                    "propagate through multiple PCBs. It is capable of simple regex expanding and applies natural "
                    "(human) sort for pairing generated keys and values."
    )

    parser.add_argument('connection', help="File describing connection between ports and ends defined in the map chain.")
    parser.add_argument('map_chain', help="Chain (list) of yaml files describing mappings. Different levels of "
                                          "mapping are separated by commas ','. Each level can consist of multiple "
                                          "files. In such case use square brackets '[]' to group them. Lists can be "
                                          "nested. Example: 'level_1,[level_2_1,[level_2_2_1,level_2_2_2]],level_3'."
                                          "The chain must start with mapping of FPGA pins and should end with mapping"
                                          " of terminal pins (in short, it is user responsibility to preserve "
                                          "the correct order of mappings when invoking the program.")
    parser.add_argument('output_file', help="Output constraints file destination.")

    return parser.parse_args()


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

        for k, v in map_dict.items():
            aux = get_mapping_from_entry(k, v)
            l1 = len(aux)
            l2 = len(mapping)
            mapping.update(aux)
            l3 = len(mapping)
            if l1 + l2 != l3:
                print(f"Conflict in keys names after mapping entry: {k}, file: {file}")
                sys.exit(1)

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
                    print(f"Conflict in keys names after mapping entry: {k}, file: {file}")
                    sys.exit(1)

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


def map_chain_sanity_check(chain_string):
    if chain_string.count('[') != chain_string.count(']'):
        print("Inconsistent number of '[' and ']' in map_chain string")
        sys.exit(1)


def prepare_map_chain(chain_string):

    chain_list, _ = parse_chain_list_string(chain_string)

    map_chain = []
    for link in chain_list:
        if type(link) is not list:
            link = [link]
        map_chain.append(prepare_chain_link(link))

    pass
    return map_chain


def resolve_map_chain(map_chain):
    pins = list(map_chain[0].keys())

    mapping = {}

    for pin in pins:
        key = pin

        aux = {'pin': pin}

        for i in range(0, len(map_chain)):
            if key not in map_chain[i]:
                break

            if 'terminal' in map_chain[i][key]:
                if 'terminal' in aux:
                    print(f"ERROR: Trying to map to the terminal end: '{key}', map chain level: {i}")
                    sys.exit(1)
                else:
                    aux['terminal'] = None

            key = map_chain[i][key]['end']

        mapping[key] = aux

    return mapping


def read_connection_file(file):
    with open(file) as f:
        yaml = YAML(typ='safe')
        mapping = yaml.load(f)

    global_settings = mapping.pop('__global__', None)
    if global_settings is not None:
        for port in mapping:
            for k, v in global_settings.items():
                if k in mapping[port]:
                    aux = mapping[port][k]
                    mapping[port][k] = copy.deepcopy(v)
                    mapping[port][k].update(aux)
                else:
                    mapping[port][k] = v

    connection = {}
    for k, v in mapping.items():
        aux = get_mapping_from_entry(k, v)
        l1 = len(aux)
        l2 = len(connection)
        connection.update(aux)
        l3 = len(connection)
        if l1 + l2 != l3:
            print(f"Conflict in keys names after mapping port: {k}, file: {file}")
            sys.exit(1)

    return connection


def map_ports_to_pins(connection, mapping):
    found_violation = False

    for k in connection:

        end = connection[k]['end']
        m = mapping.pop(end, None)

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


def main():
    args = parse_command_line_arguments()

    connection = read_connection_file(args.connection)

    map_chain_sanity_check(args.map_chain)
    map_chain = prepare_map_chain(args.map_chain)
    mapping = resolve_map_chain(map_chain)

    connection = map_ports_to_pins(connection, mapping)

    generate_constraint_file(connection, args.output_file)
    pass


if __name__ == '__main__':
    main()
