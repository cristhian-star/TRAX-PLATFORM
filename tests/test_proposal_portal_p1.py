"""Public presentation contract against isolated, real ORM records."""
import os
import re
from html import unescape
from urllib.parse import urlencode, urlsplit, parse_qs
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from sqlalchemy import event
from app import create_app, db
from app.config.config import TestingConfig
from app.models.user import User
from app.models.professional import Professional
from app.models.proposal_request import ProposalRequest
from app.models.proposal_application import ProposalApplication
from app.models.verification_request import VerificationRequest


class ProposalPortalTest(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:", "SECRET_KEY": "portal-test"}):
            self.app = create_app(TestingConfig)
        self.app.config.update(RATELIMIT_ENABLED=False)
        self.client = self.app.test_client()
        with self.app.app_context():
            self.assertEqual(str(db.engine.url), "sqlite:///:memory:")
            db.create_all()
            db.session.add_all([
                User(id=1, nombre="PRIVATE_OWNER", email="private-owner@test.invalid", password="private-secret", rol="CLIENTE"),
                User(id=2, nombre="Professional", email="professional@test.invalid", password="unused", rol="PROFESIONAL"),
            ])
            db.session.flush()
            db.session.add(Professional(id=1, user_id=2, nombre="Professional", servicio="Electricidad", zona="Palermo", perfil_completo=True))
            for number in range(1, 16):
                db.session.add(ProposalRequest(id=number, cliente_id=1, owner_user_id=1,
                    titulo=f"Trabajo {number:02}", descripcion="Descripción real " * 30,
                    industria="Construcción" if number % 2 else "Servicios",
                    categoria="Electricidad" if number % 2 else "Plomería",
                    rubro="Tableros" if number % 2 else "Desagües", ubicacion="Palermo" if number % 2 else "Belgrano",
                    presupuesto_estimado=0 if number == 15 else None,
                    estado="PUBLICADA", created_at=datetime(2026, 1, 1) + timedelta(days=number)))
            for number, state in ((16, "CERRADA"), (17, "CANCELADA")):
                db.session.add(ProposalRequest(id=number, cliente_id=1, owner_user_id=1, categoria="HIDDEN_CATEGORY", titulo=state + "_PRIVATE", estado=state))
            db.session.add(ProposalApplication(proposal_id=15, professional_id=1, professional_user_id=2, mensaje="PRIVATE_APPLICATION"))
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def html(self, query=""):
        response = self.client.get("/propuestas" + query)
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def login(self, user=2):
        with self.client.session_transaction() as session:
            session.update(user_id=user, user_role="PROFESIONAL", verified=True)

    def test_anonymous_real_fields_public_only_and_privacy(self):
        html = self.html()
        self.assertIn("15 propuestas publicadas", html)
        self.assertIn("Presupuesto estimado", html)
        self.assertIn("$0.00", html)
        self.assertIn("1 postulación", html)
        self.assertIn('href="/propuestas/15"', html)
        self.assertIn("…", html)
        for private in ("PRIVATE_OWNER", "private-owner@", "private-secret", "PRIVATE_APPLICATION", "HIDDEN_CATEGORY", "CERRADA_PRIVATE", "CANCELADA_PRIVATE", "Monto ofrecido", "Vence en", ">Postularme<"):
            self.assertNotIn(private, html)

    def test_individual_and_combined_filters(self):
        for query in ("industria=Construcci%C3%B3n", "categoria=Electricidad", "rubro=Tableros", "ubicacion=Palermo", "industria=Construcci%C3%B3n&categoria=Electricidad&rubro=Tableros&ubicacion=Palermo"):
            with self.subTest(query=query):
                html = self.html("?" + query)
                self.assertIn("8 propuestas publicadas", html)
                self.assertIn("Trabajo 15", html)
                self.assertNotIn("Trabajo 14", html)
        self.assertIn("No encontramos coincidencias", self.html("?rubro=Inexistente"))
        self.assertIn('href="/propuestas">Limpiar filtros', self.html("?ubicacion=Palermo"))

    def test_recent_pagination_and_out_of_range(self):
        html = self.html()
        self.assertLess(html.index("Trabajo 15"), html.index("Trabajo 14"))
        self.assertNotIn("Trabajo 01", html)
        self.assertIn("Trabajo 01", self.html("?page=2"))
        self.assertIn("Esta página no tiene propuestas", self.html("?page=99"))
        self.assertIn("ubicacion=Palermo&amp;page=2&amp;per_page=2", self.html("?ubicacion=Palermo&per_page=2"))

    def test_invalid_parameters_and_safe_errors(self):
        for query in ("page=-1", "page=0", "page=9999999999999", "page=oops", "per_page=51", "per_page=0", "page=1&page=2", "rubro=a&rubro=b", "ubicacion=" + "x" * 121):
            with self.subTest(query=query):
                response = self.client.get("/propuestas?" + query)
                self.assertEqual(response.status_code, 400)
                self.assertNotIn("Traceback", response.get_data(as_text=True))
                self.assertIn("Revisá los filtros de búsqueda", response.get_data(as_text=True))
        self.assertIn("15 propuestas publicadas", self.html("?unknown=value"))
        self.assertIn("No encontramos coincidencias", self.html("?rubro=%27%20OR%201%3D1--"))

    def test_escaped_content_and_filters(self):
        with self.app.app_context():
            proposal = db.session.get(ProposalRequest, 15)
            proposal.titulo = '<script>alert("title")</script>'
            proposal.descripcion = '<img src=x onerror="alert(1)">'
            db.session.commit()
        html = self.html()
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;img", html)
        self.assertNotIn('<img src=x', html)
        html = self.html('?ubicacion=%22%3E%3Cscript%3Ealert(1)%3C/script%3E')
        self.assertNotIn('<script>alert(1)', html)

    def test_get_does_not_write_and_queries_do_not_grow_per_card(self):
        statements = []
        def record(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement.lstrip().upper())
        with self.app.app_context():
            engine = db.engine
            event.listen(engine, "before_cursor_execute", record)
            try:
                with patch.object(db.session, "commit") as commit:
                    self.html("?per_page=1")
                    one = sum(s.startswith("SELECT") for s in statements)
                    statements.clear()
                    self.html("?per_page=50")
                    many = sum(s.startswith("SELECT") for s in statements)
                    commit.assert_not_called()
                    self.assertEqual(one, many)
                    self.assertFalse(any(s.startswith(("INSERT", "UPDATE", "DELETE")) for s in statements))
            finally:
                event.remove(engine, "before_cursor_execute", record)

    def test_central_eligibility_and_persisted_roles(self):
        self.login()
        html = self.html()
        self.assertIn("Necesitás una verificación aprobada", html)
        self.assertNotIn(">Postularme<", html)
        self.assertNotIn('action="/propuestas/14/postular"', self.client.get('/propuestas/14').get_data(as_text=True))
        with self.app.app_context():
            db.session.add(VerificationRequest(user_id=2, tipo_usuario="PROFESIONAL", estado="APROBADO"))
            db.session.commit()
        self.assertIn(">Postularme<", self.html())
        self.assertIn("Ya te postulaste", self.html())
        self.assertIn('action="/propuestas/14/postular"', self.client.get('/propuestas/14').get_data(as_text=True))
        self.login(1)
        self.assertNotIn(">Postularme<", self.html())

    def test_empty_catalog(self):
        with self.app.app_context():
            ProposalRequest.query.update({"estado": "CERRADA"})
            db.session.commit()
        self.assertIn("Todavía no hay propuestas publicadas", self.html())


    def test_navigation_canonical_for_anonymous_and_authenticated(self):
        for user in (None, 1, 2):
            if user:
                self.login(user)
            html = self.html()
            menu = html.split('aria-label="Operaciones principales"', 1)[1].split('</div>', 1)[0]
            self.assertRegex(menu, r'href="/propuestas"[^>]*aria-current="page"')
            self.assertNotIn('/?operacion=propuestas', menu)
            self.assertIn('/?operacion=contratacion', menu)
            self.assertIn('/urgencias/nueva', menu)

    def test_home_native_get_fields_and_other_modes(self):
        html = self.client.get('/').get_data(as_text=True)
        panel = html.split('id="operation-panel-proposal"', 1)[1].split('</section>', 1)[0]
        self.assertIn('action="/propuestas" method="GET"', panel)
        self.assertIn('name="rubro"', panel)
        self.assertIn('name="ubicacion"', panel)
        self.assertNotIn('name="categoria"', panel)
        self.assertIn('action="/buscar"', html)
        self.assertIn('/presupuestos/nuevo', html)
        self.assertIn('/urgencias/nueva', html)
        result = self.html('?' + urlencode({'rubro': 'Tableros', 'ubicacion': 'Palermo', 'per_page': 2}))
        self.assertIn('value="Tableros"', result)
        self.assertIn('value="Palermo"', result)
        self.assertIn('8 propuestas publicadas', result)
        self.assertIn('rubro=Tableros&amp;ubicacion=Palermo&amp;page=2', result)

    def test_removable_filter_chips_preserve_other_values_and_reset_page(self):
        html = self.html('?rubro=Tableros&ubicacion=Palermo&per_page=2&page=2')
        chips = html.split('aria-label="Filtros activos"', 1)[1].split('</nav>', 1)[0]
        links = [unescape(link) for link in re.findall(r'href="([^"]+)"', chips)]
        self.assertEqual(len(links), 2)
        queries = [parse_qs(urlsplit(link).query) for link in links]
        self.assertEqual(queries, [{'ubicacion': ['Palermo'], 'per_page': ['2']}, {'rubro': ['Tableros'], 'per_page': ['2']}])
        for link in links:
            self.assertEqual(self.client.get(link).status_code, 200)
        self.assertNotIn('aria-label="Filtros activos"', self.html())
