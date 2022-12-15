import unittest
from .al_general import ALIndividual, ALAddress


class test_aladdress(unittest.TestCase):
    def test_empty_is_empty(self):
        addr = ALAddress(address="", city="")
        self.assertEqual(addr.on_one_line(), "")


if __name__ == "__main__":
    unittest.main()
