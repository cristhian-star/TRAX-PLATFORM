"""Decorative proposals header: real static resources and native fallback."""
import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from app import create_app, db
from app.config.config import TestingConfig

ROOT = Path(__file__).resolve().parents[1]

class ProposalHeroTest(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:", "SECRET_KEY": "hero-isolated"}):
            self.app = create_app(TestingConfig)
        with self.app.app_context():
            self.assertEqual(str(db.engine.url), "sqlite:///:memory:")
            db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_header_fallback_and_resources(self):
        html = self.client.get('/propuestas').get_data(as_text=True)
        header = html.split('<header class="proposals-p1__header">')[1].split('</header>')[0]
        photos = header.split('data-proposal-carousel')[1].split('</div>')[0]
        paths = re.findall(r'data-src="([^"]+)"', photos)
        self.assertEqual(paths, [f'/static/images/proposals/hero/proposal-hero-{i:02}.webp' for i in range(1,13)])
        self.assertIn('data-transition="fade"', photos)
        self.assertIn('fetchpriority="high" loading="eager"', photos)
        self.assertIn('src="'+paths[0]+'" width="1448" height="1086" alt="" aria-hidden="true"', photos)
        self.assertEqual(photos.count('alt="" aria-hidden="true"'), 2)
        self.assertNotIn('<button', photos)
        self.assertNotIn('<a ', photos)
        self.assertNotIn('tabindex', photos)
        self.assertIn('EXPLORÁ OPORTUNIDADES', header)
        self.assertIn('<h1', header)
        self.assertNotIn('proposal-filters', header)
        self.assertEqual(html.count('src="/static/js/emergency-hero-carousel-v1.js"'),1)
        for path in paths:
            with self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)
            with Image.open(ROOT / 'app' / path.lstrip('/')) as image:
                image.load()
                self.assertEqual(image.format,'WEBP')
                self.assertEqual(image.size,(1448,1086))
                self.assertFalse(set(image.info) & {'exif','xmp','icc_profile'})
            self.assertLess((ROOT / 'app' / path.lstrip('/')).stat().st_size,250000)

    def test_local_resources_and_reduced_motion_style(self):
        for path in ('app/templates/listado_propuestas.html','app/static/js/emergency-hero-carousel-v1.js','app/static/css/proposals-portal-p1.css'):
            text=(ROOT/path).read_text(encoding='utf-8')
            for forbidden in ('Downloads','C:\\Users','http://','https://'):
                self.assertNotIn(forbidden,text)
        self.assertIn('prefers-reduced-motion: reduce',(ROOT/'app/static/css/proposals-portal-p1.css').read_text(encoding='utf-8'))
