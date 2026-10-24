"""Home copy aligned with the other pages and the owner's tasting sheet (23/10).

Plain lxml, no Odoo: the migration runs it on every stored language of the
saved home and it keeps the snippet templates in step. Elements are found by
class and position, so it works whatever words each language holds; a missing
element is skipped and running it twice changes nothing.
"""
from lxml import etree

REGINA_LEAD = '<strong>Il carattere della nostra terra.</strong>'
REGINA = ("L&#8217;olio extravergine La Regina nasce dalle olive Peranzana dei nostri uliveti di Torremaggiore, "
          "nel nord della Puglia. Un fruttato medio-intenso con sentori di pomodoro verde, carciofo e mandorla "
          "fresca; amaro e piccante ben equilibrati. &#200; l&#8217;olio da usare a crudo, su bruschette, verdure e "
          "zuppe.")
FAMILY = 'Tre generazioni, gli stessi ulivi.'
PERANZANA_CAPTION = 'Solo Peranzana, solo dai nostri ulivi.'
ORIGIN = ("Coltiviamo i nostri ulivi nell&#8217;agro di Torremaggiore, nell&#8217;Alto Tavoliere: &#232; la terra "
          "d&#8217;origine della Peranzana.")
# Owner's words (25/10): medium-intense fruity, fresh olive; green tomato, artichoke, fresh almond; elegant and
# harmonious; soft and round, bitter and pungent delicate and balanced; clean finish, low acidity.
SENSORY = (
    ("Pomodoro verde.<br/>Carciofo e mandorla.",
     "La Peranzana ha un profilo elegante e armonico. Al naso un fruttato medio-intenso di oliva appena colta: "
     "prima il verde del pomodoro e del carciofo, poi la mandorla fresca."),
    ("Morbido.<br/>Equilibrato.",
     "In bocca &#232; morbido e rotondo. Amaro e piccante si sentono, delicati e ben bilanciati tra loro, senza "
     "mai coprire il resto. Il finale &#232; pulito, con un&#8217;acidit&#224; bassa."),
    ("Un filo a crudo.",
     "Su bruschette calde, zuppe di legumi, insalate, carpacci di carne o pesce e sulla pasta della tradizione "
     "pugliese."),
)
PROCESS_INTRO = 'Seguiamo ogni passaggio di persona. <a class="text-link" href="/l-olio#processo">Come nasce La Regina</a>'
PROCESS = (
    ("Ottobre e novembre", "La raccolta",
     "Raccogliamo le olive dalla pianta all&#8217;inizio dell&#8217;invaiatura, quando il frutto comincia a "
     "cambiare colore: &#232; il momento in cui l&#8217;oliva &#232; pi&#249; ricca di polifenoli e di profumi."),
    ("Entro 8 ore", "La molitura",
     "Moliamo le olive nel nostro frantoio di fiducia, con estrazione a freddo sotto i 27 &#176;C, e seguiamo la "
     "molitura di persona."),
)
CLOSING = ("Il nome Torrepulia unisce Torremaggiore e la Puglia. In questo angolo dell&#8217;Alto Tavoliere "
           "crescono i nostri ulivi, dai secolari del nonno a quelli piantati da poco: da qui nasce La Regina.")


def _has_class(name):
    return "contains(concat(' ', normalize-space(@class), ' '), ' %s ')" % name


def _remove(node):
    parent = node.getparent()
    if node.tail and node.tail.strip():
        previous = node.getprevious()
        if previous is not None:
            previous.tail = (previous.tail or '') + node.tail
        else:
            parent.text = (parent.text or '') + node.tail
    parent.remove(node)


def _set_inner(node, markup):
    fresh = etree.fromstring('<x>%s</x>' % markup)
    for child in list(node):
        node.remove(child)
    node.text = fresh.text
    for child in fresh:
        node.append(child)


def refine_section(section):
    """Align one saved home section; returns nothing, edits in place."""
    name = section.get('data-snippet')
    if name == 's_cinematic_1':
        for node in section.xpath(".//div[%s] | .//div[%s]" % (_has_class('section-line'), _has_class('product-note'))):
            _remove(node)
        paragraphs = section.xpath(".//div[%s]/p" % _has_class('regina-copy'))
        if len(paragraphs) > 1:
            _set_inner(paragraphs[0], REGINA_LEAD)
            _set_inner(paragraphs[1], REGINA)
    elif name == 's_cinematic_2':
        for node in section.xpath(".//div[%s]/p" % _has_class('family-heading')):
            _set_inner(node, FAMILY)
    elif name == 's_cinematic_5':
        for node in section.xpath(".//p[%s]" % _has_class('mc-oil-finale')):
            _remove(node)
    elif name == 's_cinematic_3':
        for node in section.xpath(".//div[%s]/span[%s]" % (_has_class('mc-peranzana-heading'), _has_class('photo-caption'))):
            _set_inner(node, PERANZANA_CAPTION)
        for node in section.xpath(".//div[%s]/p" % _has_class('mc-peranzana-origin')):
            _set_inner(node, ORIGIN)
        for panel, (title, text) in zip(section.xpath(".//div[%s]" % _has_class('mc-sensory-panel')), SENSORY):
            for node in panel.xpath("./p[%s]" % _has_class('sensory-title')):
                _set_inner(node, title)
            for node in panel.xpath("./p[%s]" % _has_class('sensory-text')):
                _set_inner(node, text)
        for node in section.xpath(".//div[%s]/p" % _has_class('process-intro')):
            _set_inner(node, PROCESS_INTRO)
        for article, (when, title, text) in zip(section.xpath(".//div[%s]/article" % _has_class('process')), PROCESS):
            for node in article.xpath('./span'):
                _set_inner(node, when)
            for node in article.xpath('./h4'):
                _set_inner(node, title)
            for node in article.xpath('./p'):
                _set_inner(node, text)
    elif name == 's_cinematic_6':
        for node in section.xpath(".//div[%s]/p" % _has_class('territory-copy')):
            _set_inner(node, CLOSING)
        for node in section.xpath(".//div[%s]/a[%s]" % (_has_class('territory-copy'), _has_class('text-link'))):
            node.set('href', '/territorio')
            icon = node.find('img')
            node.text = 'Il territorio '
            for child in list(node):
                if child is not icon:
                    node.remove(child)
            if icon is not None:
                icon.tail = None


# 25/10: only the reworded elements, so the sections the 23/10 alignment rebuilt keep any later Builder edit.
def recopy_section(section):
    name = section.get('data-snippet')
    if name == 's_cinematic_1':
        paragraphs = section.xpath(".//div[%s]/p" % _has_class('regina-copy'))
        if len(paragraphs) > 1:
            _set_inner(paragraphs[0], REGINA_LEAD)
            _set_inner(paragraphs[1], REGINA)
    elif name == 's_cinematic_2':
        for node in section.xpath(".//div[%s]/p" % _has_class('family-heading')):
            _set_inner(node, FAMILY)
    elif name == 's_cinematic_3':
        for node in section.xpath(".//span[%s]" % _has_class('photo-caption')):
            _set_inner(node, PERANZANA_CAPTION)
        panels = section.xpath(".//div[%s]" % _has_class('mc-sensory-panel'))
        for panel, (title, text) in zip(panels[:2], SENSORY):
            for node in panel.xpath("./p[%s]" % _has_class('sensory-title')):
                _set_inner(node, title)
            for node in panel.xpath("./p[%s]" % _has_class('sensory-text')):
                _set_inner(node, text)
        for article, (_when, _title, text) in zip(section.xpath(".//div[%s]/article" % _has_class('process')), PROCESS):
            for node in article.xpath('./p'):
                _set_inner(node, text)
