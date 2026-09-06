from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
CONTENT_TYPES_BY_FORMAT = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_WIDTH = 6000
MAX_IMAGE_HEIGHT = 6000
THUMBNAIL_SIZE = (640, 480)


@dataclass(frozen=True)
class ProcessedImage:
    image_bytes: bytes
    thumbnail_bytes: bytes
    content_type: str
    extension: str
    width: int
    height: int
    file_size_bytes: int
    checksum_sha256: str


def _extension(filename):
    if not filename or "." not in filename:
        return ""

    return filename.rsplit(".", 1)[1].lower()


def _normalized_format(image):
    image_format = (image.format or "").upper()
    if image_format == "JPG":
        return "JPEG"

    return image_format


def _output_format(image_format):
    return "JPEG" if image_format == "JPEG" else image_format


def _output_extension(image_format):
    return "jpg" if image_format == "JPEG" else image_format.lower()


def _safe_image_copy(image, image_format):
    image = ImageOps.exif_transpose(image)
    if image_format == "JPEG" and image.mode not in ("RGB", "L"):
        return image.convert("RGB")
    if image_format in ("PNG", "WEBP") and image.mode not in ("RGB", "RGBA"):
        return image.convert("RGBA")

    return image.copy()


def _encode(image, image_format):
    output = BytesIO()
    save_kwargs = {"format": _output_format(image_format)}
    if image_format == "JPEG":
        save_kwargs.update({"quality": 85, "optimize": True})
    elif image_format == "PNG":
        save_kwargs.update({"optimize": True})
    elif image_format == "WEBP":
        save_kwargs.update({"quality": 85, "method": 6})

    image.save(output, **save_kwargs)
    return output.getvalue()


def process_uploaded_image(file_storage):
    filename = file_storage.filename or ""
    extension = _extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Formato de imagen no permitido")

    raw_bytes = file_storage.read()
    if not raw_bytes:
        raise ValueError("Imagen vacia o corrupta")
    if len(raw_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("La imagen supera el tamano maximo permitido")

    try:
        image = Image.open(BytesIO(raw_bytes))
        image.verify()
        image = Image.open(BytesIO(raw_bytes))
    except (UnidentifiedImageError, OSError):
        raise ValueError("Imagen invalida o corrupta") from None

    image_format = _normalized_format(image)
    if image_format not in ALLOWED_FORMATS:
        raise ValueError("Formato de imagen no permitido")
    if image_format == "GIF":
        raise ValueError("GIF animado no permitido")

    declared_content_type = (getattr(file_storage, "mimetype", "") or "").lower()
    real_content_type = CONTENT_TYPES_BY_FORMAT[image_format]
    if declared_content_type and declared_content_type not in (real_content_type, "application/octet-stream"):
        raise ValueError("El tipo MIME declarado no coincide con la imagen")

    if extension in ("jpg", "jpeg") and image_format != "JPEG":
        raise ValueError("La extension no coincide con el tipo real de imagen")
    if extension == "png" and image_format != "PNG":
        raise ValueError("La extension no coincide con el tipo real de imagen")
    if extension == "webp" and image_format != "WEBP":
        raise ValueError("La extension no coincide con el tipo real de imagen")

    width, height = image.size
    if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
        raise ValueError("La imagen supera las dimensiones maximas permitidas")

    safe_image = _safe_image_copy(image, image_format)
    image_bytes = _encode(safe_image, image_format)

    thumbnail = safe_image.copy()
    thumbnail.thumbnail(THUMBNAIL_SIZE)
    thumbnail_bytes = _encode(thumbnail, image_format)

    return ProcessedImage(
        image_bytes=image_bytes,
        thumbnail_bytes=thumbnail_bytes,
            content_type=real_content_type,
        extension=_output_extension(image_format),
        width=width,
        height=height,
        file_size_bytes=len(image_bytes),
        checksum_sha256=sha256(image_bytes).hexdigest(),
    )
