"""Creation validation through HTTP and the direct service, isolated SQLite."""
import unittest
from unittest.mock import patch
from sqlalchemy import event
from app import db
from app.models.proposal_request import ProposalRequest
from app.services.proposal_service import create_proposal_request, PROPOSAL_MODALITIES
import tests.test_proposal_portal_p1 as fixtures


class ProposalCreationValidationTest(unittest.TestCase):
    setUp = fixtures.ProposalPortalTest.setUp
    tearDown = fixtures.ProposalPortalTest.tearDown
    login = fixtures.ProposalPortalTest.login

    def data(self):
        return dict(industria='Construccion', categoria='Electricidad', rubro='Electricista',
                    especialidad='Industrial', titulo='Proyecto QA', descripcion='<b>Conservar</b>',
                    ubicacion='CABA', modalidad='Presencial', cantidad_profesionales='1')

    def invalid(self):
        return [('cantidad_profesionales', v) for v in ('0','-1','51','1.5','abc','NaN','Infinity','1e1')]+[
            ('titulo','x'*161),('descripcion','x'*1801),('modalidad','Teleport'),
            ('titulo','   '),('descripcion','   '),('modalidad','')]

    def test_http_invalid_both_roles_no_writes_and_recovery(self):
        for actor in (1,2):
            self.login(actor)
            for field,value in self.invalid():
                with self.subTest(actor=actor,field=field,value=value[:20]):
                    data=self.data();data[field]=value
                    writes=[]
                    def track(conn,cursor,statement,parameters,context,many):
                        if statement.lstrip().split()[0].upper() in ('INSERT','UPDATE','DELETE'):
                            writes.append(statement)
                    with self.app.app_context():
                        event.listen(db.engine,'before_cursor_execute',track)
                        try:
                            with patch('app.routes.operation_routes.notify_proposal_created') as notify:
                                response=self.client.post('/propuestas/nueva?vista=publicaciones',data=data)
                                notify.assert_not_called()
                            self.assertFalse(writes)
                        finally: event.remove(db.engine,'before_cursor_execute',track)
                    self.assertEqual(response.status_code,400)
                    self.assertNotIn('Location',response.headers)
                    if field != 'descripcion':self.assertIn('&lt;b&gt;Conservar&lt;/b&gt;',response.text)
                    if field == 'cantidad_profesionales':self.assertIn('value="'+value+'"',response.text)
                    if field == 'modalidad':
                        self.assertIn('<option value="" selected>Seleccionar modalidad válida</option>',response.text)
                        self.assertNotIn('<option value="Teleport"',response.text)
                    self.assertEqual('pc-create' in response.text,actor==2)

    def test_direct_invalid_cannot_bypass_or_write(self):
        for actor in (1,2):
            for field,value in self.invalid()+[('cantidad_profesionales',1.5),('cantidad_profesionales',True)]:
                with self.subTest(actor=actor,field=field,value=str(value)[:20]),self.app.app_context():
                    data=self.data();data[field]=value
                    with patch.object(db.session,'add') as add,patch.object(db.session,'commit') as commit:
                        with self.assertRaises(ValueError):create_proposal_request(owner_user_id=actor,**data)
                        add.assert_not_called();commit.assert_not_called()

    def test_valid_boundaries_modes_normalized_and_single(self):
        for actor in (1,2):
            self.login(actor)
            for mode in PROPOSAL_MODALITIES:
                for quantity in ('1','50'):
                    data=self.data();data.update(titulo='  '+'t'*160+'  ',descripcion='  '+'d'*1800+'  ',modalidad=mode,cantidad_profesionales=quantity)
                    response=self.client.post('/propuestas/nueva',data=data)
                    self.assertEqual(response.status_code,302)
                    with self.app.app_context():
                        row=ProposalRequest.query.order_by(ProposalRequest.id.desc()).first()
                        self.assertEqual((len(row.titulo),len(row.descripcion)),(160,1800))
                        self.assertEqual((row.cantidad_profesionales,row.modalidad),(int(quantity),mode))
                        self.assertEqual(row.hiring_mode,'SINGLE')

    def test_direct_valid_defaults_and_boundaries(self):
        for actor in (1,2):
            for quantity,expected in ((None,1),('',1),('  ',1),(1,1),(50,50)):
                with self.app.app_context():
                    data=self.data();data.update(titulo=' '+'t'*160+' ',descripcion=' '+'d'*1800+' ',cantidad_profesionales=quantity)
                    row=create_proposal_request(owner_user_id=actor,**data)
                    self.assertEqual((row.cantidad_profesionales,len(row.titulo),len(row.descripcion)),(expected,160,1800))

    def test_http_absent_empty_defaults(self):
        for actor in (1,2):
            self.login(actor)
            for absent in (True,False):
                data=self.data()
                if absent:data.pop('cantidad_profesionales')
                else:data['cantidad_profesionales']=''
                self.assertEqual(self.client.post('/propuestas/nueva',data=data).status_code,302)
                with self.app.app_context():self.assertEqual(ProposalRequest.query.order_by(ProposalRequest.id.desc()).first().cantidad_profesionales,1)

    def test_corrected_resubmit_one_publication_and_notification(self):
        for actor in (1,2):
            self.login(actor)
            with self.app.app_context():count=ProposalRequest.query.count()
            data=self.data();data['cantidad_profesionales']='0'
            with patch('app.routes.operation_routes.notify_proposal_created') as notify:
                self.assertEqual(self.client.post('/propuestas/nueva',data=data).status_code,400)
                data['cantidad_profesionales']='1'
                self.assertEqual(self.client.post('/propuestas/nueva',data=data).status_code,302)
                notify.assert_called_once()
            with self.app.app_context():self.assertEqual(ProposalRequest.query.count(),count+1)

    def test_dates_money_and_csrf_stay_controlled(self):
        for actor in (1,2):
            self.login(actor)
            for field,value in [('fecha_inicio_estimada','not-date'),('fecha_limite_postulacion','2026-02-30')]+[('presupuesto_estimado',v) for v in ('NaN','sNaN','Infinity','-Infinity')]:
                data=self.data();data[field]=value
                self.assertEqual(self.client.post('/propuestas/nueva',data=data).status_code,400)
            self.app.config['WTF_CSRF_ENABLED']=True
            self.assertEqual(self.client.post('/propuestas/nueva',data=self.data()).status_code,400)
            self.app.config['WTF_CSRF_ENABLED']=False
