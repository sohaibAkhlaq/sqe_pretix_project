import html
import os
import re
import pypdf
import markdown_it
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_MD_PATH = os.path.join(BASE_DIR, 'docs', 'MASTER_REPORT.md')
OUTPUT_PDF_PATH_C = os.path.join(BASE_DIR, 'Project_24i-3108_24i-3107_24i-3074_C.pdf')

LEGACY_PDF = os.path.join(BASE_DIR, 'Project_24i-3108_24i-3074_24i-3107.pdf')
if os.path.exists(LEGACY_PDF):
    os.remove(LEGACY_PDF)


def preprocess_markdown(md_text: str) -> str:
    """Strip MASTER_REPORT.md front-matter header/TOC so formal Cover/Memo/TOC replace it cleanly."""
    # Remove everything before "## 1. Executive Summary & System Architecture"
    m = re.search(r'^## 1\. Executive Summary', md_text, flags=re.MULTILINE)
    body = md_text[m.start():] if m else md_text
    # Remove trailing "## Sign-Off & Attestation" if present (moved to Memo/Appendix)
    body = re.sub(r'\n---\s*\n## Sign-Off & Attestation[\s\S]*$', '', body)
    # Strip GitHub alert markers like "> [!NOTE]" / "> [!IMPORTANT]" while keeping text
    body = re.sub(r'^>\s*\[!(NOTE|IMPORTANT|WARNING|TIP|CAUTION)\]\s*\n?', '', body, flags=re.MULTILINE)
    return body


def build_cover_html() -> str:
    return """
    <div class="cover-page">
      <div class="cover-logo"><img src="docs/assets/fast_nuces_logo.jpg" style="width: 0.9in; height: auto;" alt="FAST-NUCES Logo"/></div>
      <div class="cover-uni">
        <div>NATIONAL UNIVERSITY OF COMPUTER &amp; EMERGING SCIENCES</div>
        <div>FAST SCHOOL OF COMPUTING, ISLAMABAD CAMPUS</div>
      </div>
      <div class="cover-rule">________________________________________________________________________________</div>
      <div class="cover-title">
        <div>AUTOMATED QUALITY ENGINEERING &amp;</div>
        <div>TESTING OF PRETIX TICKETING</div>
        <div>PLATFORM (SE3002 FINAL PROJECT)</div>
      </div>
      <div class="cover-rule">________________________________________________________________________________</div>
      <table class="cover-table">
        <thead>
          <tr>
            <th>Consultant / Evaluator</th>
            <th>Student Roll #</th>
            <th>Assigned Research &amp; Technical Role</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Sohaib</td>
            <td>24i-3108</td>
            <td>Area 1 Lead: Static Analysis, White-Box Unit Testing, AST Mutation &amp; CI Quality Gate</td>
          </tr>
          <tr>
            <td>M. Hasaam</td>
            <td>24i-3107</td>
            <td>Area 2 Lead: OpenAPI 3.0, Test Data Generation, API Integration, k6 &amp; Chaos Recovery</td>
          </tr>
          <tr>
            <td>Shaiman</td>
            <td>24i-3074</td>
            <td>Area 3 Lead: Use Cases, Playwright E2E, Usability/Accessibility &amp; Defensive Security</td>
          </tr>
        </tbody>
      </table>
      <div class="cover-meta">
        <div>Course Instructor: SE3002 Software Quality Engineering Faculty (Section C)</div>
        <div>Date of Submission: November 29, 2026</div>
      </div>
    </div>
    """


def build_front_matter_html(toc_entries) -> str:
    rows = []
    for item in toc_entries:
        lvl = item.get('level', 1)
        cls = f"leader-row leader-lvl-{lvl}"
        label = html.escape(item['title'])
        pg = html.escape(str(item.get('page', '—')))
        rows.append(
            f'<div class="{cls}"><span class="leader-text">{label}</span>'
            f'<span class="leader-dots"></span><span class="leader-page">{pg}</span></div>'
        )
    return f"""
    <div class="toc-page">
      <div class="front-heading">TABLE OF CONTENTS</div>
      <div class="leader-list">{chr(10).join(rows)}</div>
    </div>
    """


def build_references_html() -> str:
    return """
    <div class="level1-section">
      <h1 class="l1-heading">19. REFERENCES</h1>
      <div class="apa-refs">
        <p>Basili, V. R., Caldiera, G., and Rombach, H. D. (1994). The Goal Question Metric approach. In <em>Encyclopedia of Software Engineering</em> (pp. 528–532). Wiley.</p>
        <p>Deque Systems. (2024). <em>axe-core: Accessibility engine for automated Web UI testing (Version 4.9.1)</em> [Computer software]. https://github.com/dequelabs/axe-core</p>
        <p>Google Chrome Developers. (2025). <em>Google Lighthouse automated auditing tool (Version 13.6.0)</em> [Computer software]. https://developer.chrome.com/docs/lighthouse</p>
        <p>Grafana Labs. (2026). <em>Grafana k6 OSS: Modern load testing tool (Version 2.2.0)</em> [Computer software]. https://k6.io/</p>
        <p>IEEE. (2008). <em>IEEE Std 829-2008: Standard for software and system test documentation</em>. Institute of Electrical and Electronics Engineers.</p>
        <p>ISO/IEC/IEEE. (2013). <em>ISO/IEC/IEEE 29119-2: Software and systems engineering — Software testing — Part 2: Test processes</em>. International Organization for Standardization.</p>
        <p>OWASP Foundation. (2026). <em>OWASP Zed Attack Proxy (ZAP) (Version 2.17.0)</em> [Computer software]. https://www.zaproxy.org/</p>
        <p>pretix. (2026). <em>pretix: Reinventing ticket sales for conferences, festivals, exhibitions (Version 2026.9.3, Commit db000dc)</em> [Computer software]. https://github.com/pretix/pretix</p>
        <p>Python Packaging Authority. (2026). <em>pip-audit: Tool for scanning Python environments for known vulnerabilities (Version 2.10.1)</em> [Computer software]. https://github.com/pypa/pip-audit</p>
        <p>SonarSource. (2025). <em>SonarQube Community Edition (Version 9.9.8 LTS)</em> [Computer software]. https://www.sonarsource.com/products/sonarqube/</p>
      </div>
    </div>
    """


def postprocess_body_html(raw_html: str):
    """
    Applies exact formal academic rules:
    - Level 1 (<h2> in MD -> <h1> class l1-heading, uppercase, new page)
    - Level 2 (<h3> in MD -> <h2> class l2-heading, title case)
    - Level 3 (<h4> in MD -> <h3> class l3-heading, bold italic)
    - Converts mermaid <pre><code class="language-mermaid"> to <div class="mermaid">
    - Adds sequential Table N: captions BELOW every table, repeating thead
    - Adds sequential Figure N: captions BELOW every image/figure div
    - Extracts heading/table/figure anchors for 2-pass TOC/LOT/LOF page lookup
    """
    # Convert mermaid code blocks to <div class="mermaid">
    raw_html = re.sub(
        r'<pre><code class="language-mermaid">([\s\S]*?)</code></pre>',
        lambda m: f'<div class="figure-block"><div class="mermaid">{html.unescape(m.group(1))}</div></div>',
        raw_html,
    )

    # Remove old <p><strong>Figure ...</strong></p> blocks above <img> and attach caption BELOW
    fig_counter = 0
    figure_entries = []

    def replace_fig_div(m):
        nonlocal fig_counter
        block = m.group(0)
        cap_m = re.search(r'<p><strong>(Figure[^<]*)</strong></p>', block)
        img_m = re.search(r'<img\s+[^>]*>', block)
        if not img_m:
            return block
        fig_counter += 1
        raw_cap = html.unescape(cap_m.group(1)) if cap_m else f"Figure {fig_counter}"
        clean_cap = re.sub(r'^Figure\s+[0-9.a-zA-Z]+:\s*', '', raw_cap).strip()
        clean_cap = clean_cap.replace(' & ', ' and ')
        full_cap = f"Figure {fig_counter}: {clean_cap}"
        fid = f"fig-{fig_counter}"
        figure_entries.append({'id': fid, 'title': full_cap})
        img_tag = re.sub(r'style="[^"]*"', '', img_m.group(0))
        img_tag = re.sub(r'width="[^"]*"', '', img_tag)
        return (
            f'<div class="figure-block" id="{fid}">'
            f'{img_tag}'
            f'<div class="caption-below">{html.escape(full_cap)}</div>'
            f'</div>'
        )

    raw_html = re.sub(r'<div style="text-align: center;[^"]*">[\s\S]*?</div>', replace_fig_div, raw_html)

    # Number standalone mermaid figures too
    def replace_mermaid_fig(m):
        nonlocal fig_counter
        fig_counter += 1
        fid = f"fig-{fig_counter}"
        full_cap = f"Figure {fig_counter}: System / Verification Workflow Diagram"
        figure_entries.append({'id': fid, 'title': full_cap})
        return (
            f'<div class="figure-block" id="{fid}">'
            f'{m.group(1)}'
            f'<div class="caption-below">{html.escape(full_cap)}</div>'
            f'</div>'
        )

    raw_html = re.sub(r'<div class="figure-block">(<div class="mermaid">[\s\S]*?</div>)</div>', replace_mermaid_fig, raw_html)

    # Number every <table> and place "Table N: Caption" BELOW the table
    tbl_counter = 0
    table_entries = []
    # Track nearest preceding heading for contextual table captions
    tokens = re.split(r'(<h[234][^>]*>[\s\S]*?</h[234]>|<table>[\s\S]*?</table>)', raw_html)
    last_heading = "Summary Data"
    out_parts = []
    for tok in tokens:
        if re.match(r'^<h[234]', tok):
            last_heading = re.sub(r'<[^>]+>', '', tok).strip()
            last_heading = re.sub(r'\s*\(Rubric Component[^)]*\)', '', last_heading).strip()
            out_parts.append(tok)
        elif tok.startswith('<table>'):
            tbl_counter += 1
            tid = f"tbl-{tbl_counter}"
            cap_text = html.unescape(re.sub(r'^\d+(?:\.\d+)*\.?\s*', '', last_heading).strip())
            cap_text = cap_text.replace(' & ', ' and ')
            full_cap = f"Table {tbl_counter}: {cap_text}"
            table_entries.append({'id': tid, 'title': full_cap})
            # Mark numeric cells for centering
            tbl_html = tok
            tbl_html = tbl_html.replace('<table>', f'<table class="formal-table" id="{tid}">', 1)
            out_parts.append(
                f'<div class="table-wrapper">'
                f'{tbl_html}'
                f'<div class="caption-below">{html.escape(full_cap)}</div>'
                f'</div>'
            )
        else:
            out_parts.append(tok)
    raw_html = ''.join(out_parts)

    # Extract and transform headings (H2 -> Level 1 new page, H3 -> Level 2, H4 -> Level 3)
    toc_entries = []
    l1_idx = 0
    l2_idx = 0
    l3_idx = 0

    def transform_heading(m):
        nonlocal l1_idx, l2_idx, l3_idx
        tag = m.group(1)
        text = html.unescape(re.sub(r'<[^>]+>', '', m.group(2)).strip())
        if tag == 'h2':
            l1_idx += 1
            l2_idx = 0
            l3_idx = 0
            clean = re.sub(r'^\d+\.\s*', '', text)
            clean = re.sub(r'\s*\(Rubric Component[^)]*\)', '', clean).strip().upper()
            clean = clean.replace(' & ', ' AND ')
            title = f"{l1_idx}. {clean}"
            hid = f"sec-{l1_idx}"
            toc_entries.append({'id': hid, 'level': 1, 'title': title})
            prefix = '</div>' if l1_idx > 1 else ''
            return f'{prefix}<div class="level1-section"><h1 class="l1-heading" id="{hid}">{html.escape(title)}</h1>'
        elif tag == 'h3':
            l2_idx += 1
            l3_idx = 0
            clean = re.sub(r'^\d+\.\d+\s*', '', text)
            clean = re.sub(r'\s*\(Rubric Component[^)]*\)', '', clean).strip().replace(' & ', ' and ')
            title = f"{l1_idx}.{l2_idx} {clean}"
            hid = f"sec-{l1_idx}-{l2_idx}"
            toc_entries.append({'id': hid, 'level': 2, 'title': title})
            return f'<h2 class="l2-heading" id="{hid}">{html.escape(title)}</h2>'
        else:
            l3_idx += 1
            clean = re.sub(r'^\d+(?:\.\d+)*\s*', '', text)
            clean = re.sub(r'\s*\(Rubric Component[^)]*\)', '', clean).strip().rstrip(':').replace(' & ', ' and ')
            title = f"{l1_idx}.{l2_idx}.{l3_idx} {clean}"
            hid = f"sec-{l1_idx}-{l2_idx}-{l3_idx}"
            toc_entries.append({'id': hid, 'level': 3, 'title': title})
            return f'<h3 class="l3-heading" id="{hid}">{html.escape(title)}</h3>'

    raw_html = re.sub(r'<(h[234])[^>]*>([\s\S]*?)</\1>', transform_heading, raw_html)
    if l1_idx > 0:
        raw_html += '</div>'

    return raw_html, toc_entries, table_entries, figure_entries


def build_css() -> str:
    return """
    @page {
        size: letter portrait;
        margin: 1in;
    }
    * {
        box-sizing: border-box;
        color: #000000 !important;
        font-family: "Times New Roman", Times, serif !important;
    }
    body {
        font-family: "Times New Roman", Times, serif;
        font-size: 11pt;
        line-height: 1.15;
        color: #000000;
        background: #ffffff;
        margin: 0;
        padding: 0;
        text-align: justify;
    }
    p {
        margin-top: 0;
        margin-bottom: 6pt;
        text-align: justify;
    }
    /* Cover Page */
    .cover-page {
        position: relative;
        width: 100%;
        min-height: 8.8in;
        padding-top: 0.2in;
        page-break-after: always;
    }
    .cover-logo {
        position: absolute;
        top: 0;
        right: 0;
        width: 0.9in;
    }
    .cover-uni {
        text-align: center;
        font-size: 12pt;
        font-weight: bold;
        text-transform: uppercase;
        margin-top: 1.1in;
        line-height: 1.3;
    }
    .cover-rule {
        text-align: center;
        font-size: 11pt;
        margin: 12pt 0;
        overflow: hidden;
        white-space: nowrap;
    }
    .cover-title {
        text-align: center;
        font-size: 18pt;
        font-weight: bold;
        font-style: italic;
        text-transform: uppercase;
        line-height: 1.25;
        margin: 10pt 0;
    }
    .cover-table {
        width: 75%;
        margin: 24pt auto;
        border-collapse: collapse;
        font-size: 11pt;
    }
    .cover-table th, .cover-table td {
        border: 0.5pt solid #000000;
        padding: 4pt 6pt;
        background: #ffffff;
    }
    .cover-table th {
        font-weight: bold;
        text-align: center;
    }
    .cover-table td {
        text-align: left;
    }
    .cover-meta {
        text-align: center;
        font-size: 11pt;
        font-weight: bold;
        margin-top: 24pt;
        line-height: 1.5;
    }
    /* Front Matter */
    .front-matter-page {
        page-break-after: always;
    }
    .toc-page {
        page-break-after: always;
    }
    .memo-heading, .exec-summary-heading, .front-heading {
        font-size: 13pt;
        font-weight: bold;
        text-transform: uppercase;
        text-align: left;
        margin-top: 14pt;
        margin-bottom: 6pt;
    }
    .memo-heading { margin-top: 0; }
    .black-rule {
        border: 0;
        border-top: 0.75pt solid #000000;
        margin: 4pt 0 10pt 0;
    }
    .memo-block {
        margin-bottom: 12pt;
    }
    .memo-row {
        display: grid;
        grid-template-columns: 1in 1fr;
        margin-bottom: 4pt;
        text-align: left;
    }
    .memo-label {
        font-weight: bold;
    }
    .sig-block {
        display: flex;
        justify-content: space-between;
        margin-top: 22pt;
        margin-bottom: 18pt;
        gap: 14pt;
    }
    .sig-item {
        flex: 1;
        font-size: 10pt;
        text-align: left;
    }
    .sig-line {
        border-bottom: 0.75pt solid #000000;
        height: 18pt;
        margin-bottom: 4pt;
    }
    .exec-list {
        padding-left: 0.25in;
        margin: 6pt 0;
    }
    .exec-list li {
        margin-bottom: 6pt;
    }
    /* Dot Leaders */
    .leader-list {
        margin-top: 4pt;
    }
    .leader-row {
        display: flex;
        align-items: baseline;
        margin-bottom: 3pt;
        font-size: 10.5pt;
        text-align: left;
    }
    .leader-lvl-1 {
        font-weight: bold;
        text-transform: uppercase;
        margin-top: 4pt;
    }
    .leader-lvl-2 {
        font-weight: normal;
        padding-left: 0.3in;
    }
    .leader-lvl-3 {
        font-weight: normal;
        padding-left: 0.6in;
    }
    .leader-dots {
        flex: 1;
        border-bottom: 1pt dotted #000000;
        margin: 0 5pt;
    }
    .leader-page {
        font-weight: normal;
        white-space: nowrap;
    }
    /* Headings */
    .level1-section {
        page-break-before: always;
    }
    h1.l1-heading {
        font-size: 13pt;
        font-weight: bold;
        text-transform: uppercase;
        text-align: left;
        margin-top: 18pt;
        margin-bottom: 8pt;
        page-break-after: avoid;
    }
    h2.l2-heading {
        font-size: 12pt;
        font-weight: bold;
        text-align: left;
        margin-top: 12pt;
        margin-bottom: 4pt;
        page-break-after: avoid;
    }
    h3.l3-heading {
        font-size: 11pt;
        font-weight: bold;
        font-style: italic;
        text-align: left;
        margin-top: 10pt;
        margin-bottom: 4pt;
        page-break-after: avoid;
    }
    /* Lists */
    ul {
        list-style-type: square;
        padding-left: 0.25in;
        margin: 0 0 6pt 0;
    }
    ol {
        padding-left: 0.25in;
        margin: 0 0 6pt 0;
    }
    li {
        margin-bottom: 3pt;
        text-align: justify;
    }
    /* Tables */
    .table-wrapper {
        margin: 10pt 0 12pt 0;
        width: 100%;
    }
    table.formal-table {
        width: 100%;
        table-layout: fixed;
        border-collapse: collapse;
        font-size: 9pt;
        background: #ffffff;
    }
    table.formal-table thead {
        display: table-header-group;
    }
    table.formal-table tr {
        page-break-inside: avoid;
    }
    table.formal-table th, table.formal-table td {
        border: 0.5pt solid #000000;
        padding: 3pt;
        background: #ffffff !important;
        vertical-align: top;
        word-wrap: break-word;
        overflow-wrap: anywhere;
        word-break: break-word;
    }
    table.formal-table th {
        font-weight: bold;
        text-align: center;
    }
    table.formal-table td {
        text-align: left;
    }
    table.formal-table td.num-cell {
        text-align: center;
    }
    .caption-below {
        font-size: 10pt;
        font-weight: bold;
        text-align: center;
        margin-top: 4pt;
        margin-bottom: 8pt;
        page-break-before: avoid;
    }
    /* Figures (Original Colors Restored) */
    .figure-block {
        text-align: center;
        margin: 10pt 0 12pt 0;
        page-break-inside: avoid;
    }
    .figure-block img {
        max-width: 100%;
        max-height: 4.5in;
        width: auto;
        height: auto;
        border: 0.5pt solid #000000;
        display: block;
        margin: 0 auto;
    }
    .mermaid {
        text-align: center;
        margin: 0 auto;
    }
    /* Code & Blockquotes (Zero Boxes Around Text) */
    code {
        font-size: 10pt;
        font-weight: bold;
        background: transparent;
        border: none;
        padding: 0;
    }
    pre {
        border: none;
        background: transparent;
        padding: 4pt 0 4pt 12pt;
        font-size: 8.5pt;
        white-space: pre-wrap;
        word-break: break-word;
        page-break-inside: avoid;
    }
    pre code {
        border: none;
        padding: 0;
        font-weight: normal;
    }
    blockquote {
        margin: 6pt 0 6pt 0.25in;
        padding-left: 8pt;
        border-left: none;
    }
    /* References */
    .apa-refs p {
        padding-left: 0.5in;
        text-indent: -0.5in;
        line-height: 1.0;
        margin-bottom: 6pt;
        text-align: left;
    }
    .appendix-item {
        page-break-before: always;
    }
    """


def render_html_document(cover_html, front_html, body_html, refs_html) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SE3002 Final Project Report - pretix v2026.9.3</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {{
        delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}}
        ]
    }});"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>{build_css()}</style>
</head>
<body>
{cover_html}
{front_html}
{body_html}
{refs_html}
<script>
  if (window.mermaid) {{
    mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
  }}
  // Center numeric-only table cells
  document.querySelectorAll('table.formal-table td').forEach(td => {{
    const txt = td.innerText.trim();
    if (/^[0-9.,%+-]+(\\s*(ms|s|hrs|h|B|KB|%|\\/\\s*[0-9.,]+))?$/.test(txt)) {{
      td.classList.add('num-cell');
    }}
  }});
</script>
</body>
</html>"""


def find_pages_for_titles(pdf_path: str, entries: list) -> list:
    reader = pypdf.PdfReader(pdf_path)
    page_texts = [(i + 1, re.sub(r'\s+', ' ', (p.extract_text() or '')).lower()) for i, p in enumerate(reader.pages)]
    # Find the first body page (after TABLE OF CONTENTS)
    body_start_idx = 3
    for i, (pno, ptxt) in enumerate(page_texts):
        if i >= 2 and '1. executive summary and system architecture' in ptxt and 'table of contents' not in ptxt:
            body_start_idx = i
            break
    for entry in entries:
        needle = re.sub(r'\s+', ' ', entry['title']).strip().lower()
        short_needle = needle[:48]
        found = None
        for pno, ptxt in page_texts[body_start_idx:]:
            if short_needle in ptxt:
                found = pno
                break
        entry['page'] = found if found is not None else '—'
    return entries


def main():
    with open(REPORT_MD_PATH, 'r', encoding='utf-8') as f:
        md_content = preprocess_markdown(f.read())

    # Protect $$...$$ and $...$ math blocks from Markdown '_' italics mangling
    math_blocks = []
    def _stash_math(m):
        idx = len(math_blocks)
        math_blocks.append(m.group(0))
        return f"@@MATHBLOCK{idx}@@"
    md_protected = re.sub(r'\$\$[\s\S]*?\$\$|\$[^\n$]+?\$', _stash_math, md_content)

    md = markdown_it.MarkdownIt('commonmark', {'html': True, 'breaks': True}).enable('table')
    raw_html = md.render(md_protected)
    for idx, mb in enumerate(math_blocks):
        raw_html = raw_html.replace(f"@@MATHBLOCK{idx}@@", mb)
    body_html, toc_entries, table_entries, figure_entries = postprocess_body_html(raw_html)

    # Add References to TOC (Appendices removed)
    toc_entries.append({'id': 'sec-19', 'level': 1, 'title': '19. REFERENCES'})

    cover_html = build_cover_html()
    header_tpl = (
        '<div style="font-family: \'Times New Roman\', Times, serif; font-size: 9pt; color: #000000; '
        'width: 100%; margin: 0 1in; text-align: right; border-bottom: 0.5pt solid #000000; padding-bottom: 3pt;">'
        'SE3002 Software Quality Engineering</div>'
    )
    footer_tpl = (
        '<div style="font-family: \'Times New Roman\', Times, serif; font-size: 9pt; color: #000000; '
        'width: 100%; margin: 0 1in; text-align: right;">Page <span class="pageNumber"></span></div>'
    )

    temp_html = os.path.join(BASE_DIR, 'temp_report_render.html')
    temp_cover_pdf = os.path.join(BASE_DIR, 'temp_cover.pdf')
    temp_body_pdf = os.path.join(BASE_DIR, 'temp_body.pdf')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Pass 1: Render complete document with header/footer to measure exact page numbers
        front_p1 = build_front_matter_html(toc_entries)
        refs_p1 = build_references_html()
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(render_html_document(cover_html, front_p1, body_html, refs_p1))
        page.goto(f"file:///{temp_html.replace(os.sep, '/')}", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.pdf(
            path=temp_body_pdf,
            format='Letter',
            print_background=True,
            margin={'top': '1in', 'bottom': '1in', 'left': '1in', 'right': '1in'},
            display_header_footer=True,
            header_template=header_tpl,
            footer_template=footer_tpl,
        )

        # Resolve real page numbers from Pass 1 PDF
        find_pages_for_titles(temp_body_pdf, toc_entries)

        # Pass 2A: Render Cover Page (page 1, zero header/footer)
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(render_html_document(cover_html, '', '', ''))
        page.goto(f"file:///{temp_html.replace(os.sep, '/')}", wait_until="networkidle")
        page.wait_for_timeout(500)
        page.pdf(
            path=temp_cover_pdf,
            format='Letter',
            print_background=True,
            margin={'top': '1in', 'bottom': '1in', 'left': '1in', 'right': '1in'},
            display_header_footer=False,
        )

        # Pass 2B: Render full document with resolved dot-leader page numbers (take pages[1:] so Page 2 = TOC)
        front_p2 = build_front_matter_html(toc_entries)
        refs_p2 = build_references_html()
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(render_html_document(cover_html, front_p2, body_html, refs_p2))
        page.goto(f"file:///{temp_html.replace(os.sep, '/')}", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.pdf(
            path=temp_body_pdf,
            format='Letter',
            print_background=True,
            margin={'top': '1in', 'bottom': '1in', 'left': '1in', 'right': '1in'},
            display_header_footer=True,
            header_template=header_tpl,
            footer_template=footer_tpl,
        )
        # Pass 2C: Render single-line page border overlay (0.85pt solid #000 at 0.55in inset)
        border_html = """<!DOCTYPE html><html><head><style>
        @page { size: letter portrait; margin: 0; }
        body { margin: 0; padding: 0; background: transparent; }
        .page-frame {
            position: fixed;
            top: 0.55in; left: 0.55in; right: 0.55in; bottom: 0.55in;
            border: 0.85pt solid #000000;
            box-sizing: border-box;
        }
        </style></head><body><div class="page-frame"></div></body></html>"""
        temp_border_pdf = os.path.join(BASE_DIR, 'temp_border.pdf')
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(border_html)
        page.goto(f"file:///{temp_html.replace(os.sep, '/')}", wait_until="load")
        page.pdf(
            path=temp_border_pdf,
            format='Letter',
            print_background=False,
            margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'},
            display_header_footer=False,
        )
        browser.close()

    # Merge Page 1 (no header/footer) + Pages 2..N (with header/footer starting at Page 2),
    # and stamp single-line border onto every page
    writer = pypdf.PdfWriter()
    cover_reader = pypdf.PdfReader(temp_cover_pdf)
    body_reader = pypdf.PdfReader(temp_body_pdf)
    border_page = pypdf.PdfReader(temp_border_pdf).pages[0]

    writer.add_page(cover_reader.pages[0])
    for pg in body_reader.pages[1:]:
        writer.add_page(pg)
    for out_pg in writer.pages:
        out_pg.merge_page(border_page)

    target_pdf = OUTPUT_PDF_PATH_C
    try:
        with open(target_pdf, 'wb') as out_f:
            writer.write(out_f)
    except PermissionError:
        target_pdf = os.path.join(BASE_DIR, 'Project_24i-3108_24i-3107_24i-3074_C_formal.pdf')
        with open(target_pdf, 'wb') as out_f:
            writer.write(out_f)

    for tmp in (temp_html, temp_cover_pdf, temp_body_pdf, temp_border_pdf):
        if os.path.exists(tmp):
            os.remove(tmp)

    print(
        f"Generated: {target_pdf} "
        f"({os.path.getsize(target_pdf) / 1024:.1f} KB, {len(writer.pages)} pages)"
    )


if __name__ == '__main__':
    main()
