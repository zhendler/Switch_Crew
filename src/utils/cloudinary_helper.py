from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile


async def upload_photo_to_cloudinary(file: UploadFile):
    file_bytes = await file.read()

    response = cloudinary.uploader.upload(file_bytes, folder="user_photos/")

    return response["secure_url"]


def generate_transformed_image_url(
    public_id: str, width: int, height: int, crop_mode="fill"
):
    return cloudinary.CloudinaryImage(public_id).build_url(
        transformation=[
            {"width": width, "height": height, "crop": crop_mode, "gravity": "auto"}
        ]
    )


def get_cloudinary_image_id(url: str) -> str:
    parsed_url = urlparse(url)
    path = parsed_url.path
    parts = path.split("/")
    if "upload" in parts:
        upload_index = parts.index("upload")
        image_path = "/".join(parts[upload_index + 1 :])
        image_id = image_path.rsplit(".", 1)[0]
        return image_id
    return None
