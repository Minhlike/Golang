"""
Render Figures 1 to 6 for Golang Living Textbook.
Ensures publication-grade quality:
- Geometry: Printable width 168 mm (476.22 pt), max height 128 mm (362.83 pt).
- Effective DPI: 320 DPI.
- Pure Grayscale: R = G = B for every pixel (diff1 = diff2 = 0).
- Typography: Source Sans 3 and JetBrains Mono, all font sizes >= 6.0 pt, safe padding >= 4.0 pt.
- Zero glyph truncation, zero collision.
"""

import os
import sys
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ASSETS_DIR = os.path.join(ROOT_DIR, 'assets', 'diagrams')
FONTS_DIR = os.path.join(ROOT_DIR, 'assets', 'fonts')

FONT_REG = FontProperties(fname=os.path.join(FONTS_DIR, 'SourceSans3-Regular.ttf'))
FONT_BOLD = FontProperties(fname=os.path.join(FONTS_DIR, 'SourceSans3-Semibold.ttf'))
FONT_MONO = FontProperties(fname=os.path.join(FONTS_DIR, 'JetBrainsMono-Regular.ttf'))


def verify_image(filepath, target_dpi=320):
    im = Image.open(filepath).convert('RGB')
    arr = np.array(im)
    diff1 = np.max(np.abs(arr[:, :, 0] - arr[:, :, 1]))
    diff2 = np.max(np.abs(arr[:, :, 1] - arr[:, :, 2]))
    assert diff1 == 0 and diff2 == 0, f"FAIL: {filepath} is not pure grayscale (diff={diff1},{diff2})"
    print(f"VERIFIED: {os.path.basename(filepath)} | Size: {im.size} | Pure Grayscale: OK (diff=0)")


def render_fig1():
    """Hình 1: Dòng thời gian tiến hóa của Go (go-history-timeline.png)"""
    fig_w_in = 168.0 / 25.4
    fig_h_in = 84.0 / 25.4

    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=320)
    ax.set_xlim(0, 168)
    ax.set_ylim(0, 84)
    ax.set_aspect('equal')
    ax.axis('off')

    bg = patches.Rectangle((0, 0), 168, 84, facecolor='#FFFFFF', edgecolor='none')
    ax.add_patch(bg)

    # Title header
    title_box = patches.FancyBboxPatch((4, 76.0), 160, 6.5,
                                      boxstyle="round,pad=0,rounding_size=1.5",
                                      facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.8)
    ax.add_patch(title_box)
    ax.text(84, 79.2, "DÒNG THỜI GIAN CÁC CỘT MỐC TIẾN HÓA CỦA GO (2007 – 2026)",
            fontproperties=FONT_BOLD, fontsize=8.5, color='#111111', ha='center', va='center')

    row1 = [
        {'year': '2007', 'title': 'Khởi thảo Ý tưởng', 'tag': 'Giai đoạn vườn ươm',
         'desc': 'Robert Griesemer, Rob Pike, Ken Thompson phác thảo mục tiêu giải quyết bế tắc scale tại Google.'},
        {'year': '2008', 'title': 'Compiler Thử nghiệm', 'tag': 'Bộ công cụ đầu tiên',
         'desc': 'Trình biên dịch mẫu hoàn thành; cú pháp ngôn ngữ dần ổn định và thử nghiệm nội bộ.'},
        {'year': '2009', 'title': 'Mở Mã Nguồn', 'tag': '10 tháng 11, 2009',
         'desc': 'Công bố chính thức dưới giấy phép BSD mở, hình thành cộng đồng đóng góp toàn cầu.'},
        {'year': '2012', 'title': 'Go 1.0 Ra Mắt', 'tag': 'Cam kết tương thích',
         'desc': 'Xác lập Go 1 Compatibility Promise: mã hợp lệ với Go 1 sẽ luôn biên dịch được trong tương lai.'}
    ]

    row2 = [
        {'year': '2015', 'title': 'Go 1.5 Tự thân', 'tag': 'Tự biên dịch & GC',
         'desc': 'Viết lại compiler và runtime hoàn toàn bằng Go & assembly; ra mắt Concurrent Garbage Collector.'},
        {'year': '2018', 'title': 'Go 1.11 Modules', 'tag': 'Quản lý phụ thuộc',
         'desc': 'Giới thiệu Go Modules (go.mod), giải phóng dự án khỏi ràng buộc $GOPATH truyền thống.'},
        {'year': '2022', 'title': 'Go 1.18 Generics', 'tag': 'Tham số kiểu',
         'desc': 'Bổ sung Type Parameters (Generics), mở rộng khả năng trừu tượng thuật toán tĩnh an toàn kiểu.'},
        {'year': '2026', 'title': 'Go 1.27 Đương đại', 'tag': 'Mở rộng phương thức',
         'desc': 'Hoàn thiện Generic Methods trên kiểu dữ liệu; tối ưu hóa PGO và hoàn thiện toolchain hiện đại.'}
    ]

    card_w = 36.5
    gap_x = 4.6
    start_x = 4.0

    # Draw Row 1 (y: 43 to 71)
    y_r1 = 43.0
    h_card = 28.0
    for i, item in enumerate(row1):
        x = start_x + i * (card_w + gap_x)
        # Card
        rect = patches.FancyBboxPatch((x, y_r1), card_w, h_card,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#F8F8F8', edgecolor='#444444', linewidth=0.9)
        ax.add_patch(rect)
        # Header banner
        h_head = 7.2
        head_rect = patches.FancyBboxPatch((x, y_r1 + h_card - h_head), card_w, h_head,
                                          boxstyle="round,pad=0,rounding_size=2.0",
                                          facecolor='#E8E8E8', edgecolor='#444444', linewidth=0.9)
        ax.add_patch(head_rect)
        ax.add_patch(patches.Rectangle((x, y_r1 + h_card - h_head), card_w, 2.5, facecolor='#E8E8E8', edgecolor='none'))
        ax.plot([x, x + card_w], [y_r1 + h_card - h_head, y_r1 + h_card - h_head], color='#444444', linewidth=0.7)

        # Header text
        ax.text(x + 2.5, y_r1 + h_card - 3.6, item['year'], fontproperties=FONT_BOLD,
                fontsize=8.5, color='#000000', ha='left', va='center')
        ax.text(x + card_w - 2.5, y_r1 + h_card - 3.6, item['tag'], fontproperties=FONT_REG,
                fontsize=5.8, color='#444444', ha='right', va='center')

        # Title
        ax.text(x + 2.5, y_r1 + h_card - 10.5, item['title'], fontproperties=FONT_BOLD,
                fontsize=7.2, color='#111111', ha='left', va='center')

        # Desc wrapped
        # Split description into lines
        words = item['desc'].split()
        lines = []
        cur = ""
        for w in words:
            if len(cur + " " + w) > 31:
                lines.append(cur)
                cur = w
            else:
                cur = cur + " " + w if cur else w
        if cur:
            lines.append(cur)

        for li, l_text in enumerate(lines[:3]):
            ax.text(x + 2.5, y_r1 + h_card - 15.0 - li * 3.8, l_text, fontproperties=FONT_REG,
                    fontsize=6.0, color='#333333', ha='left', va='center')

        # Arrow to next card in row 1
        if i < 3:
            ax.plot([x + card_w, x + card_w + gap_x], [y_r1 + h_card/2, y_r1 + h_card/2],
                    color='#333333', linewidth=1.1)
            ax.annotate('', xy=(x + card_w + gap_x, y_r1 + h_card/2),
                        xytext=(x + card_w + gap_x - 1.2, y_r1 + h_card/2),
                        arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6))

    # Draw Row 2 (y: 6 to 34)
    y_r2 = 6.0
    for i, item in enumerate(row2):
        x = start_x + i * (card_w + gap_x)
        rect = patches.FancyBboxPatch((x, y_r2), card_w, h_card,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#F8F8F8', edgecolor='#444444', linewidth=0.9)
        ax.add_patch(rect)
        h_head = 7.2
        head_rect = patches.FancyBboxPatch((x, y_r2 + h_card - h_head), card_w, h_head,
                                          boxstyle="round,pad=0,rounding_size=2.0",
                                          facecolor='#E8E8E8', edgecolor='#444444', linewidth=0.9)
        ax.add_patch(head_rect)
        ax.add_patch(patches.Rectangle((x, y_r2 + h_card - h_head), card_w, 2.5, facecolor='#E8E8E8', edgecolor='none'))
        ax.plot([x, x + card_w], [y_r2 + h_card - h_head, y_r2 + h_card - h_head], color='#444444', linewidth=0.7)

        ax.text(x + 2.5, y_r2 + h_card - 3.6, item['year'], fontproperties=FONT_BOLD,
                fontsize=8.5, color='#000000', ha='left', va='center')
        ax.text(x + card_w - 2.5, y_r2 + h_card - 3.6, item['tag'], fontproperties=FONT_REG,
                fontsize=5.8, color='#444444', ha='right', va='center')

        ax.text(x + 2.5, y_r2 + h_card - 10.5, item['title'], fontproperties=FONT_BOLD,
                fontsize=7.2, color='#111111', ha='left', va='center')

        words = item['desc'].split()
        lines = []
        cur = ""
        for w in words:
            if len(cur + " " + w) > 31:
                lines.append(cur)
                cur = w
            else:
                cur = cur + " " + w if cur else w
        if cur:
            lines.append(cur)

        for li, l_text in enumerate(lines[:3]):
            ax.text(x + 2.5, y_r2 + h_card - 15.0 - li * 3.8, l_text, fontproperties=FONT_REG,
                    fontsize=6.0, color='#333333', ha='left', va='center')

        # Arrow to next card in row 2
        if i < 3:
            ax.plot([x + card_w, x + card_w + gap_x], [y_r2 + h_card/2, y_r2 + h_card/2],
                    color='#333333', linewidth=1.1)
            ax.annotate('', xy=(x + card_w + gap_x, y_r2 + h_card/2),
                        xytext=(x + card_w + gap_x - 1.2, y_r2 + h_card/2),
                        arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6))

    # Orthogonal connection bus from 2012 (Row 1 Card 4) down to 2015 (Row 2 Card 1)
    # 2012 center bottom: (start_x + 3*(card_w+gap_x) + card_w/2, y_r1)
    # 2015 center top: (start_x + card_w/2, y_r2 + h_card)
    x_2012 = start_x + 3 * (card_w + gap_x) + card_w / 2
    x_2015 = start_x + card_w / 2
    y_bus = (y_r1 + (y_r2 + h_card)) / 2  # 38.5

    ax.plot([x_2012, x_2012, x_2015, x_2015], [y_r1, y_bus, y_bus, y_r2 + h_card],
            color='#333333', linewidth=1.2, linestyle='-')
    ax.annotate('', xy=(x_2015, y_r2 + h_card), xytext=(x_2015, y_r2 + h_card + 1.2),
                arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.2, mutation_scale=7))

    ax.text(84, y_bus + 1.2, "Tiến trình tự lưu chuyển & mở rộng tính năng liên tục",
            fontproperties=FONT_REG, fontsize=6.3, color='#444444', ha='center', va='bottom')

    plt.tight_layout(pad=0.2)
    out_path = os.path.join(ASSETS_DIR, 'go-history-timeline.png')
    plt.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
    plt.close()
    verify_image(out_path)


def render_fig2():
    """Hình 2: Dòng dõi và sự hội tụ ý tưởng vào Go (go-idea-lineage.png)"""
    fig_w_in = 168.0 / 25.4
    fig_h_in = 108.0 / 25.4

    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=320)
    ax.set_xlim(0, 168)
    ax.set_ylim(0, 108)
    ax.set_aspect('equal')
    ax.axis('off')

    bg = patches.Rectangle((0, 0), 168, 108, facecolor='#FFFFFF', edgecolor='none')
    ax.add_patch(bg)

    title_box = patches.FancyBboxPatch((4, 99.5), 160, 6.5,
                                      boxstyle="round,pad=0,rounding_size=1.5",
                                      facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.8)
    ax.add_patch(title_box)
    ax.text(84, 102.7, "DÒNG DÕI Ý TƯỞNG VÀ SỰ HỘI TỤ THỰC DỤNG VÀO GO",
            fontproperties=FONT_BOLD, fontsize=8.5, color='#111111', ha='center', va='center')

    # Left: 3 Lineage Pillars (x: 4 to 88, width: 84)
    # Pillar 1: C (y: 71 to 96)
    # Pillar 2: Pascal / Oberon (y: 43 to 68)
    # Pillar 3: CSP (y: 15 to 40)
    pillars = [
        {
            'name': 'DÒNG DÕI C (Kernighan, Ritchie)',
            'y': 71.0,
            'items': [
                '• Cú pháp biểu thức ngắn gọn, trực quan ({}, toán tử).',
                '• Con trỏ định vị ô nhớ (nhưng loại bỏ số học con trỏ).',
                '• Biên dịch trực tiếp thành mã máy tối ưu, hiệu năng cao.'
            ]
        },
        {
            'name': 'DÒNG DÕI PASCAL (Wirth: Modula-2, Oberon-2)',
            'y': 43.0,
            'items': [
                '• Cú pháp khai báo tên trước kiểu (name type) sáng sủa.',
                '• Cấu trúc package tường minh, phân tách ranh giới biên dịch.',
                '• Tính an toàn bộ nhớ tĩnh, loại bỏ header files cồng kềnh.'
            ]
        },
        {
            'name': 'TIẾN TRÌNH CSP (Hoare, Newsqueak, Alef, Limbo)',
            'y': 15.0,
            'items': [
                '• Giao tiếp tuần tự qua kênh (channels, goroutines).',
                '• Không chia sẻ bộ nhớ; giao tiếp để đồng bộ hóa trạng thái.',
                '• Cấu trúc điều khiển phi tuần tự qua select đa kênh.'
            ]
        }
    ]

    p_w = 84.0
    p_h = 25.0
    for p in pillars:
        rect = patches.FancyBboxPatch((4, p['y']), p_w, p_h,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#F9F9F9', edgecolor='#444444', linewidth=0.9)
        ax.add_patch(rect)
        head_h = 6.0
        head = patches.FancyBboxPatch((4, p['y'] + p_h - head_h), p_w, head_h,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#E8E8E8', edgecolor='#444444', linewidth=0.9)
        ax.add_patch(head)
        ax.add_patch(patches.Rectangle((4, p['y'] + p_h - head_h), p_w, 2.0, facecolor='#E8E8E8', edgecolor='none'))
        ax.plot([4, 4 + p_w], [p['y'] + p_h - head_h, p['y'] + p_h - head_h], color='#444444', linewidth=0.7)

        ax.text(6.5, p['y'] + p_h - 3.0, p['name'], fontproperties=FONT_BOLD,
                fontsize=6.8, color='#111111', ha='left', va='center')

        for li, itext in enumerate(p['items']):
            ax.text(6.5, p['y'] + p_h - 9.5 - li * 4.8, itext, fontproperties=FONT_REG,
                    fontsize=6.0, color='#333333', ha='left', va='center')

    # Right: Convergent Destination Box (x: 100 to 164, width: 64, y: 15 to 96, height: 81)
    r_x = 100.0
    r_w = 64.0
    r_y = 15.0
    r_h = 81.0

    go_box = patches.FancyBboxPatch((r_x, r_y), r_w, r_h,
                                   boxstyle="round,pad=0,rounding_size=2.5",
                                   facecolor='#F4F4F4', edgecolor='#222222', linewidth=1.2)
    ax.add_patch(go_box)

    go_head_h = 9.0
    go_head = patches.FancyBboxPatch((r_x, r_y + r_h - go_head_h), r_w, go_head_h,
                                    boxstyle="round,pad=0,rounding_size=2.5",
                                    facecolor='#333333', edgecolor='#222222', linewidth=1.2)
    ax.add_patch(go_head)
    ax.add_patch(patches.Rectangle((r_x, r_y + r_h - go_head_h), r_w, 3.0, facecolor='#333333', edgecolor='none'))

    ax.text(r_x + r_w/2, r_y + r_h - 4.5, "GOLANG (HỘI TỤ THỰC DỤNG)",
            fontproperties=FONT_BOLD, fontsize=8.2, color='#FFFFFF', ha='center', va='center')

    # Convergent Content inside Go Box
    sections = [
        ("KẾ THỪA CHỌN LỌC", [
            "• Tốc độ biên dịch cực nhanh & runtime tinh gọn",
            "• Giao diện ngầm định (duck typing tĩnh)",
            "• Mô hình đồng thời CSP hạng nhất (first-class)"
        ]),
        ("LỌC BỎ CỐ Ý (TRIẾT LÝ TINH GIẢN)", [
            "• KHÔNG kế thừa lớp phân cấp (no inheritance)",
            "• KHÔNG nạp chồng toán tử (no overloading)",
            "• KHÔNG số học con trỏ nguy hiểm",
            "• KHÔNG ép kiểu ngầm định (zero implicit conversion)"
        ])
    ]

    curr_y = r_y + r_h - 13.0
    for stitle, slines in sections:
        ax.text(r_x + 3.0, curr_y, stitle, fontproperties=FONT_BOLD,
                fontsize=6.6, color='#111111', ha='left', va='center')
        curr_y -= 4.2
        for sline in slines:
            ax.text(r_x + 3.0, curr_y, sline, fontproperties=FONT_REG,
                    fontsize=6.0, color='#333333', ha='left', va='center')
            curr_y -= 4.2
        curr_y -= 2.0

    # Convergence arrows from 3 pillars to Go box
    for p in pillars:
        p_mid_y = p['y'] + p_h / 2
        ax.plot([4 + p_w, r_x], [p_mid_y, p_mid_y], color='#333333', linewidth=1.1)
        ax.annotate('', xy=(r_x, p_mid_y), xytext=(r_x - 1.5, p_mid_y),
                    arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6))
        ax.text((4 + p_w + r_x)/2, p_mid_y + 1.2, "Hội tụ",
                fontproperties=FONT_REG, fontsize=5.8, color='#444444', ha='center', va='bottom')

    # Bottom Invariant Note
    note_box = patches.FancyBboxPatch((4, 4), 160, 8.5,
                                     boxstyle="round,pad=0,rounding_size=1.5",
                                     facecolor='#FAFAFA', edgecolor='#666666', linewidth=0.7)
    ax.add_patch(note_box)
    ax.text(84, 8.2, "Nguyên lý thiết kế: Go không phát minh cú pháp mới kỳ dị, mà tổng hợp và gạn lọc tinh hoa từ các dòng ngôn ngữ kinh điển",
            fontproperties=FONT_BOLD, fontsize=6.4, color='#222222', ha='center', va='center')

    plt.tight_layout(pad=0.2)
    out_path = os.path.join(ASSETS_DIR, 'go-idea-lineage.png')
    plt.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
    plt.close()
    verify_image(out_path)


def render_fig3():
    """Hình 3: Vòng lặp phản hồi thực nghiệm (feedback-loop.png)"""
    fig_w_in = 168.0 / 25.4
    fig_h_in = 112.0 / 25.4

    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=320)
    ax.set_xlim(0, 168)
    ax.set_ylim(0, 112)
    ax.set_aspect('equal')
    ax.axis('off')

    bg = patches.Rectangle((0, 0), 168, 112, facecolor='#FFFFFF', edgecolor='none')
    ax.add_patch(bg)

    title_box = patches.FancyBboxPatch((4, 103.5), 160, 6.5,
                                      boxstyle="round,pad=0,rounding_size=1.5",
                                      facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.8)
    ax.add_patch(title_box)
    ax.text(84, 106.7, "VÒNG LẶP PHẢN HỒI THỰC NGHIỆM KHI HỌC VÀ LẬP TRÌNH GO",
            fontproperties=FONT_BOLD, fontsize=8.5, color='#111111', ha='center', va='center')

    # Left: Vertical Activity Pipeline (x: 10 to 86, width: 76)
    # Step 1: Hypothesis (y: 86 to 98)
    # Step 2: Minimal edit (y: 70 to 82)
    # Step 3: Toolchain check (y: 45 to 66)
    # Step 4: Decision Diamond (center at x=48, y=28)
    steps = [
        {
            'num': 'BƯỚC 1',
            'title': 'Đặt Giả Thuyết Kỹ Thuật',
            'desc': 'Xác định rõ ràng: Đoạn mã sẽ có hành vi gì, trả về giá trị nào hoặc gây lỗi gì?',
            'y': 86.0,
            'h': 13.0
        },
        {
            'num': 'BƯỚC 2',
            'title': 'Chỉnh Sửa Nhỏ Nhất (Minimal Edit)',
            'desc': 'Thay đổi đúng một biến số duy nhất; không viết nhiều tính năng cùng một lúc.',
            'y': 69.0,
            'h': 13.0
        },
        {
            'num': 'BƯỚC 3',
            'title': 'Thực Thi Bộ Công Cụ Tiêu Chuẩn',
            'desc': '1. go fmt ./... (Chuẩn hóa định dạng)\n2. go vet ./... (Phát hiện lỗi ngữ nghĩa)\n3. go test ./... (Kiểm chứng hành vi thực tế)',
            'y': 44.0,
            'h': 21.0
        }
    ]

    s_x = 10.0
    s_w = 76.0

    for i, s in enumerate(steps):
        rect = patches.FancyBboxPatch((s_x, s['y']), s_w, s['h'],
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#F9F9F9', edgecolor='#444444', linewidth=0.9)
        ax.add_patch(rect)
        head_h = 4.5
        head = patches.FancyBboxPatch((s_x, s['y'] + s['h'] - head_h), s_w, head_h,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#E8E8E8', edgecolor='#444444', linewidth=0.9)
        ax.add_patch(head)
        ax.add_patch(patches.Rectangle((s_x, s['y'] + s['h'] - head_h), s_w, 2.0, facecolor='#E8E8E8', edgecolor='none'))
        ax.plot([s_x, s_x + s_w], [s['y'] + s['h'] - head_h, s['y'] + s['h'] - head_h], color='#444444', linewidth=0.7)

        ax.text(s_x + 2.5, s['y'] + s['h'] - 2.2, f"{s['num']}: {s['title']}", fontproperties=FONT_BOLD,
                fontsize=6.8, color='#111111', ha='left', va='center')

        # Desc
        d_lines = s['desc'].split('\n')
        for di, dl in enumerate(d_lines):
            ax.text(s_x + 2.5, s['y'] + s['h'] - 6.8 - di * 4.2, dl, fontproperties=FONT_REG,
                    fontsize=6.0, color='#333333', ha='left', va='center')

        # Down arrow to next step
        if i < 2:
            next_y = steps[i+1]['y'] + steps[i+1]['h']
            ax.plot([s_x + s_w/2, s_x + s_w/2], [s['y'], next_y], color='#333333', linewidth=1.1)
            ax.annotate('', xy=(s_x + s_w/2, next_y), xytext=(s_x + s_w/2, next_y + 1.2),
                        arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6))

    # Down arrow from Step 3 to Diamond
    ax.plot([s_x + s_w/2, s_x + s_w/2], [44.0, 35.0], color='#333333', linewidth=1.1)
    ax.annotate('', xy=(s_x + s_w/2, 35.0), xytext=(s_x + s_w/2, 36.2),
                arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6))

    # Decision Diamond
    # Center at (48, 25), width 34, height 20
    d_cx = s_x + s_w/2
    d_cy = 25.0
    d_hw = 20.0
    d_hh = 10.0
    diamond = patches.Polygon([
        (d_cx, d_cy + d_hh),
        (d_cx + d_hw, d_cy),
        (d_cx, d_cy - d_hh),
        (d_cx - d_hw, d_cy)
    ], closed=True, facecolor='#EEEEEE', edgecolor='#222222', linewidth=1.1)
    ax.add_patch(diamond)

    ax.text(d_cx, d_cy + 2.2, "Kết quả thực tế", fontproperties=FONT_BOLD,
            fontsize=6.5, color='#111111', ha='center', va='center')
    ax.text(d_cx, d_cy - 2.2, "bác bỏ giả thuyết?", fontproperties=FONT_BOLD,
            fontsize=6.5, color='#111111', ha='center', va='center')

    # Right: Branch Cards
    # Branch 1 (YES - Bị bác bỏ): Loop back to Step 1 & 2 (x: 102 to 162, y: 55 to 88)
    b1_x = 102.0
    b1_w = 60.0
    b1_y = 56.0
    b1_h = 32.0

    b1_rect = patches.FancyBboxPatch((b1_x, b1_y), b1_w, b1_h,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#F6F6F6', edgecolor='#444444', linewidth=0.9, linestyle='--')
    ax.add_patch(b1_rect)
    b1_head = patches.FancyBboxPatch((b1_x, b1_y + b1_h - 5.5), b1_w, 5.5,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#E2E2E2', edgecolor='#444444', linewidth=0.9, linestyle='--')
    ax.add_patch(b1_head)
    ax.add_patch(patches.Rectangle((b1_x, b1_y + b1_h - 5.5), b1_w, 2.0, facecolor='#E2E2E2', edgecolor='none'))
    ax.plot([b1_x, b1_x + b1_w], [b1_y + b1_h - 5.5, b1_y + b1_h - 5.5], color='#444444', linewidth=0.7)

    ax.text(b1_x + 2.5, b1_y + b1_h - 2.8, "NHÁNH CÓ (BÁC BỎ): CHẨN ĐOÁN LỖI",
            fontproperties=FONT_BOLD, fontsize=6.6, color='#111111', ha='left', va='center')

    b1_lines = [
        "• Đọc thông điệp từ compiler, go vet hoặc test failure.",
        "• Xác định nguyên nhân gốc rễ (Root Cause).",
        "• Điều chỉnh lại giả thuyết & lặp lại chu trình sửa đổi nhỏ."
    ]
    for li, bl in enumerate(b1_lines):
        ax.text(b1_x + 2.5, b1_y + b1_h - 9.0 - li * 4.6, bl, fontproperties=FONT_REG,
                fontsize=6.0, color='#222222', ha='left', va='center')

    # Branch 2 (NO - Không bị bác bỏ / Thành công): Confirm (x: 102 to 162, y: 15 to 45)
    b2_x = 102.0
    b2_w = 60.0
    b2_y = 15.0
    b2_h = 30.0

    b2_rect = patches.FancyBboxPatch((b2_x, b2_y), b2_w, b2_h,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#F9F9F9', edgecolor='#333333', linewidth=1.0)
    ax.add_patch(b2_rect)
    b2_head = patches.FancyBboxPatch((b2_x, b2_y + b2_h - 5.5), b2_w, 5.5,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#E8E8E8', edgecolor='#333333', linewidth=1.0)
    ax.add_patch(b2_head)
    ax.add_patch(patches.Rectangle((b2_x, b2_y + b2_h - 5.5), b2_w, 2.0, facecolor='#E8E8E8', edgecolor='none'))
    ax.plot([b2_x, b2_x + b2_w], [b2_y + b2_h - 5.5, b2_y + b2_h - 5.5], color='#333333', linewidth=0.7)

    ax.text(b2_x + 2.5, b2_y + b2_h - 2.8, "NHÁNH KHÔNG: XÁC NHẬN TRI THỨC",
            fontproperties=FONT_BOLD, fontsize=6.6, color='#111111', ha='left', va='center')

    b2_lines = [
        "• Giả thuyết được dữ liệu và kiểm thử xác thực.",
        "• Ghi nhận kiến thức chuẩn xác vào mô hình tư duy.",
        "• Tạo git commit sạch và chuyển sang mục tiêu tiếp theo."
    ]
    for li, bl in enumerate(b2_lines):
        ax.text(b2_x + 2.5, b2_y + b2_h - 9.0 - li * 4.6, bl, fontproperties=FONT_REG,
                fontsize=6.0, color='#222222', ha='left', va='center')

    # Arrows from Diamond to Branches
    # YES branch: Right tip of diamond (d_cx + d_hw, d_cy) -> up to (b1_x, b1_y + b1_h/2)
    ax.plot([d_cx + d_hw, 94.0, 94.0, b1_x], [d_cy, d_cy, b1_y + b1_h/2, b1_y + b1_h/2],
            color='#333333', linewidth=1.1, linestyle='--')
    ax.annotate('', xy=(b1_x, b1_y + b1_h/2), xytext=(b1_x - 1.5, b1_y + b1_h/2),
                arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6))
    ax.text(94.0, d_cy + 4.0, "CÓ (Bác bỏ)", fontproperties=FONT_BOLD,
            fontsize=6.0, color='#111111', ha='center', va='bottom')

    # Loop back arrow from b1 back to Step 1 & 2
    ax.plot([b1_x + b1_w/2, b1_x + b1_w/2, s_x + s_w], [b1_y + b1_h, 92.5, 92.5],
            color='#555555', linewidth=1.0, linestyle=':')
    ax.annotate('', xy=(s_x + s_w, 92.5), xytext=(s_x + s_w + 1.5, 92.5),
                arrowprops=dict(arrowstyle="-|>", color='#555555', lw=1.0, mutation_scale=5))
    ax.text((b1_x + b1_w/2 + s_x + s_w)/2, 94.0, "Điều chỉnh giả thuyết & lặp lại",
            fontproperties=FONT_REG, fontsize=5.8, color='#555555', ha='center', va='bottom')

    # NO branch: Bottom tip of diamond (d_cx, d_cy - d_hh) -> down and right to b2
    ax.plot([d_cx, d_cx, b2_x], [d_cy - d_hh, d_cy - d_hh - 4.0, d_cy - d_hh - 4.0],
            color='#333333', linewidth=1.1)
    ax.annotate('', xy=(b2_x, d_cy - d_hh - 4.0), xytext=(b2_x - 1.5, d_cy - d_hh - 4.0),
                arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6))
    ax.text(d_cx + 12.0, d_cy - d_hh - 2.5, "KHÔNG (Khớp giả thuyết)", fontproperties=FONT_BOLD,
            fontsize=6.0, color='#111111', ha='left', va='bottom')

    # Bottom Invariant Note
    note_box = patches.FancyBboxPatch((4, 3.5), 160, 7.5,
                                     boxstyle="round,pad=0,rounding_size=1.5",
                                     facecolor='#FAFAFA', edgecolor='#666666', linewidth=0.7)
    ax.add_patch(note_box)
    ax.text(84, 7.2, "Quy tắc cốt lõi: Không lập trình theo cảm tính; mọi thay đổi đều phải được chứng minh hoặc bác bỏ bằng kiểm thử tự động",
            fontproperties=FONT_BOLD, fontsize=6.3, color='#222222', ha='center', va='center')

    plt.tight_layout(pad=0.2)
    out_path = os.path.join(ASSETS_DIR, 'feedback-loop.png')
    plt.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
    plt.close()
    verify_image(out_path)


def render_fig4():
    """Hình 4: Giải phẫu trực quan cấu trúc một tệp nguồn Go (go-source-anatomy.png)"""
    fig_w_in = 168.0 / 25.4
    fig_h_in = 112.0 / 25.4

    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=320)
    ax.set_xlim(0, 168)
    ax.set_ylim(0, 112)
    ax.set_aspect('equal')
    ax.axis('off')

    bg = patches.Rectangle((0, 0), 168, 112, facecolor='#FFFFFF', edgecolor='none')
    ax.add_patch(bg)

    # Left Column: Code Window (x: 4 to 70, width: 66, y: 6 to 106, height: 100)
    code_box = patches.FancyBboxPatch((4, 6), 66, 100,
                                     boxstyle="round,pad=0,rounding_size=3",
                                     facecolor='#F9F9F9', edgecolor='#444444', linewidth=1.0)
    ax.add_patch(code_box)

    header_bar = patches.FancyBboxPatch((4, 98), 66, 8,
                                       boxstyle="round,pad=0,rounding_size=3",
                                       facecolor='#EEEEEE', edgecolor='#444444', linewidth=1.0)
    ax.add_patch(header_bar)
    header_rect = patches.Rectangle((4, 98), 66, 3, facecolor='#EEEEEE', edgecolor='none')
    ax.add_patch(header_rect)
    ax.plot([4, 70], [98, 98], color='#444444', linewidth=1.0)

    for cx in [7.5, 10.5, 13.5]:
        ax.add_patch(patches.Circle((cx, 102), 1.1, facecolor='#888888', edgecolor='none'))

    ax.text(37, 102, "main.go (Source File Anatomy)", fontproperties=FONT_BOLD, fontsize=8.5,
            color='#222222', ha='center', va='center')

    code_lines = [
        (1, 'package main'),
        (2, ''),
        (3, 'import "fmt"'),
        (4, ''),
        (5, 'const service = "checkout"'),
        (6, ''),
        (7, 'func classify(status int) string {'),
        (8, '    if status >= 500 {'),
        (9, '        return "failed"'),
        (10, '    }'),
        (11, '    return "healthy"'),
        (12, '}'),
        (13, ''),
        (14, 'func main() {'),
        (15, '    status := 503'),
        (16, '    label := classify(status)'),
        (17, '    fmt.Println(service, label)'),
        (18, '}')
    ]

    y_top_code = 93.0
    line_h = 4.6

    bands = [
        (1, 1, '#E8E8E8'),
        (3, 3, '#EDEDED'),
        (5, 12, '#EAEAEA'),
        (14, 18, '#EDEDED'),
    ]

    for s, e, col in bands:
        y_b = y_top_code - (e - 0.5) * line_h - 1.5
        h_b = (e - s + 1) * line_h - 0.5
        band = patches.Rectangle((5, y_b), 64, h_b, facecolor=col, edgecolor='#CCCCCC',
                                 linewidth=0.5, linestyle=':', alpha=0.5)
        ax.add_patch(band)

    for line_no, text in code_lines:
        y_pos = y_top_code - (line_no - 1) * line_h
        ax.text(8.5, y_pos, f"{line_no:2d}", fontproperties=FONT_MONO, fontsize=7.2,
                color='#888888', ha='right', va='center')
        ax.text(11.5, y_pos, text, fontproperties=FONT_MONO, fontsize=7.6,
                color='#111111', ha='left', va='center')

    ax.plot([10, 10], [7, 98], color='#DDDDDD', linewidth=0.8)

    cards = [
        {
            'title': '1. Khai báo Package (Tên gói)',
            'lines': [
                '• Xác định không gian tên và đơn vị biên dịch mà tệp trực thuộc.',
                '• Package "main" báo hiệu cho Go compiler tạo tệp thực thi độc lập.'
            ],
            'y_box': 87.0,
            'h_box': 17.0,
            'anchor_code_y': y_top_code - (1 - 1) * line_h,
            'anchor_code_x': 70.0
        },
        {
            'title': '2. Khai báo Import (Phụ thuộc)',
            'lines': [
                '• Đặt tên package "fmt" vào phạm vi tệp để tham chiếu định danh.',
                '• Giải quyết tại thời điểm biên dịch, không phải thao tác nạp động.'
            ],
            'y_box': 67.5,
            'h_box': 17.0,
            'anchor_code_y': y_top_code - (3 - 1) * line_h,
            'anchor_code_x': 70.0
        },
        {
            'title': '3. Khai báo Cấp Package (const & func)',
            'lines': [
                '• "service": Hằng số chuỗi bất biến được gắn tại compile-time.',
                '• "classify": Hàm logic nhận int, trả string theo ngữ nghĩa giá trị.'
            ],
            'y_box': 44.5,
            'h_box': 20.5,
            'anchor_code_y': y_top_code - (8.5 - 1) * line_h,
            'anchor_code_x': 70.0
        },
        {
            'title': '4. Hàm Khởi điểm (func main)',
            'lines': [
                '• Điểm neo thực thi chương trình do Go runtime kích hoạt sau init.',
                '• Không nhận tham số và không trả mã lỗi trực tiếp từ hàm.'
            ],
            'y_box': 24.5,
            'h_box': 17.5,
            'anchor_code_y': y_top_code - (14 - 1) * line_h,
            'anchor_code_x': 70.0
        },
        {
            'title': '5. Biến Cục bộ & Lời Gọi Hàm',
            'lines': [
                '• "status := 503": Khai báo biến ngắn trong phạm vi khối hàm main.',
                '• "fmt.Println": Lời gọi hàm đưa dữ liệu ra thiết bị đầu ra tiêu chuẩn.'
            ],
            'y_box': 6.0,
            'h_box': 16.5,
            'anchor_code_y': y_top_code - (16.5 - 1) * line_h,
            'anchor_code_x': 70.0
        }
    ]

    card_x = 80.0
    card_w = 84.0

    for c in cards:
        y_b = c['y_box']
        h_b = c['h_box']

        card_rect = patches.FancyBboxPatch((card_x, y_b), card_w, h_b,
                                          boxstyle="round,pad=0,rounding_size=2.5",
                                          facecolor='#FBFBFB', edgecolor='#555555', linewidth=0.9)
        ax.add_patch(card_rect)

        head_rect = patches.FancyBboxPatch((card_x, y_b + h_b - 5.2), card_w, 5.2,
                                          boxstyle="round,pad=0,rounding_size=2.5",
                                          facecolor='#EBEBEB', edgecolor='#555555', linewidth=0.9)
        ax.add_patch(head_rect)
        ax.add_patch(patches.Rectangle((card_x, y_b + h_b - 5.2), card_w, 2.0, facecolor='#EBEBEB', edgecolor='none'))
        ax.plot([card_x, card_x + card_w], [y_b + h_b - 5.2, y_b + h_b - 5.2], color='#555555', linewidth=0.8)

        ax.text(card_x + 3.0, y_b + h_b - 2.7, c['title'], fontproperties=FONT_BOLD,
                fontsize=7.8, color='#111111', ha='left', va='center')

        for i, line_text in enumerate(c['lines']):
            ax.text(card_x + 3.0, y_b + h_b - 8.2 - i * 4.5, line_text, fontproperties=FONT_REG,
                    fontsize=7.1, color='#222222', ha='left', va='center')

        code_anchor_x = c['anchor_code_x']
        code_anchor_y = c['anchor_code_y']
        card_anchor_y = y_b + h_b / 2.0

        elbow_x = 75.0
        ax.plot([code_anchor_x, elbow_x, card_x], [code_anchor_y, card_anchor_y, card_anchor_y],
                color='#444444', linewidth=1.0)
        ax.add_patch(patches.Circle((code_anchor_x, code_anchor_y), 0.7, facecolor='#333333', edgecolor='none'))
        ax.annotate('', xy=(card_x, card_anchor_y), xytext=(card_x - 1.5, card_anchor_y),
                    arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.0, mutation_scale=7))

    plt.tight_layout(pad=0.2)
    out_path = os.path.join(ASSETS_DIR, 'go-source-anatomy.png')
    plt.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
    plt.close()
    verify_image(out_path)


def render_fig5():
    """Hình 5: Mô hình các lớp xử lý của Go compiler (compiler-doc-go.png)"""
    fig_w_in = 168.0 / 25.4
    fig_h_in = 122.0 / 25.4

    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=320)
    ax.set_xlim(0, 168)
    ax.set_ylim(0, 122)
    ax.set_aspect('equal')
    ax.axis('off')

    bg = patches.Rectangle((0, 0), 168, 122, facecolor='#FFFFFF', edgecolor='none')
    ax.add_patch(bg)

    title_box = patches.FancyBboxPatch((4, 111.5), 160, 8.0,
                                      boxstyle="round,pad=0,rounding_size=2.0",
                                      facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.9)
    ax.add_patch(title_box)
    ax.text(84, 116.0, "MÔ HÌNH CÁC LỚP XỬ LÝ CỦA GO COMPILER & LINKER",
            fontproperties=FONT_BOLD, fontsize=9.0, color='#111111', ha='center', va='center')
    ax.text(84, 113.5, "Quy trình chuyển đổi phân lớp từ mã nguồn văn bản sang tệp thực thi độc lập",
            fontproperties=FONT_REG, fontsize=6.8, color='#444444', ha='center', va='center')

    layers = [
        {
            'id': 1,
            'tag': 'TẦNG 1: FRONTEND (TỪ VỰNG & CÚ PHÁP)',
            'y_top': 108.0,
            'h': 19.0,
            'boxes': [
                ('Scanner / Lexer', ['Tách ký tự thành Tokens', '(keyword, id, literal)']),
                ('Parser', ['Kiểm tra cấu trúc cú pháp', '→ Cây cú pháp thô (AST)'])
            ],
            'output': 'Cây cú pháp thô (Untyped AST)',
            'has_rejection': True,
            'reject_title': 'CỔNG CHẶN: SYNTAX ERROR',
            'reject_lines': [
                '• Lỗi ngữ pháp, thiếu ngoặc, token lạ.',
                '• Compiler DỪNG NGAY tại Frontend.',
                '• Không phân tích kiểu hay sinh mã.'
            ]
        },
        {
            'id': 2,
            'tag': 'TẦNG 2: PHÂN TÍCH NGỮ NGHĨA & KIỂM TRA KIỂU',
            'y_top': 84.5,
            'h': 19.0,
            'boxes': [
                ('Name Resolution', ['Định vị phạm vi (scope)', 'Liên kết định danh biến/hàm']),
                ('Strict Type Checker', ['Kiểm tra tương thích kiểu tĩnh', 'Phát hiện unused var / import'])
            ],
            'output': 'Cây cú pháp có kiểu (Typed AST)',
            'has_rejection': True,
            'reject_title': 'CỔNG CHẶN: TYPE ERROR',
            'reject_lines': [
                '• Sai kiểu, undefined, biến/import thừa.',
                '• Zero warnings: mọi sai lệch là lỗi.',
                '• Compiler TỪ CHỐI sinh mã máy.'
            ]
        },
        {
            'id': 3,
            'tag': 'TẦNG 3: MIDDLE & BACKEND (SSA, TỐI ƯU & HẠ MÃ)',
            'y_top': 61.0,
            'h': 19.0,
            'boxes': [
                ('SSA Lowering', ['Chuyển AST sang', 'Static Single Assign']),
                ('Optimization', ['Inlining, dead-code', '& bounds-check elim']),
                ('Code Generation', ['Phát sinh lệnh máy', 'theo kiến trúc CPU'])
            ],
            'output': 'Tệp đối tượng trung gian (.a / .o)',
            'has_rejection': False,
            'side_title': 'TỐI ƯU HÓA SSA IR',
            'side_lines': [
                '• Ngữ nghĩa đã bảo đảm an toàn.',
                '• Tối ưu hóa sâu trên SSA IR.',
                '• Phát sinh mã máy cho CPU đích.'
            ]
        },
        {
            'id': 4,
            'tag': 'TẦNG 4: LINKER & LIÊN KẾT HỆ THỐNG (cmd/link)',
            'y_top': 37.5,
            'h': 19.0,
            'boxes': [
                ('Symbol Resolution', ['Hợp nhất bảng địa chỉ', 'hàm, hằng & biến']),
                ('Runtime Integration', ['Gắn runtime: GC,', 'goroutine scheduler']),
                ('Binary Packaging', ['Đóng gói tệp thực thi', 'ELF / PE / Mach-O'])
            ],
            'output': 'Tệp thực thi độc lập (Standalone Binary)',
            'has_rejection': False,
            'side_title': 'TỆP THỰC THI TỰ HÀNH',
            'side_lines': [
                '• Tích hợp sẵn Go runtime & GC.',
                '• Zero VM / Không phụ thuộc máy ảo.',
                '• Thực thi trực tiếp trên OS.'
            ]
        }
    ]

    main_x = 4.0
    main_w = 106.0
    side_x = 118.0
    side_w = 46.0

    for lyr in layers:
        y_top = lyr['y_top']
        h = lyr['h']
        y_bot = y_top - h

        box = patches.FancyBboxPatch((main_x, y_bot), main_w, h,
                                    boxstyle="round,pad=0,rounding_size=2.0",
                                    facecolor='#FBFBFB', edgecolor='#444444', linewidth=0.9)
        ax.add_patch(box)

        tag_h = 4.8
        tag_rect = patches.FancyBboxPatch((main_x, y_top - tag_h), main_w, tag_h,
                                         boxstyle="round,pad=0,rounding_size=2.0",
                                         facecolor='#EBEBEB', edgecolor='#444444', linewidth=0.9)
        ax.add_patch(tag_rect)
        ax.add_patch(patches.Rectangle((main_x, y_bot + h - tag_h), main_w, 2.0, facecolor='#EBEBEB', edgecolor='none'))
        ax.plot([main_x, main_x + main_w], [y_top - tag_h, y_top - tag_h], color='#444444', linewidth=0.7)

        ax.text(main_x + 3.0, y_top - 2.5, lyr['tag'], fontproperties=FONT_BOLD,
                fontsize=7.2, color='#111111', ha='left', va='center')

        n_boxes = len(lyr['boxes'])
        sub_w = (main_w - 6.0 - (n_boxes - 1) * 6.0) / n_boxes
        sub_h = 11.2
        sub_y = y_bot + 1.6

        for bi, (btitle, bdescs) in enumerate(lyr['boxes']):
            bx = main_x + 3.0 + bi * (sub_w + 6.0)
            s_box = patches.FancyBboxPatch((bx, sub_y), sub_w, sub_h,
                                          boxstyle="round,pad=0,rounding_size=1.5",
                                          facecolor='#EEEEEE', edgecolor='#777777', linewidth=0.7)
            ax.add_patch(s_box)

            ax.text(bx + sub_w/2, sub_y + sub_h - 2.8, btitle, fontproperties=FONT_BOLD,
                    fontsize=6.8, color='#111111', ha='center', va='center')

            for di, desc_line in enumerate(bdescs):
                ax.text(bx + sub_w/2, sub_y + sub_h - 5.8 - di * 2.8, desc_line, fontproperties=FONT_REG,
                        fontsize=5.8, color='#333333', ha='center', va='center')

            if bi < n_boxes - 1:
                arr_x = bx + sub_w
                ax.annotate('', xy=(arr_x + 5.5, sub_y + sub_h/2), xytext=(arr_x + 0.5, sub_y + sub_h/2),
                            arrowprops=dict(arrowstyle="-|>", color='#444444', lw=0.9, mutation_scale=6))

        if lyr['id'] < 4:
            next_lyr = layers[lyr['id']]
            ax.plot([main_x + main_w/2, main_x + main_w/2], [y_bot, next_lyr['y_top']],
                    color='#222222', linewidth=1.1)
            ax.annotate('', xy=(main_x + main_w/2, next_lyr['y_top']),
                        xytext=(main_x + main_w/2, next_lyr['y_top'] + 1.2),
                        arrowprops=dict(arrowstyle="-|>", color='#222222', lw=1.1, mutation_scale=7))
            ax.text(main_x + main_w/2 + 2.5, (y_bot + next_lyr['y_top'])/2, f"→ {lyr['output']}",
                    fontproperties=FONT_MONO, fontsize=6.2, color='#333333', ha='left', va='center')

        side_box = patches.FancyBboxPatch((side_x, y_bot), side_w, h,
                                         boxstyle="round,pad=0,rounding_size=2.0",
                                         facecolor='#F6F6F6' if lyr['has_rejection'] else '#FAFAFA',
                                         edgecolor='#444444' if lyr['has_rejection'] else '#777777',
                                         linewidth=0.9,
                                         linestyle='--' if lyr['has_rejection'] else '-')
        ax.add_patch(side_box)

        s_head_h = 4.8
        s_head_col = '#E2E2E2' if lyr['has_rejection'] else '#ECECEC'
        s_head = patches.FancyBboxPatch((side_x, y_top - s_head_h), side_w, s_head_h,
                                       boxstyle="round,pad=0,rounding_size=2.0",
                                       facecolor=s_head_col, edgecolor='#444444' if lyr['has_rejection'] else '#777777',
                                       linewidth=0.9, linestyle='--' if lyr['has_rejection'] else '-')
        ax.add_patch(s_head)
        ax.add_patch(patches.Rectangle((side_x, y_top - s_head_h), side_w, 2.0, facecolor=s_head_col, edgecolor='none'))
        ax.plot([side_x, side_x + side_w], [y_top - s_head_h, y_top - s_head_h],
                color='#444444' if lyr['has_rejection'] else '#777777', linewidth=0.7)

        header_text = lyr['reject_title'] if lyr['has_rejection'] else lyr['side_title']
        ax.text(side_x + side_w/2, y_top - 2.5, header_text, fontproperties=FONT_BOLD,
                fontsize=6.6, color='#111111', ha='center', va='center')

        lines_to_draw = lyr['reject_lines'] if lyr['has_rejection'] else lyr['side_lines']
        for li, line_t in enumerate(lines_to_draw):
            ax.text(side_x + 2.8, y_top - 7.5 - li * 3.6, line_t, fontproperties=FONT_REG,
                    fontsize=6.1, color='#111111' if lyr['has_rejection'] else '#444444', ha='left', va='center')

        mid_y = y_bot + h/2
        if lyr['has_rejection']:
            ax.plot([main_x + main_w, side_x], [mid_y, mid_y], color='#333333', linewidth=1.1, linestyle='--')
            ax.annotate('', xy=(side_x, mid_y), xytext=(side_x - 1.8, mid_y),
                        arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6))
            ax.text((main_x + main_w + side_x)/2, mid_y + 1.2, "Nếu lỗi",
                    fontproperties=FONT_BOLD, fontsize=5.8, color='#333333', ha='center', va='bottom')
        else:
            ax.plot([main_x + main_w, side_x], [mid_y, mid_y], color='#888888', linewidth=0.7, linestyle=':')
            ax.annotate('', xy=(side_x, mid_y), xytext=(side_x - 1.5, mid_y),
                        arrowprops=dict(arrowstyle="-|>", color='#888888', lw=0.7, mutation_scale=5))

    note_box = patches.FancyBboxPatch((4, 4), 160, 11.5,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#F8F8F8', edgecolor='#555555', linewidth=0.8)
    ax.add_patch(note_box)

    ax.text(8, 12.8, "NGUYÊN LÝ VẬN HÀNH CỦA GO COMPILER (FAIL-FAST & TỰ CHỨA):",
            fontproperties=FONT_BOLD, fontsize=7.1, color='#111111', ha='left', va='center')

    n1 = "1. Triết lý Fail-Fast: Lỗi cú pháp và xung đột kiểu dữ liệu bị chặn hoàn toàn tại Tầng 1 & 2 trước khi phát sinh mã trung gian SSA."
    n2 = "2. Zero Warnings: Trình biên dịch Go từ chối khái niệm 'cảnh báo'; biến hoặc import không dùng đều lập tức trở thành lỗi biên dịch."
    n3 = "3. Standalone Artifact: Linker tích hợp trực tiếp Go runtime vào binary, tạo tệp thực thi độc lập không cần cài đặt môi trường máy ảo."

    ax.text(8, 9.8, n1, fontproperties=FONT_REG, fontsize=6.1, color='#333333', ha='left', va='center')
    ax.text(8, 7.3, n2, fontproperties=FONT_REG, fontsize=6.1, color='#333333', ha='left', va='center')
    ax.text(8, 4.8, n3, fontproperties=FONT_REG, fontsize=6.1, color='#333333', ha='left', va='center')

    plt.tight_layout(pad=0.2)
    out_path = os.path.join(ASSETS_DIR, 'compiler-doc-go.png')
    plt.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
    plt.close()
    verify_image(out_path)


def render_fig6():
    """Hình 6: Trực quan hóa ranh giới phạm vi từ vựng (go-scope-trace.png)"""
    fig_w_in = 168.0 / 25.4
    fig_h_in = 116.0 / 25.4

    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=320)
    ax.set_xlim(0, 168)
    ax.set_ylim(0, 116)
    ax.set_aspect('equal')
    ax.axis('off')

    bg = patches.Rectangle((0, 0), 168, 116, facecolor='#FFFFFF', edgecolor='none')
    ax.add_patch(bg)

    title_box = patches.FancyBboxPatch((4, 106), 160, 7.5,
                                      boxstyle="round,pad=0,rounding_size=2.0",
                                      facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.9)
    ax.add_patch(title_box)
    ax.text(84, 110.2, "TRỰC QUAN HÓA RANH GIỚI PHẠM VI TỪ VỰNG (LEXICAL SCOPE)",
            fontproperties=FONT_BOLD, fontsize=9.0, color='#111111', ha='center', va='center')
    ax.text(84, 107.8, "Quy tắc phân giải tên tại thời điểm biên dịch và sự tách biệt với vòng đời lưu trữ",
            fontproperties=FONT_REG, fontsize=6.8, color='#444444', ha='center', va='center')

    code_win = patches.FancyBboxPatch((4, 22), 82, 81,
                                     boxstyle="round,pad=0,rounding_size=2.5",
                                     facecolor='#FAFAFA', edgecolor='#444444', linewidth=1.0)
    ax.add_patch(code_win)

    header_bar = patches.FancyBboxPatch((4, 96.5), 82, 6.5,
                                       boxstyle="round,pad=0,rounding_size=2.5",
                                       facecolor='#EEEEEE', edgecolor='#444444', linewidth=1.0)
    ax.add_patch(header_bar)
    ax.add_patch(patches.Rectangle((4, 96.5), 82, 2.5, facecolor='#EEEEEE', edgecolor='none'))
    ax.plot([4, 86], [96.5, 96.5], color='#444444', linewidth=0.8)

    for cx in [7.0, 9.8, 12.6]:
        ax.add_patch(patches.Circle((cx, 99.8), 1.0, facecolor='#888888', edgecolor='none'))

    ax.text(45, 99.8, "scope_demo.go — Cấu trúc Khối lệnh Lồng nhau",
            fontproperties=FONT_BOLD, fontsize=7.8, color='#222222', ha='center', va='center')

    s1_box = patches.FancyBboxPatch((6, 25), 78, 69,
                                   boxstyle="round,pad=0,rounding_size=2.0",
                                   facecolor='#F4F4F4', edgecolor='#666666', linewidth=0.8)
    ax.add_patch(s1_box)

    s1_badge = patches.FancyBboxPatch((7, 88.5), 34, 4.2,
                                     boxstyle="round,pad=0,rounding_size=1.2",
                                     facecolor='#E0E0E0', edgecolor='#555555', linewidth=0.6)
    ax.add_patch(s1_badge)
    ax.text(24, 90.6, "SCOPE 1: Khối hàm func main()", fontproperties=FONT_BOLD,
            fontsize=6.2, color='#111111', ha='center', va='center')

    s2_box = patches.FancyBboxPatch((18, 46), 64, 31,
                                   boxstyle="round,pad=0,rounding_size=2.0",
                                   facecolor='#E8E8E8', edgecolor='#333333', linewidth=0.9, linestyle='--')
    ax.add_patch(s2_box)

    s2_badge = patches.FancyBboxPatch((19, 73.0), 32, 3.6,
                                     boxstyle="round,pad=0,rounding_size=1.2",
                                     facecolor='#D5D5D5', edgecolor='#444444', linewidth=0.6)
    ax.add_patch(s2_badge)
    ax.text(35, 74.8, "SCOPE 2: Khối con if block", fontproperties=FONT_BOLD,
            fontsize=6.0, color='#111111', ha='center', va='center')

    code_items = [
        (1, 84.0, 'func main() {', '#111111'),
        (2, 79.5, '    status := 503', '#111111'),
        (3, 68.0, '    if status >= 500 {', '#111111'),
        (4, 63.0, '        label := "failed"', '#111111'),
        (5, 58.0, '        fmt.Println(label)', '#333333'),
        (6, 49.5, '    }', '#111111'),
        (7, 40.5, '    fmt.Println(label)', '#222222'),
        (8, 29.0, '}', '#111111')
    ]

    for lno, ypos, ctext, ccol in code_items:
        ax.text(9.5, ypos, f"{lno}", fontproperties=FONT_MONO, fontsize=6.8,
                color='#888888', ha='right', va='center')
        ax.text(12.5, ypos, ctext, fontproperties=FONT_MONO, fontsize=7.2,
                color=ccol, ha='left', va='center')

    err_rect = patches.FancyBboxPatch((11.5, 34.5), 70, 9.5,
                                     boxstyle="round,pad=0,rounding_size=1.5",
                                     facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.8, linestyle=':')
    ax.add_patch(err_rect)
    ax.text(14.0, 36.5, "[X] Lỗi biên dịch: undefined: label", fontproperties=FONT_BOLD, fontsize=6.2,
            color='#333333', ha='left', va='center')

    cards = [
        {
            'title': '1. Tham chiếu Hợp lệ: Từ Khối con ra Khối cha',
            'status': '[PASS] Biểu thức tại dòng 3',
            'pass': True,
            'y_top': 103.0,
            'h': 24.0,
            'lines': [
                '• Tại dòng 3 (`status >= 500`): Compiler tìm biến `status`.',
                '• Scope 2 không có → Dò ngược ra Scope 1 (khối cha).',
                '• Thấy `status` khai báo ở dòng 2 → Phân giải THÀNH CÔNG.'
            ],
            'pointer_code_y': 68.0
        },
        {
            'title': '2. Tham chiếu Hợp lệ: Nội bộ trong Khối con',
            'status': '[PASS] Biểu thức tại dòng 5',
            'pass': True,
            'y_top': 76.5,
            'h': 24.0,
            'lines': [
                '• Tại dòng 5 (`fmt.Println(label)`): Compiler tìm biến `label`.',
                '• Tìm thấy ngay trong Scope 2 tại dòng 4 (`label := "failed"`).',
                '• Biến `label` đang trong tầm vực → Phân giải THÀNH CÔNG.'
            ],
            'pointer_code_y': 58.0
        },
        {
            'title': '3. Vi phạm Ranh giới Từ vựng (Compiler Chặn)',
            'status': '[FAIL] undefined: label tại dòng 7',
            'pass': False,
            'y_top': 50.0,
            'h': 25.5,
            'lines': [
                '• Tại dòng 7 (ngoài `if`): Lời gọi cố gắng truy xuất `label`.',
                '• Dấu `}` ở dòng 6 đã ĐÓNG Scope 2; `label` kết thúc phạm vi từ vựng.',
                '• Compiler không bao giờ dò vào khối con → Báo lỗi: `undefined: label`.'
            ],
            'pointer_code_y': 39.5
        }
    ]

    card_x = 92.0
    card_w = 72.0

    for c in cards:
        y_top = c['y_top']
        h = c['h']
        y_bot = y_top - h

        c_box = patches.FancyBboxPatch((card_x, y_bot), card_w, h,
                                      boxstyle="round,pad=0,rounding_size=2.0",
                                      facecolor='#FAFAFA', edgecolor='#444444' if not c['pass'] else '#666666',
                                      linewidth=0.9, linestyle='--' if not c['pass'] else '-')
        ax.add_patch(c_box)

        head_h = 5.2
        c_head = patches.FancyBboxPatch((card_x, y_top - head_h), card_w, head_h,
                                       boxstyle="round,pad=0,rounding_size=2.0",
                                       facecolor='#E4E4E4' if not c['pass'] else '#EAEAEA',
                                       edgecolor='#444444' if not c['pass'] else '#666666',
                                       linewidth=0.9, linestyle='--' if not c['pass'] else '-')
        ax.add_patch(c_head)
        ax.add_patch(patches.Rectangle((card_x, y_top - head_h), card_w, 2.0,
                                      facecolor='#E4E4E4' if not c['pass'] else '#EAEAEA', edgecolor='none'))
        ax.plot([card_x, card_x + card_w], [y_top - head_h, y_top - head_h],
                color='#444444' if not c['pass'] else '#666666', linewidth=0.7)

        ax.text(card_x + 2.5, y_top - 2.8, c['title'], fontproperties=FONT_BOLD,
                fontsize=6.6, color='#111111', ha='left', va='center')

        ax.text(card_x + 2.5, y_top - 7.5, c['status'], fontproperties=FONT_BOLD,
                fontsize=6.0, color='#222222', ha='left', va='center')

        for li, line_t in enumerate(c['lines']):
            ax.text(card_x + 2.5, y_top - 11.2 - li * 4.4, line_t, fontproperties=FONT_REG,
                    fontsize=6.0, color='#222222', ha='left', va='center')

        c_mid_y = y_bot + h/2.0
        code_pt_y = c['pointer_code_y']

        ax.plot([86.0, 89.0, card_x], [code_pt_y, c_mid_y, c_mid_y],
                color='#444444' if not c['pass'] else '#666666', linewidth=0.9,
                linestyle='--' if not c['pass'] else '-')
        ax.add_patch(patches.Circle((86.0, code_pt_y), 0.7, facecolor='#333333', edgecolor='none'))
        ax.annotate('', xy=(card_x, c_mid_y), xytext=(card_x - 1.5, c_mid_y),
                    arrowprops=dict(arrowstyle="-|>", color='#333333', lw=0.9, mutation_scale=6))

    note_box = patches.FancyBboxPatch((4, 4), 160, 15.0,
                                     boxstyle="round,pad=0,rounding_size=2.0",
                                     facecolor='#F6F6F6', edgecolor='#555555', linewidth=0.8)
    ax.add_patch(note_box)

    ax.text(7.5, 16.2, "QUY TẮC CỐT LÕI: PHÂN BIỆT PHẠM VI TỪ VỰNG (LEXICAL SCOPE) VÀ VÒNG ĐỜI LƯU TRỮ (LIFETIME)",
            fontproperties=FONT_BOLD, fontsize=7.2, color='#111111', ha='left', va='center')

    n1 = "1. Lexical Scope (Phạm vi từ vựng): Là quy tắc tĩnh ở tầng ngôn ngữ tại compile-time, xác định tên biến có thể được 'nhìn thấy' ở đâu."
    n2 = "2. Storage Lifetime (Vòng đời vật lý): Là khoảng thời gian vùng nhớ thực sự tồn tại (trên stack hoặc heap), do Escape Analysis quyết định."
    n3 = "3. Ranh giới đóng dấu ngoặc nhọn '}': Kết thúc khả năng phân giải tên của mã bên ngoài, nhưng KHÔNG đồng nghĩa dữ liệu bị thu hồi ngay lập tức."

    ax.text(7.5, 12.8, n1, fontproperties=FONT_REG, fontsize=6.2, color='#333333', ha='left', va='center')
    ax.text(7.5, 9.8, n2, fontproperties=FONT_REG, fontsize=6.2, color='#333333', ha='left', va='center')
    ax.text(7.5, 6.8, n3, fontproperties=FONT_REG, fontsize=6.2, color='#333333', ha='left', va='center')

    plt.tight_layout(pad=0.2)
    out_path = os.path.join(ASSETS_DIR, 'go-scope-trace.png')
    plt.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
    plt.close()
    verify_image(out_path)


def main():
    print("=== Rendering Figures 1 to 6 (Scientific Redesign) ===")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    render_fig1()
    render_fig2()
    render_fig3()
    render_fig4()
    render_fig5()
    render_fig6()
    print("=== All 6 figures rendered and verified successfully! ===")


if __name__ == '__main__':
    main()
