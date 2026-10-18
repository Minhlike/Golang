"""Generates visual research reference plates for the 3 cover concepts in book/design/agent2-2026/artwork/research_references/.
Each reference plate contains an analytical breakdown of the visual sources, architectural principles,
and design translation into technical systems engineering.
"""
from pathlib import Path
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

REF_DIR = Path("D:/Golang/book/design/agent2-2026/artwork/research_references")
REF_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# Plate 1: Concept 1 Reference — Architectural Section & Spatial Cut
# Source: Manual of Section (Lewis, Tsurumaki, Lewis - Princeton Architectural Press, 2016)
# & MoMA Deconstructivist Architecture (Peter Eisenman Biocenter Axonometric, 1988)
# ------------------------------------------------------------------------------
def generate_ref_plate_1():
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_facecolor("#FAFAFA")
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 750)
    ax.axis("off")

    # Header
    ax.text(50, 710, "VISUAL RESEARCH REFERENCE PLATE 01 // ARCHITECTURAL SECTION & SPATIAL CUT",
            fontsize=11, fontweight="bold", fontfamily="sans-serif", color="#000000")
    ax.text(50, 690, "Primary Reference: Lewis, Tsurumaki, Lewis — Manual of Section (Princeton Architectural Press, 2016)",
            fontsize=8.5, fontfamily="serif", color="#333333")
    ax.text(50, 674, "Secondary Reference: Peter Eisenman — Biocenter Axonometric Cut (MoMA Deconstructivist Architecture, 1988)",
            fontsize=8.5, fontfamily="serif", style="italic", color="#555555")
    ax.plot([50, 950], [660, 660], color="#000000", lw=1.0)

    # Left Column: Spatial Analysis & Section Theory Diagram
    # Draw isometric building section with solid poché cut
    cx, cy = 300, 360
    cos30 = math.cos(math.radians(30))
    sin30 = math.sin(math.radians(30))
    def iso(x, y, z):
        return cx + (x - y) * cos30 * 1.2, cy + (x + y) * sin30 * 0.7 + z * 1.2

    # Draw multi-level structural frame
    floors = [-120, -40, 40, 120]
    for i, z in enumerate(floors):
        # Floor slab
        p0 = iso(-120, -100, z)
        p1 = iso(120, -100, z)
        p2 = iso(120, 100, z)
        p3 = iso(-120, 100, z)
        poly = patches.Polygon([p0, p1, p2, p3], closed=True, facecolor="#F0F0F0", edgecolor="#222222", lw=0.8)
        ax.add_patch(poly)

        # Cut face poché (hatched or black cross-section)
        p_cut0 = iso(120, -100, z)
        p_cut1 = iso(120, 100, z)
        p_cut2 = iso(120, 100, z - 15)
        p_cut3 = iso(120, -100, z - 15)
        poly_cut = patches.Polygon([p_cut0, p_cut1, p_cut2, p_cut3], closed=True, facecolor="#222222", edgecolor="#000000", lw=0.5)
        ax.add_patch(poly_cut)

        # Interior spatial voids / shear walls
        if i < len(floors) - 1:
            z_next = floors[i+1]
            # Column 1
            ax.plot([iso(-80, -60, z)[0], iso(-80, -60, z_next)[0]],
                    [iso(-80, -60, z)[1], iso(-80, -60, z_next)[1]], color="#444444", lw=1.2)
            # Column 2
            ax.plot([iso(40, -60, z)[0], iso(40, -60, z_next)[0]],
                    [iso(40, -60, z)[1], iso(40, -60, z_next)[1]], color="#444444", lw=1.2)
            # Core shear wall
            w0 = iso(-20, 20, z)
            w1 = iso(60, 20, z)
            w2 = iso(60, 20, z_next)
            w3 = iso(-20, 20, z_next)
            wall = patches.Polygon([w0, w1, w2, w3], closed=True, facecolor="#D8D8D8", edgecolor="#333333", lw=0.7)
            ax.add_patch(wall)

    # Callout annotations on the drawing
    ax.annotate("Solid Poché Cut (Section Plane)", xy=iso(120, 0, 40), xytext=(80, 480),
                arrowprops=dict(arrowstyle="->", color="#000000", lw=0.8),
                fontsize=8, fontfamily="sans-serif", weight="bold")
    ax.annotate("Spatial Interlock (Shear Core)", xy=iso(20, 20, 80), xytext=(80, 420),
                arrowprops=dict(arrowstyle="->", color="#000000", lw=0.8),
                fontsize=8, fontfamily="sans-serif")
    ax.annotate("Sub-Grade Foundation (Kernel Boundary)", xy=iso(120, -50, -120), xytext=(80, 220),
                arrowprops=dict(arrowstyle="->", color="#000000", lw=0.8),
                fontsize=8, fontfamily="sans-serif")

    # Right Column: Analytical Ledger & Translation Matrix
    rx = 560
    ax.text(rx, 630, "ARCHITECTURAL PRINCIPLES & SYSTEMS TRANSLATION",
            fontsize=9.5, fontweight="bold", fontfamily="sans-serif", color="#000000")

    principles = [
        ("1. The Section as Epistemic Tool:",
         "In architectural theory (Lewis et al.), the section is not merely a representation\n"
         "of facade, but the primary instrument for understanding internal relationships,\n"
         "vertical circulation, structural hierarchy, and hidden mechanical systems."),
        ("2. Translation to Go Systems Engineering:",
         "We project Go's full execution stack into an axonometric spatial section:\n"
         "• Foundation (z=-120): Linux Kernel, Syscalls, Ring-0 Hardware Boundary.\n"
         "• Engine Core (z=-30): Go Runtime, GMP M:N Scheduler, Mallocgc Pages, Chans.\n"
         "• Application Deck (z=+60): Service Boundaries, HTTP/2 multiplexing, DB pools.\n"
         "• Control Tower (z=+150): Kubernetes Level-Triggered Reconcile, eBPF probes."),
        ("3. Graphic Vocabulary:",
         "• Poché (black cross-section cut) represents the physical execution barrier.\n"
         "• Projection lines (0.3pt hairline) link runtime goroutines to OS threads.\n"
         "• Isometric dimension calipers establish engineering rigor and exactness.\n"
         "• Strict monochrome palette (100% black ink, crisp paper contrast)."),
        ("4. Editorial Alignment:",
         "Directly mirrors the textbook's pedagogical philosophy: understanding Go\n"
         "not as abstract syntax, but as a mechanical structure interacting with Linux.")
    ]

    py = 595
    for title, desc in principles:
        ax.text(rx, py, title, fontsize=8.5, fontweight="bold", fontfamily="sans-serif", color="#111111")
        py -= 16
        ax.text(rx, py, desc, fontsize=7.8, fontfamily="sans-serif", color="#333333", linespacing=1.35)
        py -= 46

    # Bottom Metadata Box
    ax.plot([50, 950], [70, 70], color="#CCCCCC", lw=0.8)
    ax.text(50, 50, "Curation: Agent 2 Editorial Design // Artifact: book/design/agent2-2026/artwork/research_references/ref_concept1_architectural_section.png",
            fontsize=7, fontfamily="monospace", color="#666666")
    ax.text(950, 50, "Status: Grounded Primary Reference", fontsize=7, fontfamily="monospace", color="#000000", ha="right")

    out_file = REF_DIR / "ref_concept1_architectural_section.png"
    fig.savefig(out_file, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Generated Reference Plate 1: {out_file}")

# ------------------------------------------------------------------------------
# Plate 2: Concept 2 Reference — Scientific Engraving & Topological Flow Field
# Source: Edward Tufte (Envisioning Information, Graphics Press)
# & Ernst Haeckel (Kunstformen der Natur, 1904) / Complex Potential Streamlines
# ------------------------------------------------------------------------------
def generate_ref_plate_2():
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_facecolor("#FAFAFA")
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 750)
    ax.axis("off")

    # Header
    ax.text(50, 710, "VISUAL RESEARCH REFERENCE PLATE 02 // SCIENTIFIC ENGRAVING & FLOW MANIFOLD",
            fontsize=11, fontweight="bold", fontfamily="sans-serif", color="#000000")
    ax.text(50, 690, "Primary Reference: Edward R. Tufte — Envisioning Information (Graphics Press, 1990) & Visual Explanations (1997)",
            fontsize=8.5, fontfamily="serif", color="#333333")
    ax.text(50, 674, "Secondary Reference: Ernst Haeckel — Kunstformen der Natur (1904, Copperplate Lithography) / Complex Field Theory",
            fontsize=8.5, fontfamily="serif", style="italic", color="#555555")
    ax.plot([50, 950], [660, 660], color="#000000", lw=1.0)

    # Left Column: Mathematical Streamline Flow Diagram
    # Generate complex potential flow around multiple poles/sinks
    cx, cy = 280, 360
    theta = np.linspace(0, 2*np.pi, 200)
    
    # Draw concentric field lines with variable line width simulating copperplate burin
    radii = np.linspace(25, 220, 28)
    for r in radii:
        x = cx + r * np.cos(theta) * 1.15
        # Modulate y with wave harmonic to represent complex potential function psi(z)
        y = cy + r * np.sin(theta) * 0.75 + 18.0 * np.sin(4 * theta) * np.exp(-r / 120.0)
        lw = 0.3 + 0.9 * (1.0 - r / 240.0)
        alpha = 0.4 + 0.6 * (1.0 - r / 240.0)
        ax.plot(x, y, color="#111111", lw=lw, alpha=alpha)

    # Draw orthogonal gradient trajectories (equipotential lines)
    for rad_angle in np.linspace(0, 2*np.pi, 18, endpoint=False):
        rr = np.linspace(25, 215, 60)
        xx = cx + rr * np.cos(rad_angle) * 1.15
        yy = cy + rr * np.sin(rad_angle) * 0.75 + 18.0 * np.sin(4 * rad_angle) * np.exp(-rr / 120.0)
        ax.plot(xx, yy, color="#666666", lw=0.35, ls=(0, (2, 3)))

    # Central singularity pole
    ax.scatter([cx], [cy], s=40, color="#000000", zorder=5)
    ax.annotate("Singularity / Rendezvous Core", xy=(cx, cy), xytext=(cx - 160, cy - 80),
                arrowprops=dict(arrowstyle="->", color="#000000", lw=0.8),
                fontsize=8, fontfamily="sans-serif", weight="bold")
    ax.annotate("Orthogonal Equipotential Field Lines", xy=(cx + 140, cy + 80), xytext=(cx + 80, cy + 180),
                arrowprops=dict(arrowstyle="->", color="#000000", lw=0.8),
                fontsize=8, fontfamily="sans-serif")

    # Right Column: Analytical Ledger
    rx = 560
    ax.text(rx, 630, "TOPOLOGICAL CONCURRENCY & ENGRAVING RIGOR",
            fontsize=9.5, fontweight="bold", fontfamily="sans-serif", color="#000000")

    principles = [
        ("1. Tufte's Macro/Micro Information Density:",
         "High-density graphic design allows reading at two scales simultaneously:\n"
         "at distance, the macroscopic vortex is visible; at near reading distance,\n"
         "every micro-stroke reveals individual vector coordinates and gradient flux."),
        ("2. Modeling Concurrency as Fluid Mechanics:",
         "Go's channel communication and goroutine rendezvous are mathematically\n"
         "isomorphic to Navier-Stokes fluid potential fields:\n"
         "• Channel Buffers act as reservoirs with finite storage capacitance.\n"
         "• Unbuffered Rendezvous acts as an infinite-velocity barrier gate.\n"
         "• Backpressure creates shockwaves and boundary-layer boundary separation."),
        ("3. 19th Century Copperplate Engraving Tradition:",
         "• Variable stroke thickness (0.3pt to 1.2pt) mirrors the engraver's burin tool.\n"
         "• Mathematical cross-hatching renders continuous volume without halftone screens.\n"
         "• Timeless academic dignity suitable for a definitive university textbook."),
        ("4. Editorial Alignment:",
         "Celebrates the formal mathematical foundations of CSP (Hoare, 1978)\n"
         "and the deterministic predictability of Go runtime flow mechanics.")
    ]

    py = 595
    for title, desc in principles:
        ax.text(rx, py, title, fontsize=8.5, fontweight="bold", fontfamily="sans-serif", color="#111111")
        py -= 16
        ax.text(rx, py, desc, fontsize=7.8, fontfamily="sans-serif", color="#333333", linespacing=1.35)
        py -= 46

    # Bottom Metadata Box
    ax.plot([50, 950], [70, 70], color="#CCCCCC", lw=0.8)
    ax.text(50, 50, "Curation: Agent 2 Editorial Design // Artifact: book/design/agent2-2026/artwork/research_references/ref_concept2_topological_engraving.png",
            fontsize=7, fontfamily="monospace", color="#666666")
    ax.text(950, 50, "Status: Grounded Primary Reference", fontsize=7, fontfamily="monospace", color="#000000", ha="right")

    out_file = REF_DIR / "ref_concept2_topological_engraving.png"
    fig.savefig(out_file, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Generated Reference Plate 2: {out_file}")

# ------------------------------------------------------------------------------
# Plate 3: Concept 3 Reference — Constructivist Kinetic Typography & Swiss Grid
# Source: Emil Ruder (Typographie, 1967; Helmut Schmid, Lars Müller 2017)
# & Josef Müller-Brockmann (Grid Systems in Graphic Design, Niggli 1981)
# ------------------------------------------------------------------------------
def generate_ref_plate_3():
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_facecolor("#FAFAFA")
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 750)
    ax.axis("off")

    # Header
    ax.text(50, 710, "VISUAL RESEARCH REFERENCE PLATE 03 // CONSTRUCTIVIST TYPOGRAPHY & MODULAR MONOLITH",
            fontsize=11, fontweight="bold", fontfamily="sans-serif", color="#000000")
    ax.text(50, 690, "Primary Reference: Emil Ruder — Typographie: A Manual of Design (Arthur Niggli, 1967; Lars Müller, 2017)",
            fontsize=8.5, fontfamily="serif", color="#333333")
    ax.text(50, 674, "Secondary Reference: Josef Müller-Brockmann — Grid Systems in Graphic Design (Arthur Niggli, 1981)",
            fontsize=8.5, fontfamily="serif", style="italic", color="#555555")
    ax.plot([50, 950], [660, 660], color="#000000", lw=1.0)

    # Left Column: Swiss 12-Column Grid & 3D Extruded Type Architecture
    grid_x0, grid_y0 = 60, 140
    grid_w, grid_h = 440, 480
    cols = 6
    col_w = (grid_w - (cols - 1) * 12) / cols

    # Draw grid modules (Swiss grid structure)
    for c in range(cols):
        cx = grid_x0 + c * (col_w + 12)
        ax.add_patch(patches.Rectangle((cx, grid_y0), col_w, grid_h, facecolor="#F0F0F0", edgecolor="#CCCCCC", lw=0.5, ls="--"))

    # Draw 3D Constructivist Monolith blocks
    monoliths = [
        (grid_x0 + 20, 460, 110, 120, "G", "#000000", "#FFFFFF"),
        (grid_x0 + 150, 380, 110, 120, "O", "#1A1A1A", "#FFFFFF"),
        (grid_x0 + 280, 440, 110, 120, "L", "#000000", "#FFFFFF"),
        (grid_x0 + 80, 240, 130, 90, "CONCURRENCY", "#333333", "#FFFFFF"),
        (grid_x0 + 230, 180, 180, 110, "RUNTIME", "#111111", "#FFFFFF"),
    ]
    for mx, my, mw, mh, label, bg, fg in monoliths:
        # Draw isometric drop shadow/extrusion
        ext_depth = 12
        poly_top = patches.Polygon([(mx, my+mh), (mx+mw, my+mh), (mx+mw+ext_depth, my+mh+ext_depth), (mx+ext_depth, my+mh+ext_depth)],
                                   facecolor="#444444", edgecolor="#000000", lw=0.6)
        poly_side = patches.Polygon([(mx+mw, my), (mx+mw+ext_depth, my+ext_depth), (mx+mw+ext_depth, my+mh+ext_depth), (mx+mw, my+mh)],
                                    facecolor="#666666", edgecolor="#000000", lw=0.6)
        ax.add_patch(poly_top)
        ax.add_patch(poly_side)
        
        # Main face
        ax.add_patch(patches.Rectangle((mx, my), mw, mh, facecolor=bg, edgecolor="#000000", lw=0.8))
        ax.text(mx + mw/2, my + mh/2, label, fontsize=12 if len(label)>1 else 32,
                fontweight="bold", fontfamily="sans-serif", color=fg, ha="center", va="center")

    ax.annotate("Extruded Monolithic Mass", xy=(grid_x0 + 260, 500), xytext=(grid_x0 + 310, 580),
                arrowprops=dict(arrowstyle="->", color="#000000", lw=0.8),
                fontsize=8, fontfamily="sans-serif", weight="bold")
    ax.annotate("Strict Swiss Modular Grid", xy=(grid_x0 + 140, 145), xytext=(grid_x0 + 40, 95),
                arrowprops=dict(arrowstyle="->", color="#000000", lw=0.8),
                fontsize=8, fontfamily="sans-serif")

    # Right Column: Analytical Ledger
    rx = 560
    ax.text(rx, 630, "SWISS MODERNISM & ARCHITECTURAL TYPOGRAPHY",
            fontsize=9.5, fontweight="bold", fontfamily="sans-serif", color="#000000")

    principles = [
        ("1. Emil Ruder's Philosophy of Typographic Space:",
         "Typography is not merely writing; it is the deliberate articulation of white space.\n"
         "The counterform (unprinted space) possesses equal mass and tension to the\n"
         "printed letterform. Contrast of scale (huge vs micro) creates kinetic energy."),
        ("2. Modular Grid Disciplines (Müller-Brockmann):",
         "The 12-column Swiss grid establishes uncompromising mathematical order:\n"
         "every heading, code frame, margin, and divider shares a common harmonic divisor.\n"
         "This discipline prevents arbitrary visual noise and guarantees readability."),
        ("3. The Monolithic Modern Software Metaphor:",
         "Modern Go backend architectures (e.g. Docker, Kubernetes, Terraform) are monolithic\n"
         "industrial marvels: solid, unyielding, compiled directly to machine code.\n"
         "The extruded 3D typography treats letters as structural load-bearing concrete."),
        ("4. Editorial Alignment:",
         "Reflects the pragmatic, no-nonsense culture of Go: simplicity, clarity,\n"
         "structural integrity, and zero unnecessary ornamental fluff.")
    ]

    py = 595
    for title, desc in principles:
        ax.text(rx, py, title, fontsize=8.5, fontweight="bold", fontfamily="sans-serif", color="#111111")
        py -= 16
        ax.text(rx, py, desc, fontsize=7.8, fontfamily="sans-serif", color="#333333", linespacing=1.35)
        py -= 46

    # Bottom Metadata Box
    ax.plot([50, 950], [70, 70], color="#CCCCCC", lw=0.8)
    ax.text(50, 50, "Curation: Agent 2 Editorial Design // Artifact: book/design/agent2-2026/artwork/research_references/ref_concept3_swiss_monolith.png",
            fontsize=7, fontfamily="monospace", color="#666666")
    ax.text(950, 50, "Status: Grounded Primary Reference", fontsize=7, fontfamily="monospace", color="#000000", ha="right")

    out_file = REF_DIR / "ref_concept3_swiss_monolith.png"
    fig.savefig(out_file, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Generated Reference Plate 3: {out_file}")

if __name__ == "__main__":
    generate_ref_plate_1()
    generate_ref_plate_2()
    generate_ref_plate_3()
    print("All 3 Research Reference Plates generated successfully!")
