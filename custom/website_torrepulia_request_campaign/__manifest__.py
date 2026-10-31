{
    'name': 'Torrepulia Seasonal Request Campaigns',
    'version': '20.0.1.15.0',
    'author': 'Torrepulia',
    'description': 'Configurable seasonal showcase using the shared quote request selection. Operational and migration instructions are in README.md.',
    'license': 'LGPL-3',
    'depends': ['website_torrepulia_request_theme'],
    'data': ['security/ir.access.csv', 'views/campaign.xml', 'views/snippet.xml', 'views/legacy_receipt.xml', 'data/page.xml'],
    'assets': {
        'web.assets_frontend': [
            'website_torrepulia_request_campaign/static/src/js/campaign.js',
            'website_torrepulia_request_campaign/static/src/scss/campaign.scss',
        ],
        'website.website_builder_assets': [
            'website_torrepulia_request_campaign/static/src/js/campaign_options.js',
            'website_torrepulia_request_campaign/static/src/xml/campaign_options.xml',
        ],
        'website.assets_inside_builder_iframe': [
            'website_torrepulia_request_campaign/static/src/js/campaign.edit.js',
        ],
    },
    'installable': True,
}
