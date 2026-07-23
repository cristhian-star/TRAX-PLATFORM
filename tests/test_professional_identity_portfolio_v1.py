import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import patch


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

from PIL import Image

from app import create_app, db
from app.config.config import TestingConfig
from app.models.audit_log import AuditLog
from app.models.professional import Professional
from app.models.professional_media import ProfessionalMedia
from app.models.user import User
from app.services.media_image_service import process_uploaded_image
from app.services.media_storage_service import CloudinaryMediaStorage, LocalMediaStorage
from app.services.professional_media_service import (
    MAX_GALLERY_IMAGES,
    build_professional_media_context,
    get_professionals_avatar_context,
    reorder_professional_gallery,
    soft_delete_professional_media,
    upload_professional_media,
)


def image_file(name="test.jpg", fmt="JPEG", size=(80, 60), exif=False):
    image = Image.new("RGB", size, color=(20, 120, 180))
    output = BytesIO()
    kwargs = {"format": fmt}
    if exif:
        metadata = Image.Exif()
        metadata[0x010E] = "descripcion privada"
        kwargs["exif"] = metadata
    image.save(output, **kwargs)
    output.seek(0)
    output.filename = name
    return output


class ProfessionalIdentityPortfolioTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app(config_class=TestingConfig, initialize_schema=False)
        self.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            RATELIMIT_ENABLED=False,
            SERVER_NAME="localhost",
            LOCAL_MEDIA_UPLOAD_ROOT=self.tmp.name,
            LOCAL_MEDIA_PUBLIC_BASE_URL="/media-test",
            MEDIA_STORAGE_PROVIDER="local",
            MEDIA_AUTO_PUBLISH=True,
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.owner = User(nombre="Profesional", email="pro-media@trax.test", password="hash", rol="PROFESIONAL")
            self.other = User(nombre="Otro", email="otro-media@trax.test", password="hash", rol="PROFESIONAL")
            self.admin = User(nombre="Admin", email="admin-media@trax.test", password="hash", rol="SUPER_ADMIN")
            db.session.add_all([self.owner, self.other, self.admin])
            db.session.flush()
            self.professional = Professional(
                user_id=self.owner.id,
                nombre="Media Pro",
                servicio="Electricidad",
                especialidad="Electricidad",
                zona="CABA",
                telefono="5491100003003",
                descripcion="Perfil con media",
                logo_url="https://legacy.test/logo.jpg",
                cover_url="https://legacy.test/cover.jpg",
                gallery_urls="https://legacy.test/one.jpg",
                portfolio_urls="https://legacy.test/two.jpg",
                perfil_completo=True,
            )
            self.other_professional = Professional(
                user_id=self.other.id,
                nombre="Otro Pro",
                servicio="Gas",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add_all([self.professional, self.other_professional])
            db.session.commit()
            self.owner_id = self.owner.id
            self.other_id = self.other.id
            self.admin_id = self.admin.id
            self.professional_id = self.professional.id
            self.other_professional_id = self.other_professional.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tmp.cleanup()

    def login(self, user_id, role="PROFESIONAL"):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_name"] = "Tester"
            sess["user_role"] = role

    def test_process_valid_image_reencodes_strips_exif_and_calculates_checksum(self):
        processed = process_uploaded_image(image_file(exif=True))

        self.assertEqual(processed.content_type, "image/jpeg")
        self.assertEqual(processed.width, 80)
        self.assertEqual(processed.height, 60)
        self.assertEqual(len(processed.checksum_sha256), 64)
        processed_image = Image.open(BytesIO(processed.image_bytes))
        self.assertEqual(len(processed_image.getexif()), 0)

    def test_rejects_false_mime_extension_corrupt_file_size_and_dimensions(self):
        with self.assertRaises(ValueError):
            process_uploaded_image(image_file(name="fake.png", fmt="JPEG"))

        declared_mismatch = image_file(name="declared.jpg", fmt="JPEG")
        declared_mismatch.mimetype = "image/png"
        with self.assertRaises(ValueError):
            process_uploaded_image(declared_mismatch)

        corrupt = BytesIO(b"not-image")
        corrupt.filename = "bad.jpg"
        with self.assertRaises(ValueError):
            process_uploaded_image(corrupt)

        too_large = BytesIO(b"x" * (5 * 1024 * 1024 + 1))
        too_large.filename = "large.jpg"
        with self.assertRaises(ValueError):
            process_uploaded_image(too_large)

        with patch("app.services.media_image_service.MAX_IMAGE_WIDTH", 10):
            with self.assertRaises(ValueError):
                process_uploaded_image(image_file())

    def test_local_storage_upload_and_delete(self):
        with self.app.app_context():
            storage = LocalMediaStorage(upload_root=self.tmp.name, public_base_url="/media-test")
            processed = process_uploaded_image(image_file())
            stored = storage.upload_image(processed, ProfessionalMedia.TYPE_GALLERY)

            self.assertTrue(stored.public_url.startswith("/media-test/gallery/"))
            self.assertTrue(stored.thumbnail_url.endswith("_thumb.jpg"))
            storage.delete_image(stored.storage_key)

    def test_upload_avatar_replaces_previous_and_keeps_legacy_fallback(self):
        with self.app.app_context():
            first = upload_professional_media(self.owner_id, image_file("one.jpg"), ProfessionalMedia.TYPE_AVATAR)
            second = upload_professional_media(self.owner_id, image_file("two.jpg"), ProfessionalMedia.TYPE_AVATAR)

            self.assertEqual(second.status, ProfessionalMedia.STATUS_PUBLISHED)
            self.assertEqual(
                ProfessionalMedia.query.filter_by(
                    professional_id=self.professional_id,
                    media_type=ProfessionalMedia.TYPE_AVATAR,
                    status=ProfessionalMedia.STATUS_PUBLISHED,
                ).count(),
                1,
            )
            self.assertEqual(db.session.get(ProfessionalMedia, first.id).status, ProfessionalMedia.STATUS_DELETED)
            context = build_professional_media_context(db.session.get(Professional, self.professional_id))
            self.assertEqual(context["avatar_url"], second.thumbnail_url)

    def test_gallery_limit_and_primary(self):
        with self.app.app_context():
            for index in range(MAX_GALLERY_IMAGES):
                upload_professional_media(self.owner_id, image_file(f"{index}.jpg"), ProfessionalMedia.TYPE_GALLERY)

            with self.assertRaises(ValueError):
                upload_professional_media(self.owner_id, image_file("overflow.jpg"), ProfessionalMedia.TYPE_GALLERY)

    def test_ownership_blocks_delete_from_other_user(self):
        with self.app.app_context():
            media = upload_professional_media(self.owner_id, image_file(), ProfessionalMedia.TYPE_GALLERY)
            with self.assertRaises(PermissionError):
                soft_delete_professional_media(self.other_id, media.id)

    def test_reorder_rejects_foreign_media_ids(self):
        with self.app.app_context():
            own_media = upload_professional_media(self.owner_id, image_file("own.jpg"), ProfessionalMedia.TYPE_GALLERY)
            foreign_media = upload_professional_media(self.other_id, image_file("foreign.jpg"), ProfessionalMedia.TYPE_GALLERY)

            with self.assertRaises(PermissionError):
                reorder_professional_gallery(self.owner_id, [own_media.id, foreign_media.id])

    def test_private_upload_route_creates_media_and_audit(self):
        self.login(self.owner_id)
        response = self.client.post(
            "/profesional/media/galeria",
            data={
                "image": (image_file("route.jpg"), "route.jpg"),
                "title": "Trabajo route",
                "alt_text": "Tablero terminado",
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            media = ProfessionalMedia.query.filter_by(title="Trabajo route").one()
            self.assertEqual(media.status, ProfessionalMedia.STATUS_PUBLISHED)
            self.assertGreaterEqual(AuditLog.query.count(), 1)

    def test_csrf_invalid_is_rejected_for_upload(self):
        csrf_app = create_app(config_class=TestingConfig, initialize_schema=False)
        csrf_app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=True,
            RATELIMIT_ENABLED=False,
            SERVER_NAME="localhost",
            LOCAL_MEDIA_UPLOAD_ROOT=self.tmp.name,
        )
        csrf_client = csrf_app.test_client()
        with csrf_app.app_context():
            db.drop_all()
            db.create_all()
            user = User(nombre="Pro CSRF", email="csrf-media@trax.test", password="hash", rol="PROFESIONAL")
            db.session.add(user)
            db.session.flush()
            db.session.add(Professional(user_id=user.id, nombre="Pro CSRF", servicio="Gas", zona="CABA"))
            db.session.commit()
            user_id = user.id

        with csrf_client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_role"] = "PROFESIONAL"

        response = csrf_client.post(
            "/profesional/media/avatar",
            data={"image": (image_file("csrf.jpg"), "csrf.jpg")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)

        with csrf_app.app_context():
            db.session.remove()
            db.drop_all()

    def test_public_profile_hides_rejected_media_and_uses_legacy_fallback(self):
        with self.app.app_context():
            media = upload_professional_media(self.owner_id, image_file(), ProfessionalMedia.TYPE_GALLERY)
            media.status = ProfessionalMedia.STATUS_REJECTED
            media_public_url = media.public_url
            db.session.commit()

        response = self.client.get(f"/profesional/{self.professional_id}")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("https://legacy.test/logo.jpg", body)
        self.assertIn("https://legacy.test/one.jpg", body)
        self.assertNotIn(media_public_url, body)

    def test_admin_can_moderate_media(self):
        with self.app.app_context():
            media = upload_professional_media(self.owner_id, image_file(), ProfessionalMedia.TYPE_GALLERY)
            media.status = ProfessionalMedia.STATUS_PENDING
            db.session.commit()
            media_id = media.id

        self.login(self.admin_id, role="SUPER_ADMIN")
        response = self.client.post(f"/admin/media/{media_id}/rechazar", data={"motivo": "Contenido no aprobado"})

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            media = db.session.get(ProfessionalMedia, media_id)
            self.assertEqual(media.status, ProfessionalMedia.STATUS_REJECTED)
            self.assertEqual(media.reviewed_by_user_id, self.admin_id)

    def test_avatar_context_uses_single_query_scope_and_legacy_fallback(self):
        with self.app.app_context():
            upload_professional_media(self.owner_id, image_file(), ProfessionalMedia.TYPE_AVATAR)
            professionals = Professional.query.order_by(Professional.id.asc()).all()
            context = get_professionals_avatar_context(professionals)

            self.assertIn(self.professional_id, context)
            self.assertTrue(context[self.professional_id]["avatar_url"].startswith("/media-test/avatar/"))
            self.assertIsNone(context[self.other_professional_id]["avatar_url"])

    def test_cloudinary_requires_configuration_without_exposing_secrets(self):
        with self.app.app_context():
            self.app.config.update(
                CLOUDINARY_CLOUD_NAME=None,
                CLOUDINARY_API_KEY=None,
                CLOUDINARY_API_SECRET=None,
            )
            with self.assertRaises(Exception) as context:
                CloudinaryMediaStorage()

        self.assertNotIn("API_SECRET", str(context.exception))


if __name__ == "__main__":
    unittest.main()
