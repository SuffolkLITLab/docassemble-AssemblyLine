import unittest
from .al_general import ALIndividual, ALAddress


class test_aladdress(unittest.TestCase):
    def setUp(self):
        self.addr = ALAddress()

    def test_empty_is_empty(self):
        addr = ALAddress(address="", city="")
        self.assertEqual(addr.on_one_line(), "")

    def test_no_unit_floor_room(self):
        self.assertFalse(hasattr(self.addr, "unit"))
        self.assertFalse(hasattr(self.addr, "floor"))
        self.assertFalse(hasattr(self.addr, "room"))
        self.assertEqual(self.addr.formatted_unit(), "")

    def test_require_unit_exception(self):
        self.assertFalse(hasattr(self.addr, "unit"))
        with self.assertRaises(AttributeError):
            self.addr.formatted_unit(require=True)

    def test_unit_isnumeric(self):
        self.addr.unit = "123"
        self.assertEqual(self.addr.formatted_unit(), "Unit 123")

    def test_unit_no_space_without_known_descriptors(self):
        self.addr.unit = "1A"
        self.assertEqual(self.addr.formatted_unit(), "Unit 1A")

    def test_unit_with_space_and_known_descriptor(self):
        self.addr.unit = "Apt 1A"
        self.assertEqual(self.addr.formatted_unit(), "Apt 1A")

    def test_bare_unit(self):
        self.addr.unit = "1A"
        self.assertEqual(self.addr.formatted_unit(bare=True), "1A")

    def test_floor_formatting(self):
        self.addr.floor = "5"
        self.assertEqual(self.addr.formatted_unit(), "Floor 5")

    def test_room_formatting(self):
        self.addr.room = "101"
        self.assertEqual(self.addr.formatted_unit(), "Room 101")


if __name__ == "__main__":
    unittest.main()
