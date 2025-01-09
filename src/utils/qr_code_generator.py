import io
import qrcode


def generate_qr_code(url_link: str):

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    qr_image_bytes = io.BytesIO()
    img.save(qr_image_bytes, format="PNG")
    qr_image_bytes.seek(0)

    return qr_image_bytes.read()
