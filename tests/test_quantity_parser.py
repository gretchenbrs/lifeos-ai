import unittest

from app.services.quantity_parser import QuantityParser


class QuantityParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = QuantityParser()

    def test_normalizes_piece_aliases(self) -> None:
        for amount in ("1pc", "1 pc", "1 piece", "1 pics"):
            parsed = self.parser.parse_ingredient(f"egg ({amount})")
            self.assertIsNotNone(parsed)
            assert parsed is not None
            self.assertEqual(parsed.unit, "piece")
            self.assertEqual(parsed.quantity, 1)

    def test_converts_weight_units_to_grams(self) -> None:
        kilogram = self.parser.parse_ingredient("rice (0.3kg)")
        ounces = self.parser.parse_ingredient("rice (2oz)")

        self.assertIsNotNone(kilogram)
        self.assertIsNotNone(ounces)
        assert kilogram is not None and ounces is not None
        self.assertEqual(kilogram.unit, "gram")
        self.assertEqual(ounces.unit, "gram")
        self.assertEqual(kilogram.grams, 300)
        self.assertAlmostEqual(ounces.grams or 0, 56.699, places=3)

    def test_recognizes_natural_egg_count(self) -> None:
        parsed = self.parser.parse_ingredient("egg (1 egg)")

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.unit, "piece")

    def test_accepts_a_bare_count_for_eggs_only(self) -> None:
        parsed = self.parser.parse_ingredient("eggs (1)")

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.unit, "piece")
        self.assertEqual(parsed.quantity, 1)
        self.assertIsNone(self.parser.parse_ingredient("rice (1)"))

    def test_rejects_ambiguous_single_letter_unit(self) -> None:
        self.assertIsNone(self.parser.parse_ingredient("egg (1p)"))


if __name__ == "__main__":
    unittest.main()
