"""Explicit gate: only the dedicated disposable proposals_qa instance."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from sqlalchemy.engine import make_url
from app import db
from app.models.user import User
from app.models.proposal_request import ProposalRequest
from app.models.proposal_application import ProposalApplication
from app.models.verification_request import VerificationRequest
from app.models.contract_request import ContractRequest
from app.services.proposal_service import accept_application, apply_to_proposal
from app.services.contract_service import require_client_owner
from tests.postgresql_contracting_fixture import PostgreSQLContractingFixture


class ProfessionalProposalsPostgres(PostgreSQLContractingFixture, unittest.TestCase):
    OWNER_ROLE = "PROFESIONAL"

    @classmethod
    def setUpClass(cls):
        url = make_url(os.environ['TRAX_POSTGRES_TEST_URL'])
        if (url.host,url.port,url.database) != ('127.0.0.1',55481,'proposals_qa'):
            raise RuntimeError('Only disposable proposals_qa on port 55481 is authorized')
        super().setUpClass()

    def setUp(self):
        super().setUp()
        with self.app.app_context():
            application=db.session.get(ProposalApplication,self.application_id)
            application.estado='POSTULADA'
            application.proposal.estado='PUBLICADA'
            self.proposal_id=application.proposal_id
            db.session.add(VerificationRequest(user_id=self.professional_user_id,tipo_usuario='PROFESIONAL',estado='APROBADO'))
            db.session.commit()

    def race(self, call):
        barrier=Barrier(2)
        def worker(_):
            with self.app.app_context():
                barrier.wait(timeout=10)
                return call()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker,[0,1]))

    def test_professional_acceptance_concurrency(self):
        results=self.race(lambda: accept_application(self.proposal_id,self.application_id,self.owner_id).contract.id)
        self.assertEqual(results[0],results[1])
        with self.app.app_context():
            self.assertEqual(self._counts(),dict(contracts=1,commands=0,events=2,audits=1,notifications=2))
            c=ContractRequest.query.one()
            self.assertEqual(c.estado,'CREADA')
            require_client_owner(c,self.owner_id)
            with self.assertRaises(PermissionError):require_client_owner(c,self.professional_user_id)
            proposal=db.session.get(ProposalRequest,self.proposal_id)
            self.assertEqual(proposal.estado,'CERRADA')
            self.assertEqual(proposal.hiring_mode,'SINGLE')

    def test_application_concurrency_no_duplicates(self):
        with self.app.app_context():
            db.session.delete(db.session.get(ProposalApplication,self.application_id));db.session.commit()
        def apply():
            try:return apply_to_proposal(self.proposal_id,self.professional_user_id,'QA').id
            except ValueError:
                db.session.rollback();return 'duplicate'
        result=self.race(apply)
        self.assertEqual(result.count('duplicate'),1)
        with self.app.app_context():self.assertEqual(ProposalApplication.query.count(),1)

    def test_acceptance_rollback(self):
        with self.app.app_context():
            with patch('app.services.proposal_service.create_contract_from_proposal_application',side_effect=RuntimeError('injected rollback')):
                with self.assertRaises(RuntimeError):accept_application(self.proposal_id,self.application_id,self.owner_id)
            self.assertEqual(db.session.get(ProposalApplication,self.application_id).estado,'POSTULADA')
            self.assertEqual(db.session.get(ProposalRequest,self.proposal_id).estado,'PUBLICADA')
            self.assertEqual(self._counts(),dict(contracts=0,commands=0,events=0,audits=0,notifications=0))

    def test_other_domains_keep_client_role(self):
        from app.services.contracting_core_service import create_contract_from_budget_offer
        with self.app.app_context():
            with self.assertRaises(PermissionError):create_contract_from_budget_offer(self.offer_id,actor_user_id=self.owner_id)
            with self.assertRaises(PermissionError):accept_application(self.proposal_id,self.application_id,self.professional_user_id)
            self.assertEqual(ContractRequest.query.count(),0)
