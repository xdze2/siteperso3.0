# rebuild the left menu of every page of the course: page list + h2 of each page.
# adds id="..." to h2 that have none. run after adding/renaming a section.
import os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
PAGES = [('index.html', 'sommaire'), ('tone.html', '1. tone'), ('hatching.html', '2. hatching'),
         ('lines.html', '3. lines'),
         ('perception.html', '4. perception'), ('references.html', 'references')]
NAV_CSS = """      nav {
        width: 340px; flex-shrink: 0; box-sizing: border-box;
        padding: 2rem 1rem 2rem 2rem;
        position: sticky; top: 0; align-self: flex-start;
        max-height: 100vh; overflow-y: auto;
      }
      nav ul.sub { margin: 0.4rem 0 0 0.6rem; }
      nav ul.sub li { margin-bottom: 0.25rem; line-height: 1.15; }
      nav ul.sub a { text-transform: none; letter-spacing: 0; font-size: 0.72rem; color: #6e6356; }
      nav li.here > a { font-weight: bold; }
"""

def slug(s):
    s = re.sub(r'&[a-z]+;', '', s.lower())
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:40]

def h2s(path):
    src = open(path, encoding='utf-8').read()
    out = []
    def fix(m):
        attrs, inner = m.group(1), m.group(2)
        text = html.unescape(re.sub(r'<[^>]+>', '', inner)).strip()
        mid = re.search(r'id="([^"]+)"', attrs)
        hid = mid.group(1) if mid else slug(text)
        out.append((hid, text))
        return m.group(0) if mid else f'<h2 id="{hid}"{attrs}>{inner}</h2>'
    src = re.sub(r'<h2([^>]*)>(.*?)</h2>', fix, src, flags=re.S)
    return src, out

pages = [(f, label) for f, label in PAGES if os.path.exists(os.path.join(ROOT, f))]
srcs, heads = {}, {}
for f, _ in pages:
    srcs[f], heads[f] = h2s(os.path.join(ROOT, f))

for f, _ in pages:
    lines = ['    <nav>', '      <ul>',
             '        <li><a href="../../index.html">Home</a></li>',
             '        <li><a href="../../drawing/index.html">drawing</a></li>']
    for g, label in pages:
        here = ' class="here"' if g == f else ''
        lines.append(f'        <li{here}><a href="{g}">{label}</a>')
        if g != 'index.html' and heads[g]:
            lines.append('          <ul class="sub">')
            for hid, text in heads[g]:
                lines.append(f'            <li><a href="{g}#{hid}">{html.escape(text)}</a></li>')
            lines.append('          </ul>')
        lines.append('        </li>')
    lines += ['      </ul>', '    </nav>']
    src = re.sub(r'    <nav>.*?</nav>', '\n'.join(lines), srcs[f], count=1, flags=re.S)
    # nav css: replace the first "nav { ... }" rule and anything this script added
    src = re.sub(r'      nav \{[^}]*\}\n(      nav ul\.sub[^\n]*\n|      nav li\.here[^\n]*\n)*', NAV_CSS, src, count=1)
    open(os.path.join(ROOT, f), 'w', encoding='utf-8').write(src)
    print(f, len(heads[f]), 'sections')
