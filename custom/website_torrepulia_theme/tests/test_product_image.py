import base64
import io
from unittest.mock import patch

from PIL import Image

from odoo.tests import TransactionCase, tagged

from ..models.product_image import normalize_existing


def webp(width, height, mode='RGB', alpha=128):
    output = io.BytesIO()
    Image.new(mode, (width, height), (46, 73, 59, alpha)[:len(mode)]).save(output, 'WEBP')
    # RPC clients send base64 strings; the ORM keeps BinaryValue objects.
    return base64.b64encode(output.getvalue()).decode()


def size(value):
    return Image.open(value.open()).size


@tagged('post_install', '-at_install')
class TestProductImageNormalization(TransactionCase):
    def test_webp_upload_gets_native_thumbnails(self):
        product = self.env['product.template'].create({'name': 'WebP photo', 'image_1920': webp(3375, 2250)})
        self.assertEqual(size(product.image_1920), (1920, 1280))
        self.assertEqual(size(product.image_128), (128, 85))
        image = self.env['product.image'].create({'name': 'Extra', 'product_tmpl_id': product.id,
                                                  'image_1920': webp(2400, 2400, 'RGBA')})
        self.assertEqual(Image.open(image.image_1920.open()).format, 'PNG')
        self.assertEqual(size(image.image_1024), (1024, 1024))
        opaque = self.env['product.image'].create({'name': 'Opaque alpha', 'product_tmpl_id': product.id,
                                                   'image_1920': webp(800, 800, 'RGBA', alpha=255)})
        self.assertEqual(Image.open(opaque.image_1920.open()).format, 'JPEG')

    def test_other_formats_are_untouched_and_existing_webp_is_migrated(self):
        output = io.BytesIO()
        Image.new('RGB', (600, 400)).save(output, 'JPEG')
        jpeg = base64.b64encode(output.getvalue()).decode()
        product = self.env['product.template'].create({'name': 'JPEG photo', 'image_1920': jpeg})
        self.assertEqual(size(product.image_1920), (600, 400))
        # Reproduce a photo stored before this version, without the upload hook.
        with patch('odoo.addons.website_torrepulia_theme.models.product_image.normalized_vals',
                   lambda model, vals: vals):
            legacy = self.env['product.template'].create({'name': 'Legacy WebP', 'image_1920': webp(3000, 1500)})
        self.assertEqual(size(legacy.image_128), (3000, 1500))
        normalize_existing(self.env)
        legacy.invalidate_recordset()
        self.assertEqual(size(legacy.image_128), (128, 64))
