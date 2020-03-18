import unittest
import subprocess


class Test(unittest.TestCase):
    def test(self):
        expected = """WARNING: Port 'port_1' mapped to pin 'A1' connected to non terminal end 'endpoint_1'!
WARNING: Port 'port_2' mapped to pin 'A2' connected to non terminal end 'endpoint_2'!
WARNING: Port 'port_3' mapped to pin 'A3' connected to non terminal end 'endpoint_3'!
"""

        path = "./tests/port_to_non_terminal/"
        map_chain = f"{path}l_1.yaml,[{path}l_2_1.yaml,[{path}l_2_2_1.yaml,{path}l_2_2_2]]"
        actual = subprocess.check_output(['python',
                                          'fpga_port2pin_mapper.py',
                                          'map',
                                          f"{path}connection.yaml",
                                          map_chain,
                                          'tmp.xdc'])
        actual = str(actual.decode('utf-8'))
        self.assertEqual(expected, actual)
