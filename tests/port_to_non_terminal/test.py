import unittest
import subprocess


class Test(unittest.TestCase):
    def test(self):
        expected = ""

        path = "./tests/port_to_non_terminal/"
        map_chain = f"{path}l_1.yaml,[{path}l_2_1.yaml,[{path}l_2_2_1.yaml,{path}l_2_2_2.yaml]]"
        actual = subprocess.check_output(['python',
                                          'fpga_port2pin_mapper.py',
                                          f"{path}connection.yaml",
                                          map_chain,
                                          'tmp.xdc'])
        self.assertEqual(expected, actual)
