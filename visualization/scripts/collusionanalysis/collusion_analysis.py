#!/usr/bin/env python3
"""
Collusion Analysis Visualization for TruthMarketTwin Project

This module generates visualizations for analyzing seller collusion behavior
in the marketplace experiments.

Data sources:
- data/case_analysis/deception_rate_by_collusion.csv
- data/case_analysis/type_distribution_by_condition.csv
- data/case_analysis/type_distribution_by_round.csv
- data/case_analysis/type_distribution_by_prompt_type.csv
- data/case_analysis/posts_labeled.jsonl

Collusion types (annotated by Claude Sonnet 4.6):
1. Direct Collusion Proposal - Explicit invitation to coordinate deception
2. Deception Strategy Broadcast - Sharing personal deceptive plans
3. Collusion Coordination & Reinforcement - Building on others' deceptive strategies
4. Social Normalization of Deception - Framing deception as normal market behavior
5. Neutral / Market Information Sharing - Non-deceptive information exchange
6. Anti-Collusion / Pro-Honesty - Explicit opposition to deception
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from fig_utils import (
    COLORS,
    setup_style,
    label_panel,
    mannwhitney_p,
    sig_marker_display,
    add_significance_bracket,
    add_sig_footnote,
    save_figure,
)

setup_style()

# ── Collusion Type Definitions ───────────────────────────────────────────────

COLLUSION_TYPES = {
    1: {
        "name": "Direct Collusion Proposal",
        "abbrev": "Type 1",
        "description": "Explicit invitation to coordinate deception",
        "color": "#9B2226",  # dark red - most severe
        "collusive": True,
    },
    2: {
        "name": "Deception Strategy Broadcast",
        "abbrev": "Type 2",
        "description": "Sharing personal deceptive plans",
        "color": "#AE2012",  # bright red
        "collusive": True,
    },
    3: {
        "name": "Collusion Coordination",
        "abbrev": "Type 3",
        "description": "Building on others' deceptive strategies",
        "color": "#D4866A",  # terracotta
        "collusive": True,
    },
    4: {
        "name": "Social Normalization",
        "abbrev": "Type 4",
        "description": "Framing deception as normal behavior",
        "color": "#E8A87C",  # light orange
        "collusive": True,
    },
    5: {
        "name": "Neutral Information",
        "abbrev": "Type 5",
        "description": "Non-deceptive market information",
        "color": "#6B6B6B",  # gray - neutral
        "collusive": False,
    },
    6: {
        "name": "Anti-Collusion",
        "abbrev": "Type 6",
        "description": "Opposition to deception",
        "color": "#2D6A4F",  # green - pro-honesty
        "collusive": False,
    },
}

# ── Experiment Conditions ─────────────────────────────────────────────────────

CONDITIONS = {
    "r_wsc_F_policy_making": "Rep (Policy)",
    "r_wsc_F_pressure_quickprofits": "Rep (Pressure)",
    "r_wsc_F_psychological-based-attack": "Rep (Psych)",
    "r_wsc_R_policy_making": "Rep+Comm (Policy)",
    "r_wsc_R_pressure_quickprofits": "Rep+Comm (Pressure)",
    "r_wsc_R_psychological-based-attack": "Rep+Comm (Psych)",
    "rw_wsc_F_policy_making": "Warrant (Policy)",
    "rw_wsc_F_pressure_quickprofits": "Warrant (Pressure)",
    "rw_wsc_F_psychological-based-attack": "Warrant (Psych)",
    "rw_wsc_R_policy_making": "Warrant+Comm (Policy)",
    "rw_wsc_R_pressure_quickprofits": "Warrant+Comm (Pressure)",
    "rw_wsc_R_psychological-based-attack": "Warrant+Comm (Psych)",
}

# ── Data Loading Functions ────────────────────────────────────────────────────

def load_deception_by_collusion(data_dir: str) -> pd.DataFrame:
    """Load deception rate by collusion status data."""
    path = Path(data_dir) / "case_analysis" / "deception_rate_by_collusion.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_type_distribution_by_condition(data_dir: str) -> pd.DataFrame:
    """Load type distribution by experiment condition."""
    path = Path(data_dir) / "case_analysis" / "type_distribution_by_condition.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_type_distribution_by_round(data_dir: str) -> pd.DataFrame:
    """Load type distribution by round."""
    path = Path(data_dir) / "case_analysis" / "type_distribution_by_round.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_type_distribution_by_prompt(data_dir: str) -> pd.DataFrame:
    """Load type distribution by prompt type."""
    path = Path(data_dir) / "case_analysis" / "type_distribution_by_prompt_type.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_qualitative_examples(data_dir: str) -> List[Dict]:
    """Load qualitative examples for each type."""
    path = Path(data_dir) / "case_analysis" / "qualitative_examples.json"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_type_distribution_real_vs_fake(data_dir: str) -> pd.DataFrame:
    """Load type distribution for real vs fake communication channels."""
    path = Path(data_dir) / "case_analysis" / "type_distribution_real_vs_fake.csv"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


def _load_labeled_posts(data_dir: str) -> List[Dict]:
    """Load all labeled posts from posts_labeled.jsonl."""
    path = Path(data_dir) / "case_analysis" / "posts_labeled.jsonl"
    if not path.exists():
        print(f"  WARNING: {path} not found")
        return []
    posts = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    posts.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return posts


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1: Deception Rate by Collusion Status
# ─────────────────────────────────────────────────────────────────────────────

def fig1_deception_by_collusion(data_dir: str, output_dir: Path) -> None:
    """Create bar chart showing deception rates with/without collusion."""
    df = load_deception_by_collusion(data_dir)
    if df.empty:
        print("  WARNING: Empty dataframe for fig1")
        return

    fig, ax = plt.subplots(figsize=(5, 4))

    x_pos = [0, 1]
    bars = ax.bar(x_pos, df["deception_rate"].values,
                  color=[COLORS["neutral"], "#AE2012"],
                  width=0.5, edgecolor="white", linewidth=0.5)

    # Add value labels
    for bar, rate, n in zip(bars, df["deception_rate"].values, df["n_posts"].values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f"{rate*100:.1f}%\n(n={n})",
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(["No Collusion Detected\n(4729 posts)",
                        "Collusion Detected\n(683 posts)"],
                       fontsize=10)
    ax.set_ylabel("Deception Rate", fontsize=11)
    ax.set_title("Seller Collusion Dramatically Increases Deception\n"
                 "(4.9% → 41.3%, 8.4x increase)",
                 fontsize=11, fontweight='bold', pad=10)
    ax.set_ylim(0, 0.55)
    ax.axhline(y=0.05, color='gray', linestyle='--', alpha=0.5, label='5% threshold')

    # Add annotation
    increase = (df["deception_rate"].values[1] / df["deception_rate"].values[0])
    ax.annotate(f"{increase:.1f}x increase",
                xy=(0.5, 0.25), xytext=(0.5, 0.40),
                fontsize=12, fontweight='bold', color='#AE2012',
                ha='center', va='center',
                arrowprops=dict(arrowstyle='->', color='#AE2012', lw=2))

    add_sig_footnote(fig, extra="Collusion detected via Claude Sonnet 4.6 annotation")
    save_figure(fig, output_dir / "fig1_deception_by_collusion.png")
    print("  [Fig1] Deception by collusion status saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1-1: Sankey Diagrams by Round
# ─────────────────────────────────────────────────────────────────────────────

def _compute_agent_transitions(df: pd.DataFrame,
                                rnd1: int, rnd2: int) -> Tuple[int, int, int, int]:
    """
    Track agents across two rounds.  For each unique (experiment_id, run_id, agent_name):
      - R1 deceptive: any deceptive_listing in rnd1
      - R2 collusive: any post with primary_type in 1-4 in rnd2
    Only agents appearing in BOTH rounds are counted.
    Returns (dec_coll, dec_nocoll, nodec_coll, nodec_nocoll).
    """
    dc = dn = nc_c = nc_n = 0
    for _, grp in df.groupby(["experiment_id", "run_id", "agent_name"]):
        r1 = grp[grp["round"] == rnd1]
        r2 = grp[grp["round"] == rnd2]
        if len(r1) == 0 or len(r2) == 0:
            continue
        was_dec = bool(r1["behavior_deception"].any())
        is_coll = bool(r2["post_collusion"].any())
        if   was_dec and     is_coll: dc   += 1
        elif was_dec and not is_coll: dn   += 1
        elif not was_dec and is_coll: nc_c += 1
        else:                         nc_n += 1
    return dc, dn, nc_c, nc_n


def _draw_sankey_ax(ax, cc: int, cn: int, nc: int, nn: int,
                    x_offset: float = 0.0, x_scale: float = 1.0,
                    sublabel: str = "") -> None:
    """
    Draw a simple mini Sankey diagram on the given axis.
    
    Parameters:
    - cc: Collusion post + Deception behavior
    - cn: Collusion post + No deception
    - nc: No collusion post + Deception behavior  
    - nn: No collusion post + No deception
    - x_offset: Horizontal offset
    - x_scale: Horizontal scale
    - sublabel: Sublabel for the plot
    """
    total = cc + cn + nc + nn
    if total == 0:
        ax.text(0.5, 0.5, "No Data", ha='center', va='center', fontsize=8)
        return
    
    # Calculate proportions
    p_cc = cc / total
    p_cn = cn / total
    p_nc = nc / total
    p_nn = nn / total
    
    # Node positions (normalized to 0-1, then scaled)
    left = 0.15 * x_scale + x_offset
    right = 0.85 * x_scale + x_offset
    node_width = 0.12 * x_scale
    
    # Colors
    C_COLL = "#AE2012"      # Collusion - red
    C_NOCOLL = "#6B6B6B"   # No Collusion - gray
    C_DEC = "#9B2226"      # Deception - dark red
    C_NODEC = "#52B788"    # No Deception - green
    
    # Left nodes (Post Collusion Status)
    coll_height = p_cc + p_cn
    nocoll_height = p_nc + p_nn
    
    # Draw left nodes
    if coll_height > 0:
        ax.add_patch(plt.Rectangle((left, 1 - coll_height), node_width, coll_height,
                                    facecolor=C_COLL, edgecolor='white', linewidth=0.5))
        if coll_height > 0.1:
            ax.text(left + node_width/2, 1 - coll_height/2, f"{coll_height:.0%}", 
                   ha='center', va='center', fontsize=6, color='white', fontweight='bold')
    
    if nocoll_height > 0:
        ax.add_patch(plt.Rectangle((left, 0), node_width, nocoll_height,
                                    facecolor=C_NOCOLL, edgecolor='white', linewidth=0.5))
        if nocoll_height > 0.1:
            ax.text(left + node_width/2, nocoll_height/2, f"{nocoll_height:.0%}",
                   ha='center', va='center', fontsize=6, color='white', fontweight='bold')
    
    # Right nodes (Behavior)
    dec_height = p_cc + p_nc
    nodec_height = p_cn + p_nn
    
    if dec_height > 0:
        ax.add_patch(plt.Rectangle((right, 1 - dec_height), node_width, dec_height,
                                    facecolor=C_DEC, edgecolor='white', linewidth=0.5))
        if dec_height > 0.1:
            ax.text(right + node_width/2, 1 - dec_height/2, f"{dec_height:.0%}",
                   ha='center', va='center', fontsize=6, color='white', fontweight='bold')
    
    if nodec_height > 0:
        ax.add_patch(plt.Rectangle((right, 0), node_width, nodec_height,
                                    facecolor=C_NODEC, edgecolor='white', linewidth=0.5))
        if nodec_height > 0.1:
            ax.text(right + node_width/2, nodec_height/2, f"{nodec_height:.0%}",
                   ha='center', va='center', fontsize=6, color='white', fontweight='bold')
    
    # Draw flow ribbons between left and right nodes using cubic Bezier curves
    # Flow colors: Coordinated (cc) = dark red, Verbal (cn) = pink, Hidden (nc) = darker red, Honest (nn) = green
    R_CC = "#AE2012"   # Coll→Dec (Coordinated Deception)
    R_CN = "#E07A5F"   # Coll→NoDec (Verbal Collusion) 
    R_NC = "#9B2226"   # NoColl→Dec (Hidden Deception)
    R_NN = "#52B788"   # NoColl→NoDec (Honest)
    
    # Helper to draw a ribbon with cubic Bezier curves
    def ribbon(xleft, xright, ly0, ly1, ry0, ry1, color, alpha):
        """Draw a ribbon/flow using cubic Bezier curves."""
        if (ly1 - ly0) < 4e-4 or (ry1 - ry0) < 4e-4:
            return
        mx = (xleft + xright) / 2
        verts = [
            (xleft, ly1), (mx, ly1), (mx, ry1), (xright, ry1),
            (xright, ry0), (mx, ry0), (mx, ly0), (xleft, ly0),
            (xleft, ly1),
        ]
        codes = [MPath.MOVETO,
                 MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.LINETO,
                 MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes),
                               fc=color, ec='none', alpha=alpha, zorder=2))
    
    # Calculate flow boundaries for proper Sankey layout
    # Left node: Coll occupies [1-coll_height, 1], NoColl occupies [0, 1-coll_height]
    # Right node: Dec occupies [1-dec_height, 1], NoDec occupies [0, 1-dec_height]
    
    # Calculate proportional heights within each node
    # For left Coll node: cc portion and cn portion
    coll_total = cc + cn
    nocoll_total = nc + nn
    
    # Left Coll node: occupies [1-coll_height, 1]
    # Split between cc (top) and cn (bottom)
    if coll_total > 0:
        cc_top = 1.0
        cc_bottom = 1.0 - (cn / coll_total) * coll_height if cn > 0 else 1.0
        cn_bottom = 1.0 - coll_height
        cn_top = cn_bottom + (cn / coll_total) * coll_height if cn > 0 else 1.0 - coll_height
    else:
        cc_top = cc_bottom = 1.0
        cn_top = cn_bottom = 1.0 - coll_height
    
    # Left NoColl node: occupies [0, 1-coll_height]
    # Split between nc (top) and nn (bottom)
    if nocoll_total > 0:
        nc_top = 1.0 - coll_height
        nc_bottom = 1.0 - coll_height - (nc / nocoll_total) * nocoll_height
        nn_bottom = 0.0
        nn_top = (nn / nocoll_total) * nocoll_height
    else:
        nc_top = nc_bottom = 1.0 - coll_height
        nn_top = nn_bottom = 0.0
    
    # Right Dec node: occupies [1-dec_height, 1]
    # Split between cc (top) and nc (bottom)
    dec_total = cc + nc
    nodec_total = cn + nn
    
    if dec_total > 0:
        dec_cc_top = 1.0
        dec_cc_bottom = 1.0 - (nc / dec_total) * dec_height if nc > 0 else 1.0
        dec_nc_bottom = 1.0 - dec_height
        dec_nc_top = dec_nc_bottom + (nc / dec_total) * dec_height if nc > 0 else 1.0 - dec_height
    else:
        dec_cc_top = dec_cc_bottom = 1.0
        dec_nc_top = dec_nc_bottom = 1.0 - dec_height
    
    # Right NoDec node: occupies [0, 1-dec_height]
    # Split between cn (top) and nn (bottom)
    if nodec_total > 0:
        nodec_cn_top = 1.0 - dec_height
        nodec_cn_bottom = 1.0 - dec_height - (cn / nodec_total) * nodec_height
        nodec_nn_bottom = 0.0
        nodec_nn_top = (nn / nodec_total) * nodec_height
    else:
        nodec_cn_top = nodec_cn_bottom = 1.0 - dec_height
        nodec_nn_top = nodec_nn_bottom = 0.0
    
    # Draw flows
    # cc: Left Coll (top) → Right Dec (top)
    if cc > 0:
        ribbon(left + node_width, right,
               cc_bottom, cc_top,
               dec_cc_bottom, dec_cc_top,
               R_CC, 0.65)
    
    # cn: Left Coll (bottom) → Right NoDec (top)
    if cn > 0:
        ribbon(left + node_width, right,
               cn_bottom, cn_top,
               nodec_cn_bottom, nodec_cn_top,
               R_CN, 0.60)
    
    # nc: Left NoColl (top) → Right Dec (bottom)
    if nc > 0:
        ribbon(left + node_width, right,
               nc_bottom, nc_top,
               dec_nc_bottom, dec_nc_top,
               R_NC, 0.60)
    
    # nn: Left NoColl (bottom) → Right NoDec (bottom)
    if nn > 0:
        ribbon(left + node_width, right,
               nn_bottom, nn_top,
               nodec_nn_bottom, nodec_nn_top,
               R_NN, 0.55)
    
    # Node labels
    ax.text(left - 0.02, 0.5, "Coll" if coll_height > 0.3 else "", 
           ha='right', va='center', fontsize=5, fontweight='bold', color=C_COLL)
    ax.text(left - 0.02, 0.5, "NoColl" if nocoll_height > 0.3 else "", 
           ha='right', va='center', fontsize=5, fontweight='bold', color=C_NOCOLL)
    ax.text(right + node_width + 0.02, 0.5, "Dec" if dec_height > 0.3 else "",
           ha='left', va='center', fontsize=5, fontweight='bold', color=C_DEC)
    ax.text(right + node_width + 0.02, 0.5, "NoDec" if nodec_height > 0.3 else "",
           ha='left', va='center', fontsize=5, fontweight='bold', color=C_NODEC)
    
    # Sublabel
    if sublabel:
        ax.text(0.5, -0.05, sublabel, ha='center', va='top', fontsize=5, style='italic')


def _draw_threestage_sankey_panel(ax,
                                   r1_cc: int, r1_cn: int, r1_nc: int, r1_nn: int,
                                   tr_dc: int, tr_dn: int, tr_nc_c: int, tr_nc_n: int,
                                   r10_cc: int, r10_cn: int, r10_nc: int, r10_nn: int,
                                   rnd1: int, rnd2: int) -> None:
    """
    3-stage Sankey on one axes — 4 node columns:
      Stage A  Col1→Col2 : R1 Post Collusion  → R1 Deception Behavior
      Stage B  Col2→Col3 : R1 Deception       → R10 Post Collusion  (agent tracking)
      Stage C  Col3→Col4 : R10 Post Collusion → R10 Deception Behavior

    Column heights are self-consistent: each column sums to 1, and the
    node-split proportions propagate correctly from stage to stage.
    """
    # ── Semantic colors ───────────────────────────────────────────────────
    C_NOCOLL = "#6E8CAB"    # steel-blue-gray  – No Collusion post
    C_COLL   = "#C0392B"    # vivid red        – Collusion post
    C_NODEC  = "#27AE60"    # forest green     – No Deception behavior
    C_DEC    = "#7B241C"    # deep crimson     – Deception behavior

    # Ribbon fills (semi-transparent)
    R_NN = "#A4BCC9"   # NoColl→NoDec : muted blue-gray
    R_ND = "#E8A04E"   # NoColl→Dec   : amber (the "unexpected" flow)
    R_CN = "#EDAB96"   # Coll→NoDec   : salmon
    R_CD = "#C0392B"   # Coll→Dec     : vivid red

    RB_NN = "#7DCEA0"  # NoDec→NoColl : light green (maintained honesty)
    RB_NC = "#EDAB96"  # NoDec→Coll   : salmon (new colluder)
    RB_DN = "#A4BCC9"  # Dec→NoColl   : muted blue (de-escalation)
    RB_DC = "#C0783A"  # Dec→Coll     : burnt orange (escalation)

    # ── Node column x-positions ───────────────────────────────────────────
    COLS = [
        (0.04, 0.13),  # Col1: R1 Post Collusion
        (0.37, 0.46),  # Col2: R1 Behavior
        (0.64, 0.73),  # Col3: R10 Post Collusion
        (0.97, 1.06),  # Col4: R10 Behavior
    ]
    GAP = 0.010  # vertical gap between stacked nodes

    x1l, x1r = COLS[0]
    x2l, x2r = COLS[1]
    x3l, x3r = COLS[2]
    x4l, x4r = COLS[3]

    # ── Stage A: heights from R1 post data ───────────────────────────────
    r1_total = r1_cc + r1_cn + r1_nc + r1_nn
    if r1_total == 0:
        ax.axis('off')
        return

    f_cc = r1_cc / r1_total;  f_cn = r1_cn / r1_total
    f_nc = r1_nc / r1_total;  f_nn = r1_nn / r1_total

    h1_nocoll = f_nc + f_nn    # Col1 bottom node height
    h1_coll   = f_cc + f_cn    # Col1 top node height
    h2_nodec  = f_nn + f_cn    # Col2 bottom node height
    h2_dec    = f_cc + f_nc    # Col2 top node height

    # ── Stage B: agent transitions, scaled to match Col2 heights ─────────
    tr_dec_tot   = max(tr_dc + tr_dn,   1)
    tr_nodec_tot = max(tr_nc_c + tr_nc_n, 1)

    b_dec_coll   = h2_dec   * (tr_dc   / tr_dec_tot)
    b_dec_nocoll = h2_dec   * (tr_dn   / tr_dec_tot)
    b_nodec_coll   = h2_nodec * (tr_nc_c / tr_nodec_tot)
    b_nodec_nocoll = h2_nodec * (tr_nc_n / tr_nodec_tot)

    h3_coll   = b_dec_coll   + b_nodec_coll
    h3_nocoll = b_dec_nocoll + b_nodec_nocoll

    # ── Stage C: deception rates from R10 post data ───────────────────────
    r10c_tot  = max(r10_cc + r10_cn, 1)
    r10nc_tot = max(r10_nc + r10_nn, 1)

    c_coll_dec     = h3_coll   * (r10_cc / r10c_tot)
    c_coll_nodec   = h3_coll   * (r10_cn / r10c_tot)
    c_nocoll_dec   = h3_nocoll * (r10_nc / r10nc_tot)
    c_nocoll_nodec = h3_nocoll * (r10_nn / r10nc_tot)

    h4_nodec = c_coll_nodec + c_nocoll_nodec
    h4_dec   = c_coll_dec   + c_nocoll_dec

    # ── Ribbon helper (cubic Bezier) ──────────────────────────────────────
    def ribbon(xleft, xright, ly0, ly1, ry0, ry1, color, alpha):
        if (ly1 - ly0) < 4e-4 or (ry1 - ry0) < 4e-4:
            return
        mx = (xleft + xright) / 2
        verts = [
            (xleft, ly1), (mx, ly1), (mx, ry1), (xright, ry1),
            (xright, ry0), (mx, ry0), (mx, ly0), (xleft, ly0),
            (xleft, ly1),
        ]
        codes = [MPath.MOVETO,
                 MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.LINETO,
                 MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes),
                               fc=color, ec='none', alpha=alpha, zorder=2))
        # thin center-line highlight for depth
        cy_l = (ly0 + ly1) / 2;  cy_r = (ry0 + ry1) / 2
        hl = min((ly1-ly0), (ry1-ry0)) * 0.18
        verts_hl = [
            (xleft, cy_l+hl), (mx, cy_l+hl), (mx, cy_r+hl), (xright, cy_r+hl),
            (xright, cy_r-hl), (mx, cy_r-hl), (mx, cy_l-hl), (xleft, cy_l-hl),
            (xleft, cy_l+hl),
        ]
        ax.add_patch(PathPatch(MPath(verts_hl, codes),
                               fc='white', ec='none', alpha=0.15, zorder=3))

    # ── Node helper (rounded rect + labels) ──────────────────────────────
    def node(xl, xr, yb_raw, yt_raw, color, pct_val,
             outer_lbl, side, count=None):
        h = yt_raw - yb_raw
        if h < 5e-5:
            return
        yb = yb_raw + GAP * 0.4
        yt = yt_raw - GAP * 0.4
        if yt - yb < 1e-4:
            return
        # shadow
        ax.add_patch(mpatches.FancyBboxPatch(
            (xl + 0.005, yb - 0.006), xr - xl, yt - yb,
            boxstyle="round,pad=0.007",
            fc='#333333', ec='none', alpha=0.13, zorder=3))
        # body
        ax.add_patch(mpatches.FancyBboxPatch(
            (xl, yb), xr - xl, yt - yb,
            boxstyle="round,pad=0.007",
            fc=color, ec='white', lw=1.4, zorder=4))
        # percentage text inside
        cy = (yb + yt) / 2
        if h > 0.10:
            ax.text((xl+xr)/2, cy, f"{pct_val*100:.0f}%",
                    ha='center', va='center', fontsize=8,
                    color='white', fontweight='bold', zorder=5)
        elif h > 0.050:
            ax.text((xl+xr)/2, cy, f"{pct_val*100:.0f}%",
                    ha='center', va='center', fontsize=6.5,
                    color='white', fontweight='bold', zorder=5)
        # outer label
        if outer_lbl:
            pad = 0.020
            lbl_str = outer_lbl if count is None else f"{outer_lbl}\nn={count}"
            fs_lbl = 6.5
            if side == 'left':
                ax.text(xl - pad, cy, lbl_str,
                        ha='right', va='center', fontsize=fs_lbl,
                        color=color, fontweight='bold', zorder=5,
                        linespacing=1.2)
            else:
                ax.text(xr + pad, cy, lbl_str,
                        ha='left', va='center', fontsize=fs_lbl,
                        color=color, fontweight='bold', zorder=5,
                        linespacing=1.2)

    # ── Draw nodes ────────────────────────────────────────────────────────
    node(x1l, x1r, 0,        h1_nocoll, C_NOCOLL, h1_nocoll,
         "No Coll", 'left', count=r1_nc+r1_nn)
    node(x1l, x1r, h1_nocoll, 1.0,      C_COLL,   h1_coll,
         "Coll",    'left', count=r1_cc+r1_cn)

    node(x2l, x2r, 0,        h2_nodec,  C_NODEC, h2_nodec,
         "No Dec",  'right', count=r1_nn+r1_cn)
    node(x2l, x2r, h2_nodec, 1.0,       C_DEC,   h2_dec,
         "Dec",     'right', count=r1_cc+r1_nc)

    node(x3l, x3r, 0,        h3_nocoll, C_NOCOLL, h3_nocoll,
         "No Coll", 'left', count=tr_dn+tr_nc_n)
    node(x3l, x3r, h3_nocoll, 1.0,      C_COLL,   h3_coll,
         "Coll",    'left', count=tr_dc+tr_nc_c)

    node(x4l, x4r, 0,        h4_nodec,  C_NODEC, h4_nodec,
         "No Dec",  'right', count=r10_nn+r10_cn)
    node(x4l, x4r, h4_nodec, 1.0,       C_DEC,   h4_dec,
         "Dec",     'right', count=r10_cc+r10_nc)

    # ── Stage A ribbons (Col1 → Col2) ─────────────────────────────────────
    # Col1 stacking (within NoColl: [0,f_nn]→NoDec, [f_nn,h1_nocoll]→Dec)
    # Col1 stacking (within Coll:   [h1_nocoll,h1_nocoll+f_cn]→NoDec, [+f_cn,1]→Dec)
    # Col2 sink stacking (NoDec: [0,f_nn]←NoColl, [f_nn,h2_nodec]←Coll)
    #                    (Dec:  [h2_nodec,h2_nodec+f_nc]←NoColl, [+f_nc,1]←Coll)
    for (ly0, ly1, ry0, ry1, col, alp) in [
        (0,               f_nn,             0,               f_nn,                R_NN, 0.58),
        (f_nn,            h1_nocoll,        h2_nodec,        h2_nodec + f_nc,     R_ND, 0.72),
        (h1_nocoll,       h1_nocoll + f_cn, f_nn,            h2_nodec,            R_CN, 0.62),
        (h1_nocoll + f_cn, 1.0,             h2_nodec + f_nc, 1.0,                 R_CD, 0.72),
    ]:
        ribbon(x1r, x2l, ly0, ly1, ry0, ry1, col, alp)

    # ── Stage B ribbons (Col2 → Col3) ─────────────────────────────────────
    # Col2 source (NoDec: [0,b_nn_n]→NoColl, [b_nn_n,h2_nodec]→Coll)
    #             (Dec:  [h2_nodec,h2_nodec+b_dec_n]→NoColl, [+b_dec_n,1]→Coll)
    # Col3 sink   (NoColl: [0,b_nn_n]←NoDec, [b_nn_n,h3_nocoll]←Dec)
    #             (Coll:  [h3_nocoll,h3_nocoll+b_nn_c]←NoDec, [+b_nn_c,1]←Dec)
    for (ly0, ly1, ry0, ry1, col, alp) in [
        (0,                    b_nodec_nocoll,          0,                        b_nodec_nocoll,          RB_NN, 0.58),
        (b_nodec_nocoll,       h2_nodec,                h3_nocoll,                h3_nocoll + b_nodec_coll, RB_NC, 0.68),
        (h2_nodec,             h2_nodec + b_dec_nocoll, b_nodec_nocoll,           h3_nocoll,               RB_DN, 0.62),
        (h2_nodec + b_dec_nocoll, 1.0,                  h3_nocoll + b_nodec_coll, 1.0,                     RB_DC, 0.72),
    ]:
        ribbon(x2r, x3l, ly0, ly1, ry0, ry1, col, alp)

    # ── Stage C ribbons (Col3 → Col4) ─────────────────────────────────────
    # Col3 source (NoColl: [0,c_nc_n]→NoDec, [c_nc_n,h3_nocoll]→Dec)
    #             (Coll:   [h3_nocoll,h3_nocoll+c_c_n]→NoDec, [+c_c_n,1]→Dec)
    # Col4 sink   (NoDec: [0,c_nc_n]←NoColl, [c_nc_n,h4_nodec]←Coll)
    #             (Dec:   [h4_nodec,h4_nodec+c_nc_d]←NoColl, [+c_nc_d,1]←Coll)
    for (ly0, ly1, ry0, ry1, col, alp) in [
        (0,                    c_nocoll_nodec,             0,                      c_nocoll_nodec,            R_NN, 0.58),
        (c_nocoll_nodec,       h3_nocoll,                  h4_nodec,               h4_nodec + c_nocoll_dec,   R_ND, 0.72),
        (h3_nocoll,            h3_nocoll + c_coll_nodec,   c_nocoll_nodec,         h4_nodec,                  R_CN, 0.62),
        (h3_nocoll + c_coll_nodec, 1.0,                    h4_nodec + c_nocoll_dec, 1.0,                      R_CD, 0.72),
    ]:
        ribbon(x3r, x4l, ly0, ly1, ry0, ry1, col, alp)

    # ── Column header labels ──────────────────────────────────────────────
    HDR_Y = 1.115
    for (xl, xr), lbl in zip(COLS, [
        f"Rnd {rnd1}  Post Collusion",
        f"Rnd {rnd1}  Behavior",
        f"Rnd {rnd2}  Post Collusion",
        f"Rnd {rnd2}  Behavior",
    ]):
        ax.text((xl + xr) / 2, HDR_Y, lbl,
                ha='center', va='bottom', fontsize=7.5,
                fontweight='bold', color='#2C3E50')

    # Stage connector labels at the bottom
    for mx, lbl in [
        ((x1r + x2l) / 2, "A: post→beh"),
        ((x2r + x3l) / 2, "B: beh→post\n(agent)"),
        ((x3r + x4l) / 2, "C: post→beh"),
    ]:
        ax.text(mx, -0.055, lbl,
                ha='center', va='top', fontsize=5.5,
                color='#888888', style='italic')

    ax.set_xlim(-0.22, 1.28)
    ax.set_ylim(-0.12, 1.25)
    ax.axis('off')


def fig1_1_sankey_by_condition(data_dir: str, output_dir: Path,
                               rounds: Tuple[int, int] = (1, 10)) -> None:
    """
    2x2 grid of panels, one per market condition.
    Each panel contains two side-by-side mini-Sankeys for the two selected rounds.

    rounds: tuple of two round numbers to compare (default: first vs last).
    """
    posts = _load_labeled_posts(data_dir)
    if not posts:
        print("  WARNING: No labeled posts for fig1-1")
        return

    df = pd.DataFrame(posts)
    df["post_collusion"] = df["primary_type"].isin([1, 2, 3, 4])
    df["behavior_deception"] = df["deceptive_listing"].astype(bool)

    COND_GROUPS = [
        ("Rep  (No Seller Comm)",
         lambda e: e.startswith("r_wsc_")  and "_F_" in e),
        ("Rep  (Seller Comm)",
         lambda e: e.startswith("r_wsc_")  and "_R_" in e),
        ("Rep + Warrant  (No Seller Comm)",
         lambda e: e.startswith("rw_wsc_") and "_F_" in e),
        ("Rep + Warrant  (Seller Comm)",
         lambda e: e.startswith("rw_wsc_") and "_R_" in e),
    ]
    layout = [(0, 0), (0, 1), (1, 0), (1, 1)]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.subplots_adjust(wspace=0.55, hspace=0.55)

    # Two mini-Sankeys per panel: left half [0, 0.47], right half [0.53, 1.0]
    # x_offset + x_scale must keep unit-space bars [0.18..0.82] within [0, 1]
    SLOTS = [
        (0.00, 0.47),   # left slot:  Round rounds[0]
        (0.53, 0.47),   # right slot: Round rounds[1]
    ]

    for (row, col), (title, mask_fn) in zip(layout, COND_GROUPS):
        ax = axes[row][col]
        cdf = df[df["experiment_id"].apply(mask_fn)]

        for slot_idx, (x_off, x_sc) in enumerate(SLOTS):
            rnd = rounds[slot_idx]
            rdf = cdf[cdf["round"] == rnd]
            cc = int((rdf["post_collusion"] & rdf["behavior_deception"]).sum())
            cn = int((rdf["post_collusion"] & ~rdf["behavior_deception"]).sum())
            nc = int((~rdf["post_collusion"] & rdf["behavior_deception"]).sum())
            nn = int((~rdf["post_collusion"] & ~rdf["behavior_deception"]).sum())
            _draw_sankey_ax(ax, cc, cn, nc, nn,
                            x_offset=x_off, x_scale=x_sc,
                            sublabel=f"Round {rnd}")

        # Separator line between the two mini-Sankeys
        ax.axvline(x=0.50, color='#CCCCCC', linewidth=0.8, linestyle='--', zorder=1)

        ax.set_xlim(-0.08, 1.08)
        ax.set_ylim(-0.05, 1.22)
        ax.set_title(title, fontsize=9, fontweight='bold', pad=6)
        ax.axis('off')

    fig.suptitle(
        f"Post Collusion → Seller Deception Behavior: Round {rounds[0]} vs Round {rounds[1]}\n"
        "by Market Condition  (Left node: Post Collusion Status | Right node: Behavior)",
        fontsize=12, fontweight='bold', y=1.02
    )

    legend_handles = [
        mpatches.Patch(fc="#AE2012", label="Collusion post (types 1-4)"),
        mpatches.Patch(fc="#6B6B6B", label="No Collusion post (types 5-6)"),
        mpatches.Patch(fc="#9B2226", label="Deception (behavior)"),
        mpatches.Patch(fc="#52B788", label="No Deception (behavior)"),
        mpatches.Patch(fc="#E09B70", label="No-Collusion post → Deception"),
        mpatches.Patch(fc="#D4866A", label="Collusion post → No Deception"),
    ]
    fig.legend(handles=legend_handles, loc='lower center', ncol=3,
               frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.07))

    add_sig_footnote(fig, y=-0.13,
                     extra="Flow width proportional to post fraction within each condition × round")
    save_figure(fig, output_dir / "fig1_1_sankey_by_condition.png")
    print("  [Fig1-1] Sankey by condition (2 rounds) saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1-2: Embedding Cluster + Word Clouds
# ─────────────────────────────────────────────────────────────────────────────

_WC_STOPWORDS_EXTRA = {
    "will", "can", "us", "also", "one", "let", "well", "may", "want",
    "need", "use", "get", "make", "just", "way", "product", "products",
    "market", "marketplace", "seller", "sellers", "buyer", "customers",
    "customer", "business", "quality", "high", "low", "think", "know",
    "time", "good", "like", "new", "ensure", "help", "believe", "important",
    "fellow", "approach", "strategy", "strategies", "consider",
}

# 4 market conditions for fig1-2
_COND_DEFS = [
    ("Rep\n(No Seller Comm)",
     lambda e: e.startswith("r_wsc_")  and "_F_" in e,
     "#6B6B6B", "Greys"),
    ("Rep\n(Seller Comm)",
     lambda e: e.startswith("r_wsc_")  and "_R_" in e,
     "#52B788", "Greens"),
    ("Rep + Warrant\n(No Seller Comm)",
     lambda e: e.startswith("rw_wsc_") and "_F_" in e,
     "#1565c0", "Blues"),
    ("Rep + Warrant\n(Seller Comm)",
     lambda e: e.startswith("rw_wsc_") and "_R_" in e,
     "#9B2226", "Reds"),
]


def _assign_condition(exp_id: str) -> str:
    for name, mask_fn, _, _ in _COND_DEFS:
        if mask_fn(exp_id):
            return name
    return "Unknown"


def fig1_2_embedding_cluster(data_dir: str, output_dir: Path) -> None:
    """
    UMAP scatter + word clouds organized by 4 market conditions (2x2).

    Left 2/3 of figure: UMAP scatter colored by market condition.
    Right 2x2: one word cloud per condition.
    Embeddings cached to data/case_analysis/post_embeddings_cache.npy.
    """
    try:
        import umap as umap_module
        from wordcloud import WordCloud, STOPWORDS as WC_STOPWORDS
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"  WARNING: Missing package for fig1-2 ({e}). Skipping.")
        return

    posts = _load_labeled_posts(data_dir)
    if not posts:
        print("  WARNING: No labeled posts for fig1-2")
        return

    df = pd.DataFrame(posts)
    df["condition"] = df["experiment_id"].apply(_assign_condition)

    # ── Embeddings (with cache) ───────────────────────────────────────────
    cache_path = Path(data_dir) / "case_analysis" / "post_embeddings_cache.npy"
    texts = df["post_content"].tolist()
    embeddings = None

    if cache_path.exists():
        cached = np.load(cache_path)
        if len(cached) == len(texts):
            embeddings = cached

    if embeddings is None:
        print(f"  Computing sentence embeddings for {len(texts)} posts "
              "(first run, ~1-2 min; cached afterwards)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(texts, show_progress_bar=False, batch_size=64)
        np.save(cache_path, embeddings)
        print("  Embeddings cached.")

    # ── UMAP reduction ────────────────────────────────────────────────────
    print("  Running UMAP dimensionality reduction...")
    reducer = umap_module.UMAP(
        n_components=2, n_neighbors=15, min_dist=0.1,
        metric='cosine', random_state=42
    )
    coords = reducer.fit_transform(embeddings)
    df["ux"] = coords[:, 0]
    df["uy"] = coords[:, 1]

    # ── Figure layout: UMAP left (2 rows × 2 cols), word clouds right 2x2 ──
    fig = plt.figure(figsize=(18, 8))
    gs = fig.add_gridspec(2, 4, wspace=0.40, hspace=0.50)
    ax_scatter = fig.add_subplot(gs[:, :2])

    # Word cloud axes: top-left, top-right, bottom-left, bottom-right
    wc_axes = [
        fig.add_subplot(gs[0, 2]),
        fig.add_subplot(gs[0, 3]),
        fig.add_subplot(gs[1, 2]),
        fig.add_subplot(gs[1, 3]),
    ]

    # ── UMAP scatter ─────────────────────────────────────────────────────
    for name, _, color, _ in _COND_DEFS:
        mask = df["condition"] == name
        label_str = name.replace("\n", " ")
        ax_scatter.scatter(
            df.loc[mask, "ux"], df.loc[mask, "uy"],
            c=color, label=f"{label_str} (n={mask.sum()})",
            s=7, alpha=0.5, linewidths=0, rasterized=True
        )

    ax_scatter.set_title(
        "Post Content Embedding Clusters\n(UMAP; colored by Market Condition)",
        fontsize=11, fontweight='bold'
    )
    ax_scatter.set_xlabel("UMAP Dimension 1", fontsize=10)
    ax_scatter.set_ylabel("UMAP Dimension 2", fontsize=10)
    ax_scatter.legend(loc='lower left', fontsize=8, frameon=True,
                      framealpha=0.85, markerscale=3)
    ax_scatter.tick_params(labelsize=8)

    # ── Word Clouds ───────────────────────────────────────────────────────
    stopwords = set(WC_STOPWORDS) | _WC_STOPWORDS_EXTRA

    for ax, (cond_name, _, color, cmap) in zip(wc_axes, _COND_DEFS):
        cond_df = df[df["condition"] == cond_name]
        title_str = cond_name.replace("\n", " ")
        ax.set_title(f"{title_str}\n(n={len(cond_df)})",
                     fontsize=8, fontweight='bold', color=color, pad=3)

        if len(cond_df) < 3:
            ax.axis('off')
            continue

        text_blob = " ".join(cond_df["post_content"].tolist())
        wc = WordCloud(
            width=380, height=180,
            background_color='white',
            stopwords=stopwords,
            colormap=cmap,
            max_words=60,
            prefer_horizontal=0.85,
            collocations=False,
            min_font_size=7,
        )
        wc.generate(text_blob)
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')

    fig.suptitle(
        "Post Content Analysis: Embedding Clusters & Word Frequency by Market Condition",
        fontsize=13, fontweight='bold', y=1.02
    )

    add_sig_footnote(
        fig,
        extra="Embeddings: all-MiniLM-L6-v2; UMAP(neighbors=15, min_dist=0.1, cosine)"
    )
    save_figure(fig, output_dir / "fig1_2_embedding_cluster.png")
    print("  [Fig1-2] Embedding cluster + word clouds saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2: Collusion Type Distribution by Mechanism × Communication (4 bars)
# ─────────────────────────────────────────────────────────────────────────────

def fig2_collusion_by_mechanism(data_dir: str, output_dir: Path) -> None:
    """
    Stacked bar chart: 4 groups —
      Rep (No Seller Comm) | Rep (Seller Comm) | Warrant (No Comm) | Warrant (Comm)
    experiment_id pattern: {r|rw}_wsc_{F|R}_* where F=Fake(No Comm), R=Real(Comm)
    """
    df = load_type_distribution_by_condition(data_dir)
    if df.empty:
        print("  WARNING: Empty dataframe for fig2")
        return

    exp_ids = df["experiment_id"].tolist()

    groups = {
        "Rep\n(No Seller Comm)":    [c for c in exp_ids if c.startswith("r_wsc_")  and "_F_" in c],
        "Rep\n(Seller Comm)":       [c for c in exp_ids if c.startswith("r_wsc_")  and "_R_" in c],
        "Warrant\n(No Seller Comm)":[c for c in exp_ids if c.startswith("rw_wsc_") and "_F_" in c],
        "Warrant\n(Seller Comm)":   [c for c in exp_ids if c.startswith("rw_wsc_") and "_R_" in c],
    }

    type_cols = [f"type_{i}" for i in range(1, 7)]

    group_means = {}
    for label, conds in groups.items():
        if conds:
            group_means[label] = df[df["experiment_id"].isin(conds)][type_cols].mean()
        else:
            group_means[label] = pd.Series(np.zeros(6), index=type_cols)

    group_labels = list(group_means.keys())
    n_groups = len(group_labels)
    x_pos = np.arange(n_groups)
    width = 0.55

    fig, ax = plt.subplots(figsize=(11, 5))
    bottom = np.zeros(n_groups)

    for type_id in [1, 2, 3, 4, 5, 6]:
        col = f"type_{type_id}"
        values = np.array([group_means[lab][col] * 100 for lab in group_labels])
        type_info = COLLUSION_TYPES[type_id]

        ax.bar(x_pos, values, width=width, bottom=bottom,
               color=type_info["color"], label=type_info["abbrev"],
               edgecolor="white", linewidth=0.5)

        for i, (val, bot) in enumerate(zip(values, bottom)):
            if val > 7:
                ax.text(x_pos[i], bot + val / 2, f"{val:.1f}%",
                        ha='center', va='center', fontsize=8,
                        color='white', fontweight='bold')

        bottom = bottom + values

    # Divider between Rep and Warrant groups
    ax.axvline(x=1.5, color='gray', linestyle='--', linewidth=1.0, alpha=0.6)
    ax.text(0.5, 108, "Reputation Only", ha='center', va='center',
            fontsize=9, color='gray', style='italic')
    ax.text(2.5, 108, "Reputation + Warrant", ha='center', va='center',
            fontsize=9, color='gray', style='italic')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(group_labels, fontsize=10)
    ax.set_ylabel("Percentage of Posts (%)", fontsize=11)
    ax.set_title(
        "Collusion Type Distribution by Mechanism and Seller Communication\n"
        "(Seller Comm = sellers allowed to post in shared channel)",
        fontsize=11, fontweight='bold', pad=10
    )
    ax.set_ylim(0, 115)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.13),
              ncol=3, frameon=False, fontsize=9)

    add_sig_footnote(fig, y=-0.20, extra="Types 1-4 = collusive, Type 5 = neutral, Type 6 = anti-collusion")
    save_figure(fig, output_dir / "fig2_collusion_by_mechanism.png")
    print("  [Fig2] Collusion by mechanism (4 groups) saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3: Collusion Evolution Over Rounds (two subplots)
# ─────────────────────────────────────────────────────────────────────────────

def fig3_collusion_evolution(data_dir: str, output_dir: Path) -> None:
    """
    Two-panel figure:
    (a) Left: Types 1-4 (collusive messaging) evolution over rounds
    (b) Right: Types 5-6 (neutral / anti-collusion) evolution over rounds
    """
    df = load_type_distribution_by_round(data_dir)
    if df.empty:
        print("  WARNING: Empty dataframe for fig3")
        return

    rounds = df["round"].values

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(14, 5))
    fig.subplots_adjust(wspace=0.30)

    # ── (a) Collusive types 1-4 ───────────────────────────────────────────
    for type_id in [1, 2, 3, 4]:
        col = str(type_id)
        values = df[col].values * 100
        ti = COLLUSION_TYPES[type_id]
        ax_a.plot(rounds, values, color=ti["color"], label=ti["abbrev"],
                  linestyle='-', linewidth=1.5, marker='o', markersize=5,
                  markevery=2)

    ax_a.set_xlabel("Round", fontsize=11)
    ax_a.set_ylabel("Percentage of Posts (%)", fontsize=11)
    ax_a.set_title("(a) Collusive Messaging Evolution\n(Types 1–4)",
                   fontsize=11, fontweight='bold')
    ax_a.set_xticks(rounds)
    ax_a.legend(loc='upper right', frameon=False, fontsize=9)
    ax_a.grid(True, alpha=0.3, linestyle=':')
    ax_a.set_ylim(bottom=0)

    # ── (b) Neutral & Anti-collusion types 5-6 ────────────────────────────
    styles = {5: ('--', 'o'), 6: ('-', 's')}
    for type_id in [5, 6]:
        col = str(type_id)
        values = df[col].values * 100
        ti = COLLUSION_TYPES[type_id]
        ls, mk = styles[type_id]
        ax_b.plot(rounds, values, color=ti["color"], label=ti["abbrev"],
                  linestyle=ls, linewidth=1.8, marker=mk, markersize=5,
                  markevery=2)

    ax_b.set_xlabel("Round", fontsize=11)
    ax_b.set_ylabel("Percentage of Posts (%)", fontsize=11)
    ax_b.set_title("(b) Neutral & Anti-Collusion Evolution\n(Types 5–6)",
                   fontsize=11, fontweight='bold')
    ax_b.set_xticks(rounds)
    ax_b.legend(loc='upper right', frameon=False, fontsize=9)
    ax_b.grid(True, alpha=0.3, linestyle=':')
    ax_b.set_ylim(bottom=0)

    fig.suptitle("Collusion Patterns Evolve Across Rounds",
                 fontsize=13, fontweight='bold', y=1.02)

    add_sig_footnote(fig)
    save_figure(fig, output_dir / "fig3_collusion_evolution.png")
    print("  [Fig3] Collusion evolution (2 subplots) saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1-3: 2x2 Stacked Bar Chart (Communication vs Behavior)
# ─────────────────────────────────────────────────────────────────────────────

def fig1_3_2x2_stacked_bar(data_dir: str, output_dir: Path) -> None:
    """
    Stacked bar chart showing the 4 categories of posts across 4 market conditions.
    
    Categories:
    - Honest: No collusive post + No deception
    - Hidden Deception: No collusive post + Deception
    - Verbal Collusion: Collusive post + No deception
    - Coordinated Deception: Collusive post + Deception
    
    4 Market Conditions:
    - Rep (No Comm)
    - Rep + Comm  
    - Rep + Warrant (No Comm)
    - Rep + Warrant + Comm
    """
    posts = _load_labeled_posts(data_dir)
    if not posts:
        print("  WARNING: No labeled posts for fig1-3")
        return
    
    df = pd.DataFrame(posts)
    df["post_collusion"] = df["primary_type"].isin([1, 2, 3, 4])
    df["behavior_deception"] = df["deceptive_listing"].astype(bool)
    
    def get_condition_group(exp_id: str) -> str:
        if exp_id.startswith('r_wsc_F_'):
            return 'Rep_NoComm'
        elif exp_id.startswith('r_wsc_R_'):
            return 'Rep_Comm'
        elif exp_id.startswith('rw_wsc_F_'):
            return 'Warrant_NoComm'
        elif exp_id.startswith('rw_wsc_R_'):
            return 'Warrant_Comm'
        return 'Unknown'
    
    def get_2x2_category(row: pd.Series) -> str:
        if not row['post_collusion'] and not row['behavior_deception']:
            return 'Honest'
        elif not row['post_collusion'] and row['behavior_deception']:
            return 'Hidden_Deception'
        elif row['post_collusion'] and not row['behavior_deception']:
            return 'Verbal_Collusion'
        else:
            return 'Coordinated_Deception'
    
    df['condition'] = df['experiment_id'].apply(get_condition_group)
    df['category'] = df.apply(get_2x2_category, axis=1)
    
    # Filter out unknown conditions
    df = df[df['condition'] != 'Unknown']
    
    # Calculate counts per condition
    conditions = ['Rep_NoComm', 'Rep_Comm', 'Warrant_NoComm', 'Warrant_Comm']
    categories = ['Honest', 'Hidden_Deception', 'Verbal_Collusion', 'Coordinated_Deception']
    
    # Colors for each category
    cat_colors = {
        'Honest': '#52B788',                    # Green
        'Hidden_Deception': '#9B2226',           # Dark red
        'Verbal_Collusion': '#E07A5F',           # Pink/salmon
        'Coordinated_Deception': '#AE2012',      # Red
    }
    
    # Aggregate data
    data = {cond: {cat: 0 for cat in categories} for cond in conditions}
    for _, row in df.iterrows():
        cond = row['condition']
        cat = row['category']
        if cond in data and cat in data[cond]:
            data[cond][cat] += 1
    
    # Convert to percentages
    totals = {cond: sum(data[cond].values()) for cond in conditions}
    percentages = {}
    for cond in conditions:
        percentages[cond] = {}
        for cat in categories:
            if totals[cond] > 0:
                percentages[cond][cat] = (data[cond][cat] / totals[cond]) * 100
            else:
                percentages[cond][cat] = 0
    
    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(conditions))
    width = 0.6
    
    # Build stacked bars
    bottom = np.zeros(len(conditions))
    for cat in categories:
        values = [percentages[cond][cat] for cond in conditions]
        bars = ax.bar(x, values, width, label=cat, bottom=bottom, 
                      color=cat_colors[cat], edgecolor='white', linewidth=0.5)
        
        # Add text labels on bars if segment is large enough
        for i, (val, bot) in enumerate(zip(values, bottom)):
            if val >= 5:  # Only show label if segment >= 5%
                ax.text(x[i], bot + val/2, f'{val:.1f}%',
                       ha='center', va='center', fontsize=8, 
                       color='white', fontweight='bold')
        
        bottom += values
    
    # Formatting
    ax.set_xlabel('Market Condition', fontsize=12)
    ax.set_ylabel('Percentage of Posts (%)', fontsize=12)
    ax.set_title('Collusion Communication vs Deceptive Behavior\nby Market Condition',
                 fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['Rep\n(No Comm)', 'Rep\n(Comm)', 
                        'Rep + Warrant\n(No Comm)', 'Rep + Warrant\n(Comm)'],
                       fontsize=10)
    ax.legend(loc='upper right', frameon=False, fontsize=9)
    ax.set_ylim(0, 105)
    ax.grid(True, axis='y', alpha=0.3, linestyle=':')
    
    # Add sample size annotations
    for i, cond in enumerate(conditions):
        ax.text(x[i], -5, f'n={totals[cond]}',
               ha='center', va='top', fontsize=8, color='gray')
    
    plt.tight_layout()
    save_figure(fig, output_dir / "fig1_3_2x2_stacked_bar.png")
    print("  [Fig1-3] 2x2 Stacked bar chart saved.")


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate collusion analysis visualizations"
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Path to data directory containing case_analysis/"
    )
    parser.add_argument(
        "--output-dir",
        default="visualization/figs/paper/collusion_analysis",
        help="Output directory for figures"
    )
    parser.add_argument(
        "--skip-embedding",
        action="store_true",
        help="Skip fig1-2 (embedding + word cloud) — useful for quick iteration"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Collusion Analysis Visualization Generator")
    print("=" * 70)
    print(f"\nData directory: {args.data_dir}")
    print(f"Output directory: {output_dir}")

    print("\n[Fig1] Deception Rate by Collusion Status...")
    fig1_deception_by_collusion(args.data_dir, output_dir)

    print("\n[Fig1-1] Sankey: Post Collusion → Behavior Deception by Condition...")
    fig1_1_sankey_by_condition(args.data_dir, output_dir)

    if not args.skip_embedding:
        print("\n[Fig1-2] Embedding Cluster + Word Clouds (4 categories)...")
        fig1_2_embedding_cluster(args.data_dir, output_dir)
    else:
        print("\n[Fig1-2] Skipped (--skip-embedding).")

    print("\n[Fig1-3] 2x2 Stacked Bar: Communication vs Behavior...")
    fig1_3_2x2_stacked_bar(args.data_dir, output_dir)

    print("\n[Fig2] Collusion by Mechanism × Communication (4 groups)...")
    fig2_collusion_by_mechanism(args.data_dir, output_dir)

    print("\n[Fig3] Collusion Evolution Over Rounds (2 subplots)...")
    fig3_collusion_evolution(args.data_dir, output_dir)

    print("\n" + "=" * 70)
    print(f"All figures saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
