"""Product photos uploaded as WebP get real thumbnails.

Odoo stores WebP image fields untouched (odoo/tools/image.py), so image_128
to image_1920 all serve the full original: a 3375 px photo for a 72 px
thumbnail. Re-encode such uploads once, at most 1920 px, in a format Odoo
resizes; transparency is kept as PNG.
"""
import base64
import binascii
import io

from PIL import Image, WebPImagePlugin  # noqa: F401  Odoo initialises Pillow without WebP.

from odoo import api, models
from odoo.tools.binary import BinaryBytes, BinaryValue

MAX_SIDE = 1920
IMAGE_FIELDS = {
    'product.template': ('image_1920',),
    'product.product': ('image_variant_1920', 'image_1920'),
    'product.image': ('image_1920',),
}


def raw_content(value):
    """Bytes of a binary field value: RPC base64 string, BinaryValue or {filename, content}."""
    if isinstance(value, BinaryValue):
        return value.content
    if isinstance(value, dict):
        return raw_content(value.get('content'))
    if isinstance(value, str):
        try:
            return base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            return None
    return None


def resizable_image(value):
    """Return a JPEG/PNG copy of a WebP field value, else the value itself."""
    raw = raw_content(value)
    if not raw or raw[:4] != b'RIFF' or raw[8:12] != b'WEBP':
        return value
    image = Image.open(io.BytesIO(raw)).convert('RGBA')
    # Studio photos often carry a fully opaque alpha channel: keep JPEG for those.
    alpha = image.getchannel('A').getextrema()[0] < 255
    if not alpha:
        image = image.convert('RGB')
    image.thumbnail((MAX_SIDE, MAX_SIDE))
    output = io.BytesIO()
    if alpha:
        image.save(output, 'PNG', optimize=True)
    else:
        image.save(output, 'JPEG', quality=88, optimize=True, progressive=True)
    return BinaryBytes(output.getvalue())


def normalize_existing(env):
    """Re-encode stored WebP product photos; used by the 20.0.3.7.0 migration."""
    for model, fields in IMAGE_FIELDS.items():
        ids = env['ir.attachment'].sudo().search([
            ('res_model', '=', model), ('res_field', '=', fields[0]), ('mimetype', '=', 'image/webp'),
        ]).mapped('res_id')
        for record in env[model].sudo().with_context(active_test=False).browse(ids).exists():
            record[fields[0]] = record[fields[0]]


def normalized_vals(model, vals):
    keys = [key for key in IMAGE_FIELDS[model] if vals.get(key)]
    return dict(vals, **{key: resizable_image(vals[key]) for key in keys}) if keys else vals


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([normalized_vals(self._name, vals) for vals in vals_list])

    def write(self, vals):
        return super().write(normalized_vals(self._name, vals))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([normalized_vals(self._name, vals) for vals in vals_list])

    def write(self, vals):
        return super().write(normalized_vals(self._name, vals))


class ProductImage(models.Model):
    _inherit = 'product.image'

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([normalized_vals(self._name, vals) for vals in vals_list])

    def write(self, vals):
        return super().write(normalized_vals(self._name, vals))
