{
    'name': 'Torrepulia Request Theme Integration',
    'version': '20.0.1.3.1',
    'author': 'Torrepulia',
    'license': 'LGPL-3',
    'depends': ['website_torrepulia_request', 'website_torrepulia_theme'],
    'data': ['views/commerce.xml', 'views/product.xml'],
    'assets': {
        'web.assets_frontend': [
            'website_torrepulia_request_theme/static/src/js/formats.js',
            'website_torrepulia_request_theme/static/src/scss/product.scss',
            'website_torrepulia_request_theme/static/src/scss/full_width_sections.scss',
        ],
    },
    'auto_install': True,
    'installable': True,
}
