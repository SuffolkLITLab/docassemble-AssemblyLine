import unittest
from unittest.mock import patch

from . import sign


class TestSignatureFontFallback(unittest.TestCase):
    def test_configured_font_takes_precedence(self):
        with (
            patch.object(sign.os.path, "exists", return_value=True),
            patch.object(sign.ImageFont, "truetype") as load,
            patch.object(sign, "find_font_file_by_name") as find,
        ):
            self.assertIs(sign.get_font("/fonts/custom.ttf", 96), load.return_value)
            load.assert_called_once_with("/fonts/custom.ttf", 96)
            find.assert_not_called()

    def test_missing_configured_font_uses_scalable_fallback(self):
        with (
            patch.object(
                sign,
                "find_font_file_by_name",
                side_effect=[None, None, None, None, "/fonts/DejaVuSans.ttf"],
            ),
            patch.object(sign.ImageFont, "truetype") as load,
            patch.object(sign.ImageFont, "load_default") as default,
        ):
            self.assertIs(sign.get_font("MissingFont", 96), load.return_value)
            load.assert_called_once_with("/fonts/DejaVuSans.ttf", 96)
            default.assert_not_called()

    def test_unreadable_configured_font_uses_scalable_fallback(self):
        fallback = object()
        with (
            patch.object(sign.os.path, "exists", return_value=True),
            patch.object(
                sign,
                "find_font_file_by_name",
                return_value="/fonts/BadScript-Regular.ttf",
            ),
            patch.object(
                sign.ImageFont,
                "truetype",
                side_effect=[OSError("Invalid font"), fallback],
            ),
        ):
            self.assertIs(sign.get_font("/fonts/custom.ttf", 96), fallback)

    def test_unreadable_candidate_does_not_prevent_next_fallback(self):
        fallback = object()
        with (
            patch.object(
                sign,
                "find_font_file_by_name",
                side_effect=["/fonts/BadScript-Regular.ttf", "/fonts/arial.ttf"],
            ),
            patch.object(
                sign.ImageFont,
                "truetype",
                side_effect=[OSError("Invalid font"), fallback],
            ),
        ):
            self.assertIs(sign.get_font(font_size=96), fallback)

    def test_no_system_fonts_preserves_size_in_pillow_fallback(self):
        with (
            patch.object(
                sign,
                "find_font_file_by_name",
                return_value=None,
            ),
            patch.object(sign.ImageFont, "load_default") as load,
        ):
            self.assertIs(sign.get_font("MissingFont", 96), load.return_value)
            load.assert_called_once_with(size=96)

    def test_older_pillow_retains_last_resort_font(self):
        fallback = object()
        with (
            patch.object(
                sign,
                "find_font_file_by_name",
                return_value=None,
            ),
            patch.object(
                sign.ImageFont,
                "load_default",
                side_effect=[TypeError("Unexpected size argument"), fallback],
            ) as load,
        ):
            self.assertIs(sign.get_font(font_size=96), fallback)
            self.assertEqual(load.call_count, 2)
            load.assert_called_with()
