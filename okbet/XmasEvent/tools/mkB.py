"""由 A 版前台原型（XmasEvent_Frontend.html）产生 B 版（奖池 Tab：一次只显示 1 个奖池）。A 版修改后重跑本脚本即可同步。"""
p_in, p_out = '/home/claude/XmasEvent_Frontend.html', '/home/claude/XmasEvent_Frontend_B.html'
s = open(p_in, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


rep('<title>节庆特别活动 · 前台原型</title>', '<title>节庆特别活动 · 前台原型（B 版：奖池 Tab）</title>')
rep('    <h2>原型控制（模拟资料）</h2>',
    '    <h2>原型控制（模拟资料）</h2>\n    <p style="margin:0 0 6px;font-size:.67rem;color:#5a6274">B 版：奖池 Tab（POOL 1～4），一次只显示 1 个奖池（预设 Pool 1）</p>')

# ---- 奖池 Tab（标题列下方）：POOL 1～4，点击显示对应奖池 ----
rep('      <ul class="pools gpools" id="poolList" aria-label="奖池"></ul>',
    '      <div class="ptabs" id="poolTabs" role="tablist" aria-label="Prize pools"></div>\n      <ul class="pools gpools" id="poolList" aria-label="奖池"></ul>')

# ---- 渲染：只显示目前 Tab 的奖池（无收合功能） ----
rep("function renderTreePools(keys){\n  $('#poolList').innerHTML=CHESTS.map(C=>{ const best=C.cost===TOP_COST, g=topIdx(C.box), ord=poolOrd(C);\n",
    """/* B 版：奖池 Tab——标题列下方 POOL 1～4 Tab，点击只显示对应奖池（预设 Pool 1）；奖池本身无收合功能 */
let OPEN_POOL=1;
function renderTreePools(keys){
  $('#poolList').innerHTML=CHESTS.filter(C=>C.no===OPEN_POOL).map(C=>{ const best=C.cost===TOP_COST, g=topIdx(C.box), ord=poolOrd(C);
""")
rep('    return `<li class="gtree ${best?\'gtree--top\':\'\'}" data-pool="${C.no}" aria-label="Pool ${C.no}">',
    '    return `<li class="gtree gtree--open ${best?\'gtree--top\':\'\'}" data-pool="${C.no}" role="tabpanel" aria-label="Pool ${C.no}">')
rep("  $$('[data-pdraw]').forEach(b=>b.addEventListener('click',()=>drawPool(CHESTS.find(x=>x.no===+b.dataset.pdraw),+b.dataset.d)));\n}",
    """  $$('[data-pdraw]').forEach(b=>b.addEventListener('click',()=>drawPool(CHESTS.find(x=>x.no===+b.dataset.pdraw),+b.dataset.d)));
  $('#poolTabs').innerHTML=CHESTS.map(C=>`<button class="ptab ${C.no===OPEN_POOL?'is-on':''}" role="tab" aria-selected="${C.no===OPEN_POOL}" data-open="${C.no}">POOL ${C.no}</button>`).join('');
  $$('#poolTabs [data-open]').forEach(b=>b.addEventListener('click',()=>{ if(PD||+b.dataset.open===OPEN_POOL) return; OPEN_POOL=+b.dataset.open; renderAll();
    $(`#poolTabs [data-open="${OPEN_POOL}"]`).focus({preventScroll:true}); }));
}""")
# Tab 已标示奖池：卡片内不再显示 POOL N 铭牌，只留每抽消耗（靠右）
rep('      <div class="gtree__head"><span class="gtree__plate">POOL ${C.no}</span><span class="gpool__cost">',
    '      <div class="gtree__head"><span class="gpool__cost">')
# 跑马灯演出中：Tab 也停用
rep("  $$('[data-pdraw]').forEach(b=>b.disabled=true);", "  $$('[data-pdraw],[data-open]').forEach(b=>b.disabled=true);")

css = '''
/* === B 版：奖池 Tab === */
.ptabs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin:0 0 12px;}
.ptab{padding:8px 4px;border-radius:999px;font-family:Georgia,'Times New Roman',serif;font-weight:700;font-size:.8rem;letter-spacing:.04em;white-space:nowrap;cursor:pointer;
  color:#f3dcc0;background:linear-gradient(180deg,#7a1420,#4a0a12);border:1.5px solid rgba(255,214,110,.55);box-shadow:0 2px 0 #2a0408;}
.ptab:hover:not(:disabled){border-color:var(--gold-1);}
.ptab.is-on{color:#4a1606;background:linear-gradient(180deg,#fff3b0,var(--gold-1) 55%,var(--gold-2));border-color:#fff3b0;box-shadow:0 0 10px rgba(255,214,110,.6),0 2px 0 #8a5a12;}
.ptab:disabled{opacity:.6;cursor:default;}
.gtree--open .gtree__head{justify-content:flex-end;}
/* 切换 Tab 时奖池淡入 */
.gtree--open .gtree__stage,.gtree--open .pool__btns{animation:poolOpen .35s ease-out both;}
@keyframes poolOpen{from{opacity:0;transform:translateY(-8px);}to{opacity:1;transform:none;}}
@media (prefers-reduced-motion:reduce){ .gtree--open .gtree__stage,.gtree--open .pool__btns{animation:none;} }
'''
i = s.index('</style>')
s = s[:i] + css + s[i:]
open(p_out, 'w', encoding='utf-8').write(s)
print('ok')
