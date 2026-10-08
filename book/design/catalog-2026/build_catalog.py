"""Isolated editorial prototype. Never imports or invokes the production builder.

Run from any directory with ReportLab, PyMuPDF, pypdf, Pillow and numpy installed.
All writes are confined to this directory. Source files are read as UTF-8 bytes.
"""
from __future__ import annotations

import collections
import hashlib
import html
import json
import math
import re
import subprocess
from pathlib import Path

import pymupdf as fitz
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, Image, KeepTogether, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTED_HEAD = "1cc60d9be0e4a2bac78f8efefadd7a64a02f15bd"
LOCKED_SHA = "f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09"
W, H = A4
INNER, OUTER, TOP, BOTTOM = 24*mm, 18*mm, 22*mm, 20*mm
WIDTH = W-INNER-OUTER


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(name, value):
    (HERE/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def protected_snapshot():
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    return {name: sha((ROOT/name).read_bytes()) for name in names
            if name and not name.startswith("book/design/") and (ROOT/name).is_file()}


def parse(path):
    """Lossless block AST for the manuscript's line-oriented dialect, not CommonMark.

    Blank/comment/list/reference blocks are retained, not discarded. Byte identity
    is checked by reconstruction; inline constructs remain raw strings.
    """
    raw = path.read_bytes()
    lines = raw.decode("utf-8").splitlines(keepends=True)
    result, i = [], 0
    while i < len(lines):
        start = i
        text = lines[i].strip()
        fence = re.match(r"^(`{3,}|~{3,})(.*)$", text)
        if fence:
            mark, language = fence.groups()
            i += 1
            while i < len(lines) and not re.match(r"^"+re.escape(mark[0])+"{"+str(len(mark))+r",}\s*$", lines[i].strip()):
                i += 1
            if i == len(lines):
                raise ValueError(f"Unclosed fence: {path}:{start+1}")
            i += 1
            kind = "code" if language.strip() not in ("text", "console", "output", "sh", "bash", "shell", "powershell") else "terminal_output"
        elif not text:
            kind = "blank"
            i += 1
        elif re.match(r"^#{1,6} ", text):
            kind = "H"+str(len(text.split(" ", 1)[0]))
            i += 1
        elif text.startswith("<!--"):
            kind = "pagebreak" if "pagebreak" in text else "comment"
            i += 1
            while "-->" not in "".join(lines[start:i]) and i < len(lines):
                i += 1
        elif text.startswith("|"):
            kind = "table"
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                i += 1
        elif text.startswith("!["):
            kind = "image"
            i += 1
        elif text.startswith("@"):
            kind = "directive_"+text.split()[0][1:]
            i += 1
        elif text in ("---", "***", "___"):
            kind = "rule"
            i += 1
        else:
            kind = "callout" if text.startswith(">") else "list" if re.match(r"^(?:[-*+] |\d+[.)] )", text) else "prose"
            i += 1
            while i < len(lines):
                following = lines[i].strip()
                if not following or re.match(r"^(?:#{1,6} |[|>@]|!\[|<!--|`{3,}|~{3,})", following):
                    break
                if following in ("---", "***", "___"):
                    break
                if bool(re.match(r"^(?:[-*+] |\d+[.)] )", following)) != (kind == "list"):
                    break
                i += 1
        fragment = "".join(lines[start:i])
        node = {"type": kind, "line": start+1, "end_line": i, "raw": fragment}
        if fence:
            node.update(language=language.strip(), payload="".join(lines[start+1:i-1]))
        result.append(node)
    assert "".join(n["raw"] for n in result).encode("utf-8") == raw
    return result


def inventory():
    records, counts, manuscripts = [], collections.Counter(), {}
    for path in sorted((ROOT/"book/chapters").glob("*.md"))+sorted((ROOT/"book/appendices").glob("*.md")):
        nodes = parse(path)
        manuscripts[path.name] = nodes
        for node in nodes:
            counts[node["type"]] += 1
            record = {k: v for k, v in node.items() if k not in ("raw", "payload")}
            record.update(source=path.relative_to(ROOT).as_posix(), sha256=sha(node["raw"].encode("utf-8")))
            if "payload" in node:
                record["payload_sha256"] = sha(node["payload"].encode("utf-8"))
                record["literal_tabs"] = node["payload"].count("\t")
            if node["type"].startswith("H"):
                record["title"] = node["raw"].strip().split(" ", 1)[1]
            records.append(record)
    diagram_files = sorted((ROOT/"assets/diagrams").glob("*"))
    diagram_sources = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in diagram_files
                       if p.suffix in (".puml", ".iuml")}
    dump("object_inventory.json", {"dialect": "lossless line-oriented blocks; inline text retained raw", "manuscript_files": len(manuscripts),
                                   "counts": counts, "nodes": records, "diagram_sources": diagram_sources})
    return manuscripts


def fonts():
    for name, filename in (("Serif", "SourceSerif4-Regular.ttf"), ("SerifBold", "SourceSerif4-Semibold.ttf"),
                           ("Sans", "SourceSans3-Regular.ttf"), ("SansBold", "SourceSans3-Semibold.ttf"), ("Mono", "JetBrainsMono-Regular.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(ROOT/"assets/fonts"/filename)))
    pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="SerifBold", italic="Serif", boldItalic="SerifBold")
    pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="SansBold", italic="Sans", boldItalic="SansBold")


STYLES = {}


def styles():
    specs = {"body": ("Serif",14,21.5), "H1": ("SansBold",24,30), "H2": ("SansBold",17,23),
             "H3": ("SansBold",14,19), "H4": ("SansBold",12.5,17), "caption": ("Sans",10.5,14),
             "meta": ("Sans",10.5,14), "table": ("Serif",11,15.5), "atlas": ("Serif",10.5,14),
             "atlas_id": ("SansBold",11,14.5), "part": ("SansBold",30,36)}
    for key, (font,size,leading) in specs.items():
        STYLES[key] = ParagraphStyle(key, fontName=font, fontSize=size, leading=leading, textColor=colors.black,
                                    bulletFontName="Sans",bulletFontSize=size,
                                    spaceAfter=8 if key=="body" else 7, spaceBefore=12 if key.startswith("H") else 0,
                                    keepWithNext=key.startswith("H") or key=="atlas_id", allowWidows=0, allowOrphans=0)


def inline(text):
    tokens = []
    def code(match):
        tokens.append('<font name="Mono">'+html.escape(match.group(1))+"</font>")
        return f"ZZCODE{len(tokens)-1}ZZ"
    text = re.sub(r"`([^`]+)`", code, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    for n, token in enumerate(tokens):
        text = text.replace(f"ZZCODE{n}ZZ", token)
    return text


def P(text, style="body"):
    return Paragraph(inline(text), STYLES[style])


class Code(Flowable):
    """Text-only, no numbers and no gutter. ActualText is an experiment, not a guarantee."""
    def __init__(self, payload, actual_text=False):
        super().__init__()
        self.payload, self.actual_text = payload, actual_text
        self.lines = payload.splitlines()
        self.height = 20+15.5*max(1,len(self.lines))
        self.width = WIDTH

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        for line in self.lines:
            if pdfmetrics.stringWidth(line.expandtabs(4), "Mono", 11.5) > availWidth-24:
                raise ValueError("Prototype code line exceeds frame; select a complete shorter source block, never shrink code")
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillGray(.95)
        c.setStrokeGray(.4)
        c.setLineWidth(.5)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=1)
        c.setFillGray(0)
        c.setFont("Mono",11.5)
        if self.actual_text:
            actual = (b"\xfe\xff"+self.payload.encode("utf-16-be")).hex()
            c.addLiteral(f"/Span << /ActualText <{actual}> >> BDC")
        for i,line in enumerate(self.lines):
            c.drawString(12,self.height-22-i*15.5,line.expandtabs(4))
        if self.actual_text:
            c.addLiteral("EMC")


class Artwork(Flowable):
    def __init__(self, variant):
        super().__init__()
        self.variant, self.width, self.height = variant, WIDTH, 375

    def polygon(self, c, pts, gray=1):
        p = c.beginPath(); p.moveTo(*pts[0])
        for xy in pts[1:]: p.lineTo(*xy)
        p.close()
        c.setFillGray(gray); c.drawPath(p,stroke=1,fill=1)

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeGray(0); c.setLineWidth(.7)
        if self.variant == "A":
            # Original abstract exploded axonometric. Not a memory/runtime model.
            for k in range(5):
                y=45+k*55; x=83
                self.polygon(c,[(x,y+42),(x+183,y+103),(x+296,y+61),(x+113,y)],.98)
                self.polygon(c,[(x+113,y),(x+296,y+61),(x+296,y+48),(x+113,y-13)],.86)
                for j in range(1,12):
                    t=j/12
                    c.setLineWidth(.3); c.line(x+183*t,y+42+61*t,x+113+183*t,y+61*t)
                c.setLineWidth(.7)
            c.setDash(2,4); c.setStrokeGray(.5)
            for x,y in ((83,87),(379,106),(196,45)):
                c.line(x,y-13,x,y+220)
            c.setDash()
        elif self.variant == "B":
            # Original architectural ink study; large/light structure + fine detail.
            c.translate(20,10); c.scale(.9,.9)
            self.polygon(c,[(65,72),(304,144),(408,108),(172,29)],.96)
            for level in range(4):
                y=86+level*62
                self.polygon(c,[(65,y),(303,y+72),(407,y+36),(171,y-43)],1)
                for col in range(9):
                    x=65+col*29; yy=y+col*8.7
                    c.line(x,yy,x,yy+45)
                    c.setLineWidth(.25); c.line(x,yy+10,x+22,yy+17)
                    c.setLineWidth(.7)
                c.line(171,y-43,171,y+3)
                c.line(407,y+36,407,y+82)
            c.setStrokeGray(.6); c.setLineWidth(.3)
            for j in range(20):
                c.line(34+j*17,14,34+j*17,345)
            c.line(20,48,440,175)
        elif self.variant == "C":
            # Abstract specimen/contour study, not an illustration of Go internals.
            cx,cy=235,187
            for j in range(23):
                p=c.beginPath()
                for k in range(121):
                    a=k*2*math.pi/120
                    r=45+j*4.7+7*math.sin(3*a)+4*math.cos(5*a)
                    xy=(cx+1.1*r*math.cos(a),cy+.86*r*math.sin(a))
                    if k==0:p.moveTo(*xy)
                    else:p.lineTo(*xy)
                c.setLineWidth(1.0 if j%6==0 else .35)
                c.drawPath(p)
            c.setLineWidth(.4)
            for j in range(50):
                a=2*math.pi*j/50
                c.line(cx+40*math.cos(a),cy+34*math.sin(a),cx+139*math.cos(a),cy+116*math.sin(a))
            c.setLineWidth(.8); c.circle(cx,cy,18)
        else:
            c.setFont("SansBold",86)
            c.drawString(0,255,"GO")
            c.drawString(125,155,"LANG")
            c.setLineWidth(.35)
            for j in range(36):
                c.line(j*13,45,j*13,105+1.7*j)
            c.setFont("Sans",11)
            c.drawString(0,15,"NGÔN NGỮ / CƠ CHẾ / BẰNG CHỨNG")
        c.restoreState()


ARRAY_LABELS = ["a: [3]int", "[10] [20] [30]", "b: [3]int", "[99] [20] [30]",
                "b := a", "sao chép mọi phần tử", "a[0] vẫn là 10", "b[0] trở thành 99"]


class ArrayFigure(Flowable):
    def __init__(self):
        super().__init__()
        self.width, self.height = WIDTH, 210

    def wrap(self,availWidth,availHeight):
        return self.width,self.height

    def draw(self):
        c = self.canv
        c.setFillGray(0); c.setStrokeGray(.15); c.setLineWidth(.8)
        for x,head,values,note in ((0,ARRAY_LABELS[0],ARRAY_LABELS[1],ARRAY_LABELS[6]),(286,ARRAY_LABELS[2],ARRAY_LABELS[3],ARRAY_LABELS[7])):
            c.setFillGray(.96); c.rect(x,85,190,85,fill=1)
            c.setFillGray(0); c.setFont("SansBold",14); c.drawString(x+15,144,head)
            c.setFont("Mono",12); c.drawString(x+15,114,values)
            c.setFont("Sans",12); c.drawCentredString(x+95,50,note)
            c.line(x+95,85,x+95,65)
        c.setDash(2,3); c.line(190,126,277,126); c.setDash()
        p=c.beginPath(); p.moveTo(286,126); p.lineTo(277,130); p.lineTo(277,122); p.close(); c.drawPath(p,fill=1)
        c.setFont("Mono",12); c.drawCentredString(WIDTH/2,190,ARRAY_LABELS[4])
        c.setFont("Sans",12); c.drawCentredString(WIDTH/2,175,ARRAY_LABELS[5])


def table(node, small=False):
    lines = node["raw"].strip().splitlines()
    rows = [line.strip().strip("|").split("|") for line in lines if not re.match(r"^\|[ :\-|]+\|$",line.strip())]
    style = "atlas" if small else "table"
    cells = [[P(cell.strip(),style) for cell in row] for row in rows]
    n=len(cells[0])
    weights=[1]*n
    if n==2: weights=[.8,1.2]
    if n==3: weights=[.7,1,1.3]
    t=Table(cells,colWidths=[WIDTH*w/sum(weights) for w in weights],repeatRows=1,hAlign="LEFT")
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.5,colors.HexColor("#555555")),
                           ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E8E8E8")),
                           ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),8),
                           ("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),7),
                           ("BOTTOMPADDING",(0,0),(-1,-1),7)]))
    return t


PROVENANCE=[]


def render_nodes(nodes, source, small=False):
    story=[]
    for node in nodes:
        kind=node["type"]
        if kind in ("blank","comment","rule"): continue
        PROVENANCE.append({"source":source,"line":node["line"],"type":kind,"sha256":sha(node["raw"].encode("utf-8"))})
        raw=node["raw"].strip()
        if kind.startswith("H"):
            story.append(P(raw.split(" ",1)[1],"atlas_id" if small else kind))
        elif kind in ("code","terminal_output"):
            story.extend([Code(node["payload"]),Spacer(1,10)])
        elif kind=="table": story.extend([table(node,small),Spacer(1,10)])
        elif kind.startswith("directive_"):
            story.append(P("Tài liệu tham khảo" if kind=="directive_references" else raw.split(" ",1)[1] if " " in raw else raw,"caption"))
        elif kind=="image":
            if "array-copy.png" in raw:
                story.append(ArrayFigure())
            else:
                src=ROOT/"book"/source
                relative=re.search(r"\]\(([^)]+)\)",raw).group(1)
                image=Image(str((src.parent/relative).resolve()))
                image._restrictSize(WIDTH,390)
                story.append(image)
        elif kind=="callout":
            text=" ".join(line.lstrip("> ") for line in raw.splitlines())
            t=Table([[P(text,"atlas" if small else "body")]],colWidths=[WIDTH],hAlign="LEFT")
            t.setStyle(TableStyle([("BOX",(0,0),(-1,-1),.6,colors.black),("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F5F5F5")),
                                  ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
                                  ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
            story.extend([t,Spacer(1,10)])
        elif kind=="pagebreak": story.append(PageBreak())
        elif kind=="list":
            for line in raw.splitlines():
                text=re.sub(r"^[-*+]\s+","",line.strip())
                story.append(Paragraph(inline(text),STYLES["atlas" if small else "body"],bulletText="•" if re.match(r"^[-*+] ",line.strip()) else None))
        elif small and kind=="prose":
            parts=re.split(r"\n(?=[→!])",raw)
            for part in parts:
                story.append(P(" ".join(part.splitlines()),"atlas"))
        else:
            # Lists stay as literal ordered paragraphs; no content rephrasing.
            story.append(P(" ".join(raw.splitlines()),"atlas" if small else "body"))
    return story


class CatalogDoc(BaseDocTemplate):
    def __init__(self,path):
        super().__init__(str(path),pagesize=A4,title="GOLANG — Editorial Design Catalog 2026",author="Editorial prototype",pageCompression=1,invariant=1)
        self.labels={}; self.targets=[]
        def frames(left,atlas=False):
            if atlas:
                cw=(WIDTH-8*mm)/2
                return [Frame(left,BOTTOM,cw,H-TOP-BOTTOM,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),
                        Frame(left+cw+8*mm,BOTTOM,cw,H-TOP-BOTTOM,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)]
            return [Frame(left,BOTTOM,WIDTH,H-TOP-BOTTOM,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)]
        for name,left,other,atlas in (("recto",INNER,"verso",False),("verso",OUTER,"recto",False),
                                     ("atlas_recto",INNER,"atlas_verso",True),("atlas_verso",OUTER,"atlas_recto",True)):
            self.addPageTemplates(PageTemplate(name,frames=frames(left,atlas),onPage=self.chrome,autoNextPageTemplate=other))

    def chrome(self,c,doc):
        c.saveState()
        left=INNER if doc.page%2 else OUTER
        c.setFillGray(.2); c.setFont("Sans",9.5)
        c.drawString(left,H-14*mm,"GOLANG / DESIGN PROTOTYPE 2026")
        c.setStrokeGray(.7); c.setLineWidth(.4); c.line(left,15.2*mm,left+WIDTH,15.2*mm)
        c.setFont("Sans",9.5)
        if doc.page%2:c.drawRightString(left+WIDTH,11.2*mm,str(doc.page))
        else:c.drawString(left,11.2*mm,str(doc.page))
        c.restoreState()

    def afterFlowable(self,flowable):
        if hasattr(flowable,"catalog_key"):
            key=flowable.catalog_key
            label=flowable.getPlainText()
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(label,key,0)
            self.labels[key]=self.page
            self.targets.append({"key":key,"title":label,"page":self.page})


def build(manuscripts):
    fonts(); styles(); story=[]
    def section(key,title,note=None):
        if story and not isinstance(story[-1],PageBreak):story.append(PageBreak())
        p=P(title,"H1"); p.catalog_key=key; story.append(p)
        if note:story.append(P(note,"meta"))
    def add(nodes,name):story.extend(render_nodes(nodes,name))
    ch1name=next(n for n in manuscripts if n.startswith("01-"))
    ch2name=next(n for n in manuscripts if n.startswith("02-"))
    ch1,ch2=manuscripts[ch1name],manuscripts[ch2name]
    library=manuscripts["devops-library-atlas.md"]
    atlas=manuscripts["error-atlas.md"]
    section("catalog","Hệ thống biên tập / 2026","MẪU DUYỆT — không phải PDF phát hành. Nội dung bài học lấy từ Markdown hiện hành; PDF khóa chỉ là đối chứng hình thức.")
    story.extend([P("Bốn hướng bìa, một hệ thống trang ruột."),P("Giữ body serif 14 pt, code 11.5 pt, nền trắng và lề đối xứng. Đề xuất làm rõ phân cấp, giữ lưới bảng, tăng chữ Atlas và đưa sơ đồ phù hợp sang vector. Không dùng 3D để trang trí một cơ chế kỹ thuật."),
                  P("Bản mẫu chưa đạt cổng copy/paste code: TAB và whitespace không có bảo đảm chỉ nhờ PDF text hoặc ActualText. Hai thư viện extract không thay thế hai PDF reader.","meta"),
                  P("Điều hướng","H2")])
    toc=Table([[P(label,"meta"),Paragraph(f'<link href="#{key}">Xem mẫu</link>',STYLES["meta"])] for key,label in
               (("cover-A","Bìa A — exploded axonometric"),("cover-B","Bìa B — architectural ink study"),
                ("cover-C","Bìa C — scientific contour"),("cover-D","Bìa D — experimental typography"),
                ("system","Quy chuẩn, bìa sau và gáy"),("chapter","Mở chương và trang phối hợp"),
                ("figure","Văn xuôi / vector / caption"),("question","Câu hỏi"),("answer","Đáp án"),
                ("library","Library Atlas"),("atlas","Error Atlas"),("copy","Code-copy laboratory"))],colWidths=[WIDTH-75,75])
    story.append(toc)
    for variant,name,explanation in (("A","Exploded axonometric","Các lớp tách rời; dễ đọc bằng nét và khoảng trắng. Đây là artwork trừu tượng, không phải sơ đồ runtime."),
                                     ("B","Architectural ink study","Cấu trúc phối cảnh với nét cắt và chi tiết. Mật độ nét cao hơn; cần proof giấy trước khi chốt."),
                                     ("C","Scientific contour","Vòng đồng mức và lớp tiết diện trừu tượng; không đại diện một cấu trúc bộ nhớ Go."),
                                     ("D","Experimental typography","Chữ là hình chính; ít mực, ít rủi ro mất chi tiết. Chỉ bìa được phép chơi với tỷ lệ chữ.")):
        section("cover-"+variant,"GOLANG",f"BÌA {variant} / {name} / PROTOTYPE")
        story.extend([P("Giáo trình cập nhật liên tục về Kỹ nghệ phần mềm và DevOps/SRE","H3"),Artwork(variant),Spacer(1,20),
                      P("Đoàn Ngọc Hoàng Minh","H3"),P(explanation,"meta")])
    section("system","Một hệ thống, không nhiều khuôn","Quy chuẩn trang ruột dùng chung; artwork không quyết định phương pháp dạy từng chương.")
    for text,style in (("Mở phần / Library Atlas","part"),(next(n["raw"].strip().lstrip("# ") for n in ch2 if n["type"]=="H1"),"H1"),
                       ("Một baseline để dự đoán","H2"),("Chẩn đoán bằng quan sát","H3"),("Đáp án — chỉ đọc sau khi đã tự làm","H4")):
        story.append(P(text,style))
    story.append(P("Mẫu H3 trên chỉ là nhãn thử kiểu chữ, không phải nội dung mới của sách.","meta"))
    specs=[["Object","Quy chuẩn chính thức đề xuất"],["Prose","Source Serif 4 / 14 / 21.5 pt / đen"],["H1 / H2 / H3 / H4","Sans semibold / 24–17–14–12.5 pt"],["Code / terminal","JetBrains Mono / 11.5 / 15.5 pt; không gutter"],["Table / caption","11 / 15.5 pt; 10.5 / 14 pt; giữ grid"],["Atlas","10.5 / 14 pt; hai cột, gutter 8 mm"],["Geometry","A4; inner 24, outer 18, top 22, bottom 20 mm"]]
    story.append(Table([[P(v,"meta") for v in row] for row in specs],colWidths=[125,WIDTH-125],style=TableStyle([("GRID",(0,0),(-1,-1),.5,colors.gray),("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)])))
    section("binding","Bìa sau / gáy / mở phần","Bìa sau và gáy hiện chưa có trong PDF khóa. Không tự đặt ISBN, blurb hoặc chiều dày gáy.")
    story.extend([P("GOLANG","part"),P("Đoàn Ngọc Hoàng Minh","H3"),Spacer(1,30),
                  P("PLACEHOLDER — vùng bìa sau để duyệt cấu trúc. Không có nội dung quảng bá mới.","meta"),
                  P("PLACEHOLDER — gáy phụ thuộc định lượng/độ dày giấy, số tờ và kiểu đóng. UNKNOWN; không đưa kích thước minh họa thành thông số in.","meta"),Spacer(1,55)])
    add([library[0]]+ [n for n in library[1:] if n["type"]=="prose"][:1],"appendices/devops-library-atlas.md")
    section("chapter","Mở chương: từ kết quả đến câu hỏi","Trích liên tục đầu Chương 2; không dùng một template dạy học mới.")
    stop=next(i for i,n in enumerate(ch2) if n["type"]=="H2")
    add(ch2[:stop],"chapters/"+ch2name)
    section("mixed","Văn xuôi / code / bảng","Hai đoạn trích giữ thứ tự nguồn; dấu ngắt dưới đây báo phần giữa đã lược trong catalog, không lược trong bản thảo.")
    idx=next(i for i,n in enumerate(ch2) if n["type"]=="code" and "a := 10" in n["payload"])
    add(ch2[idx-2:idx+3],"chapters/"+ch2name)
    story.append(P("[NGẮT TRÍCH — xem phần liên tục trong bản thảo]","meta"))
    idx=next(i for i,n in enumerate(ch2) if n["type"]=="directive_table")
    add(ch2[idx:idx+5],"chapters/"+ch2name)
    section("figure","Văn xuôi / vector / caption","Hai nút, một cạnh copy nét đứt có hướng và hai ghi chú: giữ nguyên toàn bộ nhãn và quan hệ từ array-copy.puml.")
    idx=next(i for i,n in enumerate(ch2) if n["type"]=="code" and "a := [3]int" in n["payload"])
    end=next(i for i,n in enumerate(ch2[idx+1:],idx+1) if n["type"]=="H2")
    add(ch2[idx-2:end],"chapters/"+ch2name)
    section("raster","Sơ đồ phức tạp: giữ nguồn trước","KEEP có chủ đích: không dùng một bộ tự chuyển tất cả hình sang 3D hoặc vector mà chưa đối chiếu nhãn và cạnh.")
    diagram_node=next(n for n in library if n["type"]=="image")
    i=library.index(diagram_node)
    add(library[i:i+2],"appendices/devops-library-atlas.md")
    story.append(P("PNG này chỉ minh họa phương án KEEP và kích thước đọc. DPI hữu hiệu được đo trong qa_results.json. Vector hóa diagram này là hạng mục tích hợp sau phê duyệt, không tự nhận đã hoàn tất.","meta"))
    section("question","Câu hỏi trước đáp án","Giữ điểm dừng sư phạm; đáp án chỉ xuất hiện ở trang kế tiếp.")
    qi=next(i for i,n in enumerate(ch1) if n["type"]=="callout" and "hai dòng output" in n["raw"])
    ai=next(i for i,n in enumerate(ch1[qi:],qi) if n["type"]=="H4")
    add(ch1[qi:ai],"chapters/"+ch1name)
    section("answer","Đọc lại sau khi tự dự đoán","Đáp án giữ nguyên văn; H4 là mẫu xử lý riêng, không để literal #### rò ra trang.")
    end=next(i for i,n in enumerate(ch1[ai+1:],ai+1) if n["type"]=="H2")
    add(ch1[ai:end],"chapters/"+ch1name)
    section("table","Bảng: lưới phục vụ phân biệt dữ liệu","Bảng zero value nguyên văn Chương 1; không bỏ đường kẻ để chạy theo hình thức.")
    node=next(n for n in ch1 if n["type"]=="table" and "Zero Value" in n["raw"])
    add([node],"chapters/"+ch1name)
    section("library","Library Atlas: cơ chế có điểm neo","Trích liên tục mục 01 từ source hiện hành. Không đổi version, số liệu hoặc nhận xét implementation.")
    start=next(i for i,n in enumerate(library) if n["type"]=="H3")
    end=next(i for i,n in enumerate(library[start+1:],start+1) if n["type"]=="H3")
    add(library[start:end],"appendices/devops-library-atlas.md")
    story.append(NextPageTemplate("atlas_recto"))
    section("atlas","Error Atlas / bản tra cứu","Mẫu hai cột: giữ cả entry. Body 10.5 pt; không giới hạn số trang. Hai trích đoạn A01–A14 và J06–J11, không phải phụ lục đầy đủ.")
    start=next(i for i,n in enumerate(atlas) if n["type"]=="H3" and "A01" in n["raw"])
    end=next(i for i,n in enumerate(atlas[start:],start) if n["type"]=="H3" and "B01" in n["raw"])
    entries=[]
    for n in atlas[start:end]:
        if n["type"]=="H2":continue
        if n["type"]=="H3" and entries:
            story.append(KeepTogether(render_nodes(entries,"appendices/error-atlas.md",True))); entries=[]
        entries.append(n)
    if entries:story.append(KeepTogether(render_nodes(entries,"appendices/error-atlas.md",True)))
    story.append(P("[NGẮT TRÍCH — B đến J05 vẫn còn nguyên trong source]","meta"))
    start=next(i for i,n in enumerate(atlas) if n["type"]=="H3" and "J06" in n["raw"])
    entries=[]
    for n in atlas[start:]:
        if n["type"]=="H3" and entries:
            story.append(KeepTogether(render_nodes(entries,"appendices/error-atlas.md",True))); entries=[]
        entries.append(n)
    if entries:story.append(KeepTogether(render_nodes(entries,"appendices/error-atlas.md",True)))
    story.append(NextPageTemplate("recto"))
    section("references","Tài liệu tham khảo: giữ điểm neo","Không thêm tài liệu vào bài học. Trích nguyên văn block @references hiện hành; link và version thuộc nội dung, không thuộc artwork.")
    ref_name=next(name for name,nodes in manuscripts.items() if any(n["type"]=="directive_references" for n in nodes))
    ref_nodes=manuscripts[ref_name]
    ref_start=next(i for i,n in enumerate(ref_nodes) if n["type"]=="directive_references")
    add(ref_nodes[ref_start:],"chapters/"+ref_name)
    section("copy","Code-copy laboratory","QA fixture, không phải nội dung bài học. Cùng payload được lưu trong copy_fixture.txt; có TAB, dấu tiếng Việt, hai dấu cách cuối dòng và dòng rỗng.")
    fixture='func main() {\n\tfmt.Println("Tiếng Việt: ă â ê ô ơ ư đ")  \n\n}\n'
    (HERE/"copy_fixture.txt").write_bytes(fixture.encode("utf-8"))
    story.extend([P("A. Text thông thường; TAB được trình bày bằng tab-stop bốn cột.","H3"),Code(fixture),Spacer(1,18),
                  P("B. Cùng hình thức, thêm ActualText ở marked-content span.","H3"),Code(fixture,True),Spacer(1,20),
                  P("Không có gutter, số dòng hoặc số dòng ẩn. Hiển thị đúng indentation không chứng minh clipboard giữ đúng TAB. Kết quả extract và giới hạn PDF reader ghi riêng trong copy_code_report.md.","meta")])
    section("gate","Cổng phê duyệt","Catalog là bằng chứng prototype, không phải chứng nhận cả sách đã sẵn sàng in.")
    story.extend([P("Duyệt hướng bìa A/B/C/D; duyệt hệ thống H1–H4 và Atlas 10.5 pt; duyệt vector hóa có kiểm chứng từng sơ đồ. Giữ hình phức tạp đọc được trước khi tối ưu số trang."),
                  P("Hai điều kiện chưa đóng: clipboard chính xác trên hai PDF reader và thông số giấy/đóng gáy. Mẫu thiếu thử nghiệm không được gọi PASS. Sau phê duyệt phải có nhiệm vụ tích hợp riêng, candidate khác đường dẫn và regression toàn sách.")])
    doc=CatalogDoc(HERE/"catalog.pdf")
    # Use actual page parity instead of relying on the alternating template name,
    # including transitions from one-column to two-column and back.
    original=doc.handle_pageBegin
    def begin():
        left=INNER if (doc.page+1)%2 else OUTER
        shift=left-doc.pageTemplate.frames[0]._x1
        for f in doc.pageTemplate.frames:
            f._x1+=shift; f._x2+=shift; f._x=f._x1+f._leftPadding
        original()
    doc.handle_pageBegin=begin
    doc.build(story)
    dump("catalog_navigation.json",doc.targets)
    dump("specimen_provenance.json",PROVENANCE)
    source=(ROOT/"assets/diagrams/array-copy.puml").read_text(encoding="utf-8")
    assert all(label in source for label in ARRAY_LABELS)
    assert "a ..> b" in source
    dump("diagram_semantics.json",{"source_sha256":sha(source.encode("utf-8")),"labels":ARRAY_LABELS,"nodes":["a","b"],"edges":[{"from":"a","to":"b","style":"dotted","label":["b := a","sao chép mọi phần tử"]}],"notes_attached":{"a":"a[0] vẫn là 10","b":"b[0] trở thành 99"},"raster_keep":"library-informer-data-path.png"})


def baseline_render():
    pdf=ROOT/"Golang_Master.pdf"
    assert sha(pdf.read_bytes())==LOCKED_SHA
    doc=fitz.open(pdf)
    pages=[1,2,14,15,16,36,37,140,160,429,430,484,485,493]
    evidence=HERE/"evidence"; evidence.mkdir(exist_ok=True)
    for page in pages:
        doc[page-1].get_pixmap(matrix=fitz.Matrix(150/72,150/72),colorspace=fitz.csRGB).save(str(evidence/f"baseline-{page:03d}.png"))
    dump("baseline_pages.json",{"pdf_sha256":LOCKED_SHA,"page_count":len(doc),"render_dpi":150,"pages":[{"page":p,"image":f"evidence/baseline-{p:03d}.png","sha256":sha((evidence/f"baseline-{p:03d}.png").read_bytes())} for p in pages]})


def main():
    baseline=HERE/"protected_snapshot.json"
    if baseline.exists():
        assert protected_snapshot()==json.loads(baseline.read_text(encoding="utf-8")), "Protected source changed"
    else:dump("protected_snapshot.json",protected_snapshot())
    manuscripts=inventory()
    build(manuscripts)
    baseline_render()
    print("Built isolated catalog. Production sources/PDF unchanged.")


if __name__=="__main__":main()
