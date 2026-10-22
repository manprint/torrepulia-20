from odoo import models


class WebsiteMenu(models.Model):
    """Include the existing theme menu model in the bridge's ORM setup.

    The repository theme can be newer than its installed database version.
    Its stored navigation fields must be initialised before Odoo prefetches
    menus. Registering the inherited model runs native schema initialisation
    without updating theme XML, provisioning pages, or redeclaring its fields.
    """
    _inherit = 'website.menu'
