import json
import os
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from time import time
from urllib import parse, request
from uuid import uuid4

from flask import current_app

from app.models.professional_media import ProfessionalMedia


@dataclass(frozen=True)
class StoredImage:
    provider: str
    storage_key: str
    public_url: str
    secure_url: str
    thumbnail_url: str


class MediaStorageError(RuntimeError):
    pass


class BaseMediaStorage:
    provider = None

    def upload_image(self, processed_image, media_type):
        raise NotImplementedError

    def delete_image(self, storage_key):
        raise NotImplementedError

    def generate_thumbnail_url(self, storage_key, public_url):
        raise NotImplementedError

    def get_public_url(self, storage_key):
        raise NotImplementedError


class LocalMediaStorage(BaseMediaStorage):
    provider = ProfessionalMedia.PROVIDER_LOCAL

    def __init__(self, upload_root=None, public_base_url=None):
        self.upload_root = Path(upload_root or current_app.config["LOCAL_MEDIA_UPLOAD_ROOT"]).resolve()
        self.public_base_url = (public_base_url or current_app.config["LOCAL_MEDIA_PUBLIC_BASE_URL"]).rstrip("/")

    def upload_image(self, processed_image, media_type):
        media_dir = media_type.lower()
        storage_id = uuid4().hex
        storage_key = f"{media_dir}/{storage_id}.{processed_image.extension}"
        thumb_storage_key = f"{media_dir}/{storage_id}_thumb.{processed_image.extension}"

        target = (self.upload_root / storage_key).resolve()
        thumb_target = (self.upload_root / thumb_storage_key).resolve()
        if not str(target).startswith(str(self.upload_root)):
            raise MediaStorageError("Ruta de almacenamiento invalida")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(processed_image.image_bytes)
        thumb_target.write_bytes(processed_image.thumbnail_bytes)

        return StoredImage(
            provider=self.provider,
            storage_key=storage_key,
            public_url=f"{self.public_base_url}/{storage_key.replace(os.sep, '/')}",
            secure_url=f"{self.public_base_url}/{storage_key.replace(os.sep, '/')}",
            thumbnail_url=f"{self.public_base_url}/{thumb_storage_key.replace(os.sep, '/')}",
        )

    def delete_image(self, storage_key):
        for key in (storage_key, _thumbnail_key(storage_key)):
            target = (self.upload_root / key).resolve()
            if str(target).startswith(str(self.upload_root)) and target.exists():
                target.unlink()

    def generate_thumbnail_url(self, storage_key, public_url):
        return f"{self.public_base_url}/{_thumbnail_key(storage_key).replace(os.sep, '/')}"

    def get_public_url(self, storage_key):
        return f"{self.public_base_url}/{storage_key.replace(os.sep, '/')}"


class CloudinaryMediaStorage(BaseMediaStorage):
    provider = ProfessionalMedia.PROVIDER_CLOUDINARY

    def __init__(self):
        self.cloud_name = current_app.config.get("CLOUDINARY_CLOUD_NAME")
        self.api_key = current_app.config.get("CLOUDINARY_API_KEY")
        self.api_secret = current_app.config.get("CLOUDINARY_API_SECRET")
        self.folder = current_app.config.get("CLOUDINARY_FOLDER") or "trax/professional_media"
        if not self.cloud_name or not self.api_key or not self.api_secret:
            raise MediaStorageError("Cloudinary no configurado")

    def upload_image(self, processed_image, media_type):
        public_id = uuid4().hex
        timestamp = str(int(time()))
        params_to_sign = {
            "folder": f"{self.folder}/{media_type.lower()}",
            "public_id": public_id,
            "timestamp": timestamp,
        }
        signature = self._sign(params_to_sign)
        fields = {
            **params_to_sign,
            "api_key": self.api_key,
            "signature": signature,
        }
        upload_url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}/image/upload"
        body, content_type = _multipart_body(fields, "file", f"asset.{processed_image.extension}", processed_image.image_bytes)
        req = request.Request(upload_url, data=body, headers={"Content-Type": content_type}, method="POST")

        try:
            with request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except OSError as error:
            raise MediaStorageError("No se pudo subir la imagen al proveedor") from error

        secure_url = payload.get("secure_url")
        storage_key = payload.get("public_id") or public_id
        if not secure_url:
            raise MediaStorageError("Respuesta invalida del proveedor de imagenes")

        return StoredImage(
            provider=self.provider,
            storage_key=storage_key,
            public_url=payload.get("url") or secure_url,
            secure_url=secure_url,
            thumbnail_url=self.generate_thumbnail_url(storage_key, secure_url),
        )

    def delete_image(self, storage_key):
        timestamp = str(int(time()))
        params = {"public_id": storage_key, "timestamp": timestamp}
        fields = {
            **params,
            "api_key": self.api_key,
            "signature": self._sign(params),
        }
        delete_url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}/image/destroy"
        body = parse.urlencode(fields).encode("utf-8")
        req = request.Request(delete_url, data=body, method="POST")
        try:
            request.urlopen(req, timeout=20).close()
        except OSError as error:
            raise MediaStorageError("No se pudo eliminar la imagen del proveedor") from error

    def generate_thumbnail_url(self, storage_key, public_url):
        return public_url.replace("/upload/", "/upload/c_fill,w_480,h_360,q_auto,f_auto/")

    def get_public_url(self, storage_key):
        return f"https://res.cloudinary.com/{self.cloud_name}/image/upload/{storage_key}"

    def _sign(self, params):
        raw = "&".join(f"{key}={params[key]}" for key in sorted(params))
        return sha1(f"{raw}{self.api_secret}".encode("utf-8")).hexdigest()


def get_media_storage():
    provider = (current_app.config.get("MEDIA_STORAGE_PROVIDER") or "local").lower()
    if provider == ProfessionalMedia.PROVIDER_CLOUDINARY:
        return CloudinaryMediaStorage()

    return LocalMediaStorage()


def _thumbnail_key(storage_key):
    if "." not in storage_key:
        return f"{storage_key}_thumb"

    base, extension = storage_key.rsplit(".", 1)
    return f"{base}_thumb.{extension}"


def _multipart_body(fields, file_field, filename, file_bytes):
    boundary = f"----trax{uuid4().hex}"
    chunks = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}\r\n".encode("utf-8"))
    chunks.append(
        (
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
    )
    chunks.append(file_bytes)
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"
