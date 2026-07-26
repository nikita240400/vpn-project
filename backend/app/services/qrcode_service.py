import base64
from io import BytesIO

import qrcode


def generate_qr_base64(data: str) -> str:
    qr = qrcode.make(data)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode("utf-8")