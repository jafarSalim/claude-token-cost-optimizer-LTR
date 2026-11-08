"""Builds excel/claude_token_costs.xlsx: inputs, live formulas and native Excel charts.

Change any blue cell in Scenario or Prices and every table and chart updates.
"""
import json, pathlib, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.chart import AreaChart, LineChart, BarChart, DoughnutChart, BubbleChart, Reference, Series
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.text import RichText
from openpyxl.drawing.text import Paragraph, ParagraphProperties, CharacterProperties, Font as DFont
from openpyxl.chart.layout import Layout, ManualLayout
from tokenopt.pricing import PRICES, CURRENT, SOURCE, RETRIEVED

OUT = pathlib.Path("excel")
OUT.mkdir(exist_ok=True)
S = json.load(open("results/summary.json"))
BLUE_IN = Font(name="Calibri", color="0000FF")
BOLD = Font(name="Calibri", bold=True)
HEAD = PatternFill("solid", fgColor="1F4E79")
HEADF = Font(name="Calibri", bold=True, color="FFFFFF")
NOTE = Font(name="Calibri", italic=True, color="595959", size=9)
OFFICE = ["4472C4", "ED7D31", "A5A5A5", "FFC000", "5B9BD5", "70AD47", "264478", "9E480E"]
thin = Side(style="thin", color="BFBFBF")

wb = Workbook()
wb.remove(wb.active)


def header(ws, row, names, widths=None):
    for i, n in enumerate(names, 1):
        c = ws.cell(row, i, n)
        c.fill, c.font, c.alignment = HEAD, HEADF, Alignment(horizontal="center", vertical="center", wrap_text=True)
    if widths:
        for i, w in enumerate(widths):
            ws.column_dimensions[chr(65 + i)].width = w


def style_chart(ch, title, w=24, h=13):
    ch.title = title
    ch.width, ch.height = w, h
    ch.style = 2
    cp = CharacterProperties(latin=DFont(typeface="Calibri"), sz=1400, b=True, solidFill="404040")
    ch.title.tx.rich.p[0].pPr = ParagraphProperties(defRPr=cp)
    return ch


def fill(series, color, line=False, width=28575):
    series.graphicalProperties = GraphicalProperties()
    if line:
        series.graphicalProperties.line.solidFill = color
        series.graphicalProperties.line.width = width
        series.smooth = False
    else:
        series.graphicalProperties.solidFill = color
        series.graphicalProperties.line.solidFill = color


def labels(series, fmt=None, pos=None):
    series.dLbls = DataLabelList()
    series.dLbls.showVal = True
    for k in ("showSerName", "showCatName", "showLegendKey", "showPercent"):
        setattr(series.dLbls, k, False)
    if fmt:
        series.dLbls.numFmt = fmt
    if pos:
        series.dLbls.position = pos


def chart_sheet(name, ch, note=None):
    ws = wb.create_sheet(name)
    ws.add_chart(ch, "B2")
    if note:
        ws["B29"] = note
        ws["B29"].font = NOTE
    ws.page_setup.orientation = "landscape"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = ws.page_setup.fitToHeight = 1
    ws.print_area = "A1:Q30"
    return ws


# ---------------- Prices ----------------
pr = wb.create_sheet("Prices")
header(pr, 1, ["Model", "Input $/MTok", "5-min cache write", "1-hour cache write", "Cache read", "Output $/MTok"], [22, 13, 15, 15, 12, 14])
for i, (m, v) in enumerate(PRICES.items(), 2):
    pr.cell(i, 1, m).font = Font(name="Calibri")
    for j, x in enumerate(v, 2):
        c = pr.cell(i, j, x)
        c.font, c.number_format = BLUE_IN, '"$"#,##0.000'
LASTP = len(PRICES) + 1
pr.cell(LASTP + 2, 1, f"Source: Claude API pricing page, {SOURCE}, retrieved {RETRIEVED}. Haiku 5.5 prompts over 100,000 tokens use higher prices (not needed here).").font = NOTE

# ---------------- Scenario ----------------
sc = wb.create_sheet("Scenario", 0)
sc.column_dimensions["A"].width, sc.column_dimensions["B"].width, sc.column_dimensions["C"].width = 34, 20, 60
sc["A1"] = "Scenario inputs (blue cells can be changed)"
sc["A1"].font = Font(name="Calibri", bold=True, size=14, color="1F4E79")
rows = [("Model", "Claude Sonnet 5.5", "Must match a name in Prices"), ("Tool definitions (tokens)", 2000, "Sent with every request"),
        ("System prompt (tokens)", 3000, "Sent with every request"), ("User message per turn (tokens)", 150, "Assumption"),
        ("Reply per turn (tokens)", 400, "Assumption"), ("Sliding window (turns kept)", 6, "Used in the Strategies sheet"),
        ("Chats per day", 1000, "Assumption"), ("Days per month", 30, ""), ("Turns per chat (monthly figures)", 20, "Per Turn sheet covers 40 turns")]
for i, (a, b, c) in enumerate(rows, 3):
    sc.cell(i, 1, a).font = Font(name="Calibri")
    x = sc.cell(i, 2, b)
    x.font = BLUE_IN
    sc.cell(i, 3, c).font = NOTE
sc["A13"], sc["A13"].font = "Prices for the chosen model ($ per million tokens)", BOLD
for i, (lab, col) in enumerate([("Input", "B"), ("5-min cache write", "C"), ("1-hour cache write", "D"), ("Cache read", "E"), ("Output", "F")], 14):
    sc.cell(i, 1, lab).font = Font(name="Calibri")
    c = sc.cell(i, 2, f"=INDEX(Prices!{col}$2:{col}${LASTP},MATCH($B$3,Prices!$A$2:$A${LASTP},0))")
    c.number_format = '"$"#,##0.000'
sc["A20"], sc["B20"] = "Cache read as a share of input", "=B17/B14"
sc["B20"].number_format = "0.0%"
sc["A22"] = "Turns are assumed to arrive within the 5-minute cache lifetime."
sc["A22"].font = NOTE
P_IN, P_W5, P_W1, P_R, P_OUT = "Scenario!$B$14", "Scenario!$B$15", "Scenario!$B$16", "Scenario!$B$17", "Scenario!$B$18"
TOOLS, SYS, USER, REPLY, WIN, CHATS, DAYS, TURNS = (f"Scenario!$B${r}" for r in range(4, 12))

# ---------------- Per turn ----------------
pt = wb.create_sheet("Per Turn")
cols = ["Turn", "Tools + system", "History", "New user msg", "Reply (output)", "Prompt tokens",
        "Cost: tools+system", "Cost: history", "Cost: new msg", "Cost: reply", "Turn cost, no cache",
        "Cache read", "Cache write", "Turn cost, cache", "Cumulative, no cache", "Cumulative, cache",
        "Window history", "Window prompt", "Turn cost, window", "Window: cache read", "Turn cost, window+cache",
        "Cumulative, window", "Cumulative, window+cache", "Cumulative, cache+compaction"]
header(pt, 1, cols)
for i in range(len(cols)):
    pt.column_dimensions[chr(65 + i)].width = 13
pt.row_dimensions[1].height = 45
K = "/1000"  # cost columns are USD per 1,000 chats: tokens * price / 1e6 * 1000
cum_comp = S["cumulative_compaction_per_1000"]
for t in range(1, 41):
    r = t + 1
    f = {
        "A": t, "B": f"={TOOLS}+{SYS}", "C": f"=(A{r}-1)*({USER}+{REPLY})", "D": f"={USER}", "E": f"={REPLY}",
        "F": f"=B{r}+C{r}+D{r}", "G": f"=B{r}*{P_IN}{K}", "H": f"=C{r}*{P_IN}{K}", "I": f"=D{r}*{P_IN}{K}",
        "J": f"=E{r}*{P_OUT}{K}", "K": f"=SUM(G{r}:J{r})", "L": f"=IF(A{r}=1,0,F{r - 1})", "M": f"=F{r}-L{r}",
        "N": f"=(L{r}*{P_R}+M{r}*{P_W5}){K}+J{r}", "O": f"=SUM(K$2:K{r})", "P": f"=SUM(N$2:N{r})",
        "Q": f"=MIN(A{r}-1,{WIN})*({USER}+{REPLY})", "R": f"=B{r}+Q{r}+D{r}", "S": f"=R{r}*{P_IN}{K}+J{r}",
        "T": f"=IF(A{r}=1,0,IF(A{r}-1<={WIN},R{r - 1},B{r}))", "U": f"=(T{r}*{P_R}+(R{r}-T{r})*{P_W5}){K}+J{r}",
        "V": f"=SUM(S$2:S{r})", "W": f"=SUM(U$2:U{r})", "X": round(cum_comp[t - 1], 6),
    }
    for col, v in f.items():
        c = pt[f"{col}{r}"]
        c.value = v
        c.number_format = "#,##0" if col in "ABCDEFLMQRT" else '"$"#,##0.00'
pt["X2"].comment = Comment("Column X comes from run_analysis.py (tokenopt.simulate), because compaction needs a turn-by-turn simulation. Same scenario, Sonnet 5.5.", "model")
pt["A43"] = "Cost columns are USD per 1,000 chats. Cache: each turn reads the previous prompt and writes the new reply + message."
pt["A43"].font = NOTE
pt.freeze_panes = "B2"

# ---------------- Strategies table for monthly chart ----------------
wf = wb.create_sheet("Waterfall Data")
header(wf, 1, ["Step", "Monthly cost", "Base", "Decrease", "Increase", "Total", "Change"], [30, 14, 12, 12, 12, 12, 12])
steps = list(S["waterfall"].items())
wf["A2"], wf["B2"] = "Baseline", f"=SUM('Per Turn'!K2:INDEX('Per Turn'!K2:K41,{TURNS}))/1000*{CHATS}*{DAYS}"
wf["A3"], wf["B3"] = "Prompt caching", f"=SUM('Per Turn'!N2:INDEX('Per Turn'!N2:N41,{TURNS}))/1000*{CHATS}*{DAYS}"
names = ["Compact every 10 turns", "Replies 400 → 250", "60% of chats to Haiku"]
for i, (n, (_, v)) in enumerate(zip(names, steps[2:]), 4):
    wf.cell(i, 1, n)
    c = wf.cell(i, 2, round(v, 2))
    c.font = BLUE_IN
wf["B4"].comment = Comment("Rows 4 to 6 come from run_analysis.py, because compaction and routing need the turn-by-turn simulation.", "model")
wf["A7"], wf["B7"] = "Final", "=B6"
for r in range(2, 8):
    wf[f"B{r}"].number_format = '"$"#,##0'
    if r in (2, 7):
        wf[f"C{r}"], wf[f"D{r}"], wf[f"E{r}"], wf[f"F{r}"] = 0, 0, 0, f"=B{r}"
    else:
        wf[f"C{r}"] = f"=MIN(B{r - 1},B{r})"
        wf[f"D{r}"] = f"=MAX(B{r - 1}-B{r},0)"
        wf[f"E{r}"] = f"=MAX(B{r}-B{r - 1},0)"
        wf[f"F{r}"] = 0
        wf[f"G{r}"] = f"=B{r}/B{r - 1}-1"
        wf[f"G{r}"].number_format = "+0%;-0%"
    for col in "CDEF":
        wf[f"{col}{r}"].number_format = '"$"#,##0'

# ---------------- Token share ----------------
ts = wb.create_sheet("Token Share Data")
header(ts, 1, ["Part", "Tokens per chat", "Cost per chat"], [22, 16, 14])
parts = [("Tool definitions", f"={TOOLS}*{TURNS}", P_IN), ("System prompt", f"={SYS}*{TURNS}", P_IN),
         ("Chat history", f"=SUM('Per Turn'!C2:INDEX('Per Turn'!C2:C41,{TURNS}))", P_IN),
         ("New user messages", f"={USER}*{TURNS}", P_IN), ("Replies (output)", f"={REPLY}*{TURNS}", P_OUT)]
for i, (n, tok, price) in enumerate(parts, 2):
    ts.cell(i, 1, n)
    ts.cell(i, 2, tok).number_format = "#,##0"
    ts.cell(i, 3, f"=B{i}*{price}/1000000").number_format = '"$"#,##0.000'
ts["A7"], ts["B7"], ts["C7"] = "Total", "=SUM(B2:B6)", "=SUM(C2:C6)"
ts["B7"].number_format, ts["C7"].number_format = "#,##0", '"$"#,##0.000'

# ---------------- Break-even ----------------
be = wb.create_sheet("Break-even Data")
header(be, 1, ["Requests n", "No cache", "5-minute cache", "1-hour cache"], [12, 12, 15, 14])
for n in range(1, 11):
    r = n + 1
    be.cell(r, 1, n)
    be.cell(r, 2, f"=A{r}")
    be.cell(r, 3, f"=1.25+(A{r}-1)*Scenario!$B$20")
    be.cell(r, 4, f"=2+(A{r}-1)*Scenario!$B$20")
    for c in "BCD":
        be[f"{c}{r}"].number_format = "0.00"
be["F2"], be["G2"] = "5-minute cache pays from request", "=INT((1.25-Scenario!B20)/(1-Scenario!B20))+1"
be["F3"], be["G3"] = "1-hour cache pays from request", "=INT((2-Scenario!B20)/(1-Scenario!B20))+1"
be.column_dimensions["F"].width = 32

# ---------------- Cache saving heatmap (conditional formatting) ----------------
hm = wb.create_sheet("Cache Savings")
hm["A1"] = "Money saved by prompt caching, %"
hm["A1"].font = Font(name="Calibri", bold=True, size=16, color="1F4E79")
hm["A2"] = "Rows: shared prefix (tokens). Columns: requests sharing it. Model and prices from Scenario."
hm["A2"].font = NOTE
hm["A3"], hm["C3"] = "New input / request", 200
hm["E3"], hm["G3"] = "Output / request", 300
hm["H3"], hm["I3"] = "Cache min.", 512
for c in ("C3", "G3", "I3"):
    hm[c].font = BLUE_IN
P = [512, 1000, 2000, 5000, 10000, 20000, 50000, 100000]
N = [1, 2, 3, 5, 10, 20, 50, 100]
hm["A5"] = "Prefix \\ Requests"
hm["A5"].fill, hm["A5"].font = HEAD, HEADF
for j, n in enumerate(N, 2):
    c = hm.cell(5, j, n)
    c.fill, c.font, c.alignment = HEAD, HEADF, Alignment(horizontal="center")
for i, p in enumerate(P, 6):
    c = hm.cell(i, 1, p)
    c.fill, c.font, c.number_format = HEAD, HEADF, "#,##0"
    for j in range(2, 2 + len(N)):
        col = chr(64 + j)
        nn, pp = f"{col}$5", f"$A{i}"
        nocache = f"{nn}*(({pp}+$C$3)*{P_IN}+$G$3*{P_OUT})"
        cache = f"(({pp}+$C$3)*{P_W5}+$G$3*{P_OUT})+({nn}-1)*({pp}*{P_R}+$C$3*{P_W5}+$G$3*{P_OUT})"
        x = hm.cell(i, j, f'=IF({pp}+$C$3<$I$3,"",1-({cache})/({nocache}))')
        x.number_format, x.alignment, x.border = "0%", Alignment(horizontal="center", vertical="center"), Border(thin, thin, thin, thin)
        x.font = Font(name="Calibri", bold=True, size=12)
    hm.row_dimensions[i].height = 26
hm.conditional_formatting.add(f"B6:{chr(64 + 1 + len(N))}{5 + len(P)}",
                              ColorScaleRule(start_type="num", start_value=-0.3, start_color="F8696B", mid_type="num", mid_value=0, mid_color="FFEB84", end_type="num", end_value=0.9, end_color="63BE7B"))
hm.column_dimensions["A"].width = 19
for j in range(2, 2 + len(N)):
    hm.column_dimensions[chr(64 + j)].width = 10
hm.page_setup.orientation = "landscape"
hm.sheet_properties.pageSetUpPr.fitToPage = True
hm.print_area = f"A1:{chr(64 + 1 + len(N))}{5 + len(P)}"

# ---------------- Models ----------------
md = wb.create_sheet("Models Data")
header(md, 1, ["Model", "No cache, $/month", "With caching, $/month", "Saving"], [20, 18, 20, 10])
tok = {k: f"SUM('Per Turn'!{c}2:INDEX('Per Turn'!{c}2:{c}41,{TURNS}))" for k, c in (("in", "F"), ("out", "E"), ("read", "L"), ("write", "M"))}
for i, m in enumerate(sorted(CURRENT, key=lambda m: PRICES[m][0], reverse=True), 2):
    md.cell(i, 1, m.replace("Claude ", ""))
    look = lambda col: f"INDEX(Prices!{col}$2:{col}${LASTP},MATCH(\"{m}\",Prices!$A$2:$A${LASTP},0))"
    md.cell(i, 2, f"=({tok['in']}*{look('B')}+{tok['out']}*{look('F')})/1000000*{CHATS}*{DAYS}").number_format = '"$"#,##0'
    md.cell(i, 3, f"=({tok['read']}*{look('E')}+{tok['write']}*{look('C')}+{tok['out']}*{look('F')})/1000000*{CHATS}*{DAYS}").number_format = '"$"#,##0'
    md.cell(i, 4, f"=1-C{i}/B{i}").number_format = "0%"

# ---------------- Offline job ----------------
of = wb.create_sheet("Offline Job Data")
header(of, 1, ["Option", "Input cost", "Output cost", "Total"], [18, 12, 12, 12])
of["F1"], of["G1"] = "Documents", 10000
of["F2"], of["G2"] = "Shared instructions (tokens)", 4000
of["F3"], of["G3"] = "Document (tokens)", 3000
of["F4"], of["G4"] = "Output per document", 500
for c in ("G1", "G2", "G3", "G4"):
    of[c].font = BLUE_IN
of.column_dimensions["F"].width = 28
inp_std = f"$G$1*($G$2+$G$3)*{P_IN}/1000000"
inp_cache = f"(($G$2+$G$3)*{P_W5}+($G$1-1)*($G$2*{P_R}+$G$3*{P_W5}))/1000000"
outc = f"$G$1*$G$4*{P_OUT}/1000000"
for i, (n, a, b) in enumerate([("Standard", inp_std, outc), ("Prompt caching", inp_cache, outc),
                               ("Batch API", f"0.5*{inp_std}", f"0.5*{outc}"), ("Batch + caching", f"0.5*{inp_cache}", f"0.5*{outc}")], 2):
    of.cell(i, 1, n)
    of.cell(i, 2, "=" + a).number_format = '"$"#,##0'
    of.cell(i, 3, "=" + b).number_format = '"$"#,##0'
    of.cell(i, 4, f"=B{i}+C{i}").number_format = '"$"#,##0'
of["A7"] = "Batch + caching assumes every request after the first hits the cache. Inside batches, hits are best effort: the docs report 30% to 98%."
of["A7"].font = NOTE

# ---------------- Overview tiles ----------------
ov = wb.create_sheet("Overview", 0)
ov.sheet_view.showGridLines = False
tiles = [("='Waterfall Data'!B7/'Waterfall Data'!B2-1", "+0%;-0%", "Monthly cost after five steps", "1F4E79", "A9D18E"),
         ("='Waterfall Data'!G3", "+0%;-0%", "From prompt caching alone", "1F4E79", "9DC3E6"),
         ("='Break-even Data'!G2", "0", "Requests for caching to pay", "1F4E79", "FFD966"),
         ("=Scenario!B18/Scenario!B14", '0"×"', "Output price vs input", "1F4E79", "F4B183")]
ov.row_dimensions[2].height, ov.row_dimensions[3].height, ov.row_dimensions[4].height = 14, 62, 30
for k, (f, fmt, lab, bg, fg) in enumerate(tiles):
    col = chr(66 + 2 * k)
    ov.column_dimensions[col].width = 26
    ov.column_dimensions[chr(67 + 2 * k)].width = 2
    a, b = ov[f"{col}3"], ov[f"{col}4"]
    a.value, a.number_format = f, fmt
    a.font, a.fill, a.alignment = Font(name="Calibri", bold=True, size=36, color=fg), PatternFill("solid", fgColor=bg), Alignment(horizontal="center", vertical="center")
    b.value, b.font, b.fill, b.alignment = lab, Font(name="Calibri", size=12, color="FFFFFF"), PatternFill("solid", fgColor=bg), Alignment(horizontal="center", vertical="center")
ov.column_dimensions["A"].width = 2
ov.page_setup.orientation = "landscape"
ov.sheet_properties.pageSetUpPr.fitToPage = True
ov.print_area = "A1:I5"

# ================= Charts =================
# 1 Waterfall (stacked columns with an invisible base)
ch = BarChart(); ch.type = "col"; ch.grouping = "stacked"; ch.overlap = 100; ch.gapWidth = 60
for col, color in (("C", None), ("D", "70AD47"), ("E", "FF0000"), ("F", "4472C4")):
    s = Series(Reference(wf, min_col=ord(col) - 64, min_row=2, max_row=7), title=wf[f"{col}1"].value)
    if color is None:
        s.graphicalProperties = GraphicalProperties(noFill=True)
        s.graphicalProperties.line.noFill = True
    else:
        fill(s, color)
        labels(s, '"$"#,##0')
        # Hide labels on the zero points of this series (layout follows the current values)
        from openpyxl.chart.label import DataLabel
        vals = [v for _, v in steps]
        mon = [vals[0], vals[1], vals[2], vals[3], vals[4], vals[4]]
        for k in range(6):
            if col == "D":
                show = 0 < k < 5 and mon[k] < mon[k - 1]
            elif col == "E":
                show = 0 < k < 5 and mon[k] > mon[k - 1]
            else:
                show = k in (0, 5)
            if not show:
                s.dLbls.dLbl.append(DataLabel(idx=k, showVal=False, showSerName=False, showCatName=False, showLegendKey=False, showPercent=False))
    ch.series.append(s)
ch.set_categories(Reference(wf, min_col=1, min_row=2, max_row=7))
ch.legend = None
ch.y_axis.numFmt = '"$"#,##0'
ch.y_axis.title = "USD per month"
style_chart(ch, "Monthly cost of 1,000 chats a day, step by step (Sonnet 5.5)")
chart_sheet("Chart Waterfall", ch, "Green = saving, red = extra cost. Steps add up from left to right.")

# 2 Doughnuts: tokens and cost
for name, col, title in (("Chart Tokens", 2, "Where the tokens go in one 20-turn chat"), ("Chart Cost", 3, "Where the money goes in one 20-turn chat")):
    d = DoughnutChart(holeSize=55)
    d.add_data(Reference(ts, min_col=col, min_row=1, max_row=6), titles_from_data=True)
    d.set_categories(Reference(ts, min_col=1, min_row=2, max_row=6))
    d.dataLabels = DataLabelList(); d.dataLabels.showPercent = True; d.dataLabels.showVal = False
    d.dataLabels.showCatName = False; d.dataLabels.showSerName = False; d.dataLabels.showLegendKey = False
    from openpyxl.chart.series import DataPoint
    for k, c in enumerate(["7030A0", "FFC000", "4472C4", "70AD47", "FF0000"]):
        pt_ = DataPoint(idx=k); pt_.graphicalProperties = GraphicalProperties(solidFill=c); d.series[0].dPt.append(pt_)
    d.legend.position = "r"
    style_chart(d, title, 18, 12)
    chart_sheet(name, d)

# 3 Stacked area: cost of each turn
ar = AreaChart(); ar.grouping = "stacked"
for col, c in zip("GHIJ", ["7030A0", "4472C4", "70AD47", "FF0000"]):
    s = Series(Reference(pt, min_col=ord(col) - 64, min_row=1, max_row=41), title_from_data=True)
    fill(s, c); ar.series.append(s)
ar.set_categories(Reference(pt, min_col=1, min_row=2, max_row=41))
ar.y_axis.title = "USD per 1,000 chats"; ar.x_axis.title = "Turn"; ar.y_axis.numFmt = '"$"#,##0'
ar.legend.position = "b"
style_chart(ar, "Each turn resends the whole history, so every turn costs more")
chart_sheet("Chart Per Turn", ar)

# 4 Lines: cumulative cost by strategy
ln = LineChart()
for col, c in zip("OVPWX", ["595959", "FFC000", "4472C4", "FF0000", "70AD47"]):
    s = Series(Reference(pt, min_col=ord(col) - 64, min_row=1, max_row=41), title_from_data=True)
    fill(s, c, line=True); s.marker.symbol = "none"; ln.series.append(s)
ln.set_categories(Reference(pt, min_col=1, min_row=2, max_row=41))
ln.y_axis.title = "Cumulative USD per 1,000 chats"; ln.x_axis.title = "Turn"; ln.y_axis.numFmt = '"$"#,##0'
ln.x_axis.tickLblSkip = 5
ln.legend.position = "b"
style_chart(ln, "Over 40 turns: trimming history breaks the cache")
chart_sheet("Chart Strategies", ln, "Sliding window keeps the last 6 turns. Compaction summarizes every 10 turns.")

# 5 Break-even lines with markers
bl = LineChart()
for col, c, sym in zip("BCD", ["595959", "4472C4", "7030A0"], ["circle", "square", "triangle"]):
    s = Series(Reference(be, min_col=ord(col) - 64, min_row=1, max_row=11), title_from_data=True)
    fill(s, c, line=True); s.marker.symbol = sym; s.marker.size = 7
    s.marker.graphicalProperties = GraphicalProperties(solidFill=c); s.marker.graphicalProperties.line.solidFill = c
    bl.series.append(s)
bl.set_categories(Reference(be, min_col=1, min_row=2, max_row=11))
bl.x_axis.title = "Requests sharing the same prefix (n)"; bl.y_axis.title = "Prefix cost (1 = one uncached prefix)"
bl.legend.position = "b"
style_chart(bl, "When does caching pay off? 5-minute cache from request 2, 1-hour from request 3")
chart_sheet("Chart Break-even", bl)

# 6 Clustered bars by model (log axis)
bc = BarChart(); bc.type = "bar"; bc.gapWidth = 50
for col, c in (("B", "A5A5A5"), ("C", "70AD47")):
    s = Series(Reference(md, min_col=ord(col) - 64, min_row=1, max_row=5), title_from_data=True)
    fill(s, c); labels(s, '"$"#,##0', "outEnd"); bc.series.append(s)
bc.set_categories(Reference(md, min_col=1, min_row=2, max_row=5))
bc.x_axis.scaling.orientation = "maxMin"
bc.y_axis.scaling.logBase = 10; bc.y_axis.numFmt = '"$"#,##0'; bc.y_axis.title = "USD per month (log scale)"
bc.legend.position = "b"
style_chart(bc, "Same chat workload on each current model")
chart_sheet("Chart Models", bc)

# 7 Bubble chart: price map
bb = BubbleChart(); bb.style = 2; bb.bubbleScale = 60
seen = {}
for i, (m, v) in enumerate(PRICES.items(), 2):
    seen.setdefault((v[0], v[4]), []).append(i)
for k, ((xi, yo), rws) in enumerate(seen.items()):
    i = rws[0]
    names_ = " / ".join(pr.cell(r, 1).value.replace("Claude ", "") for r in rws)
    s = Series(values=Reference(pr, min_col=6, min_row=i), xvalues=Reference(pr, min_col=2, min_row=i), zvalues=Reference(pr, min_col=5, min_row=i), title=names_)
    cur = any(pr.cell(r, 1).value in CURRENT for r in rws)
    s.graphicalProperties = GraphicalProperties(solidFill=OFFICE[k % 8])
    bb.series.append(s)
bb.x_axis.scaling.logBase = 10; bb.y_axis.scaling.logBase = 10
bb.x_axis.scaling.min, bb.x_axis.scaling.max = 0.05, 50
bb.y_axis.scaling.min, bb.y_axis.scaling.max = 0.2, 200
bb.x_axis.title = "Input price, $ per million tokens (log)"; bb.y_axis.title = "Output price, $ per million tokens (log)"
bb.x_axis.numFmt = bb.y_axis.numFmt = '"$"0.##'
bb.legend.position = "r"
style_chart(bb, "Claude price map (bubble size = cache read price)")
chart_sheet("Chart Price Map", bb)

# 8 Stacked columns: offline job
oc = BarChart(); oc.type = "col"; oc.grouping = "stacked"; oc.overlap = 100; oc.gapWidth = 70
for col, c in (("B", "4472C4"), ("C", "ED7D31")):
    s = Series(Reference(of, min_col=ord(col) - 64, min_row=1, max_row=5), title_from_data=True)
    fill(s, c); labels(s, '"$"#,##0'); oc.series.append(s)
oc.set_categories(Reference(of, min_col=1, min_row=2, max_row=5))
oc.y_axis.numFmt = '"$"#,##0'; oc.y_axis.title = "USD for the whole job"
oc.legend.position = "b"
style_chart(oc, "Offline job, 10,000 documents: batch halves everything")
chart_sheet("Chart Offline Job", oc, "Batch + caching assumes every request after the first hits the cache. Real batch hit rates are 30% to 98% (Anthropic docs).")

order = ["Overview", "Scenario", "Prices", "Chart Waterfall", "Chart Tokens", "Chart Cost", "Chart Per Turn", "Chart Strategies",
         "Chart Break-even", "Cache Savings", "Chart Models", "Chart Price Map", "Chart Offline Job",
         "Per Turn", "Waterfall Data", "Token Share Data", "Break-even Data", "Models Data", "Offline Job Data"]
wb._sheets = [wb[n] for n in order]
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if c.font and c.font.name != "Calibri":
                f = c.font
                c.font = Font(name="Calibri", bold=f.bold, italic=f.italic, size=f.size, color=f.color)
target = sys.argv[1] if len(sys.argv) > 1 else "excel/claude_token_costs.xlsx"
wb.save(target)
print("saved", target)
