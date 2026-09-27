"""UX-05A assets and rendered decorative carousel contracts; SQLite only."""
import hashlib
import os
from pathlib import Path
import re
import unittest
from html.parser import HTMLParser
from PIL import Image
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret'
from app import create_app, db
from app.config.config import TestingConfig
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'app/static/images/explorar/carrusel'
NAMES = ('pintura-altura limpieza-tanques acabado-parquet instalacion-ventanas instalacion-solar reparacion-electrodomesticos automatizacion-industrial soldadura-estructuras soldadura-galpones construccion-pergolas decoracion-pvc estuco-veneciano').split()
class Tags(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.items=[]; self.feed(text)
    def handle_starttag(self, tag, attrs): self.items.append((tag,dict(attrs)))
class ExploreMotionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=create_app(config_class=TestingConfig, initialize_schema=False)
        cls.app.config.update(TESTING=True, RATELIMIT_ENABLED=False)
        cls.client=cls.app.test_client()
        with cls.app.app_context(): db.create_all()
        cls.html=cls.client.get('/explorar').get_data(as_text=True)
        cls.home=cls.client.get('/').get_data(as_text=True)
    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context(): db.session.remove(); db.drop_all()
    def test_home_rows_replace_cards_with_accessible_links(self):
        section=self.home.split('class="trax-home__featured"',1)[1].split('class="trax-home__trust"',1)[0]
        self.assertLess(section.index('trax-home__featured-lead'),section.index('class="featured-bands"'))
        self.assertNotIn('trax-home__featured-grid',section)
        self.assertNotIn('trax-home__featured-card',section)
        self.assertEqual(section.count('class="featured-bands__row"'),2)
        groups=re.findall(r'<div class="featured-bands__group"[^>]*>(.*?)</div>',section,re.S)
        self.assertEqual(len(groups),4)
        sources=[]
        for number,group in enumerate(groups):
            imgs=[a for t,a in Tags(group).items if t=='img']
            self.assertEqual(len(imgs),6)
            urls=[a['src'] for a in imgs]; self.assertEqual(len(set(urls)),6)
            sources.append(urls)
            links=[a for tag,a in Tags(group).items if tag=='a']
            self.assertEqual(len(links),6)
            for link in links:
                self.assertTrue(link['href'].startswith('/buscar?servicio='))
                self.assertEqual(link.get('tabindex'),'-1' if number%2 else None)
            for attrs in imgs:
                for k,v in {'alt':'','width':'960','height':'540','draggable':'false','decoding':'async','loading':'lazy','fetchpriority':'low'}.items(): self.assertEqual(attrs[k],v)
                self.assertNotIn('tabindex',attrs)
                self.assertTrue(attrs['src'].startswith('/static/images/explorar/carrusel/'))
        self.assertEqual(sources[0],sources[1]); self.assertEqual(sources[2],sources[3])
        self.assertEqual(len(set(sources[0]+sources[2])),12)
        for row in (sources[0],sources[2]): self.assertEqual(sum('soldadura-' in s for s in row),1)
        self.assertEqual(section.count('data-copy="1" aria-hidden="true"'),2)
        self.assertIn('class="featured-bands__photos">',section)
        button=next(a for t,a in Tags(section).items if a.get('class')=='featured-bands__toggle')
        self.assertIn('hidden',button); self.assertEqual(button['aria-pressed'],'false')
        self.assertEqual(len(re.findall(r'class="trax-home__slide(?: |")',self.home)),8)

    def test_assets_decode_metadata_budget_and_http(self):
        self.assertEqual({p.stem for p in ASSETS.glob('*.webp')},set(NAMES))
        hashes=[]; total=0
        for name in NAMES:
            p=ASSETS/(name+'.webp'); data=p.read_bytes(); total+=len(data)
            self.assertLessEqual(len(data),130000); hashes.append(hashlib.sha256(data).hexdigest())
            with Image.open(p) as im:
                im.load(); self.assertEqual(im.format,'WEBP'); self.assertEqual(im.size,(960,540)); self.assertEqual(im.mode,'RGB')
                self.assertFalse(getattr(im,'is_animated',False))
                for key in ('exif','xmp','icc_profile'): self.assertNotIn(key,im.info)
            for method in ('GET','HEAD'):
                response=self.client.open('/static/images/explorar/carrusel/'+p.name,method=method)
                try:
                    self.assertEqual(response.status_code,200); self.assertEqual(response.content_type,'image/webp')
                    self.assertEqual(response.data,data if method=='GET' else b'')
                finally: response.close()
        self.assertEqual(len(set(hashes)),12); self.assertLessEqual(total,1300000)
    def test_explore_single_scene_controls_static_fallback_and_catalog(self):
        images=[a for t,a in Tags(self.html).items if a.get('class','').startswith('explore-scenes__image')]
        self.assertEqual(len(images),7)
        self.assertEqual(sum('is-active' in a['class'] for a in images),1)
        self.assertIn('is-active',images[0]['class'])
        self.assertEqual(images[0]['loading'],'eager')
        self.assertEqual(images[0]['fetchpriority'],'high')
        for attrs in images:
            self.assertEqual(attrs['alt'],''); self.assertEqual(attrs['width'],'960')
            self.assertEqual(attrs['height'],'540'); self.assertTrue(attrs['src'].startswith('/static/'))
        for removed_control in ('explore-scenes__controls','data-explore-previous','data-explore-next','Pausar imágenes'):
            self.assertNotIn(removed_control,self.html)
        for removed in ('explore-motion__row','explore-motion-toggle','featured-bands','data-hero-status'):
            self.assertNotIn(removed,self.html)
        self.assertEqual(self.html.count('class="rubro-card"'),20)
        self.assertIn('name="servicio"',self.html); self.assertIn('name="zona"',self.html)
        self.assertIn('action="/buscar" method="GET"',self.html)
        for html,scriptname in ((self.html,'explore-motion'),(self.home,'featured-bands')):
            script=next(a for t,a in Tags(html).items if a.get('src','').endswith('/'+scriptname+'.js'))
            self.assertIn('defer',script)

    def test_component_css_motion_accessibility_and_fallback(self):
        explore=(ROOT/'app/static/css/explore-motion.css').read_text(encoding='utf-8')
        bands=(ROOT/'app/static/css/featured-bands.css').read_text(encoding='utf-8')
        for text in ('opacity: 0','is-active { opacity: 1; }','transition: opacity 750ms','transition: none'):
            self.assertIn(text,explore)
        self.assertNotIn('translateX',explore)
        self.assertIn('rgba(12, 35, 60, .62)',explore)
        self.assertIn('rgba(12, 35, 60, .72)',explore)
        self.assertNotIn('explore-scenes__controls',explore)
        for text in ('[data-bands-ready]','animation: featured-photo-drift var(--featured-duration) linear infinite','animation-direction: reverse','translateX(-50%)','animation-play-state: paused','animation: none','featured-bands__toggle:focus-visible'):
            self.assertIn(text,bands)
        for css in (explore,bands):
            for text in ('@media print','prefers-reduced-motion: reduce'):
                self.assertIn(text,css)
            self.assertNotIn('!important',css)
            self.assertNotRegex(css,r'url\([\s\'"]*(?:https?:|//)')

if __name__=='__main__': unittest.main()
