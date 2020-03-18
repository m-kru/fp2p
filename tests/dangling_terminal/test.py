import unittest
import subprocess


class Test(unittest.TestCase):
    def test(self):

        expected = """ERROR: Dangling terminal, key: s5, map chain node: 1
ERROR: Dangling terminal, key: s6, map chain node: 1\n"""

        path = "./tests/dangling_terminal/"
        map_chain = f"{path}l_1.yaml,[{path}l_2_1.yaml,[{path}l_2_2_1.yaml,{path}l_2_2_2.yaml]]"

        actual = ''
        try:
            actual = subprocess.check_output(['python',
                                              'fpga_port2pin_mapper.py',
                                              'map',
                                              f"{path}connection.yaml",
                                              map_chain,
                                              'tmp.xdc'])
            raise Exception("This subprocess must fail!")
        except Exception as e:
            actual = e.output

        actual = str(actual.decode('utf-8'))
        self.assertEqual(expected, actual)
