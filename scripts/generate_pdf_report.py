import os
import markdown_it
from mdit_py_plugins.anchors import anchors_plugin
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_MD_PATH = os.path.join(BASE_DIR, 'docs', 'MASTER_REPORT.md')
OUTPUT_PDF_PATH_A = os.path.join(BASE_DIR, 'Project_24i-3108_24i-3107_24i-3074_A.pdf')
if os.path.exists(os.path.join(BASE_DIR, 'Project_24i-3108_24i-3074_24i-3107.pdf')):
    os.remove(os.path.join(BASE_DIR, 'Project_24i-3108_24i-3074_24i-3107.pdf'))

with open(REPORT_MD_PATH, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Configure Markdown parser with table support
md = markdown_it.MarkdownIt('commonmark', {'html': True, 'breaks': True}).enable('table')

# Convert Markdown to HTML
html_body = md.render(md_content)

# Professional CSS template for printable PDF
full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SE3002 Final Project Report - pretix Quality Engineering</title>
<!-- KaTeX for crisp mathematical formulas -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {{
        delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}}
        ]
    }});"></script>

<style>
    @page {{
        size: A4;
        margin: 20mm 15mm 20mm 15mm;
        @bottom-right {{
            content: "Page " counter(page) " of " counter(pages);
            font-size: 8pt;
            color: #6c757d;
        }}
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.55;
        color: #212529;
        margin: 0;
        padding: 0;
    }}
    h1 {{
        color: #0b3954;
        font-size: 20pt;
        border-bottom: 2px solid #0b3954;
        padding-bottom: 6px;
        margin-top: 0;
        margin-bottom: 12px;
    }}
    h2 {{
        color: #087e8b;
        font-size: 14pt;
        border-bottom: 1px solid #dee2e6;
        padding-bottom: 4px;
        margin-top: 22px;
        margin-bottom: 10px;
        page-break-after: avoid;
    }}
    h3 {{
        color: #2b2d42;
        font-size: 11.5pt;
        margin-top: 16px;
        margin-bottom: 8px;
        page-break-after: avoid;
    }}
    p, ul, ol {{
        margin-top: 0;
        margin-bottom: 10px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        margin-bottom: 14px;
        font-size: 8.5pt;
        page-break-inside: auto;
    }}
    tr {{
        page-break-inside: avoid;
        page-break-after: auto;
    }}
    th {{
        background-color: #f1f4f8;
        color: #1a252f;
        font-weight: 600;
        border: 1px solid #ced4da;
        padding: 6px 8px;
        text-align: left;
    }}
    td {{
        border: 1px solid #dee2e6;
        padding: 5px 8px;
        vertical-align: top;
    }}
    tr:nth-child(even) td {{
        background-color: #fcfdfe;
    }}
    code {{
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
        font-size: 8.5pt;
        background-color: #f4f5f7;
        padding: 1px 4px;
        border-radius: 3px;
        border: 1px solid #e1e4e8;
    }}
    pre {{
        background-color: #f6f8fa;
        border: 1px solid #e1e4e8;
        border-radius: 4px;
        padding: 10px;
        font-size: 8pt;
        overflow-x: auto;
        page-break-inside: avoid;
    }}
    pre code {{
        background-color: transparent;
        padding: 0;
        border: none;
    }}
    blockquote {{
        margin: 12px 0;
        padding: 8px 14px;
        border-left: 4px solid #087e8b;
        background-color: #f0f7f8;
        font-size: 9pt;
    }}
    hr {{
        border: 0;
        border-top: 1px solid #e9ecef;
        margin: 16px 0;
    }}
    .footer-text {{
        font-size: 8pt;
        color: #6c757d;
        text-align: center;
        margin-top: 30px;
        border-top: 1px solid #dee2e6;
        padding-top: 8px;
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

temp_html = os.path.join(BASE_DIR, 'temp_report.html')
with open(temp_html, 'w', encoding='utf-8') as f:
    f.write(full_html)

print("Launching Playwright Chromium to render PDF...")
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file:///{temp_html.replace(os.sep, '/')}", wait_until="networkidle")
    # Wait for KaTeX rendering
    page.wait_for_timeout(1500)
    
    # Generate A-section named PDF
    page.pdf(
        path=OUTPUT_PDF_PATH_A,
        format='A4',
        print_background=True,
        margin={
            'top': '20mm',
            'bottom': '20mm',
            'left': '15mm',
            'right': '15mm'
        },
        display_header_footer=True,
        header_template='<div style="font-size: 7pt; color: #888; width: 100%; text-align: right; padding-right: 15mm;">SE3002 SQE Final Engineering Report - pretix v2026.9.3</div>',
        footer_template='<div style="font-size: 7pt; color: #888; width: 100%; text-align: center;">Page <span class="pageNumber"></span> of <span class="totalPages"></span> | FAST-NUCES Islamabad (Fall 2026)</div>'
    )
    
    browser.close()

if os.path.exists(temp_html):
    os.remove(temp_html)

print("Generated:", OUTPUT_PDF_PATH_A, f"({os.path.getsize(OUTPUT_PDF_PATH_A) / 1024:.1f} KB)")
