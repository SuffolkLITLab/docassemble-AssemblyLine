import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops, ImageFont, ImageOps
from docx.image.image import Image as DocxImage

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
                side_effect=lambda name, dirs: (
                    "/fonts/DejaVuSans.ttf" if name == "DejaVuSans" else None
                ),
            ),
            patch.object(sign.ImageFont, "truetype") as load,
            patch.object(sign.ImageFont, "load_default") as default,
        ):
            self.assertIs(sign.get_font("MissingFont", 96), load.return_value)
            load.assert_called_once_with("/fonts/DejaVuSans.ttf", 96)
            default.assert_not_called()

    def test_missing_configured_font_prefers_available_script(self):
        with (
            patch.object(
                sign,
                "find_font_file_by_name",
                side_effect=lambda name, dirs: (
                    "/fonts/segoesc.ttf" if name == "segoesc" else None
                ),
            ),
            patch.object(sign.ImageFont, "truetype") as load,
        ):
            self.assertIs(sign.get_font("MissingFont", 96), load.return_value)
            load.assert_called_once_with("/fonts/segoesc.ttf", 96)

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


class TestSignatureRendering(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "signature.png"

    def scalable_font(self, font_name, font_size):
        return ImageFont.load_default(size=font_size)

    def test_high_resolution_preserves_complete_glyphs_and_padding(self):
        # These strings have negative left bearings and large baseline offsets
        # in Pillow's bundled scalable font, including accents and descenders.
        for name, prefix in [("jgyp", ""), ("Álex Example", "/s/")]:
            with (
                self.subTest(name=name),
                patch.object(sign, "get_font", side_effect=self.scalable_font) as load,
            ):
                sign.create_signature(name, str(self.output), signature_prefix=prefix)
                load.assert_called_once_with(None, 192)
                text = f"{prefix} {name}" if prefix else name
                mask = ImageFont.load_default(size=192).getmask(text)
                # Compare with the full glyph mask, independently of draw.text's
                # baseline coordinates, to catch clipped accents and descenders.
                glyphs = ImageOps.invert(Image.frombytes("L", mask.size, bytes(mask)))
                expected = Image.new(
                    "RGB", (mask.size[0] + 160, mask.size[1] + 160), "white"
                )
                expected.paste(glyphs, (80, 80))
                with Image.open(self.output) as rendered:
                    self.assertEqual(rendered.size, expected.size)
                    self.assertIsNone(
                        ImageChops.difference(rendered, expected).getbbox()
                    )
                    for dpi in rendered.info["dpi"]:
                        self.assertAlmostEqual(dpi, 288, delta=0.1)

    def test_more_pixels_preserve_natural_docx_size(self):
        images = []
        with patch.object(sign, "get_font", side_effect=self.scalable_font):
            for multiplier in [1, 4]:
                output = Path(self.directory.name) / f"signature_{multiplier}.png"
                sign.create_signature(
                    "Alex Example", str(output), resolution_multiplier=multiplier
                )
                images.append(DocxImage.from_file(str(output)))
        low, high = images
        self.assertGreater(high.px_width, low.px_width * 3.9)
        self.assertGreater(high.px_height, low.px_height * 3.9)
        self.assertAlmostEqual(low.width.inches, high.width.inches, delta=0.05)
        self.assertAlmostEqual(low.height.inches, high.height.inches, delta=0.05)

    def test_invalid_render_sizes_are_rejected(self):
        for size, multiplier in [(0, 4), (-1, 4), (48, 0), (48, -1)]:
            with self.subTest(size=size, multiplier=multiplier):
                with self.assertRaises(ValueError):
                    sign.create_signature(
                        "Alex",
                        str(self.output),
                        font_size=size,
                        resolution_multiplier=multiplier,
                    )
