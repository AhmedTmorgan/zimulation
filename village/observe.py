"""
المراقب.

صفحةٌ واحدة قائمة بذاتها تفتح العالم وتتيح تفتيشه: تضغط على إنسانٍ فترى
ذاكرته كاملةً — كل أثرٍ ومصدره وهل وقع أصلًا — وكودَه الذي كتبه، ونسبه،
وما قاله ولماذا قاله.

وهنا وحدها يُكشَف حقل `truth`. الكائن لا يراه أبدًا، والمراقب يراه دائمًا.
هذا هو الفرق بين أن تعيش في عالمٍ وأن تنظر إليه من خارجه.
"""

import html
import json

from . import genome as G
from . import tech as T
from .lang import render_maxim
from .memory import AR_KINDS, AR_SOURCES, KINDS, SOURCES
from .mind import ACTIONS, AR_ACTIONS, AR_FEATURES, FEATURES, NA, NF


def _person(sim, a):
    traces = []
    for t in sorted(a.mem.traces, key=lambda t: -t.strength)[:40]:
        traces.append(dict(
            k=AR_KINDS[KINDS[t.kind]], y=t.year,
            v=round(t.val, 2), s=round(t.strength, 2),
            src=AR_SOURCES[SOURCES[t.src]],
            true=t.truth > 0.5, rep=t.repressed,
            tag=t.tag or "",
            who=(sim.agents[t.who].name if t.who in sim.agents else
                 (next((d.name for d in sim.dead[-3000:] if d.id == t.who), "") if t.who >= 0 else "")),
        ))
    W = a.prog.W
    top = sorted(range(NF * NA), key=lambda i: -abs(W[i]))[:14]
    code = [dict(f=AR_FEATURES[FEATURES[i // NA]], a=AR_ACTIONS[ACTIONS[i % NA]],
                 w=round(W[i], 2)) for i in top if abs(W[i]) > 0.25]
    bonds = []
    for who, v in sorted(a.bonds.affection.items(), key=lambda kv: -kv[1])[:6]:
        if who in sim.agents:
            bonds.append(dict(n=sim.agents[who].name, kind="مودّة", v=round(v, 2)))
    for who, v in sorted(a.bonds.resentment.items(), key=lambda kv: -kv[1])[:6]:
        if who in sim.agents:
            bonds.append(dict(n=sim.agents[who].name, kind="ضغينة", v=round(v, 2)))
    return dict(
        id=a.id, n=a.name, t=a.title, house=a.house, age=a.age,
        sex="أنثى" if a.sex else "ذكر", creed=a.creed(),
        born=a.birth_year, gen=a.g.generation,
        stat=dict(هيبة=round(a.prestige, 1), هيمنة=round(a.dominance, 1),
                  إيمان=round(a.faith, 2), شك=round(a.doubt, 2),
                  يأس=round(a.despair, 2), حنين=round(a.longing, 2),
                  خوف_الموت=round(a.fear_death, 2), خوف_العوز=round(a.fear_want, 2),
                  أذى=round(a.damage, 2), إصابات=a.hits,
                  إرضاع=round(a.nursing, 1)),
        traits={G.AR[k]: round(a.eg.t[i], 2) for i, k in enumerate(G.TRAITS)},
        truth=round(a.mem.truthfulness(), 3),
        traces=traces, code=code, bonds=bonds,
        maxims=[dict(t=render_maxim(m, a.concepts), taught=m.taught,
                     born=m.born, der=m.derived) for m in a.prog.maxims],
        concepts=[dict(r=cc.render(), n=cc.name, born=cc.born,
                       taught=cc.taught, ev=cc.evidence, v=round(cc.value, 2))
                  for cc in a.concepts],
        intent=(dict(a=AR_ACTIONS[ACTIONS[a.intention.action]],
                     y=a.intention.years, why=a.intention.why)
                if a.intention else None),
        derived=a.prog.derived, vows=a.prog.kept,
        said=[dict(t=u.text, why=u.trace(), kind=u.kind, y=u.year) for u in a.said],
        conv={k: round(v, 2) for k, v in sorted(a.conv.items(), key=lambda kv: -kv[1])[:8]},
        riders=a.riders[:6],
        lies=a.lies, caught=a.caught, kills=a.kills, rule=a.rule_years,
        children=len(a.children), rewrites=a.prog.rewrites,
    )


def snapshot(sim, people=90):
    w = sim.world
    cells = []
    for row in w.grid:
        for r in row:
            cells.append(dict(x=r.x, y=r.y, f=round(r.fertility, 2),
                              s=r.settled, tb=r.taboo, n=r.name))
    sts = []
    for st in w.settlements:
        sts.append(dict(id=st.id, n=st.name, x=st.x, y=st.y,
                        pop=st.pop() + sim.mass.get(st.id, 0),
                        named=st.pop(), know=len(st.knowledge),
                        ruler=(sim.agents[st.ruler].name if st.ruler in sim.agents else "—"),
                        period=round(st.known_period, 1) if st.known_period else None,
                        star=bool(st.star_known), burned=st.burned,
                        unrest=round(st.unrest, 2),
                        foul=round(st.foul, 2), lit=round(st.literacy, 2),
                        walls=round(st.walls, 1)))
    ppl = sorted(sim.agents.values(),
                 key=lambda a: -(a.prestige + a.dominance + len(a.said) * 2))[:people]
    doc = w.settlements[0].doctrine
    tenets = []
    if doc:
        for t in doc.tenets.values():
            tenets.append(dict(t=t.text, s=round(t.strength, 2),
                               true=t.true_in_world, tested=t.tested))
    know = set()
    for st in w.settlements:
        know |= st.knowledge
    return dict(
        year=sim.year, seed=sim.cfg.seed,
        pop=sim.population(), named=len(sim.agents),
        grid=w.n, cells=cells, settlements=sts,
        people=[_person(sim, a) for a in ppl],
        names=[dict(kind=n.kind, n=n.name, y=n.year, namer=n.namer,
                    after=n.after, why=n.why, lost=n.origin_lost,
                    forms=[f for _, f in n.forms]) for n in sim.names.items],
        books=[dict(k=b.kind, t=b.title, au=b.author_name, y=b.born,
                    th=b.thesis, cp=b.copies, rd=b.read_by, bu=b.burned,
                    per=round(b.period, 1) if b.period else None,
                    nc=len(b.concepts), nm=len(b.maxims))
               for st in w.settlements for b in st.library.books][:120],
        burned=sum(st.library.burned_total for st in w.settlements),
        tenets=tenets, god=doc.god if doc else "",
        complexity=round(doc.complexity, 1) if doc else 0,
        tech=[T.BY_KEY[k][1] for k in sorted(know, key=lambda k: T.ORDER[k])],
        wrath=[[y, k, round(s, 3)] for y, k, s in w.wrath.history],
        true_period=round(sum(w.wrath.history[i + 1][0] - w.wrath.history[i][0]
                              for i in range(len(w.wrath.history) - 1))
                          / max(1, len(w.wrath.history) - 1), 1)
        if len(w.wrath.history) > 1 else None,
        snaps=sim.chron.snapshots,
        events=[[e.year, e.kind, e.text] for e in sim.chron.major(2.4)][-260:],
        stats=dict(sim.stats),
    )


_CSS = """
:root{--bg:#faf8f4;--fg:#1a1714;--mut:#6b6259;--line:#e2dbd0;--card:#fff;
--acc:#8c4a2f;--acc2:#2f5d62;--ok:#2f6b3f;--bad:#9b2c2c;--warn:#8a6d1f}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#14120f;--fg:#ece5da;
--mut:#9a9086;--line:#2c2721;--card:#1c1915;--acc:#d98c62;--acc2:#6fb3ba;
--ok:#79c48d;--bad:#e07070;--warn:#d4b768}}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);direction:rtl;margin:0;
font:15px/1.7 "Segoe UI","Noto Naskh Arabic",Tahoma,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:26px 18px 80px}
h1{font-size:1.7rem;margin:0 0 4px}
h2{font-size:1.1rem;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.mut{color:var(--mut)}.sm{font-size:.85rem}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
.bar button{background:var(--card);color:var(--fg);border:1px solid var(--line);
border-radius:20px;padding:6px 15px;cursor:pointer;font:inherit;font-size:.88rem}
.bar button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
.grid{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(128px,1fr))}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 13px}
.stat b{display:block;font-size:1.35rem;font-variant-numeric:tabular-nums}
.stat span{font-size:.78rem;color:var(--mut)}
.cols{display:grid;grid-template-columns:260px 1fr;gap:16px;align-items:start}
@media(max-width:760px){.cols{grid-template-columns:1fr}}
.list{background:var(--card);border:1px solid var(--line);border-radius:10px;
max-height:640px;overflow:auto}
.list div{padding:7px 12px;border-bottom:1px solid var(--line);cursor:pointer;font-size:.88rem}
.list div:hover{background:var(--bg)}
.list div.on{background:var(--acc);color:#fff}
.pane{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{text-align:right;padding:5px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-size:.78rem;font-weight:600}
td.num{font-variant-numeric:tabular-nums}
.tag{display:inline-block;padding:1px 8px;border-radius:11px;font-size:.75rem;border:1px solid var(--line)}
.t-true{color:var(--ok);border-color:var(--ok)}
.t-false{color:var(--bad);border-color:var(--bad)}
.t-rep{color:var(--warn);border-color:var(--warn)}
.scroll{overflow-x:auto}
code{background:var(--bg);border:1px solid var(--line);border-radius:4px;
padding:1px 6px;font-family:ui-monospace,Consolas,monospace;font-size:.85em;direction:rtl}
.why{color:var(--mut);font-size:.78rem;margin-top:2px}
.map{display:grid;gap:2px;margin:12px 0}
.map i{aspect-ratio:1;border-radius:3px;position:relative}
.map i.s{outline:2px solid var(--acc);outline-offset:-2px}
.map i.tb{outline:2px dashed var(--bad);outline-offset:-2px}
.ev{border-right:2px solid var(--line);padding:2px 12px 2px 0;margin:0 0 3px;font-size:.87rem}
.ev time{color:var(--mut);font-variant-numeric:tabular-nums;margin-left:7px;font-size:.8rem}
.hide{display:none}
"""

_JS = """
const D = DATA;
const $ = s => document.querySelector(s);
const esc = s => String(s??'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function tabs(){
  document.querySelectorAll('.bar button').forEach(b=>b.onclick=()=>{
    document.querySelectorAll('.bar button').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');
    document.querySelectorAll('section').forEach(s=>s.classList.add('hide'));
    $('#'+b.dataset.t).classList.remove('hide');
  });
}

function drawMap(){
  const m = $('#map');
  m.style.gridTemplateColumns = `repeat(${D.grid},1fr)`;
  const settled = new Set(D.settlements.map(s=>s.x+','+s.y));
  D.cells.forEach(c=>{
    const i = document.createElement('i');
    const g = Math.round(30 + c.f*150);
    i.style.background = `rgb(${Math.round(g*0.55)},${g},${Math.round(g*0.5)})`;
    if(settled.has(c.x+','+c.y)) i.className='s';
    if(c.tb) i.className+=' tb';
    i.title = `${c.n} · خصوبة ${c.f}${c.tb?' · محرّم':''}`;
    m.appendChild(i);
  });
}

function personList(){
  const L = $('#plist');
  D.people.forEach((p,idx)=>{
    const d = document.createElement('div');
    d.textContent = `${p.n}${p.t?' '+p.t:''} · ${p.age}س · ${p.creed}`;
    d.onclick = ()=>{ document.querySelectorAll('#plist div').forEach(x=>x.classList.remove('on'));
                      d.classList.add('on'); showPerson(idx); };
    L.appendChild(d);
  });
  if(D.people.length) { $('#plist div').classList.add('on'); showPerson(0); }
}

function showPerson(i){
  const p = D.people[i];
  const st = Object.entries(p.stat).map(([k,v])=>`<span class="tag">${k.replace(/_/g,' ')} ${v}</span>`).join(' ');
  const tr = Object.entries(p.traits).sort((a,b)=>b[1]-a[1]).slice(0,8)
      .map(([k,v])=>`<span class="tag">${k} ${v}</span>`).join(' ');
  const traces = p.traces.map(t=>`<tr>
      <td>${esc(t.k)}${t.tag?' · '+esc(t.tag):''}${t.who?' · '+esc(t.who):''}</td>
      <td class="num">${t.y}</td><td class="num">${t.v}</td><td class="num">${t.s}</td>
      <td>${esc(t.src)}</td>
      <td><span class="tag ${t.rep?'t-rep':(t.true?'t-true':'t-false')}">${
        t.rep?'مدفون':(t.true?'وقع':'لم يقع')}</span></td></tr>`).join('');
  const code = p.code.map(c=>`<tr><td>${esc(c.f)}</td><td>${esc(c.a)}</td>
      <td class="num" style="color:${c.w>0?'var(--ok)':'var(--bad)'}">${c.w}</td></tr>`).join('');
  const mx = p.maxims.map(m=>`<div><code>${esc(m.t)}</code> <span class="mut sm">سنة ${m.born} · نُقلت ${m.taught}</span></div>`).join('') || '<span class="mut sm">لم يؤلّف شيئًا</span>';
  const cn = p.concepts.map(c=>`<div><code>${esc(c.r)}</code> <span class="mut sm">سنة ${c.born} · نُقل ${c.taught} · شاهده ${c.ev} موقفًا · ${c.v>0?'+':''}${c.v}</span></div>`).join('') || '<span class="mut sm">لم يصغ مفهومًا</span>';
  const itx = p.intent ? `<div style="margin:10px 0"><span class="tag">نيّة: ${esc(p.intent.a)} — بقي ${p.intent.y} سنة (${esc(p.intent.why)})</span></div>` : '';
  const said = p.said.map(u=>`<div style="margin-bottom:9px"><b>«${esc(u.t)}»</b>
      <span class="tag">${esc(u.kind)}</span><div class="why">← ${esc(u.why)}</div></div>`).join('')
      || '<span class="mut sm">لم يقل شيئًا يُنسب</span>';
  const bd = p.bonds.map(b=>`<span class="tag">${esc(b.kind)} ${esc(b.n)} ${b.v}</span>`).join(' ') || '<span class="mut sm">لا روابط</span>';
  const rd = p.riders.map(r=>`<div class="sm">• ${esc(r)}</div>`).join('') || '';
  $('#pane').innerHTML = `
    <h3 style="margin:0 0 3px">${esc(p.n)} ${esc(p.t||'')}</h3>
    <div class="mut sm">بيت ${esc(p.house)} · ${p.sex} · ${p.age} سنة · وُلد ${p.born} ·
      الجيل ${p.gen} · ${p.children} ولد · أعاد كتابة كوده ${p.rewrites} مرة
      ${p.lies?' · كذب '+p.lies+' مرة':''}${p.caught?' (انكشف '+p.caught+')':''}
      ${p.kills?' · قتل '+p.kills:''}${p.rule?' · حكم '+p.rule+' سنة':''}</div>
    <div style="margin:10px 0">${st}</div>
    <div style="margin:10px 0">${tr}</div>
    <div style="margin:10px 0">${bd}</div>
    <h4 style="margin:18px 0 6px">ذاكرته — وصدقُها ${(p.truth*100).toFixed(0)}٪</h4>
    <div class="mut sm" style="margin-bottom:6px">عمود «وقع/لم يقع» يراه المراقب وحده. هو لا يملك وسيلة للتمييز.</div>
    <div class="scroll"><table><tr><th>الأثر</th><th>سنة</th><th>قيمة</th><th>قوّة</th><th>مصدر</th><th></th></tr>${traces}</table></div>
    <h4 style="margin:18px 0 6px">كودُه — أقوى الوصلات</h4>
    <div class="scroll"><table><tr><th>إذا</th><th>فافعل</th><th>وزن</th></tr>${code}</table></div>
    ${itx}
    <h4 style="margin:18px 0 6px">مفاهيم صاغها</h4>${cn}
    <h4 style="margin:18px 0 6px">حِكَمه — استنتج ${p.derived} منها بلا تجربة · أوفى ${p.vows} نيّة</h4>${mx}
    <h4 style="margin:18px 0 6px">ما قاله — ولماذا</h4>${said}
    ${rd?'<h4 style="margin:18px 0 6px">تبريراته</h4>'+rd:''}`;
}

function fill(){
  $('#stats').innerHTML = [['سنة',D.year],['الأحياء',D.pop.toLocaleString()],
    ['مُحاكَون',D.named],['قرى',D.settlements.length],['معارف',D.tech.length],
    ['دورة الغضب',D.true_period??'—'],['وقائع الغضب',D.wrath.length]]
    .map(([k,v])=>`<div class="stat"><b>${v}</b><span>${k}</span></div>`).join('');
  $('#tech').textContent = D.tech.join(' · ') || '—';
  $('#names').innerHTML = D.names.map(n=>`<tr><td>${esc(n.kind)}</td><td><b>${esc(n.n)}</b></td>
    <td class="num">${n.y}</td><td>${n.lost?'<span class="mut">نُسي سببه</span>':
    esc(n.namer)+' على '+esc(n.after)+'؛ '+esc(n.why)}</td>
    <td class="sm mut">${n.forms.length>1?esc(n.forms.join(' ← ')):''}</td></tr>`).join('');
  $('#tenets').innerHTML = D.tenets.map(t=>`<tr><td>${esc(t.t)}</td>
    <td class="num">${t.s}</td><td class="num">${t.tested}</td>
    <td><span class="tag ${t.true?'t-true':'t-false'}">${t.true?'صحيحة':'كاذبة'}</span></td></tr>`).join('');
  $('#sett').innerHTML = D.settlements.map(s=>`<tr><td>${esc(s.n)}</td>
    <td class="num">${s.pop}</td><td class="num">${s.know}</td><td>${esc(s.ruler)}</td>
    <td class="num">${s.period??'—'}</td><td>${s.star?'✓':''}</td>
    <td class="num">${s.foul}</td><td class="num">${s.lit}</td>
    <td class="num">${s.walls}</td><td class="num">${s.burned||''}</td></tr>`).join('');
  $('#bsum').textContent = `${D.books.length} كتابًا حيًّا · ${D.burned} أُحرق فلم تبقَ منه نسخة`;
  $('#books').innerHTML = D.books.map(b=>`<tr>
    <td><b>${esc(b.t)}</b><div class="mut sm">${esc(b.k)} — ${esc(b.au)}</div></td>
    <td>${esc(b.th)}</td><td class="num">${b.y}</td>
    <td class="num">${b.cp}</td><td class="num">${b.rd}</td>
    <td class="num">${b.bu||''}</td><td class="num">${b.per??''}</td></tr>`).join('');
  $('#events').innerHTML = D.events.map(e=>`<p class="ev"><time>سنة ${e[0]}</time>${esc(e[2])}</p>`).join('');
}
tabs(); drawMap(); personList(); fill();
"""


def build(sim, path, people=90):
    d = snapshot(sim, people)
    body = f"""<title>مراقب القرية — سنة {sim.year:,}</title>
<style>{_CSS}</style>
<div class="wrap">
<h1>مراقب القرية</h1>
<p class="mut">بذرة {sim.cfg.seed} · سنة {sim.year:,} · ما تراه هنا يراه المراقب وحده.</p>
<div class="grid" id="stats"></div>
<div class="bar">
  <button class="on" data-t="tab-people">الناس</button>
  <button data-t="tab-world">العالم</button>
  <button data-t="tab-names">الأصول</button>
  <button data-t="tab-creed">العقيدة</button>
  <button data-t="tab-books">الكتب</button>
  <button data-t="tab-events">الوقائع</button>
</div>

<section id="tab-people"><div class="cols">
  <div class="list" id="plist"></div><div class="pane" id="pane"></div></div></section>

<section id="tab-world" class="hide">
  <h2>الأرض</h2>
  <p class="mut sm">الأخضر خصوبة · الإطار المتّصل قرية · الإطار المتقطّع محرّم</p>
  <div class="map" id="map"></div>
  <h2>القرى</h2>
  <div class="scroll"><table><tr><th>القرية</th><th>العدد</th><th>معارف</th>
    <th>الحاكم</th><th>الدورة</th><th>النجم</th><th>فساد الماء</th>
    <th>القراءة</th><th>الجدار</th><th>حرق</th></tr>
    <tbody id="sett"></tbody></table></div>
  <h2>المعرفة</h2><p id="tech"></p>
</section>

<section id="tab-names" class="hide">
  <h2>لماذا سُمّي الشيء بما سُمّي</h2>
  <div class="scroll"><table><tr><th>النوع</th><th>الاسم</th><th>سنة</th>
    <th>الأصل</th><th>الانجراف</th></tr><tbody id="names"></tbody></table></div>
</section>

<section id="tab-creed" class="hide">
  <h2>عقيدة {html.escape(d['god'])} · تعقيدها {d['complexity']}</h2>
  <div class="scroll"><table><tr><th>العقدة</th><th>الأرثوذكسية</th>
    <th>اختُبرت</th><th>في الواقع</th></tr><tbody id="tenets"></tbody></table></div>
</section>

<section id="tab-books" class="hide">
  <h2>ما كتبوه</h2>
  <p class="mut sm" id="bsum"></p>
  <div class="scroll"><table><tr><th>الكتاب</th><th>الأطروحة</th><th>سنة</th>
    <th>نُسخ</th><th>قُرئ</th><th>حُرق</th><th>يحمل الدورة</th></tr>
    <tbody id="books"></tbody></table></div>
</section>

<section id="tab-events" class="hide"><h2>ما جرى</h2><div id="events"></div></section>
</div>
<script>const DATA={json.dumps(d, ensure_ascii=False)};{_JS}</script>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path
