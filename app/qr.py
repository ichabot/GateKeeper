"""QR-code generation as a compact, scalable SVG (no Pillow dependency)."""

import qrcode


def qr_svg(data: str, quiet: int = 2, dark: str = "#14233f") -> str:
    """Return an SVG string encoding *data* (real, scannable QR code)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=quiet,
    )
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    n = len(matrix)

    rects = []
    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if val:
                rects.append(f'<rect x="{x}" y="{y}" width="1" height="1"/>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" '
        f'shape-rendering="crispEdges" role="img" aria-label="QR">'
        f'<rect width="{n}" height="{n}" fill="#ffffff"/>'
        f'<g fill="{dark}">{"".join(rects)}</g></svg>'
    )
