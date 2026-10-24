from odoo import http
from odoo.http import request


class TorrepuliaAnalysis(http.Controller):
    # La Peranzana reads its analysis here: each harvest is a profile in the backend, not a Builder edit.
    @http.route('/torrepulia/analisi', type='http', auth='public', website=True, sitemap=False, readonly=True)
    def analysis(self, **kwargs):
        Profile = request.env['torrepulia.oil.profile']
        values = {'profile': Profile._torrepulia_published_analysis(), 'season': Profile._torrepulia_season()}
        rendered = request.env['ir.ui.view']._render_template('website_torrepulia_theme.oil_analysis_content', values)
        return request.make_json_response({'html': str(rendered)})

    @http.route('/torrepulia/analisi/<int:profile_id>/rapporto.pdf', type='http', auth='public', website=True,
                sitemap=False, readonly=True)
    def report(self, profile_id, **kwargs):
        # The test report is published whole: public product pages and La Peranzana link it.
        profile = request.env['torrepulia.oil.profile'].sudo().browse(profile_id).exists()
        if not profile or not profile.report_file:
            raise request.not_found()
        stream = request.env['ir.binary']._get_stream_from(
            profile, 'report_file', filename=profile.report_filename or 'rapporto-di-prova.pdf', mimetype='application/pdf')
        return stream.get_response(as_attachment=False)
