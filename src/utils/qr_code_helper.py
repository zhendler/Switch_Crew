from io import BytesIO

import cloudinary.uploader
import qrcode


def generate_qr_code(image_url: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(image_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)
    uploaded_image_url = cloudinary.uploader.upload(img_io, folder="qr_codes/")
    return uploaded_image_url["secure_url"]