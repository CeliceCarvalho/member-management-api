from __future__ import annotations

import io
import os
from urllib.parse import quote
from uuid import uuid4

import oci
from PIL import Image, ImageOps, UnidentifiedImageError


MAX_UPLOAD_SIZE = int(os.getenv("PROFILE_IMAGE_MAX_SIZE", str(5 * 1024 * 1024)))
FINAL_IMAGE_SIZE = int(os.getenv("PROFILE_IMAGE_SIZE", "768"))
WEBP_QUALITY = int(os.getenv("PROFILE_IMAGE_QUALITY", "82"))

ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


class InvalidProfileImageError(ValueError):
    """Erro de validacao da imagem de perfil."""


def optimize_profile_image(content: bytes) -> bytes:
    if not content:
        raise InvalidProfileImageError("O arquivo esta vazio.")

    if len(content) > MAX_UPLOAD_SIZE:
        raise InvalidProfileImageError("A imagem deve possuir no maximo 5 MB.")

    try:
        with Image.open(io.BytesIO(content)) as original:
            if original.format not in ALLOWED_IMAGE_FORMATS:
                raise InvalidProfileImageError("Envie uma imagem JPEG, PNG ou WebP.")

            image = ImageOps.exif_transpose(original)

            if image.mode == "RGBA":
                background = Image.new("RGB", image.size, "white")
                background.paste(image, mask=image.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")

            image = ImageOps.fit(
                image,
                (FINAL_IMAGE_SIZE, FINAL_IMAGE_SIZE),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.4),
            )

            output = io.BytesIO()
            image.save(output, format="WEBP", quality=WEBP_QUALITY, method=6)

            return output.getvalue()

    except InvalidProfileImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidProfileImageError("O arquivo enviado nao e uma imagem valida.") from exc


class ProfileImageStorage:
    def __init__(self) -> None:
        self.region = os.environ["OCI_REGION"]
        self.namespace = os.environ["OCI_NAMESPACE"]
        self.bucket_name = os.environ["OCI_BUCKET_NAME"]

        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

        self.client = oci.object_storage.ObjectStorageClient(
            config={},
            signer=signer,
            service_endpoint=f"https://objectstorage.{self.region}.oraclecloud.com",
        )

    def upload_member_image(self, *, image_content: bytes) -> tuple[str, str]:
        optimized_image = optimize_profile_image(image_content)
        object_name = f"members/{uuid4().hex}.webp"

        self.client.put_object(
            namespace_name=self.namespace,
            bucket_name=self.bucket_name,
            object_name=object_name,
            put_object_body=optimized_image,
            content_type="image/webp",
            cache_control="public, max-age=31536000, immutable",
        )

        return object_name, self.build_public_url(object_name)

    def delete(self, object_name: str | None) -> None:
        if not object_name:
            return

        self.client.delete_object(
            namespace_name=self.namespace,
            bucket_name=self.bucket_name,
            object_name=object_name,
        )

    def build_public_url(self, object_name: str) -> str:
        encoded_object_name = quote(object_name, safe="")

        return (
            f"https://objectstorage.{self.region}.oraclecloud.com"
            f"/n/{self.namespace}"
            f"/b/{self.bucket_name}"
            f"/o/{encoded_object_name}"
        )


profile_image_storage: ProfileImageStorage | None = None


def get_profile_image_storage() -> ProfileImageStorage:
    global profile_image_storage

    if profile_image_storage is None:
        profile_image_storage = ProfileImageStorage()

    return profile_image_storage
