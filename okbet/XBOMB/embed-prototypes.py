#!/usr/bin/env python3
"""把前台／后台原型档重新打包进规格档的 iframe（data URI）。

规格档 X-BOMB_Specs.html 的「原型预览」是用 base64 data URI 把整份原型
内嵌在 iframe 里，所以每次改完 X-BOMB_Frontend.html / X-BOMB_Backend.html
都必须重新打包，否则规格档里看到的还是旧版。

用法（在本目录执行，或用绝对路径皆可）：
    python3 embed-prototypes.py            # 重新打包 fe + be
    python3 embed-prototypes.py --check    # 只检查是否同步，不写档（不同步时 exit 1）
    python3 embed-prototypes.py be         # 只打包后台
    python3 embed-prototypes.py fe be      # 指定多个
"""
from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPECS = HERE / 'X-BOMB_Specs.html'

# data-p 值 -> 原型档
PROTOS = {
    'fe': HERE / 'X-BOMB_Frontend.html',
    'be': HERE / 'X-BOMB_Backend.html',
}


def iframe_pattern(key: str) -> re.Pattern:
    """比对 <iframe ... data-p="be" ... src="data:text/html;charset=utf-8;base64,XXXX">"""
    return re.compile(
        r'(<iframe class="proto-frame ' + key + r'[^"]*" data-p="' + key + r'"'
        r'[^>]*? src="data:text/html;charset=utf-8;base64,)([A-Za-z0-9+/=]+)(")'
    )


def main(argv: list[str]) -> int:
    check_only = '--check' in argv
    keys = [a for a in argv if a in PROTOS] or list(PROTOS)

    specs = io.open(SPECS, encoding='utf-8').read()
    changed, stale = False, []

    for key in keys:
        src = PROTOS[key]
        pat = iframe_pattern(key)
        hits = pat.findall(specs)
        if len(hits) != 1:
            print(f'✗ {key}: 在 {SPECS.name} 找到 {len(hits)} 个 iframe（预期 1 个），请检查样板是否改过')
            return 2

        new_b64 = base64.b64encode(src.read_bytes()).decode()
        old_b64 = hits[0][1]
        if new_b64 == old_b64:
            print(f'✓ {key}: 已与 {src.name} 同步')
            continue

        stale.append(key)
        if check_only:
            print(f'✗ {key}: 与 {src.name} 不同步（需重新打包）')
            continue

        specs = pat.sub(lambda m: m.group(1) + new_b64 + m.group(3), specs, count=1)
        changed = True
        print(f'↻ {key}: 已重新打包 {src.name}（{src.stat().st_size:,} bytes）')

    if check_only:
        return 1 if stale else 0

    if changed:
        io.open(SPECS, 'w', encoding='utf-8').write(specs)
        print(f'→ 已写入 {SPECS.name}（{SPECS.stat().st_size:,} bytes）')
    else:
        print('→ 无需变更')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
