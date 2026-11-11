"""XmasEvent_Specs.html → Markdown（供 Claude 阅读的纯文字版规格）"""
import re, sys
from bs4 import BeautifulSoup, NavigableString, Tag

SRC, OUT = sys.argv[1], sys.argv[2]
html = re.sub(r'src="data:[^"]+"', 'src=""', open(SRC, encoding='utf-8').read())
soup = BeautifulSoup(html, 'html.parser')
HID = '〔暂隐藏〕'


def is_hidden(el):
    if not isinstance(el, Tag):
        return False
    cls = el.get('class') or []
    return el.has_attr('hidden') or 'ref-fail' in cls


def inline(el):
    """行内文字：保留粗体、代码、换行；隐藏片段加标记。"""
    if isinstance(el, NavigableString):
        return re.sub(r'\s+', ' ', str(el))
    if not isinstance(el, Tag) or el.name in ('script', 'style', 'img', 'iframe', 'svg'):
        return ''
    if el.name == 'br':
        return '\n'
    inner = ''.join(inline(c) for c in el.children)
    if el.name == 'li':
        return '\n· ' + inner.strip()
    if el.name in ('ul', 'ol'):
        return inner + '\n'
    if el.name == 'div':
        return '\n' + inner.strip() + '\n'
    if is_hidden(el):
        ls = [l.strip() for l in inner.strip().split('\n') if l.strip()]
        return '\n' + '\n'.join(HID + l for l in ls) + '\n'
    cls = el.get('class') or []
    if 'badge' in cls:
        return f'【{inner.strip()}】'
    if el.name in ('strong', 'b'):
        t = inner.strip()
        return f'**{t}**' if t else ''
    if el.name == 'code':
        return f'`{inner.strip()}`'
    if el.name == 'small':
        return f'（{inner.strip()}）'
    return inner


def clean(t):
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r' *\n *', '\n', t)
    t = re.sub(r'\*\*\s*\*\*', '', t)
    return t.strip()


def lines_as_bullets(text, indent=''):
    """多行文字 → 第一行 + 其余行为子项（原文已有「·」「- 」者去掉符号）。"""
    out = []
    for i, ln in enumerate([x for x in text.split('\n') if x.strip()]):
        ln = ln.strip()
        sub = ln.startswith('-') or ln.startswith('　-') or ln.startswith('－')
        ln2 = re.sub(r'^[·•]\s*', '', ln)
        ln2 = re.sub(r'^[　\s]*[-－]\s*', '', ln2)
        out.append(f'{indent}{"    " if sub else "  "}- {ln2}' if i or ln.startswith('·') or sub else f'{indent}{ln2}')
    return '\n'.join(out)


def cell(td):
    return clean(inline(td)).replace('\n', '<br>').replace('|', '｜')


def table_md(tbl):
    rows = tbl.find_all('tr')
    if not rows:
        return ''
    cls = tbl.get('class') or []
    # 2 栏规格表 → 定义清单
    if 'spec-table' in cls and all(len(r.find_all(['td', 'th'], recursive=False)) == 2 for r in rows) and not tbl.find('th'):
        out = []
        for r in rows:
            a, b = r.find_all('td', recursive=False)
            k = clean(inline(a)); v = clean(inline(b))
            mark = HID if is_hidden(r) else ''
            vl = [x for x in v.split('\n') if x.strip()]
            if len(vl) <= 1:
                out.append(f'- {mark}**{k}**：{v}')
            else:
                out.append(f'- {mark}**{k}**：' + ('' if vl[0].lstrip().startswith('·') else vl[0].strip()))
                rest = vl if vl[0].lstrip().startswith('·') else vl[1:]
                for ln in rest:
                    ln = ln.strip()
                    if re.match(r'^[　\s]*[-－]', ln):
                        out.append('    - ' + re.sub(r'^[　\s]*[-－]\s*', '', ln))
                    else:
                        out.append('  - ' + re.sub(r'^[·•]\s*', '', ln))
        return '\n'.join(out)
    # 一般表格
    body, pend = [], {}   # pend: col -> [remaining rows, text]（处理 rowspan）
    for r in rows:
        cells = r.find_all(['td', 'th'], recursive=False)
        row, it, col = [], iter(cells), 0
        while True:
            if col in pend and pend[col][0] > 0:
                row.append(pend[col][1]); pend[col][0] -= 1; col += 1; continue
            c = next(it, None)
            if c is None:
                break
            t = cell(c); rs = int(c.get('rowspan', 1) or 1)
            if rs > 1:
                pend[col] = [rs - 1, t]
            row.append(t); col += 1
        if is_hidden(r):
            row[0] = HID + row[0]
        body.append(row)
    w = max(len(r) for r in body)
    body = [r + [''] * (w - len(r)) for r in body]
    md = ['| ' + ' | '.join(body[0]) + ' |', '|' + '---|' * w]
    md += ['| ' + ' | '.join(r) + ' |' for r in body[1:]]
    return '\n'.join(md)


def block(el, depth=0):
    """区块转换。"""
    if isinstance(el, NavigableString):
        t = str(el).strip()
        return t
    if not isinstance(el, Tag) or el.name in ('script', 'style', 'img', 'iframe', 'button', 'svg'):
        return ''
    cls = el.get('class') or []
    hid = is_hidden(el)
    pre = HID if hid else ''
    if 'panel-title' in cls:
        return f'## {pre}{clean(inline(el))}'
    if 'panel-sub' in cls:
        return f'*{clean(inline(el))}*'
    if 'sub-title' in cls:
        return f'### {pre}{clean(inline(el))}'
    if 'card-title' in cls:
        return f'**{clean(inline(el))}**'
    if 'mod-head' in cls:
        n = el.find(class_='n'); h = el.find('h3')
        return f'### {n.get_text(strip=True) if n else ""} {clean(inline(h))}'
    if 'io-img' in cls:
        return '\n'.join(f'> 📷 截图：{clean(inline(c))}' for c in el.find_all(class_='io-cap'))
    if 'io-cap' in cls:
        return f'> 📷 截图：{clean(inline(el))}'
    if 'rule-list' in cls:
        out = []
        for li in el.find_all('li', class_='rule-item', recursive=False):
            num = li.find(class_='rule-num'); txt = li.find(class_='rule-text')
            t = clean(inline(txt))
            first, *rest = t.split('\n') if t else ['']
            head = f'{num.get_text(strip=True) if num else "-"}. ' if num else '- '
            mark = HID if is_hidden(li) else ''
            if first.lstrip().startswith('·'):
                out.append(f'{head}{mark}' + '\n' + lines_as_bullets(t, '   '))
            else:
                out.append(f'{head}{mark}{first.strip()}' + ('\n' + '\n'.join(
                    ('       - ' + re.sub(r'^[　\s]*[-－]\s*', '', x.strip())) if re.match(r'^[　\s]*[-－]', x.strip())
                    else ('   - ' + re.sub(r'^[·•]\s*', '', x.strip())) if re.match(r'^(〔暂隐藏〕)?[·•]', x.strip())
                    else ('   ' + x.strip()) for x in rest if x.strip()) if rest else ''))
        return '\n'.join(out)
    if el.name == 'table':
        return table_md(el)
    if 'callout' in cls:
        icon = el.find('span'); body = icon.find_next_sibling() if icon else el
        t = clean(inline(body))
        return '\n'.join('> ' + (x.strip()) for x in t.split('\n') if x.strip()).replace('> ', f'> {icon.get_text(strip=True) if icon else ""} ', 1)
    if 'flow' in cls:
        parts = []
        for c in el.children:
            if not isinstance(c, Tag):
                continue
            cc = c.get('class') or []
            if 'flow-node' in cc:
                parts.append('［' + clean(inline(c)).replace('\n', '：') + '］')
            elif 'flow-arrow' in cc:
                sm = c.find('small')
                parts.append(f'—({sm.get_text(strip=True)})→' if sm else '→')
        return '流程：' + ' '.join(parts)
    if 'timeline' in cls:
        out = []
        for seg in el.find_all(class_='tl-seg', recursive=False):
            b = seg.find('b', recursive=False); sp = seg.find('span', recursive=False)
            out.append(f'- **{clean(inline(b)).replace("**", "")}**：' + clean(inline(sp)).replace('\n', '；'))
        return '\n'.join(out)
    if 'note' in cls:
        return f'*{clean(inline(el))}*'
    if el.name in ('ul', 'ol'):
        return '\n'.join('- ' + clean(inline(li)).replace('\n', '；') for li in el.find_all('li', recursive=False))
    if el.name in ('p',) or (el.name in ('div', 'span') and not el.find(['div', 'table', 'ul', 'ol', 'p'])):
        t = clean(inline(el))
        return (pre + t) if t else ''
    # 容器：递归
    parts = [block(c, depth + 1) for c in el.children]
    out = '\n\n'.join(p for p in parts if p and p.strip())
    if hid and out:
        out = f'> {HID}以下内容目前在规格中隐藏（暂不提供予开发／QA）\n\n' + out
    return out


md = []
hdr = soup.find(class_='doc-header')
md.append(f'# {clean(inline(hdr.find(class_="doc-title")))}（规格文字版）')
md.append('> 转出日期：2026-11-04。本档由最新版 `XmasEvent_Specs.html` 自动转出的纯文字版，供 Claude 阅读与比对；截图、原型 iframe 已省略（仅保留截图标题）。'
          f'标有「{HID}」者为规格中目前隐藏、暂不提供予开发／QA 的内容（失败情境相关）。')
md.append(clean(inline(hdr.find(class_='doc-desc'))).replace('\n', '\n'))
md.append(' ｜ '.join(clean(inline(c)) for c in hdr.find_all(class_='meta-chip')))
spec = soup.find(class_='mview', attrs={'data-m': 'spec'})
for p in spec.find_all(class_='spanel', recursive=False):
    md.append('---')
    md.append(block(p))
chg = soup.find(class_='mview', attrs={'data-m': 'chg'})
md.append('---\n## 本次调整\n' + clean(inline(chg.find(class_='doc-desc'))))
text = '\n\n'.join(x for x in md if x.strip())
text = re.sub(r'\n{3,}', '\n\n', text)
text = re.sub(HID + r'\s*[·•]\s*', HID, text)
open(OUT, 'w', encoding='utf-8').write(text + '\n')
print(len(text), 'chars')
