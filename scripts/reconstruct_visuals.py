# scripts/reconstruct_visuals.py
import subprocess
from pathlib import Path

DIAGRAMS_DIR = Path("assets/diagrams")
PLANTUML_JAR = Path(".tools/plantuml.jar")

# Style block for authentic Buzan-adapted Grayscale Mind Maps
MINDMAP_STYLE = """<style>
mindmapDiagram {
  node {
    BackgroundColor #F4F4F2
    LineColor #000000
    LineThickness 1.2
    FontColor #000000
    FontSize 13
    RoundCorner 8
    Padding 8
  }
  :depth(0) {
    BackgroundColor #2E2E2E
    FontColor #FFFFFF
    FontSize 16
    LineThickness 2.5
    RoundCorner 12
    Padding 12
  }
  :depth(1) {
    BackgroundColor #E5E5E0
    FontColor #000000
    FontSize 14
    LineThickness 1.8
    RoundCorner 8
    Padding 10
  }
}
</style>"""

def update_mindmaps():
    # 1. go-idea-lineage.puml (Buzan Mind Map)
    go_idea_lineage = f"""@startmindmap
skinparam backgroundColor white
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 14
{MINDMAP_STYLE}
* **GOLANG\\n(Hội tụ ý tưởng)**
** DÒNG DÕI C
*** Cú pháp biểu thức
*** Quản lý con trỏ ô nhớ
*** Tốc độ thực thi mã máy
** DÒNG DÕI PASCAL
*** Modula-2
**** Khai báo module
*** Oberon-2
**** Khai báo tên trước kiểu
**** Hệ thống package gọn nhẹ
** TIẾN TRÌNH CSP
*** Tony Hoare (1978)
**** Tiến trình tuần tự giao tiếp
*** Newsqueak & Alef
**** Thử nghiệm channel & select
*** Limbo (Hệ điều hành Inferno)
**** Kênh truyền channel kiểu mạnh
@endmindmap
"""
    (DIAGRAMS_DIR / "go-idea-lineage.puml").write_text(go_idea_lineage, encoding="utf-8")

    # 2. learning-path.puml (Buzan Mind Map)
    learning_path = f"""@startmindmap
skinparam backgroundColor white
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 14
{MINDMAP_STYLE}
* **LỘ TRÌNH\\nHỌC GOLANG**
** NỀN TẢNG & DỮ LIỆU
*** Cú pháp & Kiểu nguyên tử
*** Mảng & Lát cắt (Slice)
*** Con trỏ & Cấu trúc (Struct)
*** Bọc lỗi có cấu trúc
** ĐỒNG THỜI & RUNTIME
*** Goroutine & Kênh truyền (Channel)
*** Bối cảnh Context & Hủy thực thi
*** Bộ điều phối G/M/P Scheduler
*** Phát hiện xung đột Race Detector
** DỊCH VỤ & MẠNG
*** HTTP Client & Máy chủ Server
*** Bắt tay mã hóa TLS Handshake
*** Vòng đời tắt dịch vụ an toàn
*** Cơ sở dữ liệu Transaction SQL
** HỆ THỐNG & DEVOPS
*** Công cụ dòng lệnh CLI
*** Bộ tứ Quan sát Observability
*** Đóng gói Container & Phối hợp
*** Vòng lặp điều hòa Controller K8s
@endmindmap
"""
    (DIAGRAMS_DIR / "learning-path.puml").write_text(learning_path, encoding="utf-8")

    # 3. observability-projections.puml (Buzan Mind Map)
    observability_projections = f"""@startmindmap
skinparam backgroundColor white
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 14
{MINDMAP_STYLE}
* **SỰ KIỆN HỆ THỐNG\\n(Event / Probe)**
** NHẬT KÝ (LOGS)
*** Định danh chi tiết
*** Dữ liệu có cấu trúc (JSON)
*** Bối cảnh lỗi nguyên nhân
** CHỈ SỐ (METRICS)
*** Số liệu thống kê tổng hợp
*** Bộ đếm Counter & Thước đo Gauge
*** Phân bố thời gian Histogram
** DẤU VẾT (TRACES)
*** Đường đi yêu cầu phân tán
*** Mã vết TraceID & SpanID
*** Điểm nghẽn độ trễ mạng
** TRẠNG THÁI (STATE)
*** Hiện trạng tài nguyên bộ nhớ
*** Số lượng Goroutine hoạt động
*** Tải CPU & Tần suất GC
** SỨC KHỎE (HEALTH)
*** Kiểm tra sống (Liveness)
*** Sẵn sàng nhận việc (Readiness)
*** Báo hiệu cho Orchestrator
@endmindmap
"""
    (DIAGRAMS_DIR / "observability-projections.puml").write_text(observability_projections, encoding="utf-8")

    # 4. type-information-boundaries.puml (Buzan Mind Map)
    type_info = f"""@startmindmap
skinparam backgroundColor white
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 14
{MINDMAP_STYLE}
* **TRỪU TƯỢNG HÓA\\nKIỂU DỮ LIỆU**
** GENERICS
*** Cùng thao tác trên nhiều kiểu
*** Bảo toàn thông tin kiểu compile-time
*** Ràng buộc hợp lệ qua Constraint
*** Loại bỏ chi phí ép kiểu lặp lại
** GIAO DIỆN (INTERFACE)
*** Thay thế linh hoạt theo hành vi
*** Thỏa mãn ngầm định (Implicit)
*** Thu nhỏ tối đa cam kết (Contract)
*** Dễ dàng viết giả lập kiểm thử (Mock)
** PHẢN CHIẾU (REFLECTION)
*** Khám phá kiểu tại thời điểm runtime
*** Nhận diện cấu trúc động bất định
*** Cần kiểm soát vì chi phí phụ trội cao
*** Sử dụng gói thư viện chuẩn reflect
@endmindmap
"""
    (DIAGRAMS_DIR / "type-information-boundaries.puml").write_text(type_info, encoding="utf-8")

def update_standard_puml():
    # 5. go-source-anatomy.puml
    p = DIAGRAMS_DIR / "go-source-anatomy.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "JetBrains Mono"
skinparam defaultFontSize 17
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F4F4F1
  BorderColor #000000
  FontColor #000000
  RoundCorner 4
}
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontName "Source Sans 3"
  FontSize 16
  FontColor #000000
}
skinparam arrowColor #000000
left to right direction

rectangle "package main\\n\\nimport \\"fmt\\"\\n\\nconst service = \\"checkout\\"\\n\\nfunc classify(status int) string { ... }\\n\\nfunc main() {\\n    status := 503\\n    label := classify(status)\\n    fmt.Println(service, label)\\n}" as source
note right of source
  package main: khai báo tên gói (package)
  import: nạp thư viện từ gói khác
  const và func: khai báo cấp tệp nguồn
  main: hàm khởi điểm của chương trình thực thi
  status, label: biến cục bộ trong khối lệnh main
end note
@enduml
""", encoding="utf-8")

    # 6. compiler-doc-go.puml
    p = DIAGRAMS_DIR / "compiler-doc-go.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 21
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F4F4F1
  BorderColor #000000
  FontColor #000000
  RoundCorner 6
}
skinparam arrowColor #000000
skinparam ArrowThickness 1.2
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontColor #000000
  FontName "Source Sans 3"
  FontSize 15
}
top to bottom direction

rectangle "Mã nguồn .go\\ntệp văn bản bạn viết" as source
rectangle "Token từ vựng\\npackage · định danh · số · toán tử" as tokens
rectangle "Cú pháp ngữ pháp (AST)\\nkhai báo · biểu thức · khối lệnh" as syntax
rectangle "Kiểm tra kiểu (Type Check)\\nint, string, bool, chữ ký hàm" as types
rectangle "Mã máy thực thi\\nchương trình khởi chạy" as run

source -right-> tokens : tách từ vựng
tokens -down-> syntax : dựng cây cú pháp
syntax -left-> types : phân tích ngữ nghĩa
types -down-> run : hợp lệ thực thi

note bottom of types
  Mô hình tinh thần trừu tượng.
  Compiler thực tế có thêm SSA, inlining và tối ưu mã.
end note
@enduml
""", encoding="utf-8")

    # 7. go-scope-trace.puml
    p = DIAGRAMS_DIR / "go-scope-trace.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 19
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F4F4F1
  BorderColor #000000
  FontColor #000000
  RoundCorner 4
}
skinparam arrowColor #000000
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontColor #000000
  FontName "Source Sans 3"
  FontSize 15
}
frame "Khối lệnh main (phạm vi hàm)" as main {
  rectangle "status\\n(sống trong main)" as status
  frame "Khối lệnh if (phạm vi con)" as ifblock {
    rectangle "label\\n(sống trong if)" as label
  }
}
note right of label
  label chỉ hợp lệ
  ở trong khối if
end note
note bottom of main
  Sau dấu ngoặc đóng }, label hoàn toàn biến mất khỏi scope.
end note
@enduml
""", encoding="utf-8")

    # 8. go-history-timeline.puml
    p = DIAGRAMS_DIR / "go-history-timeline.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F4F4F1
  BorderColor #000000
  FontColor #000000
  RoundCorner 6
}
skinparam arrowColor #000000
skinparam ArrowThickness 1.2
skinparam nodesep 55
skinparam ranksep 38
top to bottom direction

rectangle "2007\\nMục tiêu được phác thảo\\nTên Go được đề xuất" as y2007
rectangle "2008\\nTrình biên dịch thử nghiệm\\nBộ tiền xử lý GCC và bộ công cụ" as y2008
rectangle "2009\\nMở mã nguồn chính thức\\nNgày 10 tháng 11" as y2009
rectangle "2012\\nGo 1 phát hành\\nCam kết tương thích dài hạn" as y2012
rectangle "2015\\nGo 1.5 tự thân\\nToolchain/runtime thuần Go\\nBộ gom rác GC đồng thời" as y2015
rectangle "2018\\nGo 1.11\\nKhởi đầu quản lý Go Modules" as y2018
rectangle "2022\\nGo 1.18\\nTham số kiểu (Generics)" as y2022
rectangle "2026\\nGo 1.27\\nPhương thức tổng quát (Generic methods)" as y2026

y2007 --> y2008
y2008 --> y2009
y2009 --> y2012
y2012 -right-> y2015
y2015 --> y2018
y2018 --> y2022
y2022 --> y2026
@enduml
""", encoding="utf-8")

    # 9. slice-sharing.puml
    p = DIAGRAMS_DIR / "slice-sharing.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #222222
  FontColor #000000
  RoundCorner 5
}
skinparam arrowColor #222222
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontColor #000000
  FontName "Source Sans 3"
  FontSize 15
}
left to right direction
rectangle "a: []int\\nlen 3 · cap 3" as a
rectangle "b: []int\\nlen 3 · cap 3" as b
rectangle "mảng nền (backing array)\\n[99] [20] [30]" as store
a --> store
b --> store
note bottom of b : b := a sao chép slice header (con trỏ, len, cap)
note bottom of store : thay đổi qua b[0] phản ánh trực tiếp sang a[0]
@enduml
""", encoding="utf-8")

    # 10. append-storage.puml
    p = DIAGRAMS_DIR / "append-storage.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 17
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #222222
  FontColor #000000
  RoundCorner 5
}
skinparam arrowColor #222222
top to bottom direction
rectangle "A. Dung lượng (cap) còn đủ\\nold, s cùng trỏ mảng nền A\\nold: [99 20] · s: [99 20 30]" as reuse
rectangle "B. Dung lượng (cap) đã hết\\nold trỏ mảng nền cũ A [10 20]\\ngrown cấp phát mảng nền mới B [99 20 30]" as allocate
reuse -down-> allocate : kết quả append phụ thuộc dung lượng còn lại
@enduml
""", encoding="utf-8")

    # 11. pointer-value-call.puml
    p = DIAGRAMS_DIR / "pointer-value-call.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #222222
  FontColor #000000
  RoundCorner 5
}
skinparam arrowColor #222222
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontColor #000000
  FontName "Source Sans 3"
  FontSize 15
}
left to right direction
rectangle "bên gọi (caller)\\nbalance: int\\n100" as caller
rectangle "tham số hàm\\nx: int\\n100" as parameter
rectangle "sau x += 20\\nx: int\\n120" as changed
caller --> parameter : sao chép giá trị 100
parameter --> changed : gán cục bộ x
note bottom of caller : biến balance gốc vẫn giữ nguyên 100
@enduml
""", encoding="utf-8")

    # 12. pointer-pointee.puml
    p = DIAGRAMS_DIR / "pointer-pointee.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #222222
  FontColor #000000
  RoundCorner 5
}
skinparam arrowColor #222222
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontColor #000000
  FontName "Source Sans 3"
  FontSize 15
}
left to right direction
rectangle "biến của bên gọi\\namount: int\\n100" as amount
rectangle "tham số hàm\\nbalance: *int\\n(giá trị con trỏ)" as pointer
pointer --> amount : lưu địa chỉ ô nhớ
note bottom of pointer : *balance giải tham chiếu ô nhớ này\\nđể đọc hoặc gán giá trị
note bottom of amount : *balance += 20\\nbiến đổi amount gốc thành 120
@enduml
""", encoding="utf-8")

    # 13. struct-copy.puml
    p = DIAGRAMS_DIR / "struct-copy.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #222222
  FontColor #000000
  RoundCorner 5
}
skinparam arrowColor #222222
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontColor #000000
  FontName "Source Sans 3"
  FontSize 15
}
left to right direction
rectangle "billing: Service\\nName: billing\\nPort: 8080\\nHealthy: true\\nRetries: 0" as original
rectangle "candidate: Service\\nName: billing\\nPort: 8080\\nHealthy: false\\nRetries: 0" as copy
original --> copy : candidate := billing\\nsao chép toàn bộ các trường
note bottom of original : billing.Healthy vẫn giữ true
note bottom of copy : candidate.Healthy đổi thành false
@enduml
""", encoding="utf-8")

    # 14. map-sharing.puml
    p = DIAGRAMS_DIR / "map-sharing.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #222222
  FontColor #000000
  RoundCorner 5
}
skinparam arrowColor #222222
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontColor #000000
  FontName "Source Sans 3"
  FontSize 15
}
left to right direction
rectangle "registry\\nmap[string]int" as registry
rectangle "alias\\nmap[string]int" as alias
rectangle "dữ liệu map (bảng băm)\\nbilling → 2" as data
registry --> data
alias --> data
note bottom of alias : alias := registry\\nsao chép con trỏ header map
note bottom of data : alias[\\"billing\\"]++\\nhiển thị ngay khi đọc registry
@enduml
""", encoding="utf-8")

    # 15. method-receiver-trace.puml
    p = DIAGRAMS_DIR / "method-receiver-trace.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #222222
  FontColor #000000
  RoundCorner 5
}
skinparam arrowColor #222222
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontColor #000000
  FontName "Source Sans 3"
  FontSize 15
}
left to right direction
rectangle "biến billing\\nService\\nHealthy: true\\nRetries: 0" as billing
rectangle "Bộ tiếp nhận Summary\\n(bản sao Service value)" as summary
rectangle "Bộ tiếp nhận Record\\n(con trỏ *Service)" as record
billing --> summary : billing.Summary()
billing --> record : billing.Record(false)\\nđịa chỉ &billing
note bottom of summary : value receiver nhận bản sao\\nchỉ dùng để đọc an toàn
note bottom of record : pointer receiver sửa ô nhớ gốc\\nHealthy=false, Retries=1
@enduml
""", encoding="utf-8")

    # 16. interface-contract.puml
    p = DIAGRAMS_DIR / "interface-contract.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam defaultFontColor #000000
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #222222
  FontColor #000000
  RoundCorner 5
}
skinparam arrowColor #222222
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontColor #000000
  FontName "Source Sans 3"
  FontSize 15
}
left to right direction
rectangle "renderSummary\\n(bên sử dụng / consumer)" as consumer
rectangle "interface SummarySource\\nSummary() string\\n(cam kết hợp đồng)" as contract
rectangle "Service\\nSummary() string" as service
rectangle "StaticTarget\\nSummary() string" as static
consumer --> contract : phụ thuộc hợp đồng
service --> contract : tập method thỏa mãn
static --> contract : tập method thỏa mãn
note bottom of contract : không cần từ khóa implements\\nthỏa mãn ngầm định (implicit)
@enduml
""", encoding="utf-8")

    # 17. error-boundary-trace.puml
    p = DIAGRAMS_DIR / "error-boundary-trace.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 28
skinparam shadowing false
skinparam rectangle {
  BackgroundColor #FFFFFF
  BorderColor #222222
  FontColor #000000
}
skinparam note {
  BackgroundColor #FFFFFF
  BorderColor #555555
  FontColor #000000
}
skinparam ArrowColor #222222
top to bottom direction

rectangle "ProbeFunc\\ntrả nguyên nhân gốc" as run
rectangle "ProbeFailure\\nservice + endpoint + nguyên nhân" as failure
rectangle "applyProbe\\nbối cảnh operation với %w" as boundary
rectangle "bên gọi (caller)\\nerrors.Is / errors.As" as caller

run -down-> failure : nguyên nhân
failure -down-> boundary : lỗi được bọc (%w)
boundary -down-> caller : lỗi trả về
note bottom of caller
errors.Is: nhận diện theo loại lỗi sentinel
errors.As: trích xuất bối cảnh probe có cấu trúc
end note
@enduml
""", encoding="utf-8")

    # 18. cancellation-cleanup-trace.puml
    p = DIAGRAMS_DIR / "cancellation-cleanup-trace.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam shadowing false
skinparam activity {
  BackgroundColor #FFFFFF
  BorderColor #222222
  FontColor #000000
}
skinparam ArrowColor #222222

start
if (ctx đã bị hủy (cancel)?) then (có)
  :trả về ctx.Err();
  note right: chưa chiếm dụng tài nguyên session
  stop
else (không)
  :mở kết nối endpoint;
  if (kết nối thành công?) then (có)
    :defer session.Close();
    :run(ctx, endpoint, session);
    :Close() luôn chạy trước khi return;
    if (run() phát sinh lỗi?) then (có)
      :bảo toàn lỗi chính (primary error);
    else (không)
      :trả lỗi đóng kết nối nếu có;
    endif
  else (không)
    :trả lỗi mở kết nối;
  endif
endif
stop
@enduml
""", encoding="utf-8")

    # 19. package-boundary-graph.puml
    p = DIAGRAMS_DIR / "package-boundary-graph.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam shadowing false
skinparam rectangle {
  BackgroundColor #FFFFFF
  BorderColor #222222
  FontColor #000000
}
skinparam ArrowColor #222222
left to right direction

rectangle "cmd/opsprobe\\ngốc lắp ghép (composition root)\\nin kết quả" as cmd
rectangle "internal/config\\ncấu hình mục tiêu" as config
rectangle "probe\\nkiểm tra Check, mô hình, ranh giới lỗi" as probe

cmd --> config : nạp cấu hình
cmd --> probe : khởi tạo Service, gọi Check
note bottom of probe
không import ngược cmd hoặc config
(nguyên tắc phụ thuộc một chiều)
end note
@enduml
""", encoding="utf-8")

    # 20. performance-evidence-path.puml
    p = DIAGRAMS_DIR / "performance-evidence-path.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #333333
  RoundCorner 8
}
skinparam arrowColor #333333
left to right direction

rectangle "Triệu chứng\\nchậm hoặc phình bộ nhớ" as symptom
rectangle "Câu hỏi + tải thử nghiệm\\nđại diện thực tế" as question
rectangle "Kiểm thử giữ cam kết\\nBenchmark đo từng thao tác" as measure
rectangle "Dữ liệu profile / trace\\nthu hẹp phạm vi giả thuyết" as evidence
rectangle "Một thay đổi nhỏ\\nđược đo đạc lại" as change

symptom --> question
question --> measure
measure --> evidence
evidence --> change
change --> measure : cùng cam kết hợp đồng

note bottom of evidence
  Không võ đoán từ tên API
  hay từ cảm tính mã nguồn.
end note
@enduml
""", encoding="utf-8")

    # 21. http-client-request-path.puml
    p = DIAGRAMS_DIR / "http-client-request-path.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam shadowing false
skinparam activity {
  BackgroundColor #FFFFFF
  BorderColor #222222
  FontColor #000000
}
skinparam ArrowColor #222222

start
:Yêu cầu có context và deadline;
if (Có kết nối rảnh (idle) phù hợp?) then (có)
  :Tái sử dụng kết nối cũ;
else (không)
  :Phân giải tên miền (DNS)\\nđổi host thành địa chỉ IP;
  :Khởi tạo kết nối TCP (Dial);
  if (URL là HTTPS?) then (có)
    :Bắt tay TLS\\nvà xác minh danh tính host;
  endif
endif
:Gửi yêu cầu HTTP;
:Nhận headers và thân phản hồi;
:Bên gọi đọc luồng dữ liệu\\nvà đóng thân phản hồi (body);
stop
@enduml
""", encoding="utf-8")

    # 22. http-service-lifecycle.puml
    p = DIAGRAMS_DIR / "http-service-lifecycle.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #333333
  FontColor #000000
  RoundCorner 8
}
skinparam arrowColor #333333
left to right direction

rectangle "TIẾP NHẬN (ACCEPTING)\\nlistener mở\\nnhận yêu cầu mới" as accepting
rectangle "GIẢI TỎA (DRAINING)\\nlistener đóng\\nxử lý nốt yêu cầu đang chạy" as draining
rectangle "DỪNG HẲN (STOPPED)\\nđóng kết nối\\ngiải phóng tài nguyên" as stopped

accepting --> draining : tín hiệu dừng / deploy
draining --> stopped : yêu cầu hoàn tất\\nhoặc hết thời hạn deadline

note bottom of draining
  Draining tách biệt với việc đóng listener:
  không nhận thêm việc mới nhưng
  hoàn tất công việc đang dang dở.
end note
@enduml
""", encoding="utf-8")

    # 23. transaction-boundary.puml
    p = DIAGRAMS_DIR / "transaction-boundary.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 22
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #333333
  FontColor #000000
  RoundCorner 8
}
skinparam arrowColor #333333
top to bottom direction

rectangle "BẮT ĐẦU (BEGIN)\\nkhởi tạo giao dịch" as begin
rectangle "CẬP NHẬT\\nchecks.enabled = false" as update
rectangle "GHI NHẬT KÝ\\ncheck_events: disabled" as audit
rectangle "XÁC NHẬN (COMMIT)\\ntrạng thái mới có hiệu lực" as committed
rectangle "HOÀN NGUYÊN (ROLLBACK)\\nbảo toàn trạng thái cũ" as rolled

begin --> update
update --> audit
audit --> committed : mọi câu lệnh\\nthành công
begin ..> rolled : lỗi ở bất kỳ bước nào

note bottom of audit
  Sơ đồ khái niệm về tính nguyên tử (Atomicity).
  Mức cô lập (Isolation) cụ thể do cơ sở dữ liệu
  và cấu hình TxOptions quyết định.
end note
@enduml
""", encoding="utf-8")

    # 24. incident-command-lifecycle.puml
    p = DIAGRAMS_DIR / "incident-command-lifecycle.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 20
skinparam arrowColor #333333
hide footbox
skinparam sequence {
  ParticipantBackgroundColor #F5F5F2
  ParticipantBorderColor #333333
  ParticipantFontColor #000000
  LifeLineBorderColor #777777
  LifeLineBackgroundColor #FFFFFF
}

actor "người vận hành" as operator
participant "lệnh sự cố\\nkiểm tra + ghi nhận" as command
participant "bộ điều phối runner\\nkhởi chạy + chờ + phân loại" as runner
participant "tiến trình con\\nstdout / stderr / mã thoát" as child

operator -> command : mục tiêu + thời hạn deadline
command -> runner : đặc tả Spec + bối cảnh cha
runner -> child : tệp thực thi + đối số
child --> runner : kết quả xuất + mã thoát
runner --> command : kết quả Result + lớp lỗi
command --> operator : bản ghi chẩn đoán

note over runner
  Context bị cancel sẽ ngắt
  tiến trình con theo mặc định.
  Chính sách cho cây tiến trình (process tree) là cơ chế riêng.
end note
@enduml
""", encoding="utf-8")

    # 25. reconciliation-loop.puml
    p = DIAGRAMS_DIR / "reconciliation-loop.puml"
    p.write_text("""@startuml
left to right direction
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam rectangle {
  BackgroundColor #F7F7F4
  BorderColor #5D5D5D
  FontColor #111111
  RoundCorner 8
}
skinparam note {
  BackgroundColor #FFFCE1
  BorderColor #777777
}

rectangle "trạng thái mong muốn (Spec)\\nmã định danh gói, số bản sao, chính sách" as desired
rectangle "bộ điều khiển (Controller)\\nquan sát -> phán đoán -> hành động" as controller
rectangle "trạng thái thực tế (Status)\\nPod, tiến trình, độ sẵn sàng" as current

desired --> controller : cấu hình khai báo (Spec)
current --> controller : dữ liệu quan trắc thực tế
controller --> current : tác động điều chỉnh

note bottom of controller
  Một vòng lặp không cam kết đưa hệ thống về
  trạng thái cuối cùng ngay tức thì.
  Nó là quá trình hội tụ liên tục qua thời gian.
end note
@enduml
""", encoding="utf-8")

    # 26. delivery-evidence-chain.puml
    p = DIAGRAMS_DIR / "delivery-evidence-chain.puml"
    p.write_text("""@startuml
left to right direction
skinparam shadowing false
skinparam defaultFontName "Source Sans 3"
skinparam rectangle {
  BackgroundColor #F7F7F4
  BorderColor #5D5D5D
  FontColor #111111
  RoundCorner 8
}
skinparam note {
  BackgroundColor #FFFCE1
  BorderColor #777777
}

rectangle "phiên bản nguồn\\ncommit đã chọn" as source
rectangle "biên dịch\\nmã định danh gói (digest)" as build
rectangle "bằng chứng\\nkiểm thử + nguồn gốc" as evidence
rectangle "chính sách phê duyệt\\nquyền hạn + cổng kiểm tra" as policy
rectangle "trạng thái mong muốn\\ngói được triển khai" as deploy
rectangle "quan sát phát hành\\ntrạng thái + tín hiệu" as observe

source --> build
build --> evidence
evidence --> policy
policy --> deploy
deploy --> observe

note bottom of policy
  Mỗi bước chỉ chứng minh
  cam kết (contract) của chính nó.
end note
@enduml
""", encoding="utf-8")

def render_all():
    pumls = sorted(DIAGRAMS_DIR.glob("*.puml"))
    print(f"Rendering {len(pumls)} diagrams using {PLANTUML_JAR}...")
    cmd = ["java", "-jar", str(PLANTUML_JAR)] + [str(p) for p in pumls]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("PlantUML error:", res.stderr)
        raise RuntimeError("PlantUML rendering failed!")
    print("All diagrams rendered successfully!")

def main():
    print("1. Updating authentic Buzan Mind Maps...")
    update_mindmaps()
    print("2. Updating standard diagrams with Vietnamese-first labels...")
    update_standard_puml()
    print("3. Rendering all diagrams to PNG...")
    render_all()
    print("Done!")

if __name__ == "__main__":
    main()
