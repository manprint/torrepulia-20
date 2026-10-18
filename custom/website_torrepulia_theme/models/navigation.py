from odoo import fields, models


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    torrepulia_navigation_hidden = fields.Boolean('Exclude from Torrepulia navigation')
    torrepulia_seasonal = fields.Boolean('Torrepulia seasonal menu')


class Website(models.Model):
    _inherit = 'website'

    torrepulia_seasonal_navigation = fields.Boolean('Show seasonal oil menu', default=False)

    def _torrepulia_navigation(self):
        self.ensure_one()
        return self.menu_id.child_id.filtered(
            lambda menu: menu.website_id == self and menu.is_visible
            and not menu.torrepulia_navigation_hidden
            and (not menu.torrepulia_seasonal or self.torrepulia_seasonal_navigation)
        )

    def _torrepulia_footer_pages(self, keys):
        self.ensure_one()
        # Like website.menu._compute_visible in installed Odoo 20, inspect page
        # visibility with sudo, then expose only accessible published destinations.
        pages = self.env['website.page'].sudo()
        for key in keys:
            page = self.env.ref('website_torrepulia_theme.page_' + key, raise_if_not_found=False)
            page = page.sudo() if page else page
            if (page and page.website_id == self and page.is_visible
                    and page.view_id._handle_visibility(do_raise=False)):
                pages |= page
        return pages
