import unittest
import fpga_port2pin_mapper


class Test(unittest.TestCase):
    def test(self):
        expected = ['l1', 'l2', 'l3']

        chain_string = "l1,l2,l3"
        actual, _ = fpga_port2pin_mapper.parse_chain_list_string(chain_string)
        self.assertEqual(expected, actual)

    def test_1_nested_list(self):
        expected = ['l1', ['l2', 'l3'], 'l4']

        chain_string = "l1,[l2,l3],l4"
        actual, _ = fpga_port2pin_mapper.parse_chain_list_string(chain_string)
        self.assertEqual(expected, actual)

    def test_2_nested_list(self):
        expected = ['l1', ['l2', ['l3_1', 'l3_2']], 'l4']

        chain_string = "l1,[l2,[l3_1,l3_2]],l4"
        actual, _ = fpga_port2pin_mapper.parse_chain_list_string(chain_string)
        self.assertEqual(expected, actual)

        expected = ['l1', ['l2', ['l3_1', 'l3_2']]]
        chain_string = "l1,[l2,[l3_1,l3_2]]"
        actual, _ = fpga_port2pin_mapper.parse_chain_list_string(chain_string)
        self.assertEqual(expected, actual)

    def test_with_paths(self):
        expected = ['./tmp/l1', ['./tmp/l2', ['./tmp/l3_1', './tmp/l3_2']], './tmp/l4']

        chain_string = "./tmp/l1,[./tmp/l2,[./tmp/l3_1,./tmp/l3_2]],./tmp/l4"
        actual, _ = fpga_port2pin_mapper.parse_chain_list_string(chain_string)
        self.assertEqual(expected, actual)
