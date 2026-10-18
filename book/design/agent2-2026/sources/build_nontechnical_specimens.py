#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/build_nontechnical_specimens.py

Generates the Technical Minimalism Specimen Catalog for Non-Technical Objects:
  1. Trang Tiêu đề lót (Half-Title / Full Title Page)
  2. Mục lục tổng thể (Table of Contents)
  3. Trang Mở đầu chương (Chapter Opener)
  4. Header & Footer chạy trang đối xứng (Running Heads & Mirrored Folios)

Outputs:
  - book/design/agent2-2026/specimens/nontechnical_specimens.pdf
  - book/design/agent2-2026/specimens/specimen_p01_title_page.png
  - book/design/agent2-2026/specimens/specimen_p02_table_of_contents.png
  - book/design/agent2-2026/specimens/specimen_p03_chapter_opener.png
  - book/design/agent2-2026/specimens/specimen_p04_running_headers.png
"""

import sys
from pathlib import Path
import fitz  # PyMuPDF

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path("D:/Golang")
OUTPUT_DIR = BASE_DIR / "book" / "design" / "agent2-2026" / "specimens"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONTS_DIR = BASE_DIR / "assets" / "fonts"
OUTPUT_PDF = OUTPUT_DIR / "nontechnical_specimens.pdf"

# Register TrueType Fonts
pdfmetrics.registerFont(TTFont("BookSerif", str(FONTS_DIR / "SourceSerif4-Regular.ttf")))
pdfmetrics.registerFont(TTFont("BookSerifBold", str(FONTS_DIR / "SourceSerif4-Semibold.ttf")))
pdfmetrics.registerFont(TTFont("BookSans", str(FONTS_DIR / "SourceSans3-Regular.ttf")))
pdfmetrics.registerFont(TTFont("BookSansBold", str(FONTS_DIR / "SourceSans3-Semibold.ttf")))
pdfmetrics.registerFont(TTFont("BookMono", str(FONTS_DIR / "JetBrainsMono-Regular.ttf")))

# Page Geometry
PAGE_WIDTH = 210.0 * mm  # 595.28 pt
PAGE_HEIGHT = 297.0 * mm  # 841.89 pt
MARGIN_INSIDE = 24.0 * mm  # 68.03 pt
MARGIN_OUTSIDE = 18.0 * mm  # 51.02 pt
MARGIN_TOP = 22.0 * mm  # 62.36 pt
MARGIN_BOTTOM = 20.0 * mm  # 56.69 pt

PRINTABLE_WIDTH = PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE  # 168.0 mm (476.22 pt)
PRINTABLE_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM  # 255.0 mm (722.84 pt)


def get_styles():
    styles = {}
    styles["TitleMeta"] = ParagraphStyle(
        "TitleMeta", fontName="BookMono", fontSize=7.5, leading=10,
        textColor=colors.HexColor("#666666"), alignment=TA_LEFT
    )
    styles["MainTitle"] = ParagraphStyle(
        "MainTitle", fontName="BookSansBold", fontSize=34, leading=40,
        textColor=colors.HexColor("#000000"), alignment=TA_LEFT, spaceAfter=8
    )
    styles["SubTitle"] = ParagraphStyle(
        "SubTitle", fontName="BookSans", fontSize=11, leading=16,
        textColor=colors.HexColor("#333333"), alignment=TA_LEFT, spaceAfter=18
    )
    styles["Author"] = ParagraphStyle(
        "Author", fontName="BookSansBold", fontSize=10.5, leading=14,
        textColor=colors.HexColor("#111111"), alignment=TA_LEFT
    )
    styles["Colophon"] = ParagraphStyle(
        "Colophon", fontName="BookMono", fontSize=7.2, leading=11,
        textColor=colors.HexColor("#555555"), alignment=TA_LEFT
    )
    styles["TOCHeader"] = ParagraphStyle(
        "TOCHeader", fontName="BookSansBold", fontSize=18, leading=22,
        textColor=colors.HexColor("#000000"), alignment=TA_LEFT, spaceAfter=8
    )
    styles["TOCPart"] = ParagraphStyle(
        "TOCPart", fontName="BookSansBold", fontSize=8.5, leading=12,
        textColor=colors.HexColor("#111111"), alignment=TA_LEFT, spaceBefore=12, spaceAfter=4
    )
    styles["TOCChapterNum"] = ParagraphStyle(
        "TOCChapterNum", fontName="BookMono", fontSize=8.2, leading=12,
        textColor=colors.HexColor("#555555"), alignment=TA_LEFT
    )
    styles["TOCChapterTitle"] = ParagraphStyle(
        "TOCChapterTitle", fontName="BookSans", fontSize=9.0, leading=12,
        textColor=colors.HexColor("#111111"), alignment=TA_LEFT
    )
    styles["TOCPageNum"] = ParagraphStyle(
        "TOCPageNum", fontName="BookMono", fontSize=8.2, leading=12,
        textColor=colors.HexColor("#444444"), alignment=TA_RIGHT
    )
    styles["OpenerNum"] = ParagraphStyle(
        "OpenerNum", fontName="BookSansBold", fontSize=10, leading=13,
        textColor=colors.HexColor("#666666"), alignment=TA_LEFT, spaceAfter=4
    )
    styles["OpenerTitle"] = ParagraphStyle(
        "OpenerTitle", fontName="BookSansBold", fontSize=22, leading=28,
        textColor=colors.HexColor("#000000"), alignment=TA_LEFT, spaceAfter=12
    )
    styles["ObjectiveHeader"] = ParagraphStyle(
        "ObjectiveHeader", fontName="BookMono", fontSize=7.2, leading=9,
        textColor=colors.HexColor("#333333"), alignment=TA_LEFT, spaceAfter=4
    )
    styles["ObjectiveBody"] = ParagraphStyle(
        "ObjectiveBody", fontName="BookSerif", fontSize=8.8, leading=13.5,
        textColor=colors.HexColor("#222222"), alignment=TA_JUSTIFY
    )
    styles["BodyProse"] = ParagraphStyle(
        "BodyProse", fontName="BookSerif", fontSize=10, leading=15,
        textColor=colors.HexColor("#111111"), alignment=TA_JUSTIFY, spaceAfter=8
    )
    styles["Heading2"] = ParagraphStyle(
        "Heading2", fontName="BookSansBold", fontSize=14, leading=18,
        textColor=colors.HexColor("#000000"), alignment=TA_LEFT, spaceBefore=14, spaceAfter=6
    )
    styles["CalloutProse"] = ParagraphStyle(
        "CalloutProse", fontName="BookSerif", fontSize=9.2, leading=14,
        textColor=colors.HexColor("#222222"), alignment=TA_JUSTIFY
    )
    styles["RunningHead"] = ParagraphStyle(
        "RunningHead", fontName="BookMono", fontSize=7.5, leading=10,
        textColor=colors.HexColor("#555555")
    )
    return styles


def build_specimens_pdf():
    print("[1/2] Building nontechnical_specimens.pdf...")
    doc = BaseDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=MARGIN_INSIDE,
        rightMargin=MARGIN_OUTSIDE,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )
    frame = Frame(
        MARGIN_INSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="normal", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0
    )
    template = PageTemplate(id="specimen_page", frames=[frame])
    doc.addPageTemplates([template])

    styles = get_styles()
    story = []

    # ==========================================================================
    # SPECIMEN 1: TRANG TIÊU ĐỀ LÓT (HALF-TITLE / TITLE PAGE)
    # ==========================================================================
    story.append(Spacer(1, 45 * mm))
    story.append(Paragraph("GOLANG LIVING TEXTBOOK // TECHNICAL MONOGRAPH", styles["TitleMeta"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("G  O  L  A  N  G", styles["MainTitle"]))
    story.append(Paragraph("Giáo trình Cập nhật Liên tục về Kỹ nghệ Phần mềm và DevOps/SRE", styles["SubTitle"]))
    
    # Hairline divider
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#000000"), spaceBefore=4, spaceAfter=14))
    
    story.append(Paragraph("ĐOÀN NGỌC HOÀNG MINH", styles["Author"]))
    
    story.append(Spacer(1, 85 * mm))
    
    colophon_text = (
        "<b>ĐẶC TẢ XUẤT BẢN THƯƠNG MẠI 2026</b><br/>"
        "Định dạng: ISO A4 (210 × 297 mm) // Khâu chỉ dán gáy keo PUR<br/>"
        "Hệ thống chữ: Source Serif 4, Source Sans 3 & JetBrains Mono<br/>"
        "Kho lưu trữ mã nguồn mở: https://github.com/Minhlike/Golang<br/>"
        "Bản quyền © 2026 Đoàn Ngọc Hoàng Minh. Phát hành theo giấy phép học thuật."
    )
    story.append(Paragraph(colophon_text, styles["Colophon"]))
    story.append(PageBreak())

    # ==========================================================================
    # SPECIMEN 2: MỤC LỤC TỔNG THỂ (TABLE OF CONTENTS)
    # ==========================================================================
    story.append(Paragraph("MỤC LỤC", styles["TOCHeader"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#000000"), spaceBefore=2, spaceAfter=8))

    toc_items = [
        ("PHẦN I: NỀN TẢNG CƠ HỌC & BỘ NHỚ GO", None, None),
        ("Dẫn nhập", "Trước khi viết dòng Go đầu tiên", "3"),
        ("Tổng quan", "Mở cửa vào Go: Cài đặt và Tư duy Thực chiến", "8"),
        ("Chương 01", "Đọc và viết một chương trình Go", "14"),
        ("Chương 02", "Khi một bản sao vẫn chia sẻ dữ liệu (Pointer, Slice Header)", "35"),
        ("Chương 03", "Mô hình dữ liệu và trách nhiệm thay đổi", "45"),
        ("Chương 04", "Biên lỗi: để caller quyết định", "68"),
        ("Chương 05", "Package là ranh giới", "81"),
        ("PHẦN II: TƯƠNG TRANH & ĐỘ ỔN ĐỊNH HỆ THỐNG", None, None),
        ("Chương 06", "Thay đổi không sợ hãi (Testing, Benchmarking, Fuzzing)", "94"),
        ("Chương 07", "Dữ liệu đi vào và đi ra (io.Reader, Stream Buffering)", "114"),
        ("Chương 08", "Một race bắt đầu từ đâu (Memory Model, Race Detector)", "124"),
        ("Chương 09", "Dòng công việc có áp suất (Channel Rendezvous, Buffered Queue)", "132"),
        ("Chương 10", "Khi chương trình chậm hoặc phình (pprof, Escape Analysis)", "140"),
        ("Chương 11", "Lần theo một request HTTP (Routing, Middleware Chain)", "153"),
        ("Chương 12", "Một service sống và tắt thế nào (Graceful Shutdown, Context)", "160"),
        ("PHẦN III: DỊCH VỤ PHÂN TÁN & CƠ SỞ DỮ LIỆU", None, None),
        ("Chương 13", "Một thay đổi hoặc không có gì (SQL ACID, Idempotency)", "170"),
        ("Chương 14", "Khi kiểu trở thành dữ liệu (reflect, Generic, Type Parameter)", "186"),
        ("Chương 15", "Từ incident đến công cụ (CLI, Automation, Diagnostics)", "198"),
        ("Chương 16", "Thấy được hệ thống (Prometheus Metrics, OpenTelemetry)", "207"),
        ("Chương 17", "Đóng gói và điều phối (Containerization, Multi-stage Build)", "218"),
        ("PHẦN IV: KUBERNETES OPERATOR & eBPF NÂNG CAO", None, None),
        ("Chương 21", "Vòng lặp điều hòa và Controller Pattern", "277"),
        ("Chương 22", "Từ watch đến một controller Kubernetes thật", "287"),
        ("Chương 23", "Từ controller đến operator hoàn chỉnh (CRD, Reconciler)", "305"),
        ("Chương 27", "Quan sát Linux từ kernel bằng eBPF và Go (Cilium, Tracepoint)", "379"),
        ("BACK MATTER // TÀI LIỆU TRA CỨU", None, None),
        ("Atlas", "Hồ sơ kiến trúc 50 thư viện DevOps & Cloud hàng đầu", "429"),
        ("Phụ lục A", "Atlas Lỗi Thực Chiến: Chẩn đoán & Khắc phục nhanh", "484"),
    ]

    toc_rows = []
    toc_table_style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#F0F0F0")),
    ]
    for r_idx, (col1, col2, col3) in enumerate(toc_items):
        if col2 is None:
            # Section Header
            p_part = Paragraph(col1, styles["TOCPart"])
            toc_rows.append([p_part, "", ""])
            toc_table_style.append(("SPAN", (0, r_idx), (2, r_idx)))
            toc_table_style.append(("LINEBELOW", (0, r_idx), (2, r_idx), 0.5, colors.HexColor("#D0D0D0")))
            toc_table_style.append(("TOPPADDING", (0, r_idx), (2, r_idx), 8))
            toc_table_style.append(("BOTTOMPADDING", (0, r_idx), (2, r_idx), 3))
        else:
            p_c1 = Paragraph(col1, styles["TOCChapterNum"])
            p_c2 = Paragraph(col2, styles["TOCChapterTitle"])
            p_c3 = Paragraph(col3, styles["TOCPageNum"])
            toc_rows.append([p_c1, p_c2, p_c3])

    col_w = [25 * mm, PRINTABLE_WIDTH - 37 * mm, 12 * mm]
    t_toc = Table(toc_rows, colWidths=col_w)
    t_toc.setStyle(TableStyle(toc_table_style))
    story.append(t_toc)
    story.append(PageBreak())

    # ==========================================================================
    # SPECIMEN 3: TRANG MỞ ĐẦU CHƯƠNG (CHAPTER OPENER)
    # ==========================================================================
    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph("CHƯƠNG 01 // FOUNDATION", styles["OpenerNum"]))
    story.append(Paragraph("Đọc và viết một chương trình Go", styles["OpenerTitle"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#000000"), spaceBefore=2, spaceAfter=14))

    # Objective Box (Technical Minimalism: no heavy black border, clean left accent)
    obj_content = [
        [
            Paragraph("<b>MỤC TIÊU SƯ PHẠM VÀ RÀNG BUỘC KỸ NGHỆ // LEARNING OBJECTIVES</b>", styles["ObjectiveHeader"])
        ],
        [
            Paragraph(
                "Chương này dẫn lối kỹ sư tiếp cận Go không phải như một cú pháp bề mặt, mà như một mô hình cơ học: "
                "cách trình biên dịch phân bổ biến trên ngăn xếp, cấu trúc của tệp thực thi ELF sau khi liên kết tĩnh, "
                "và nguyên lý điều hòa vòng đời goroutine thông qua runtime footprint tối thiểu. "
                "Sau khi hoàn thành chương, người học có thể tự giải thích cội nguồn của mọi quyết định cấp phát bộ nhớ "
                "và kiểm chứng mã bằng các công cụ đo lường tiêu chuẩn.",
                styles["ObjectiveBody"]
            )
        ]
    ]
    t_obj = Table(obj_content, colWidths=[PRINTABLE_WIDTH])
    t_obj.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
        ("LINELEFT", (0, 0), (0, -1), 2.0, colors.HexColor("#000000")),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#E0E0E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(t_obj)
    story.append(Spacer(1, 16))

    story.append(Paragraph(
        "Mỗi ngôn ngữ lập trình đều mang theo một giả định ngầm về cách thế giới vận hành. Với C, đó là bộ nhớ vật lý "
        "thẳng đuột với con trỏ tự do. Với Java, đó là một máy ảo trừu tượng quản lý đối tượng qua tham chiếu gián tiếp. "
        "Với Go, thế giới được mô hình hóa qua hai trục cơ học vững chắc: <b>giá trị thực thi tức thời (value semantics)</b> "
        "và <b>sự đồng bộ hóa qua giao tiếp (channel rendezvous)</b>.",
        styles["BodyProse"]
    ))

    story.append(Paragraph(
        "Khi một kỹ sư viết dòng lệnh khai báo một cấu trúc struct, câu hỏi đầu tiên xuất hiện trong đầu không nên là "
        "cú pháp có ngắn gọn không, mà là: biến này sẽ tồn tại ở đâu trong không gian địa chỉ 64-bit của tiến trình Linux? "
        "Nó nằm trên frame của goroutine stack hay bị ép thoát ra heap do escape analysis? "
        "Sự khác biệt giữa 0 lần cấp phát (zero-allocation) và 1 lần cấp phát heap chính là lằn ranh giữa một dịch vụ vi mô "
        "chịu tải 100.000 requests/giây và một dịch vụ sụp đổ vì tail-latency của Garbage Collector.",
        styles["BodyProse"]
    ))

    story.append(Paragraph("1.1. Cấu trúc một tệp mã nguồn và ranh giới biên dịch", styles["Heading2"]))
    story.append(Paragraph(
        "Mỗi tệp Go bắt đầu bằng mệnh đề package. Package không chỉ là một không gian tên (namespace) logic nhằm tránh "
        "đụng độ định danh, mà là ranh giới biên dịch nguyên tử (atomic compilation boundary) của toolchain. "
        "Không có khái niệm vòng tròn phụ thuộc (circular dependency) được phép tồn tại: trình biên dịch Go áp đặt "
        "đồ thị có hướng không chu trình (DAG) ở mức độ kiến trúc gói.",
        styles["BodyProse"]
    ))
    story.append(PageBreak())

    # ==========================================================================
    # SPECIMEN 4: HEADER & FOOTER ĐỐI XỨNG QUA GÁY (VERSO & RECTO SPREAD)
    # ==========================================================================
    story.append(Paragraph("MẪU BỐ CỤC ĐỐI XỨNG QUA GÁY (MIRRORED FACING SPREADS)", styles["TOCHeader"]))
    story.append(Paragraph("Minh họa quy chuẩn Header/Footer chạy trang (Running Heads & Folios) theo lề sách mở đôi.", styles["SubTitle"]))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#000000"), spaceBefore=2, spaceAfter=14))

    # Verso Card
    verso_header = [
        [
            Paragraph("<b>48</b>", styles["RunningHead"]),
            Paragraph("GOLANG — GIÁO TRÌNH KỸ NGHỆ PHẦN MỀM VÀ DEVOPS/SRE", styles["RunningHead"]),
            Paragraph("<i>[TRANG CHẴN / VERSO]</i>", styles["RunningHead"]),
        ]
    ]
    t_vhead = Table(verso_header, colWidths=[15 * mm, PRINTABLE_WIDTH - 45 * mm, 30 * mm])
    t_vhead.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#000000")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_vhead)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Đặc tả Lề Trang Chẵn (Verso):</b> Lề ngoài bên trái 18.0 mm (chứa số trang 48); lề trong bên phải 24.0 mm "
        "(hướng vào khe gáy sách). Khoảng cách 24 mm đảm bảo chữ không bị che khuất khi mở sách.",
        styles["BodyProse"]
    ))

    # Callout Specimen
    callout_data = [
        [
            Paragraph(
                "<b>QUY TẮC BỘ NHỚ // GO RUNTIME SPECIFICATION:</b><br/>"
                "Mọi biến truyền vào hàm trong Go mặc định đều là truyền theo giá trị (pass-by-value). "
                "Khi bạn truyền một slice header, Go chỉ sao chép con trỏ mảng cơ sở, độ dài len và sức chứa cap (24 byte). "
                "Dữ liệu phần tử không hề bị nhân bản.",
                styles["CalloutProse"]
            )
        ]
    ]
    t_call = Table(callout_data, colWidths=[PRINTABLE_WIDTH])
    t_call.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9F9F9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("LINELEFT", (0, 0), (0, -1), 2.0, colors.HexColor("#333333")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_call)
    story.append(Spacer(1, 18))

    # Recto Card
    recto_header = [
        [
            Paragraph("<i>[TRANG LẺ / RECTO]</i>", styles["RunningHead"]),
            Paragraph("CHƯƠNG 03 — MÔ HÌNH DỮ LIỆU VÀ TRÁCH NHIỆM THAY ĐỔI", styles["RunningHead"]),
            Paragraph("<b>49</b>", styles["RunningHead"]),
        ]
    ]
    t_rhead = Table(recto_header, colWidths=[30 * mm, PRINTABLE_WIDTH - 45 * mm, 15 * mm])
    t_rhead.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#000000")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_rhead)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Đặc tả Lề Trang Lẻ (Recto):</b> Lề trong bên trái 24.0 mm (hướng vào khe gáy sách); lề ngoài bên phải 18.0 mm "
        "(chứa số trang 49). Tiêu đề chương chạy ở đầu trang lẻ giúp người đọc lật nhanh để định vị nội dung.",
        styles["BodyProse"]
    ))

    story.append(Paragraph(
        "Một quy chuẩn bất di bất dịch của nghệ thuật chế bản xuất bản là: <b>Trang mở đầu chương (Chapter Opener) "
        "tuyệt đối không bao giờ được có Running Head trên đỉnh</b>. Trên trang mở đầu chương, số trang sẽ hoặc là ẩn đi, "
        "hoặc là đưa xuống đáy trang (Drop Folio). Running Head chỉ bắt đầu xuất hiện từ trang thứ hai của chương trở đi.",
        styles["BodyProse"]
    ))

    # Build Document
    doc.build(story)
    print(f"  -> Saved: {OUTPUT_PDF}")


def render_pages():
    print("[2/2] Rendering specimen pages to 300 DPI PNG images...")
    doc = fitz.open(OUTPUT_PDF)
    names = [
        "specimen_p01_title_page.png",
        "specimen_p02_table_of_contents.png",
        "specimen_p03_chapter_opener.png",
        "specimen_p04_running_headers.png",
    ]
    for idx, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)
        out_png = OUTPUT_DIR / names[idx]
        pix.save(out_png)
        print(f"  -> Rendered: {out_png}")
    doc.close()


if __name__ == "__main__":
    build_specimens_pdf()
    render_pages()
    print("=== NON-TECHNICAL SPECIMENS GENERATION COMPLETE ===")
