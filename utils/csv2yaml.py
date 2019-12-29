import argparse


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(
        prog='csv2yaml',
        description="Simple script for converting csv files to yaml files needed by fpga_port2pin_mapper."
    )

    parser.add_argument('csv_file', help="Input csv file.")
    parser.add_argument('--sep', default=',', choices=[',', ';'], help="CSV separator.")
    parser.add_argument('--reverse', action='store_true', help="Reverse csv columns.")
    parser.add_argument('-o', help="Output yaml file.")

    return parser.parse_args()


def main():
    args = parse_command_line_arguments()

    yaml_content = ""

    with open(args.csv_file, 'r') as f:
        for line in f:
            if line == '\n' or line[0] == '#':
                continue

            key = line.split(args.sep)[0].strip()
            end = line.split(args.sep)[1].strip()

            if args.reverse:
                aux = key
                key = end
                end = aux

            yaml_content += key + ':\n  ' + 'end: ' + end + '\n'

    if args.o:
        with open(args.o, 'w') as y:
            y.write(yaml_content)
    else:
        print(yaml_content)


if __name__ == "__main__":
    main()
