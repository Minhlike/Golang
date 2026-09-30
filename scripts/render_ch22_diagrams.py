"""Render the two editable, grayscale Chapter 22 diagrams at print resolution."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pymupdf
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "diagrams"
INK = colors.HexColor("#171717")
MID = colors.HexColor("#595959")
RULE = colors.HexColor("#A8A8A8")
PALE = colors.HexColor("#F5F5F5")
WHITE = colors.white


def register_fonts() -> None:
    fonts = ROOT / "assets" / "fonts"
    pdfmetrics.registerFont(TTFont("Diagram", str(fonts / "SourceSans3-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("DiagramBold", str(fonts / "SourceSans3-Semibold.ttf")))


def label(c: canvas.Canvas, x: float, y: float, value: str, *, size: int = 18,
          bold: bool = False, color=INK) -> None:
    c.setFillColor(color)
    c.setFont("DiagramBold" if bold else "Diagram", size)
    c.drawString(x, y, value)


def card(c: canvas.Canvas, x: int, y: int, width: int, title: str,
         detail: str, *, muted: bool = False) -> None:
    c.setStrokeColor(MID if not muted else RULE)
    c.setLineWidth(1.6)
    c.setFillColor(PALE if not muted else WHITE)
    c.roundRect(x, y, width, 88, 10, stroke=1, fill=1)
    label(c, x + 15, y + 55, title, size=22, bold=True)
    label(c, x + 15, y + 25, detail, size=20, color=MID)


def arrow(c: canvas.Canvas, points: list[tuple[int, int]], *, dashed: bool = False,
          color=INK) -> None:
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(2.1)
    c.setDash(7, 5) if dashed else c.setDash()
    path = c.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    c.drawPath(path)
    c.setDash()
    (x0, y0), (x1, y1) = points[-2:]
    if x1 > x0:
        tip = [(x1, y1), (x1 - 11, y1 + 6), (x1 - 11, y1 - 6)]
    elif x1 < x0:
        tip = [(x1, y1), (x1 + 11, y1 + 6), (x1 + 11, y1 - 6)]
    elif y1 > y0:
        tip = [(x1, y1), (x1 - 6, y1 - 11), (x1 + 6, y1 - 11)]
    else:
        tip = [(x1, y1), (x1 - 6, y1 + 11), (x1 + 6, y1 + 11)]
    head = c.beginPath()
    head.moveTo(*tip[0])
    head.lineTo(*tip[1])
    head.lineTo(*tip[2])
    head.close()
    c.drawPath(head, stroke=0, fill=1)


def architecture(c: canvas.Canvas) -> None:
    label(c, 26, 533, "LUỒNG SỰ KIỆN", size=16, bold=True, color=MID)
    label(c, 26, 496, "Từ Watch đến một lần điều hòa", size=31, bold=True)
    c.setStrokeColor(RULE)
    c.line(26, 481, 874, 481)
    label(c, 26, 455, "01  NHẬN VÀ PHÂN PHỐI BIẾN ĐỘNG", size=16, bold=True, color=MID)
    for x, title, detail in [
        (26, "API Server", "nguồn thẩm quyền"),
        (244, "Reflector", "List / Watch"),
        (462, "DeltaFIFO", "gom thay đổi"),
        (680, "SharedInformer", "cập nhật · phát"),
    ]:
        card(c, x, 355, 194, title, detail)
    for x0, x1 in [(220, 242), (438, 460), (656, 678)]:
        arrow(c, [(x0, 399), (x1, 399)])

    label(c, 26, 317, "02  XẾP LỊCH VÀ XỬ LÝ THEO KEY", size=16, bold=True, color=MID)
    card(c, 26, 200, 194, "Worker", "điều hòa · ghi")
    card(c, 244, 200, 194, "WorkQueue", "gộp key · retry")
    card(c, 462, 200, 194, "Event handler", "tạo key")
    card(c, 680, 200, 194, "Indexer", "cache cục bộ", muted=True)
    arrow(c, [(462, 244), (440, 244)])
    arrow(c, [(244, 244), (222, 244)])
    arrow(c, [(721, 355), (721, 326), (559, 326), (559, 290)])
    label(c, 569, 303, "phát key", size=15, color=MID)
    arrow(c, [(803, 355), (803, 290)], dashed=True, color=MID)
    label(c, 812, 321, "cập nhật", size=15, color=MID)
    arrow(c, [(776, 200), (776, 153), (123, 153), (123, 198)],
          dashed=True, color=MID)
    label(c, 310, 167, "Worker đọc lại snapshot cục bộ", size=20, color=MID)
    c.setStrokeColor(RULE)
    c.line(26, 117, 874, 117)
    label(c, 26, 86, "Sự kiện là tín hiệu, không phải trạng thái để quyết định.", size=20)
    label(c, 26, 55, "Cache có thể trễ so với API Server; chọn API read nếu cần dữ liệu mới hơn.",
          size=20, color=MID)


def sequence(c: canvas.Canvas) -> None:
    label(c, 26, 485, "TRÌNH TỰ LIST / WATCH", size=16, bold=True, color=MID)
    label(c, 26, 448, "Giữ mốc quan sát qua mất kết nối", size=31, bold=True)
    c.setStrokeColor(RULE)
    c.line(26, 433, 874, 433)
    card(c, 70, 325, 225, "Reflector", "client-go")
    card(c, 605, 325, 225, "API Server", "Kubernetes")
    for x in (182, 717):
        c.setStrokeColor(RULE)
        c.setDash(6, 5)
        c.line(x, 325, x, 150)
        c.setDash()
    arrow(c, [(183, 305), (705, 305)])
    label(c, 312, 313, "1   LIST /api/v1/pods", size=18, bold=True)
    arrow(c, [(716, 262), (194, 262)], color=MID)
    label(c, 320, 270, "Pods + resourceVersion", size=18)
    arrow(c, [(183, 219), (705, 219)])
    label(c, 296, 227, "2   WATCH từ resourceVersion", size=18, bold=True)
    arrow(c, [(716, 176), (194, 176)], color=MID)
    label(c, 282, 184, "ADDED / MODIFIED / DELETED", size=18)
    c.setStrokeColor(RULE)
    c.line(26, 139, 874, 139)
    label(c, 26, 108, "Sau khi đứt mạng: thử Watch từ mốc đã biết.", size=19)
    label(c, 26, 79, "Nếu lịch sử không còn (410 Gone): List lại để tái lập snapshot.",
          size=18, color=MID)


def main() -> None:
    register_fonts()
    for stem, height, draw in [
        ("client-go-controller-flow", 570, architecture),
        ("client-go-list-watch", 520, sequence),
    ]:
        stream = BytesIO()
        c = canvas.Canvas(stream, pagesize=(900, height), pageCompression=1)
        draw(c)
        c.save()
        pdf = pymupdf.open(stream=stream.getvalue(), filetype="pdf")
        pix = pdf[0].get_pixmap(matrix=pymupdf.Matrix(2, 2),
                                colorspace=pymupdf.csGRAY, alpha=False)
        pix.save(str(OUT / f"{stem}.png"))


if __name__ == "__main__":
    main()
