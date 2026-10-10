{
    "name": "Torrepulia Premium Website Theme",
    "summary": "Tema e-commerce premium nativo per Torrepulia su Odoo 20.",
    "description": """
Torrepulia premium website theme for Website and eCommerce.

Includes editable editorial snippets, a curated homepage, product/shop styling,
and local brand imagery sourced from the current Torrepulia website.
    """,
    "category": "Theme",
    "version": "20.0.1.0.0",
    "author": "Torrepulia",
    "license": "LGPL-3",
    "depends": [
        "website",
        "website_sale",
    ],
    "data": [
        "views/snippets/snippets.xml",
        "views/snippets/s_hero.xml",
        "views/snippets/s_brand_story.xml",
        "views/snippets/s_product_showcase.xml",
        "views/snippets/s_peranzana.xml",
        "views/snippets/s_terroir.xml",
        "views/snippets/s_production_process.xml",
        "views/snippets/s_product_formats.xml",
        "views/snippets/s_editorial.xml",
        "views/snippets/s_cta.xml",
        "views/snippets/s_newsletter.xml",
        "views/homepage.xml",
        "views/footer.xml",
        "views/shop_templates.xml",
        "views/product_templates.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            "website_torrepulia_theme/static/src/scss/primary_variables.scss",
        ],
        "web.assets_frontend": [
            "website_torrepulia_theme/static/src/scss/theme.scss",
            "website_torrepulia_theme/static/src/js/theme.js",
        ],
        "website.website_builder_assets": [
            "website_torrepulia_theme/static/src/scss/builder.scss",
        ],
    },
    "images": [
        "static/description/cover.png",
    ],
    "installable": True,
    "application": False,
}
