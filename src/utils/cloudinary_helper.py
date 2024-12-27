import cloudinary
from cloudinary import CloudinaryImage
import cloudinary.uploader
import cloudinary.api


def generate_transformed_image_url(
    public_id: str, width: int, height: int, crop_mode="fill"
):
    return cloudinary.CloudinaryImage(public_id).build_url(
        transformation=[
            {"width": width, "height": height, "crop": crop_mode, "gravity": "auto"}
        ]
    )

def generate_transformed_url(image_name, **kwargs):
    return CloudinaryImage(image_name).build_url(**kwargs)
