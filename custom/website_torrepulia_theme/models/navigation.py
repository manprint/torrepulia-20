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

    # Social fields of the company, in the order the footer lists them, with their Odoo UI icon.
    TORREPULIA_SOCIALS = (('social_instagram', 'Instagram', 'oi_instagram'), ('social_facebook', 'Facebook', 'oi_facebook'),
                          ('social_tiktok', 'TikTok', 'oi_tiktok'), ('social_youtube', 'YouTube', 'oi_youtube'),
                          ('social_linkedin', 'LinkedIn', 'oi_linkedin'))

    def _torrepulia_footer_company(self):
        """Legal name, address, VAT number, contacts and social links, all from the company record."""
        self.ensure_one()
        company = self.company_id.sudo()
        partner = company.partner_id
        vat = (company.vat or '').replace(' ', '')
        if len(vat) > 2 and vat[:2].isalpha():
            vat = vat[2:]  # "IT00722360716" reads as "P. IVA 00722360716".
        locality = ' '.join(filter(None, [partner.zip, partner.city]))
        if partner.state_id.code and locality:
            locality += ' (%s)' % partner.state_id.code
        return {
            'name': company.name,
            'street': ', '.join(filter(None, [partner.street, partner.street2])),
            'locality': locality,
            'vat': vat,
            'email': company.email,
            'phone': company.phone,
            'socials': [(label, company[field], icon) for field, label, icon in self.TORREPULIA_SOCIALS if company[field]],
        }

    def _torrepulia_footer_payments(self):
        """Names of the payment methods a visitor can actually use on this website."""
        self.ensure_one()
        providers = self.env['payment.provider'].sudo().search([
            ('is_published', '=', True), ('company_id', '=', self.company_id.id),
            ('website_id', 'in', [False, self.id])])
        return providers.filtered(lambda p: not p.module_id or p.module_state == 'installed').mapped('name')

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
