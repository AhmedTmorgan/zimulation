"""تقرير HTML قائم بذاته — بلا تبعيات ولا شبكة."""

import html
import math

from . import tech as T
from .lang import render_maxim
from .guard import truth_of, rewrites_of, children_of
from .memory import AR_SOURCES, SOURCES


def _esc(s):
    return html.escape(str(s))


def _path(rows, key, x0, y0, w, h, lo=None, hi=None):
    if not rows:
        return "", 0, 1
    vals = [r[key] for r in rows]
    lo = min(vals) if lo is None else lo
    hi = max(vals) if hi is None else hi
    if hi - lo < 1e-9:
        hi = lo + 1.0
    xs = [r["year"] for r in rows]
    x_lo, x_hi = xs[0], max(xs[-1], xs[0] + 1)
    pts = []
    for r in rows:
        x = x0 + (r["year"] - x_lo) / (x_hi - x_lo) * w
        y = y0 + h - (r[key] - lo) / (hi - lo) * h
        pts.append(f"{x:.1f},{y:.1f}")
    return "M" + " L".join(pts), lo, hi


def _chart(rows, series, title, height=190, logy=False):
    w, h = 860, height
    pad_l, pad_b, pad_t = 54, 26, 24
    iw, ih = w - pad_l - 16, h - pad_b - pad_t
    out = [f'<figure class="chart"><figcaption>{_esc(title)}</figcaption>',
           f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{_esc(title)}">']
    out.append(f'<rect x="{pad_l}" y="{pad_t}" width="{iw}" height="{ih}" class="plot"/>')
    for i in range(1, 4):
        y = pad_t + ih * i / 4
        out.append(f'<line x1="{pad_l}" x2="{pad_l+iw}" y1="{y:.0f}" y2="{y:.0f}" class="grid"/>')
    for key, label, cls in series:
        rows2 = rows
        if logy:
            rows2 = [dict(r, **{key: math.log10(max(1.0, r[key]))}) for r in rows]
        d, lo, hi = _path(rows2, key, pad_l, pad_t, iw, ih)
        if not d:
            continue
        out.append(f'<path d="{d}" class="ln {cls}"/>')
        if logy:
            lo, hi = 10 ** lo, 10 ** hi
        out.append(f'<text x="{pad_l - 6}" y="{pad_t + 10}" class="ax">{hi:,.0f}</text>'
                   if hi > 3 else
                   f'<text x="{pad_l - 6}" y="{pad_t + 10}" class="ax">{hi:.2f}</text>')
        out.append(f'<text x="{pad_l - 6}" y="{pad_t + ih}" class="ax">{lo:,.0f}</text>'
                   if hi > 3 else
                   f'<text x="{pad_l - 6}" y="{pad_t + ih}" class="ax">{lo:.2f}</text>')
    if rows:
        out.append(f'<text x="{pad_l}" y="{h - 6}" class="ax st">سنة {rows[0]["year"]}</text>')
        out.append(f'<text x="{pad_l+iw}" y="{h - 6}" class="ax en">سنة {rows[-1]["year"]:,}</text>')
    out.append("</svg>")
    keys = " ".join(
        f'<span class="key"><i class="{c}"></i>{_esc(l)}</span>' for _, l, c in series)
    out.append(f'<div class="keys">{keys}</div></figure>')
    return "\n".join(out)


def build(sim, path):
    cfg = sim.cfg
    ch = sim.chron
    rows = ch.snapshots
    world = sim.world
    alive = list(sim.agents.values())
    everyone = alive + sim.dead

    wr = world.wrath.history
    gaps = [wr[i + 1][0] - wr[i][0] for i in range(len(wr) - 1)]
    true_gap = sum(gaps) / len(gaps) if gaps else 0.0
    discovered = ch.by_kind("discovery")

    know = set()
    for st in world.settlements:
        know |= st.knowledge
    reached = [k for k in T.LANDMARKS if k in know]

    # الحِكَم التي ألّفوها
    maxims, seen = [], set()
    for a in alive:
        for m in a.prog.maxims:
            if m.lineage in seen:
                continue
            seen.add(m.lineage)
            maxims.append((m.taught, m, a))
    maxims.sort(key=lambda p: -p[0])

    # مزيج مصادر الذاكرة
    mix = [0.0] * 5
    for a in alive:
        sm = a.mem.source_mix()
        for i in range(5):
            mix[i] += sm[i]
    n = max(1, len(alive))
    mix = [v / n for v in mix]

    truth_now = sum(a.mem.truthfulness() for a in alive) / n if alive else 0.0

    P = []
    A = P.append
    A(f"""<!-- تقرير -->
<title>القرية — سِفر {sim.year:,} سنة</title>
<style>
:root{{--bg:#faf8f4;--fg:#1a1714;--mut:#6b6259;--line:#e2dbd0;--card:#fff;
--acc:#8c4a2f;--acc2:#2f5d62;--acc3:#7a6a2f;--bad:#9b2c2c;--ok:#2f6b3f;}}
@media(prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#14120f;--fg:#ece5da;
--mut:#9a9086;--line:#2c2721;--card:#1c1915;--acc:#d98c62;--acc2:#6fb3ba;--acc3:#c9b36a;
--bad:#e07070;--ok:#79c48d;}}}}
:root[data-theme="dark"]{{--bg:#14120f;--fg:#ece5da;--mut:#9a9086;--line:#2c2721;--card:#1c1915;
--acc:#d98c62;--acc2:#6fb3ba;--acc3:#c9b36a;--bad:#e07070;--ok:#79c48d;}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--fg);direction:rtl;
font:16px/1.75 "Segoe UI","Noto Naskh Arabic",Tahoma,sans-serif;margin:0}}
.wrap{{max-width:920px;margin:0 auto;padding:48px 22px 96px}}
h1{{font-size:2.1rem;line-height:1.25;margin:0 0 6px;letter-spacing:-.01em}}
h2{{font-size:1.32rem;margin:52px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--line)}}
h3{{font-size:1.02rem;margin:26px 0 8px;color:var(--acc)}}
p{{margin:0 0 14px}} .mut{{color:var(--mut)}}
.lede{{font-size:1.06rem;color:var(--mut);margin-bottom:26px}}
.grid{{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));margin:20px 0}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:13px 15px}}
.stat b{{display:block;font-size:1.5rem;line-height:1.2;font-variant-numeric:tabular-nums}}
.stat span{{font-size:.8rem;color:var(--mut)}}
.chart{{margin:22px 0;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}}
figcaption{{font-size:.9rem;color:var(--mut);margin-bottom:6px}}
svg{{width:100%;height:auto;display:block}}
.plot{{fill:none;stroke:var(--line)}} .grid{{stroke:var(--line);stroke-dasharray:2 4}}
.ln{{fill:none;stroke-width:1.9;stroke-linejoin:round}}
.c1{{stroke:var(--acc)}}.c2{{stroke:var(--acc2)}}.c3{{stroke:var(--acc3)}}
.c4{{stroke:var(--bad)}}.c5{{stroke:var(--ok)}}
.ax{{font-size:10px;fill:var(--mut)}} .st{{text-anchor:start}} .en{{text-anchor:end}}
.keys{{display:flex;gap:14px;flex-wrap:wrap;font-size:.82rem;color:var(--mut);margin-top:6px}}
.key i{{display:inline-block;width:14px;height:2.5px;vertical-align:middle;margin-left:5px}}
.key .c1{{background:var(--acc)}}.key .c2{{background:var(--acc2)}}.key .c3{{background:var(--acc3)}}
.key .c4{{background:var(--bad)}}.key .c5{{background:var(--ok)}}
.scroll{{overflow-x:auto;margin:14px 0}}
table{{border-collapse:collapse;width:100%;font-size:.88rem;min-width:520px}}
th,td{{text-align:right;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{color:var(--mut);font-weight:600;font-size:.8rem}}
td.num{{font-variant-numeric:tabular-nums}}
.ev{{border-right:2px solid var(--line);padding:2px 14px 2px 0;margin:0 0 2px}}
.ev.big{{border-right-color:var(--acc)}}
.ev time{{color:var(--mut);font-size:.82rem;font-variant-numeric:tabular-nums;margin-left:8px}}
blockquote{{margin:0 0 16px;padding:12px 16px;background:var(--card);
border:1px solid var(--line);border-right:3px solid var(--acc);border-radius:8px}}
code{{background:var(--card);border:1px solid var(--line);border-radius:5px;
padding:2px 7px;font-family:ui-monospace,Consolas,monospace;font-size:.86em;direction:rtl}}
.maxim{{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:9px 13px;margin:0 0 7px;display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}}
.verdict{{background:var(--card);border:1px solid var(--acc);border-radius:12px;padding:18px 20px;margin:24px 0}}
</style>
<div class="wrap">
<h1>القرية</h1>
<p class="lede">أربعة وثلاثون إنسانًا، وذاكرةُ ألفي سنة لم يعشها أحد منهم.
هذا ما جرى في {sim.year:,} سنة بعد ذلك.</p>""")

    A('<div class="grid">')
    for label, val in (
        ("من بقي", f"{sim.population():,}"),
        ("مواليد", f"{sim.stats['births']:,}"),
        ("وفيات", f"{sim.stats['deaths']:,}"),
        ("وقائع الغضب", f"{sim.stats['wraths']:,}"),
        ("ثورات", f"{sim.stats['revolts']:,}"),
        ("جرائم قتل", f"{sim.stats['murders']:,}"),
        ("اضطهاد", f"{sim.stats['persecutions']:,}"),
        ("قرى", f"{len(world.settlements):,}"),
        ("معارف", f"{len(know)}"),
        ("مذاهب", f"{len(sim.doctrines)}"),
    ):
        A(f'<div class="stat"><b>{val}</b><span>{label}</span></div>')
    A("</div>")

    # ---------------------------------------------------------- الحُكم
    A('<div class="verdict"><h3 style="margin-top:0">الحُكم</h3>')
    if not alive:
        A(f"<p><strong>انقرضوا في سنة {sim.year:,}.</strong> "
          "لم يبلغوا الكتابة ولا التقويم، ولم يعرف أحدٌ منهم قطّ أن غضب إلههم "
          "كان موعدًا لا عقابًا.</p>")
    elif discovered:
        e = discovered[0]
        A(f"<p><strong>اكتشفوها.</strong> في سنة {e.year:,} {_esc(e.text)}</p>")
        A(f"<p>الدورة الحقيقية التي زرعتُها في العالم: "
          f"<strong>{true_gap:.1f}</strong> سنة. وما لم يعرفوه قرونًا صار رقمًا.</p>")
    else:
        A("<p><strong>لم يكتشفوها.</strong> ما زالوا يفسّرون الموتَ الدوريّ ذنبًا. "
          f"الدورة الحقيقية {true_gap:.1f} سنة، ولا أحد فيهم يعلم.</p>")
    if reached:
        A("<p>ما بلغوه من المعالم: " +
          "، ".join(_esc(T.BY_KEY[k][1]) for k in reached) + ".</p>")
    A("</div>")

    # ---------------------------------------------------------- الرسوم
    A("<h2>ما جرى بالأرقام</h2>")
    if rows:
        A(_chart(rows, [("pop", "العدد", "c1")], "عدد السكان"))
        A(_chart(rows, [("faith", "الإيمان", "c1"), ("doubt", "الشكّ", "c2"),
                        ("truth", "صدق الذاكرة", "c3")],
                 "الإيمان والشكّ ونسبة ما هو حقيقي في ذاكرتهم"))
        A(_chart(rows, [("tyranny", "الطغيان", "c4"), ("tech", "المعارف", "c5")],
                 "الطغيان مقابل المعرفة"))
        A(_chart(rows, [("complexity", "تعقيد الكود", "c2"),
                        ("doctrine", "تعقيد العقيدة", "c1")],
                 "الكود الذي يكتبونه مقابل العقيدة التي يراكمونها"))

    # ---------------------------------------------------------- الذاكرة
    A("<h2>ذاكرتهم</h2>")
    A(f"<p>ما يعتقده الأحياء اليوم عن ماضيهم صحيحٌ بنسبة "
      f"<strong>{truth_now:.0%}</strong>. والباقي مزروع أو مسموع أو محلوم "
      f"أو مُختلَق — ولا أحد منهم يملك وسيلة للتمييز.</p>")
    A('<div class="scroll"><table><tr><th>المصدر</th><th>الوزن في الذاكرة الحيّة</th></tr>')
    for i, s in enumerate(SOURCES):
        A(f'<tr><td>{_esc(AR_SOURCES[s])}</td><td class="num">{mix[i]:.1%}</td></tr>')
    A("</table></div>")

    # ---------------------------------------------------------- العقيدة
    A("<h2>العقيدة</h2>")
    st0 = world.settlements[0]
    d = st0.doctrine
    if d is not None:
        A(f"<p>الإله <strong>{_esc(d.god)}</strong>. تعقيد العقيدة اليوم "
          f"<strong>{d.complexity:.1f}</strong> (بدأت عند 5). "
          f"شهداء: {d.martyrs} · اضطهادات: {d.persecutions} · انشقاقات: {d.schisms}.</p>")
        A('<div class="scroll"><table><tr><th>العقدة</th><th>الأرثوذكسية</th>'
          '<th>اختُبرت</th><th>الواقع</th></tr>')
        for t in d.tenets.values():
            real = "صحيحة" if t.true_in_world else "<b>كاذبة</b>"
            A(f'<tr><td>{_esc(t.text)}</td><td class="num">{t.strength:.2f}</td>'
              f'<td class="num">{t.tested}</td><td>{real}</td></tr>')
        A("</table></div>")
        riders = []
        for t in d.tenets.values():
            riders += [r for r, _ in t.riders]
        for a in alive[:60]:
            riders += a.riders
        riders = list(dict.fromkeys(riders))[:12]
        if riders:
            A("<h3>التبريرات التي راكموها كي تنجو العقيدة من الدليل</h3>")
            for r in riders:
                A(f"<blockquote>{_esc(r)}</blockquote>")

    # ---------------------------------------------------------- الغضب
    A("<h2>الغضب</h2>")
    A(f"<p>وقع <strong>{len(wr)}</strong> مرة. المتوسط الحقيقي بين الوقائع "
      f"<strong>{true_gap:.1f}</strong> سنة — وهذا رقمٌ في فيزياء العالم لا في عقيدتهم.</p>")
    if wr:
        A('<div class="scroll"><table><tr><th>السنة</th><th>الوجه</th>'
          '<th>الشدّة</th><th>الفاصل</th></tr>')
        show = wr[:6] + ([("…", "", None)] if len(wr) > 12 else []) + wr[-6:] \
            if len(wr) > 12 else wr
        prev = None
        for row in show:
            if row[0] == "…":
                A('<tr><td colspan="4" class="mut">…</td></tr>'); prev = None; continue
            y, kind, sev = row
            gap = f"{y - prev}" if prev else "—"
            prev = y
            A(f'<tr><td class="num">{y:,}</td><td>{_esc(kind)}</td>'
              f'<td class="num">{sev:.0%}</td><td class="num">{gap}</td></tr>')
        A("</table></div>")

    # ---------------------------------------------------------- الكود
    A("<h2>الكود الذي كتبوه بأنفسهم</h2>")
    A("<p>حِكَمٌ لم يضعها أحد في البرنامج. ألّفها كائنٌ أثناء تأمّله من ارتباطٍ "
      "لمحه بين موقفٍ يتذكّره ونتيجةٍ يتذكّرها — ثم عُلّمت وورِثت وتشوّهت في كل نقل.</p>")
    if maxims:
        for taught, m, a in maxims[:16]:
            A(f'<div class="maxim"><code>{_esc(render_maxim(m))}</code>'
              f'<span class="mut">{_esc(a.name)} · نُقلت {taught} مرة</span></div>')
    else:
        A('<p class="mut">لم يؤلّفوا شيئًا بعد.</p>')

    # ---------------------------------------------------------- المدارس
    W = sim.world
    pop_of = {}
    for a in sim.agents.values():
        if a.school >= 0:
            pop_of[a.school] = pop_of.get(a.school, 0) + 1
    bk_of = {}
    for st in sim.world.settlements:
        for b in st.library.books:
            if b.school >= 0:
                bk_of[b.school] = bk_of.get(b.school, 0) + 1
    if W.schools:
        A("<h2>المدارس</h2>")
        A("<p>لم تُوضع في البرنامج مذاهب. المدرسة جوابٌ بعينه على مسألةٍ بعينها "
          "— والمسألة مفهومٌ صاغه أحدُهم، والجواب جهةُ اقترانه عنده. ومن بلغ "
          "في مسألةٍ جوابًا يناقض جواب مدرسته انشقّ عنها وأسّس ضدَّها، "
          "ومن وافق انتسب ولم يؤسّس شيئًا.<br>"
          f"قام <b>{len(W.schools):,}</b> مذهبًا، منها "
          f"<b>{sim.stats.get('schisms', 0):,}</b> عن انشقاق. "
          f"ووقعت <b>{sim.stats.get('debates', 0):,}</b> مناظرة "
          f"تحوّل فيها <b>{sim.stats.get('converts', 0):,}</b> "
          f"وتصلّب <b>{sim.stats.get('hardened', 0):,}</b>، "
          f"وانتسب بالقراءة <b>{sim.stats.get('joined', 0):,}</b>.</p>")
        A('<div class="scroll"><table><tr><th>المذهب</th><th>المسألة</th>'
          '<th>الجواب</th><th>مؤسّسه</th><th>موطنه</th><th>تأسّس</th>'
          '<th>أتباع</th><th>كتب</th><th>انشقّ عن</th></tr>')
        rank = sorted(W.schools.values(),
                      key=lambda s: (-pop_of.get(s.id, 0), s.born))[:26]
        for s in rank:
            par = W.schools.get(s.parent)
            A(f'<tr><td>{_esc(s.name)}</td><td>{_esc(s.label)}</td>'
              f'<td>{"يُثبت" if s.sign > 0 else "ينفي"}</td>'
              f'<td>{_esc(s.founder)}</td><td>{_esc(s.home)}</td>'
              f'<td class="num">{s.born:,}</td>'
              f'<td class="num">{pop_of.get(s.id, 0)}</td>'
              f'<td class="num">{bk_of.get(s.id, 0)}</td>'
              f'<td>{_esc(par.name) if par else "—"}</td></tr>')
        A("</table></div>")

    # ---------------------------------------------------------- الحقب
    eras = ch.eras(max(200, sim.year // 12) if sim.year > 400 else 100)
    if eras:
        A("<h2>الحقب</h2>")
        A('<div class="scroll"><table><tr><th>الحقبة</th><th>العدد</th><th>قرى</th>'
          '<th>معارف</th><th>إيمان</th><th>طغيان</th><th>غضب</th><th>ثورات</th>'
          '<th>قتل</th><th>صدق الذاكرة</th></tr>')
        for e in eras:
            A(f'<tr><td class="num">{e["start"]:,}–{e["end"]:,}</td>'
              f'<td class="num">{e["pop_end"]:,}</td><td class="num">{e["settlements"]}</td>'
              f'<td class="num">{e["tech"]}</td><td class="num">{e["faith"]:.2f}</td>'
              f'<td class="num">{e["tyranny"]:.2f}</td><td class="num">{e["wraths"]}</td>'
              f'<td class="num">{e["revolts"]}</td><td class="num">{e["murders"]}</td>'
              f'<td class="num">{e["truth"]:.2f}</td></tr>')
        A("</table></div>")

    # ---------------------------------------------------------- الوقائع
    A("<h2>أهمّ ما جرى</h2>")
    for e in ch.major(2.5)[:120]:
        big = " big" if e.weight >= 3.5 else ""
        A(f'<p class="ev{big}"><time>سنة {e.year:,}</time>{_esc(e.text)}</p>')

    # ---------------------------------------------------------- أناس
    A("<h2>أناس</h2>")
    def card(a, why):
        return (f'<tr><td>{_esc(a.label())}</td><td>{_esc(why)}</td>'
                f'<td class="num">{a.age}</td><td>{_esc(a.creed())}</td>'
                f'<td class="num">{truth_of(a):.2f}</td></tr>')
    picks = []
    if everyone:
        picks.append((max(everyone, key=lambda a: a.age), "أطول من عاش"))
        picks.append((max(everyone, key=lambda a: a.dominance), "أشدّهم بطشًا"))
        picks.append((max(everyone, key=lambda a: a.prestige), "أرفعهم هيبة"))
        picks.append((max(everyone, key=lambda a: a.kills), "أكثرهم قتلًا"))
        picks.append((max(everyone, key=lambda a: a.rule_years), "أطولهم حكمًا"))
        picks.append((max(everyone, key=rewrites_of), "أكثرهم إعادةً لكتابة نفسه"))
        picks.append((max(everyone, key=children_of), "أكثرهم نسلًا"))
        her = [a for a in everyone if a.heretic]
        if her:
            picks.append((her[0], "أول من أنكر"))
    A('<div class="scroll"><table><tr><th>الاسم</th><th>لماذا</th><th>العمر</th>'
      '<th>الموقف</th><th>صدق ذاكرته</th></tr>')
    done = set()
    for a, why in picks:
        if a.id in done:
            continue
        done.add(a.id)
        A(card(a, why))
    A("</table></div>")

    A(f'<h2>عن هذا العالم</h2><p class="mut">بذرة {cfg.seed} · '
      f'ماضٍ مزروع طوله {cfg.prior_years:,} سنة ({sim.history["generations"]} جيلًا) · '
      f'كائنات بمحاكاة معرفية كاملة حتى {cfg.max_named} · '
      f'دورة الغضب المضبوطة {cfg.wrath_period:.0f} سنة بتشويش ±{cfg.wrath_jitter:.0f}.<br>'
      'لم يقع شيء مما يتذكّرونه عن الألفي سنة الأولى.</p>')
    A("</div>")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(P))
    return path
