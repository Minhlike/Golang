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
* **GOLANG\\n(Há»™i tá»¥ Ã½ tÆ°á»Ÿng)**
** DÃ’NG DÃ•I C
*** CÃº phÃ¡p biá»ƒu thá»©c
*** Quáº£n lÃ½ con trá» Ã´ nhá»›
*** Tá»‘c Ä‘á»™ thá»±c thi mÃ£ mÃ¡y
** DÃ’NG DÃ•I PASCAL
*** Modula-2
**** Khai bÃ¡o module
*** Oberon-2
**** Khai bÃ¡o tÃªn trÆ°á»›c kiá»ƒu
**** Há»‡ thá»‘ng package gá»n nháº¹
** TIáº¾N TRÃŒNH CSP
*** Tony Hoare (1978)
**** Tiáº¿n trÃ¬nh tuáº§n tá»± giao tiáº¿p
*** Newsqueak & Alef
**** Thá»­ nghiá»‡m channel & select
*** Limbo (Há»‡ Ä‘iá»u hÃ nh Inferno)
**** KÃªnh truyá»n channel kiá»ƒu máº¡nh
@endmindmap
"""
    (DIAGRAMS_DIR / "go-idea-lineage.puml").write_text(go_idea_lineage, encoding="utf-8")

    # 2. learning-path.puml (Buzan Mind Map)
    learning_path = f"""@startmindmap
skinparam backgroundColor white
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 14
{MINDMAP_STYLE}
* **Lá»˜ TRÃŒNH\\nHá»ŒC GOLANG**
** Ná»€N Táº¢NG & Dá»® LIá»†U
*** CÃº phÃ¡p & Kiá»ƒu nguyÃªn tá»­
*** Máº£ng & LÃ¡t cáº¯t (Slice)
*** Con trá» & Cáº¥u trÃºc (Struct)
*** Bá»c lá»—i cÃ³ cáº¥u trÃºc
** Äá»’NG THá»œI & RUNTIME
*** Goroutine & KÃªnh truyá»n (Channel)
*** Bá»‘i cáº£nh Context & Há»§y thá»±c thi
*** Bá»™ Ä‘iá»u phá»‘i G/M/P Scheduler
*** PhÃ¡t hiá»‡n xung Ä‘á»™t Race Detector
** Dá»ŠCH Vá»¤ & Máº NG
*** HTTP Client & MÃ¡y chá»§ Server
*** Báº¯t tay mÃ£ hÃ³a TLS Handshake
*** VÃ²ng Ä‘á»i táº¯t dá»‹ch vá»¥ an toÃ n
*** CÆ¡ sá»Ÿ dá»¯ liá»‡u Transaction SQL
** Há»† THá»NG & DEVOPS
*** CÃ´ng cá»¥ dÃ²ng lá»‡nh CLI
*** Bá»™ tá»© Quan sÃ¡t Observability
*** ÄÃ³ng gÃ³i Container & Phá»‘i há»£p
*** VÃ²ng láº·p Ä‘iá»u hÃ²a Controller K8s
@endmindmap
"""
    (DIAGRAMS_DIR / "learning-path.puml").write_text(learning_path, encoding="utf-8")

    # 3. observability-projections.puml (Buzan Mind Map)
    observability_projections = f"""@startmindmap
skinparam backgroundColor white
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 14
{MINDMAP_STYLE}
* **Sá»° KIá»†N Há»† THá»NG\\n(Event / Probe)**
** NHáº¬T KÃ (LOGS)
*** Äá»‹nh danh chi tiáº¿t
*** Dá»¯ liá»‡u cÃ³ cáº¥u trÃºc (JSON)
*** Bá»‘i cáº£nh lá»—i nguyÃªn nhÃ¢n
** CHá»ˆ Sá» (METRICS)
*** Sá»‘ liá»‡u thá»‘ng kÃª tá»•ng há»£p
*** Bá»™ Ä‘áº¿m Counter & ThÆ°á»›c Ä‘o Gauge
*** PhÃ¢n bá»‘ thá»i gian Histogram
** Dáº¤U Váº¾T (TRACES)
*** ÄÆ°á»ng Ä‘i yÃªu cáº§u phÃ¢n tÃ¡n
*** MÃ£ váº¿t TraceID & SpanID
*** Äiá»ƒm ngháº½n Ä‘á»™ trá»… máº¡ng
** TRáº NG THÃI (STATE)
*** Hiá»‡n tráº¡ng tÃ i nguyÃªn bá»™ nhá»›
*** Sá»‘ lÆ°á»£ng Goroutine hoáº¡t Ä‘á»™ng
*** Táº£i CPU & Táº§n suáº¥t GC
** Sá»¨C KHá»ŽE (HEALTH)
*** Kiá»ƒm tra sá»‘ng (Liveness)
*** Sáºµn sÃ ng nháº­n viá»‡c (Readiness)
*** BÃ¡o hiá»‡u cho Orchestrator
@endmindmap
"""
    (DIAGRAMS_DIR / "observability-projections.puml").write_text(observability_projections, encoding="utf-8")

    # 4. type-information-boundaries.puml (Buzan Mind Map)
    type_info = f"""@startmindmap
skinparam backgroundColor white
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 14
{MINDMAP_STYLE}
* **TRá»ªU TÆ¯á»¢NG HÃ“A\\nKIá»‚U Dá»® LIá»†U**
** GENERICS
*** CÃ¹ng thao tÃ¡c trÃªn nhiá»u kiá»ƒu
*** Báº£o toÃ n thÃ´ng tin kiá»ƒu compile-time
*** RÃ ng buá»™c há»£p lá»‡ qua Constraint
*** Loáº¡i bá» chi phÃ­ Ã©p kiá»ƒu láº·p láº¡i
** GIAO DIá»†N (INTERFACE)
*** Thay tháº¿ linh hoáº¡t theo hÃ nh vi
*** Thá»a mÃ£n ngáº§m Ä‘á»‹nh (Implicit)
*** Thu nhá» tá»‘i Ä‘a cam káº¿t (Contract)
*** Dá»… dÃ ng viáº¿t giáº£ láº­p kiá»ƒm thá»­ (Mock)
** PHáº¢N CHIáº¾U (REFLECTION)
*** KhÃ¡m phÃ¡ kiá»ƒu táº¡i thá»i Ä‘iá»ƒm runtime
*** Nháº­n diá»‡n cáº¥u trÃºc Ä‘á»™ng báº¥t Ä‘á»‹nh
*** Cáº§n kiá»ƒm soÃ¡t vÃ¬ chi phÃ­ phá»¥ trá»™i cao
*** Sá»­ dá»¥ng gÃ³i thÆ° viá»‡n chuáº©n reflect
@endmindmap
"""
    (DIAGRAMS_DIR / "type-information-boundaries.puml").write_text(type_info, encoding="utf-8")

def update_standard_puml():
    # 5. go-source-anatomy.puml
    p = DIAGRAMS_DIR / "go-source-anatomy.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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
  package main: khai bÃ¡o tÃªn gÃ³i (package)
  import: náº¡p thÆ° viá»‡n tá»« gÃ³i khÃ¡c
  const vÃ  func: khai bÃ¡o cáº¥p tá»‡p nguá»“n
  main: hÃ m khá»Ÿi Ä‘iá»ƒm cá»§a chÆ°Æ¡ng trÃ¬nh thá»±c thi
  status, label: biáº¿n cá»¥c bá»™ trong khá»‘i lá»‡nh main
end note
@enduml
""", encoding="utf-8")

    # 6. compiler-doc-go.puml
    p = DIAGRAMS_DIR / "compiler-doc-go.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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

rectangle "MÃ£ nguá»“n .go\\ntá»‡p vÄƒn báº£n báº¡n viáº¿t" as source
rectangle "Token tá»« vá»±ng\\npackage Â· Ä‘á»‹nh danh Â· sá»‘ Â· toÃ¡n tá»­" as tokens
rectangle "CÃº phÃ¡p ngá»¯ phÃ¡p (AST)\\nkhai bÃ¡o Â· biá»ƒu thá»©c Â· khá»‘i lá»‡nh" as syntax
rectangle "Kiá»ƒm tra kiá»ƒu (Type Check)\\nint, string, bool, chá»¯ kÃ½ hÃ m" as types
rectangle "MÃ£ mÃ¡y thá»±c thi\\nchÆ°Æ¡ng trÃ¬nh khá»Ÿi cháº¡y" as run

source -right-> tokens : tÃ¡ch tá»« vá»±ng
tokens -down-> syntax : dá»±ng cÃ¢y cÃº phÃ¡p
syntax -left-> types : phÃ¢n tÃ­ch ngá»¯ nghÄ©a
types -down-> run : há»£p lá»‡ thá»±c thi

note bottom of types
  MÃ´ hÃ¬nh tinh tháº§n trá»«u tÆ°á»£ng.
  Compiler thá»±c táº¿ cÃ³ thÃªm SSA, inlining vÃ  tá»‘i Æ°u mÃ£.
end note
@enduml
""", encoding="utf-8")

    # 7. go-scope-trace.puml
    p = DIAGRAMS_DIR / "go-scope-trace.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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
frame "Khá»‘i lá»‡nh main (pháº¡m vi hÃ m)" as main {
  rectangle "status\\n(sá»‘ng trong main)" as status
  frame "Khá»‘i lá»‡nh if (pháº¡m vi con)" as ifblock {
    rectangle "label\\n(sá»‘ng trong if)" as label
  }
}
note right of label
  label chá»‰ há»£p lá»‡
  á»Ÿ trong khá»‘i if
end note
note bottom of main
  Sau dáº¥u ngoáº·c Ä‘Ã³ng }, label hoÃ n toÃ n biáº¿n máº¥t khá»i scope.
end note
@enduml
""", encoding="utf-8")

    # 8. go-history-timeline.puml
    p = DIAGRAMS_DIR / "go-history-timeline.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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

rectangle "2007\\nMá»¥c tiÃªu Ä‘Æ°á»£c phÃ¡c tháº£o\\nTÃªn Go Ä‘Æ°á»£c Ä‘á» xuáº¥t" as y2007
rectangle "2008\\nTrÃ¬nh biÃªn dá»‹ch thá»­ nghiá»‡m\\nBá»™ tiá»n xá»­ lÃ½ GCC vÃ  bá»™ cÃ´ng cá»¥" as y2008
rectangle "2009\\nMá»Ÿ mÃ£ nguá»“n chÃ­nh thá»©c\\nNgÃ y 10 thÃ¡ng 11" as y2009
rectangle "2012\\nGo 1 phÃ¡t hÃ nh\\nCam káº¿t tÆ°Æ¡ng thÃ­ch dÃ i háº¡n" as y2012
rectangle "2015\\nGo 1.5 tá»± thÃ¢n\\nToolchain/runtime thuáº§n Go\\nBá»™ gom rÃ¡c GC Ä‘á»“ng thá»i" as y2015
rectangle "2018\\nGo 1.11\\nKhá»Ÿi Ä‘áº§u quáº£n lÃ½ Go Modules" as y2018
rectangle "2022\\nGo 1.18\\nTham sá»‘ kiá»ƒu (Generics)" as y2022
rectangle "2026\\nGo 1.27\\nPhÆ°Æ¡ng thá»©c tá»•ng quÃ¡t (Generic methods)" as y2026

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
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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
rectangle "a: []int\\nlen 3 Â· cap 3" as a
rectangle "b: []int\\nlen 3 Â· cap 3" as b
rectangle "máº£ng ná»n (backing array)\\n[99] [20] [30]" as store
a --> store
b --> store
note bottom of b : b := a sao chÃ©p slice header (con trá», len, cap)
note bottom of store : thay Ä‘á»•i qua b[0] pháº£n Ã¡nh trá»±c tiáº¿p sang a[0]
@enduml
""", encoding="utf-8")

    # 10. append-storage.puml
    p = DIAGRAMS_DIR / "append-storage.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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
rectangle "A. Dung lÆ°á»£ng (cap) cÃ²n Ä‘á»§\\nold, s cÃ¹ng trá» máº£ng ná»n A\\nold: [99 20] Â· s: [99 20 30]" as reuse
rectangle "B. Dung lÆ°á»£ng (cap) Ä‘Ã£ háº¿t\\nold trá» máº£ng ná»n cÅ© A [10 20]\\ngrown cáº¥p phÃ¡t máº£ng ná»n má»›i B [99 20 30]" as allocate
reuse -down-> allocate : káº¿t quáº£ append phá»¥ thuá»™c dung lÆ°á»£ng cÃ²n láº¡i
@enduml
""", encoding="utf-8")

    # 11. pointer-value-call.puml
    p = DIAGRAMS_DIR / "pointer-value-call.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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
rectangle "bÃªn gá»i (caller)\\nbalance: int\\n100" as caller
rectangle "tham sá»‘ hÃ m\\nx: int\\n100" as parameter
rectangle "sau x += 20\\nx: int\\n120" as changed
caller --> parameter : sao chÃ©p giÃ¡ trá»‹ 100
parameter --> changed : gÃ¡n cá»¥c bá»™ x
note bottom of caller : biáº¿n balance gá»‘c váº«n giá»¯ nguyÃªn 100
@enduml
""", encoding="utf-8")

    # 12. pointer-pointee.puml
    p = DIAGRAMS_DIR / "pointer-pointee.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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
rectangle "biáº¿n cá»§a bÃªn gá»i\\namount: int\\n100" as amount
rectangle "tham sá»‘ hÃ m\\nbalance: *int\\n(giÃ¡ trá»‹ con trá»)" as pointer
pointer --> amount : lÆ°u Ä‘á»‹a chá»‰ Ã´ nhá»›
note bottom of pointer : *balance giáº£i tham chiáº¿u Ã´ nhá»› nÃ y\\nÄ‘á»ƒ Ä‘á»c hoáº·c gÃ¡n giÃ¡ trá»‹
note bottom of amount : *balance += 20\\nbiáº¿n Ä‘á»•i amount gá»‘c thÃ nh 120
@enduml
""", encoding="utf-8")

    # 13. struct-copy.puml
    p = DIAGRAMS_DIR / "struct-copy.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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
original --> copy : candidate := billing\\nsao chÃ©p toÃ n bá»™ cÃ¡c trÆ°á»ng
note bottom of original : billing.Healthy váº«n giá»¯ true
note bottom of copy : candidate.Healthy Ä‘á»•i thÃ nh false
@enduml
""", encoding="utf-8")

    # 14. map-sharing.puml
    p = DIAGRAMS_DIR / "map-sharing.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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
rectangle "dá»¯ liá»‡u map (báº£ng bÄƒm)\\nbilling â†’ 2" as data
registry --> data
alias --> data
note bottom of alias : alias := registry\\nsao chÃ©p con trá» header map
note bottom of data : alias[\\"billing\\"]++\\nhiá»ƒn thá»‹ ngay khi Ä‘á»c registry
@enduml
""", encoding="utf-8")

    # 15. method-receiver-trace.puml
    p = DIAGRAMS_DIR / "method-receiver-trace.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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
rectangle "biáº¿n billing\\nService\\nHealthy: true\\nRetries: 0" as billing
rectangle "Bá»™ tiáº¿p nháº­n Summary\\n(báº£n sao Service value)" as summary
rectangle "Bá»™ tiáº¿p nháº­n Record\\n(con trá» *Service)" as record
billing --> summary : billing.Summary()
billing --> record : billing.Record(false)\\nÄ‘á»‹a chá»‰ &billing
note bottom of summary : value receiver nháº­n báº£n sao\\nchá»‰ dÃ¹ng Ä‘á»ƒ Ä‘á»c an toÃ n
note bottom of record : pointer receiver sá»­a Ã´ nhá»› gá»‘c\\nHealthy=false, Retries=1
@enduml
""", encoding="utf-8")

    # 16. interface-contract.puml
    p = DIAGRAMS_DIR / "interface-contract.puml"
    p.write_text("""@startuml
skinparam backgroundColor white
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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
rectangle "renderSummary\\n(bÃªn sá»­ dá»¥ng / consumer)" as consumer
rectangle "interface SummarySource\\nSummary() string\\n(cam káº¿t há»£p Ä‘á»“ng)" as contract
rectangle "Service\\nSummary() string" as service
rectangle "StaticTarget\\nSummary() string" as static
consumer --> contract : phá»¥ thuá»™c há»£p Ä‘á»“ng
service --> contract : táº­p method thá»a mÃ£n
static --> contract : táº­p method thá»a mÃ£n
note bottom of contract : khÃ´ng cáº§n tá»« khÃ³a implements\\nthá»a mÃ£n ngáº§m Ä‘á»‹nh (implicit)
@enduml
""", encoding="utf-8")

    # 17. error-boundary-trace.puml
    p = DIAGRAMS_DIR / "error-boundary-trace.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 28
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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

rectangle "ProbeFunc\\ntráº£ nguyÃªn nhÃ¢n gá»‘c" as run
rectangle "ProbeFailure\\nservice + endpoint + nguyÃªn nhÃ¢n" as failure
rectangle "applyProbe\\nbá»‘i cáº£nh operation vá»›i %w" as boundary
rectangle "bÃªn gá»i (caller)\\nerrors.Is / errors.As" as caller

run -down-> failure : nguyÃªn nhÃ¢n
failure -down-> boundary : lá»—i Ä‘Æ°á»£c bá»c (%w)
boundary -down-> caller : lá»—i tráº£ vá»
note bottom of caller
errors.Is: nháº­n diá»‡n theo loáº¡i lá»—i sentinel
errors.As: trÃ­ch xuáº¥t bá»‘i cáº£nh probe cÃ³ cáº¥u trÃºc
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
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
skinparam activity {
  BackgroundColor #FFFFFF
  BorderColor #222222
  FontColor #000000
}
skinparam ArrowColor #222222

start
if (ctx Ä‘Ã£ bá»‹ há»§y (cancel)?) then (cÃ³)
  :tráº£ vá» ctx.Err();
  note right: chÆ°a chiáº¿m dá»¥ng tÃ i nguyÃªn session
  stop
else (khÃ´ng)
  :má»Ÿ káº¿t ná»‘i endpoint;
  if (káº¿t ná»‘i thÃ nh cÃ´ng?) then (cÃ³)
    :defer session.Close();
    :run(ctx, endpoint, session);
    :Close() luÃ´n cháº¡y trÆ°á»›c khi return;
    if (run() phÃ¡t sinh lá»—i?) then (cÃ³)
      :báº£o toÃ n lá»—i chÃ­nh (primary error);
    else (khÃ´ng)
      :tráº£ lá»—i Ä‘Ã³ng káº¿t ná»‘i náº¿u cÃ³;
    endif
  else (khÃ´ng)
    :tráº£ lá»—i má»Ÿ káº¿t ná»‘i;
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
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
skinparam rectangle {
  BackgroundColor #FFFFFF
  BorderColor #222222
  FontColor #000000
}
skinparam ArrowColor #222222
left to right direction

rectangle "cmd/opsprobe\\ngá»‘c láº¯p ghÃ©p (composition root)\\nin káº¿t quáº£" as cmd
rectangle "internal/config\\ncáº¥u hÃ¬nh má»¥c tiÃªu" as config
rectangle "probe\\nkiá»ƒm tra Check, mÃ´ hÃ¬nh, ranh giá»›i lá»—i" as probe

cmd --> config : náº¡p cáº¥u hÃ¬nh
cmd --> probe : khá»Ÿi táº¡o Service, gá»i Check
note bottom of probe
khÃ´ng import ngÆ°á»£c cmd hoáº·c config
(nguyÃªn táº¯c phá»¥ thuá»™c má»™t chiá»u)
end note
@enduml
""", encoding="utf-8")

    # 20. performance-evidence-path.puml
    p = DIAGRAMS_DIR / "performance-evidence-path.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
skinparam defaultFontName "Source Sans 3"
skinparam defaultFontSize 18
skinparam rectangle {
  BackgroundColor #F5F5F2
  BorderColor #333333
  RoundCorner 8
}
skinparam arrowColor #333333
left to right direction

rectangle "Triá»‡u chá»©ng\\ncháº­m hoáº·c phÃ¬nh bá»™ nhá»›" as symptom
rectangle "CÃ¢u há»i + táº£i thá»­ nghiá»‡m\\nÄ‘áº¡i diá»‡n thá»±c táº¿" as question
rectangle "Kiá»ƒm thá»­ giá»¯ cam káº¿t\\nBenchmark Ä‘o tá»«ng thao tÃ¡c" as measure
rectangle "Dá»¯ liá»‡u profile / trace\\nthu háº¹p pháº¡m vi giáº£ thuyáº¿t" as evidence
rectangle "Má»™t thay Ä‘á»•i nhá»\\nÄ‘Æ°á»£c Ä‘o Ä‘áº¡c láº¡i" as change

symptom --> question
question --> measure
measure --> evidence
evidence --> change
change --> measure : cÃ¹ng cam káº¿t há»£p Ä‘á»“ng

note bottom of evidence
  KhÃ´ng vÃµ Ä‘oÃ¡n tá»« tÃªn API
  hay tá»« cáº£m tÃ­nh mÃ£ nguá»“n.
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
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
skinparam activity {
  BackgroundColor #FFFFFF
  BorderColor #222222
  FontColor #000000
}
skinparam ArrowColor #222222

start
:YÃªu cáº§u cÃ³ context vÃ  deadline;
if (CÃ³ káº¿t ná»‘i ráº£nh (idle) phÃ¹ há»£p?) then (cÃ³)
  :TÃ¡i sá»­ dá»¥ng káº¿t ná»‘i cÅ©;
else (khÃ´ng)
  :PhÃ¢n giáº£i tÃªn miá»n (DNS)\\nÄ‘á»•i host thÃ nh Ä‘á»‹a chá»‰ IP;
  :Khá»Ÿi táº¡o káº¿t ná»‘i TCP (Dial);
  if (URL lÃ  HTTPS?) then (cÃ³)
    :Báº¯t tay TLS\\nvÃ  xÃ¡c minh danh tÃ­nh host;
  endif
endif
:Gá»­i yÃªu cáº§u HTTP;
:Nháº­n headers vÃ  thÃ¢n pháº£n há»“i;
:BÃªn gá»i Ä‘á»c luá»“ng dá»¯ liá»‡u\\nvÃ  Ä‘Ã³ng thÃ¢n pháº£n há»“i (body);
stop
@enduml
""", encoding="utf-8")

    # 22. http-service-lifecycle.puml
    p = DIAGRAMS_DIR / "http-service-lifecycle.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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

rectangle "TIáº¾P NHáº¬N (ACCEPTING)\\nlistener má»Ÿ\\nnháº­n yÃªu cáº§u má»›i" as accepting
rectangle "GIáº¢I Tá»ŽA (DRAINING)\\nlistener Ä‘Ã³ng\\nxá»­ lÃ½ ná»‘t yÃªu cáº§u Ä‘ang cháº¡y" as draining
rectangle "Dá»ªNG Háº²N (STOPPED)\\nÄ‘Ã³ng káº¿t ná»‘i\\ngiáº£i phÃ³ng tÃ i nguyÃªn" as stopped

accepting --> draining : tÃ­n hiá»‡u dá»«ng / deploy
draining --> stopped : yÃªu cáº§u hoÃ n táº¥t\\nhoáº·c háº¿t thá»i háº¡n deadline

note bottom of draining
  Draining tÃ¡ch biá»‡t vá»›i viá»‡c Ä‘Ã³ng listener:
  khÃ´ng nháº­n thÃªm viá»‡c má»›i nhÆ°ng
  hoÃ n táº¥t cÃ´ng viá»‡c Ä‘ang dang dá»Ÿ.
end note
@enduml
""", encoding="utf-8")

    # 23. transaction-boundary.puml
    p = DIAGRAMS_DIR / "transaction-boundary.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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

rectangle "Báº®T Äáº¦U (BEGIN)\\nkhá»Ÿi táº¡o giao dá»‹ch" as begin
rectangle "Cáº¬P NHáº¬T\\nchecks.enabled = false" as update
rectangle "GHI NHáº¬T KÃ\\ncheck_events: disabled" as audit
rectangle "XÃC NHáº¬N (COMMIT)\\ntráº¡ng thÃ¡i má»›i cÃ³ hiá»‡u lá»±c" as committed
rectangle "HOÃ€N NGUYÃŠN (ROLLBACK)\\nbáº£o toÃ n tráº¡ng thÃ¡i cÅ©" as rolled

begin --> update
update --> audit
audit --> committed : má»i cÃ¢u lá»‡nh\\nthÃ nh cÃ´ng
begin ..> rolled : lá»—i á»Ÿ báº¥t ká»³ bÆ°á»›c nÃ o

note bottom of audit
  SÆ¡ Ä‘á»“ khÃ¡i niá»‡m vá» tÃ­nh nguyÃªn tá»­ (Atomicity).
  Má»©c cÃ´ láº­p (Isolation) cá»¥ thá»ƒ do cÆ¡ sá»Ÿ dá»¯ liá»‡u
  vÃ  cáº¥u hÃ¬nh TxOptions quyáº¿t Ä‘á»‹nh.
end note
@enduml
""", encoding="utf-8")

    # 24. incident-command-lifecycle.puml
    p = DIAGRAMS_DIR / "incident-command-lifecycle.puml"
    p.write_text("""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
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

actor "ngÆ°á»i váº­n hÃ nh" as operator
participant "lá»‡nh sá»± cá»‘\\nkiá»ƒm tra + ghi nháº­n" as command
participant "bá»™ Ä‘iá»u phá»‘i runner\\nkhá»Ÿi cháº¡y + chá» + phÃ¢n loáº¡i" as runner
participant "tiáº¿n trÃ¬nh con\\nstdout / stderr / mÃ£ thoÃ¡t" as child

operator -> command : má»¥c tiÃªu + thá»i háº¡n deadline
command -> runner : Ä‘áº·c táº£ Spec + bá»‘i cáº£nh cha
runner -> child : tá»‡p thá»±c thi + Ä‘á»‘i sá»‘
child --> runner : káº¿t quáº£ xuáº¥t + mÃ£ thoÃ¡t
runner --> command : káº¿t quáº£ Result + lá»›p lá»—i
command --> operator : báº£n ghi cháº©n Ä‘oÃ¡n

note over runner
  Context bá»‹ cancel sáº½ ngáº¯t
  tiáº¿n trÃ¬nh con theo máº·c Ä‘á»‹nh.
  ChÃ­nh sÃ¡ch cho cÃ¢y tiáº¿n trÃ¬nh (process tree) lÃ  cÆ¡ cháº¿ riÃªng.
end note
@enduml
""", encoding="utf-8")

    # 25. reconciliation-loop.puml
    p = DIAGRAMS_DIR / "reconciliation-loop.puml"
    p.write_text("""@startuml
left to right direction
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
skinparam defaultFontName "Source Sans 3"
skinparam rectangle {
  BackgroundColor #F7F7F4
  BorderColor #5D5D5D
  FontColor #111111
  RoundCorner 8
}
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
}

rectangle "tráº¡ng thÃ¡i mong muá»‘n (Spec)\\nmÃ£ Ä‘á»‹nh danh gÃ³i, sá»‘ báº£n sao, chÃ­nh sÃ¡ch" as desired
rectangle "bá»™ Ä‘iá»u khiá»ƒn (Controller)\\nquan sÃ¡t -> phÃ¡n Ä‘oÃ¡n -> hÃ nh Ä‘á»™ng" as controller
rectangle "tráº¡ng thÃ¡i thá»±c táº¿ (Status)\\nPod, tiáº¿n trÃ¬nh, Ä‘á»™ sáºµn sÃ ng" as current

desired --> controller : cáº¥u hÃ¬nh khai bÃ¡o (Spec)
current --> controller : dá»¯ liá»‡u quan tráº¯c thá»±c táº¿
controller --> current : tÃ¡c Ä‘á»™ng Ä‘iá»u chá»‰nh

note bottom of controller
  Má»™t vÃ²ng láº·p khÃ´ng cam káº¿t Ä‘Æ°a há»‡ thá»‘ng vá»
  tráº¡ng thÃ¡i cuá»‘i cÃ¹ng ngay tá»©c thÃ¬.
  NÃ³ lÃ  quÃ¡ trÃ¬nh há»™i tá»¥ liÃªn tá»¥c qua thá»i gian.
end note
@enduml
""", encoding="utf-8")

    # 26. delivery-evidence-chain.puml
    p = DIAGRAMS_DIR / "delivery-evidence-chain.puml"
    p.write_text("""@startuml
left to right direction
skinparam shadowing false
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
  FontColor #000000
}
skinparam defaultFontName "Source Sans 3"
skinparam rectangle {
  BackgroundColor #F7F7F4
  BorderColor #5D5D5D
  FontColor #111111
  RoundCorner 8
}
skinparam note {
  BackgroundColor #F5F5F2
  BorderColor #777777
}

rectangle "phiÃªn báº£n nguá»“n\\ncommit Ä‘Ã£ chá»n" as source
rectangle "biÃªn dá»‹ch\\nmÃ£ Ä‘á»‹nh danh gÃ³i (digest)" as build
rectangle "báº±ng chá»©ng\\nkiá»ƒm thá»­ + nguá»“n gá»‘c" as evidence
rectangle "chÃ­nh sÃ¡ch phÃª duyá»‡t\\nquyá»n háº¡n + cá»•ng kiá»ƒm tra" as policy
rectangle "tráº¡ng thÃ¡i mong muá»‘n\\ngÃ³i Ä‘Æ°á»£c triá»ƒn khai" as deploy
rectangle "quan sÃ¡t phÃ¡t hÃ nh\\ntráº¡ng thÃ¡i + tÃ­n hiá»‡u" as observe

source --> build
build --> evidence
evidence --> policy
policy --> deploy
deploy --> observe

note bottom of policy
  Má»—i bÆ°á»›c chá»‰ chá»©ng minh
  cam káº¿t (contract) cá»§a chÃ­nh nÃ³.
end note
@enduml
""", encoding="utf-8")

def render_all():
    pumls = sorted(DIAGRAMS_DIR.glob("*.puml"))
    print(f"Rendering {len(pumls)} diagrams using {PLANTUML_JAR} at 300 DPI...")
    cmd = [
        "java",
        "-DPLANTUML_LIMIT_SIZE=8192",
        "-jar", str(PLANTUML_JAR),
        "-Ddpi=300",
        "-charset", "UTF-8",
    ] + [str(p) for p in pumls]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("PlantUML error:", res.stderr)
        raise RuntimeError("PlantUML rendering failed!")
    print("All diagrams rendered successfully at 300 DPI!")

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
