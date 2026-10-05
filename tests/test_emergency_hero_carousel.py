"""E3 asset and rendered document contracts; no persistent database."""
import os
from html.parser import HTMLParser
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image
from app import create_app
from app.config.config import TestingConfig

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['electricista-tablero', 'plomero-desague', 'cerrajero-hogar',
         'cerrajero-automotor', 'auxilio-vehicular-auto', 'auxilio-movil-moto']


class HeroParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.tags = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-emergency-carousel' in attrs:
            self.inside = True
            self.root = attrs
        elif self.inside:
            self.tags.append((tag, attrs))

    def handle_endtag(self, tag):
        if tag == 'div':
            self.inside = False


class EmergencyHeroTest(unittest.TestCase):
    def test_assets_are_small_valid_webp_without_metadata(self):
        for name in NAMES:
            with self.subTest(name=name):
                path = ROOT / 'app/static/images/emergencias/hero' / (name + '.webp')
                self.assertLess(path.stat().st_size, 250_000)
                with Image.open(path) as image:
                    image.load()
                    self.assertEqual(image.format, 'WEBP')
                    self.assertEqual(image.size, (1448, 1086))
                    self.assertFalse(set(image.info) & {'exif', 'xmp', 'icc_profile'})

    def test_rendered_decorative_contract_and_no_js_fallback(self):
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:',
                                    'SECRET_KEY': 'e3-test-only'}, clear=True):
            app = create_app(TestingConfig)
        response = app.test_client().get('/urgencias/nueva')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        parser = HeroParser()
        parser.feed(html)
        self.assertEqual(parser.root['aria-hidden'], 'true')
        expected = ['/static/images/emergencias/hero/' + n + '.webp' for n in NAMES]
        self.assertEqual([a['data-src'] for t, a in parser.tags if t == 'template'], expected)
        self.assertFalse(any(t in ('a', 'button', 'input') for t, a in parser.tags))
        self.assertFalse(any('tabindex' in a for t, a in parser.tags))
        images = [a for t, a in parser.tags if t == 'img']
        self.assertEqual(len(images), 2)
        self.assertEqual(images[0]['src'], expected[0])
        self.assertEqual(images[0]['fetchpriority'], 'high')
        self.assertNotIn('hidden', images[0])
        self.assertIn('hidden', images[1])
        for image in images:
            self.assertEqual(image['alt'], '')
            self.assertEqual(image['aria-hidden'], 'true')
            self.assertEqual((image['width'], image['height']), ('1448', '1086'))
        for rel in ('app/templates/nueva_emergencia.html', 'app/static/css/emergency-entry-v2.css',
                    'app/static/js/emergency-hero-carousel-v1.js'):
            text = (ROOT / rel).read_text(encoding='utf-8')
            self.assertNotIn('Downloads', text)
            self.assertNotIn('https://', text)
            self.assertNotIn('http://', text)


if __name__ == '__main__':
    unittest.main()
