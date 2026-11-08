"""Renders the workbook's Excel charts to PNG with LibreOffice (for the README)."""
import pathlib, subprocess, sys, tempfile
from openpyxl import load_workbook
from PIL import Image, ImageChops

SRC = pathlib.Path("excel/claude_token_costs.xlsx")
OUT = pathlib.Path("results")
PAGES = {"Overview": "overview.png", "Chart Waterfall": "waterfall.png", "Chart Tokens": "donut_tokens.png", "Chart Cost": "donut_cost.png",
         "Chart Per Turn": "cost_per_turn.png", "Chart Strategies": "strategies_over_turns.png", "Chart Break-even": "cache_breakeven.png",
         "Cache Savings": "caching_heatmap.png", "Chart Models": "model_costs.png", "Chart Price Map": "price_map.png", "Chart Offline Job": "batch_and_cache.png"}
tmp = pathlib.Path(tempfile.mkdtemp())
wb = load_workbook(SRC)
for ws in wb.worksheets:
    ws.sheet_state = "visible" if ws.title in PAGES else "hidden"
wb.active = wb.sheetnames.index("Overview")
copy = tmp / "render.xlsx"
wb.save(copy)
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(copy)], check=True, capture_output=True, timeout=180)
subprocess.run(["pdftoppm", "-r", "200", "-png", str(tmp / "render.pdf"), str(tmp / "p")], check=True)
pages = sorted(tmp.glob("p-*.png"), key=lambda p: int(p.stem.split("-")[1]))
visible = [n for n in wb.sheetnames if n in PAGES]
print(len(pages), "pages for", len(visible), "sheets")
if len(pages) != len(visible):
    sys.exit("page count mismatch")
for name, page in zip(visible, pages):
    im = Image.open(page).convert("RGB")
    bg = Image.new("RGB", im.size, "white")
    box = ImageChops.difference(im, bg).point(lambda v: 255 if v > 12 else 0).getbbox()
    pad = 24
    im = im.crop((max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, im.width), min(box[3] + pad, im.height)))
    im.save(OUT / PAGES[name])
    print(name, "->", PAGES[name], im.size)
