"""
اختبارات القلب.

أثمن ما في هذا المشروع ليس ميكانيكاته، بل **ضمان الحتمية**: بذرةٌ واحدة
مع إصدارٍ واحد تعطي التاريخ نفسه بالحرف. بغير هذا الضمان لا نتيجةَ قابلة
للتحقّق، ولا مساهمَ يستطيع أن يعرف هل كسر شيئًا.

    python -m pytest tests -q      (أو)      python tests/test_core.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from village.config import Config
from village.engine import Sim
from village import genome as G
from village import mind as M
from village import naming as NM
from village import speech as SP
from village.memory import MemoryBank, S_IMPLANT, S_LIVED, K_VISION


def _sim(seed=7, years=0, **kw):
    cfg = Config()
    cfg.seed = seed
    cfg.mem_limit_mb = 0
    for k, v in kw.items():
        setattr(cfg, k, v)
    s = Sim(cfg)
    if years:
        s.run(years)
    return s


# ===================================================== الحتمية
def test_same_seed_same_history():
    """نفس البذرة ⇒ نفس التاريخ بالحرف. هذا هو العقد الأساسي."""
    a = _sim(11, 120)
    b = _sim(11, 120)
    assert a.population() == b.population()
    assert a.stats == b.stats
    assert [e.text for e in a.chron.events] == [e.text for e in b.chron.events]
    assert [x.name for x in a.names.items] == [x.name for x in b.names.items]


def test_different_seed_different_history():
    """وبذرتان مختلفتان ⇒ تاريخان مختلفان — وإلا فالعشوائية معطّلة."""
    a = _sim(11, 120)
    b = _sim(12, 120)
    assert a.population() != b.population() or a.stats != b.stats


def test_resume_matches_continuous():
    """التقطيع لا يغيّر النتيجة: 60+60 = 120."""
    a = _sim(5, 120)
    b = _sim(5, 60)
    b.run(60)
    assert a.population() == b.population()
    assert a.stats == b.stats


# ===================================================== حاجز الصدق
def test_agent_cannot_read_truth():
    """
    لا شيء في مسار قرار الكائن يقرأ `truth`. هذا حاجزٌ نصونه بالاختبار
    لا بالنيّة: إن تسرّب يومًا انهار المشروع كله.
    """
    import inspect
    for mod in (M, SP):
        src = inspect.getsource(mod)
        assert ".truth" not in src, f"{mod.__name__} يقرأ صدق الأثر"
    # ودالّة القرار لا ترى الآثار أصلًا
    assert "truth" not in inspect.getsource(M.decide)
    assert "truth" not in inspect.getsource(M.reflect)


def test_false_memory_indistinguishable():
    """الأثر الملفّق يُسترجَع كما يُسترجَع المعاش تمامًا."""
    import random
    mem = MemoryBank(40, 0.6)
    mem.store(K_VISION, 0, val=0.8, strength=1.5, truth=1.0, src=S_LIVED)
    mem.store(K_VISION, 0, val=0.8, strength=1.5, truth=0.0, src=S_IMPLANT)
    got = mem.recall(random.Random(1), 1, kind=K_VISION, k=5)
    assert len(got) == 2
    assert {t.strength for t in got} == {1.5 * 1.05}


# ===================================================== الموارد
def test_memory_stays_flat():
    """رنٌّ طويل لا يسرّب: كان هذا الباج يجمّد الأجهزة."""
    from village.guard import rss_mb
    s = _sim(3, 40)
    before = rss_mb()
    s.run(220)
    after = rss_mb()
    assert after - before < 60, f"تسرّب {after - before:.0f} ميجابايت"


def test_pathogens_bounded():
    """السلالات لا تتكاثر أسّيًا — كانت تبلغ الملايين."""
    s = _sim(3, 200)
    assert len(s.pathogens) <= s.cfg.max_strains


def test_dead_are_compact():
    """الراحل يُحفظ سجلًّا لا كائنًا كاملًا."""
    from village.guard import Departed
    s = _sim(3, 80)
    assert s.dead, "لم يمت أحد — الاختبار بلا معنى"
    assert all(isinstance(d, Departed) for d in s.dead)
    assert not hasattr(s.dead[0], "mem")


def test_population_balance():
    """مواليد − وفيات = فرقُ التعداد. اختلّ هذا مرّة بمئات الآلاف."""
    s = _sim(9, 200)
    start = len(Sim(Config()).agents)
    drift = s.stats["births"] - s.stats["deaths"] - (s.population() - start)
    assert abs(drift) <= 2, f"الميزان مختلّ بمقدار {drift}"


# ===================================================== العقيدة فردية
def test_conviction_is_personal():
    """قناعة الواحد لا تكون قناعة الجميع."""
    s = _sim(4, 40)
    key = "wrath_is_sin"
    vals = [a.conv.get(key, 0.0) for a in s.agents.values() if key in a.conv]
    assert len(vals) > 5
    assert max(vals) - min(vals) > 0.25, "الجميع يعتقد الشيء نفسه بالقدر نفسه"


def test_orthodoxy_is_aggregate():
    """ما تعلنه القرية متوسطٌ لما في الصدور، لا مصدرٌ له."""
    s = _sim(4, 40)
    st = s.world.settlements[0]
    t = st.doctrine.tenets["wrath_is_sin"]
    held = [a.conv.get("wrath_is_sin", 0.0) for a in s.agents.values()]
    assert min(held) <= t.strength <= max(held) + 0.2


# ===================================================== الكلام له نَسَب
def test_every_utterance_has_provenance():
    """كل قولٍ يُنسَب إلى ما في حياة قائله. وإلا فهو من كتابتي أنا."""
    s = _sim(6, 180)
    said = [u for a in s.agents.values() for u in a.said]
    assert said, "لم يقولوا شيئًا"
    for u in said:
        assert u.why, f"قولٌ بلا نَسَب: {u.text}"
        assert u.author > 0


def test_no_prewritten_claims_left():
    """لا قوائم نصوصٍ جاهزة يختار منها الكائن."""
    import inspect
    from village import faith as FA
    src = inspect.getsource(FA)
    assert "_RIDERS" not in src and "_rider" not in src


# ===================================================== القوانين المخبّأة
def test_star_correlation_is_real():
    """ارتباط النجم بالخصب قائمٌ في الفيزياء — وإلا فاكتشافه وهم."""
    s = _sim(2)
    w = s.world
    hits = 0
    for y in range(1, 900):
        w.step_climate(y, s.rs.get("climate"))
        if w.star_early(y) == w.bountiful():
            hits += 1
    assert hits / 899 > 0.60, "لا ارتباط — فالكشف الذي يقع عليه بلا أساس"


def test_wrath_is_periodic_not_moral():
    """الغضب دوريّ، ولا علاقة له بتقوى ولا طقس."""
    import inspect
    from village.engine import Sim as S
    src = inspect.getsource(S._wrath)
    for word in ("faith", "conv[", "clergy", "tribute > "):
        assert word not in src.split("frail")[0], f"التقوى تدخل حساب الهلاك: {word}"


def test_method_requires_discovery():
    """لا منهج تجريبي بغير سابقةٍ طبيعية حلّت محلّ تفسيرٍ إلهي."""
    import inspect
    src = inspect.getsource(Sim._tech)
    assert 'known_period is None' in src and '"method"' in src


# ===================================================== الأصول
def test_names_carry_origins():
    """كل مسمّى يعرف من سمّاه وعلى أي شيء."""
    s = _sim(8, 520)
    assert s.names.items, "لم يسمّوا شيئًا في ستّة قرون"
    for n in s.names.items:
        assert n.namer and n.year >= 0
        assert n.tale()


def test_origins_get_forgotten():
    """ويُنسى السبب ويبقى الاسم — وهذا هو المقصود."""
    s = _sim(8, 700)
    lost = [n for n in s.names.items if n.origin_lost]
    assert lost, "لم يُنسَ سببُ شيء بعد تسعة قرون"




# ===================================================== السببية
def test_no_lifespan_constant():
    """
    لا رقمَ اسمه «العمر» في الكود. العمر نتيجةٌ لا معامل — وإن عاد
    ثابتًا يومًا فقد عاد النموذج إلى فرض نتائجه.
    """
    import inspect
    from village.engine import Sim as S
    src = inspect.getsource(S._lifecycle)
    assert "base_lifespan" not in src, "عاد العمر معاملًا مفروضًا"
    assert "CA.hazard" in src and "CA.wear" in src


def test_causes_have_levers():
    """كل سببٍ يُطفَأ فتُقارن الدنيا به وبدونه."""
    cfg = Config()
    for k in ("cause_water", "cause_toil", "cause_soma", "cause_tumour"):
        assert hasattr(cfg, k), f"لا مِعوَل لـ{k}"


def test_mechanism_signs_are_right():
    """
    الآلية معزولةً عن البيئة: رفعُ أذًى يزيد العمر. وإن انقلبت إشارةٌ
    هنا فالخلل في الآلية لا في الإيكولوجيا.
    """
    import subprocess
    import sys as _s
    from analytic import age_at_failure
    base = age_at_failure(Config())
    for k in ("cause_water", "cause_toil", "cause_soma"):
        cfg = Config()
        setattr(cfg, k, False)
        assert age_at_failure(cfg) >= base, f"إشارة {k} مقلوبة في الآلية"


def test_tumour_needs_long_life():
    """الورم لا يُرى حيث يقصر العمر — وهذا شرطُ صدق النموذج."""
    s = _sim(21, 200)
    dead = [d for d in s.dead if d.cause == "ورم"]
    if not dead:
        return                      # لم يبلغوا العمر الذي يُظهره
    mean_t = sum(d.age for d in dead) / len(dead)
    others = [d.age for d in s.dead if d.age >= 5 and d.cause != "ورم"]
    assert mean_t > sum(others) / len(others), "الورم يصيب الشباب — خطأ"
    assert len(dead) / max(1, len(s.dead)) < 0.12, "الورم أكثر من حقّه"


def test_every_death_has_a_chain():
    """لا موتَ بوسمٍ مجرّد: لكل موتةٍ من التراكم سلسلةُ سببٍ تُقرأ."""
    s = _sim(22, 140)
    natural = [d for d in s.dead if d.cause in ("وهنٌ", "ورم", "إنهاك", "حادث")]
    assert natural, "لم يمت أحدٌ موتًا طبيعيًا"
    for d in natural[:40]:
        assert d.why_died, f"موتةٌ بلا سبب: {d.name}"
        assert "أذًى" in d.why_died or "تراكم" in d.why_died or "بلغ" in d.why_died


def test_water_and_literacy_are_derived():
    """فسادُ الماء والجهل نتيجتان لا ثابتان."""
    from village import causes as CA
    know_dirty = {"copper", "bronze", "iron", "irrigation"}
    know_clean = know_dirty | {"pottery", "law", "geometry", "medicine", "method"}
    reg = object()
    assert CA.foul(reg, 800, know_clean) < CA.foul(reg, 800, know_dirty)
    assert CA.foul(reg, 60, know_dirty) < CA.foul(reg, 900, know_dirty)


def test_epidemics_are_derived():
    """
    الوباء نتيجةٌ لا احتمالٌ ثابت: يرتفع بالاستئناس والكثافة والاتصال،
    وينخفض بالطبّ. وإن لم يتحرّك بتحرّكها فقد عاد ثابتًا.
    """
    import inspect
    from village import causes as CA
    from village.engine import Sim as S
    assert "outbreak_chance" not in inspect.getsource(S._disease)
    small = _sim(31, 60)
    big = _sim(31, 320)
    assert CA.outbreak_pressure(big) > CA.outbreak_pressure(small) * 1.8, \
        "لم يرتفع ضغط الوباء مع نموّ المجتمع واتصاله"


def test_period_detection_works():
    """
    آلية الكشف نفسها — لا تبلغها رنّاتُ السبعمئة سنة (تحتاج نحو 1200)،
    فتبقى غير مختبَرة إن لم تُفحَص مباشرةً.

    وشروطها ثلاثة، ويسقط الكشف بسقوط أيّها: سجلٌّ لا يقلّ عن ستّ وقائع،
    وتقويمٌ يثبّت الأرقام، وعقلٌ يقارن.
    """
    from village.faith import detect_period
    clean = [0, 27, 54, 81, 108, 135, 162]          # نظمٌ تامّ
    real = [0, 21, 54, 78, 109, 131, 163]           # بتشويشٍ كتشويش العالم
    noisy = [0, 6, 41, 48, 96, 101, 155]            # بلا دوريّة

    got = detect_period(clean, 0.9, True)
    assert got is not None and 25 <= got <= 29, f"لم يُقرأ النظم التام: {got}"
    # وما كان نظمُه تامًّا يراه كلُّ أحد — وذلك صواب لا خلل
    assert detect_period(clean, 0.05, True) is not None

    # أما تشويشُ الواقع فلا يُخترق إلا بعقل
    assert detect_period(real, 0.85, True) is not None, "لم يره العقل القوي"
    assert detect_period(real, 0.15, True) is None, "رآه العقل الضعيف"

    assert detect_period(real, 0.9, False) is None, "كُشف بلا تقويم"
    assert detect_period(real[:4], 0.9, True) is None, "كُشف بسجلٍّ قصير"
    assert detect_period(noisy, 0.95, True) is None, "كُشفت دوريّةٌ لا وجود لها"


def test_taboo_gates_the_calendar():
    """المحرّم على إحصاء النجوم يحجب التقويم — وهو آخر بوّابةٍ قبل الكشف."""
    from village import tech as T
    blocked = set(T.TABOO_BLOCKS["counting_stars"])
    assert "calendar" in blocked and "astronomy" in blocked
    assert "counting" not in blocked, "حجبُ الإحصاء يقطع الطريق كلَّه"
    assert "writing" not in blocked


# ---------------------------------------------------------------- المناخ
def test_climate_is_not_a_written_cycle():
    """
    الجيبُ المكتوب يعطي نوبةً على ميقات. والمرجّح المخمَّد لا يعطيه.
    فإن تساوت أطوال النوبات فقد رجعنا إلى ما هربنا منه.
    """
    import random
    import itertools
    import statistics as S
    from village.climate import Climate
    cfg = Config()
    r = random.Random(3)
    sky = Climate(cfg, r)
    v = [sky.step(y, r, 0.0) for y in range(2000)]
    runs = [len(list(g)) for _, g in itertools.groupby(1 if x > 1.0 else 0 for x in v)]
    assert len(runs) > 60, f"نوبتان فقط؟ {len(runs)}"
    assert S.pstdev(runs) > 0.8 * S.mean(runs),         f"أطوال النوبات متقاربة ({S.mean(runs):.1f}±{S.pstdev(runs):.1f}) — هذا ميقات"


def test_star_and_bounty_share_a_cause_not_a_line_of_code():
    """
    الارتباط بين النجم والخصب يجب أن يمرّ **بالغبار**. فإن ثُبّت الغبار
    ولم ينكسر الارتباط فمعناه أني كتبتُه في موضعين لا أنه في عالمهم.
    """
    import random
    from village.climate import Climate
    cfg = Config()

    def agree(freeze):
        r = random.Random(21)
        sky = Climate(cfg, r)
        hits = 0
        for y in range(1500):
            sky.step(y, r, 0.0)
            if freeze:
                sky.dust = sky.norm      # هواءٌ لا يتغيّر: تُقطع القناة
            hits += (sky.star_early() == sky.bountiful())
        return hits / 1500.0

    live, cut = agree(False), agree(True)
    assert live > 0.60, f"العلامة لا تُفيد شيئًا ({live:.2f})"
    assert cut < 0.55, f"الارتباط بقي بعد قطع الغبار ({cut:.2f}) — فهو يدي لا عالمهم"


def test_every_tuned_sky_constant_is_declared():
    """لا تُخبَّأ مضبوطةٌ في ملفّ المناخ خارج البيان."""
    import re
    from village import climate as CL
    src = pathlib.Path(CL.__file__).read_text(encoding="utf-8")
    names = set(re.findall(r"^([A-Z][A-Z_0-9]*) = ", src, re.M))
    orbital = {"PRECESSION", "OBLIQUITY", "ECCENTRIC"}
    missing = names - orbital - set(CL.TUNED) - {"TUNED"}
    assert not missing, f"مضبوطات لم تُعلَن: {missing}"


def test_manifest_counts_the_sky():
    """عدد المعاملات الحرّة يُحصى من الكود، فلا يمكن أن يكذب."""
    from village import plugin as PG
    from village import climate as CL
    txt = PG.manifest()
    assert f"`climate` {len(CL.TUNED)}" in txt, "بيانٌ لا يُحصي مضبوطات المناخ"
    assert "لم تُعلن" in txt, "بيانٌ لا يعترف بما لم يُحصَ"


# ---------------------------------------------------------------- المفاهيم
def test_they_can_conceive_of_harm_not_only_good():
    """
    كان كلُّ ما يُصاغ من جنسٍ واحد: «هذان يجتمعان فيأتي الخير» — لأن
    الكدح وحده كان يُسجَّل موقفًا يُقاس عليه. فلا محرَّمَ يُستنبَط ولا
    خوفَ يُصاغ ولا خلافَ ممكن، إذ لا يختلف اثنان وكلاهما يُثبت.
    """
    sim = _sim(seed=5, years=320)
    vals = [c.value for a in sim.agents.values() for c in a.concepts]
    assert len(vals) > 40, f"لم يصوغوا ما يكفي ({len(vals)})"
    neg = sum(1 for v in vals if v < 0)
    assert neg >= 0.12 * len(vals),         f"{neg} من {len(vals)} سالب — نصفُ نحوهم ميّت"


def test_lived_pain_reaches_the_mind_not_only_lived_labour():
    """كلّ ما عاشه يصلح أن يُتعلَّم منه، لا الحصاد وحده."""
    sim = _sim(seed=9, years=120)
    seen = set()
    for a in sim.agents.values():
        for _, _, tr in a.prog.episodes:
            if tr is not None:
                seen.add(tr.kind)
    assert len(seen) >= 3, f"العقل لا يرى إلا {seen}"


# ---------------------------------------------------------------- المدارس
def test_a_school_is_a_position_not_a_number():
    """
    لا تقوم مدرسةٌ بمجرّد التأليف. وكلُّ مدرسةٍ لها أمٌّ يجب أن تخالفها
    في المسألة نفسها — وإلا فالانشقاق اسمٌ بلا معنى.
    """
    from village import library as LB
    sim = _sim(seed=11, years=420)
    W = sim.world
    for s in W.schools.values():
        assert s.topic, "مدرسةٌ بلا مسألة"
        par = W.schools.get(s.parent)
        if par is not None:
            assert LB.opposes(s, par),                 f"«{s.name}» انشقّت عن «{par.name}» بلا خلاف"


def test_every_sky_lever_moves_the_world():
    """
    مِعوَلٌ لا يحرّك شيئًا دعوى كاذبة. فكلُّ سببٍ في السماء يُطفَأ وحده،
    ويجب أن تختلف الدنيا به وبدونه اختلافًا يُقاس.
    """
    import random
    import statistics as S
    from village.climate import Climate

    def run(**off):
        cfg = Config()
        for k, v in off.items():
            setattr(cfg, k, v)
        r = random.Random(17)
        sky = Climate(cfg, r)
        # عريٌ يتصاعد، وإلا لم يظهر أثرُ البياض أصلًا
        return [sky.step(y, r, min(0.45, 0.00012 * y)) for y in range(3000)]

    base = run()
    bm, bs = S.mean(base), S.pstdev(base)
    for lever in ("sky_orbit", "sky_ocean", "sky_volcano", "sky_albedo"):
        v = run(**{lever: False})
        dm = abs(S.mean(v) - bm)
        ds = abs(S.pstdev(v) - bs)
        assert dm > 0.004 or ds > 0.004,             f"«{lever}» يُطفأ فلا تتغيّر الدنيا (Δوسط {dm:.4f}، Δانحراف {ds:.4f})"


# ============================================== الطبّ: ما لا يعرفونه
#: ما لا يجوز أن يُقرأ من داخل مسار قرارِ كائن.
_SECRETS = (".counter", ".toxic", ".potency", ".mech", ".stubborn",
            "best_dose")
#: ومن يجوز له: النبات نفسه (فيه تُحسب الحقيقة)، والعلل، والمراقب.
_ORACLES = ("flora.py", "malady.py", "report.py", "observe.py",
            "analytic.py", "validate.py")


def test_healer_cannot_read_the_cure():
    """
    **العمود الفقري لهذه الإضافة كلها.**

    في هذا العالم دواءٌ لأكثر الأدواء، ونحن نعرفه. فإن تسرّب إلى عقل
    كائنٍ حرفٌ منه — قوّةُ النبتة أو سمّيتها أو آليّة الداء — لم يعد
    ما يفعلونه اكتشافًا، صار قراءةً لما كتبتُه لهم. وهذا هو الكذب
    الذي بُني المشروع كلّه على تجنّبه.
    """
    import village
    root = pathlib.Path(village.__file__).parent
    bad = []
    for f in sorted(root.glob("*.py")):
        if f.name in _ORACLES:
            continue
        src = f.read_text(encoding="utf-8")
        # يُطرح ما في التعليقات والنصوص التوثيقية
        code = chr(10).join(ln.split("#")[0] for ln in src.splitlines())
        for s in _SECRETS:
            if s in code:
                bad.append(f"{f.name}: {s}")
    assert not bad, "تسرّبت حقيقةُ الدواء إلى: " + "، ".join(bad)


def test_no_illness_without_its_cause():
    """
    لا يقع داءٌ لم يُصنَع سببُه. قومٌ لم يستأنسوا لا يصيبهم داءُ الماشية،
    وقريةٌ دون الحدّ الحرج لا يستوطنها داءُ الزحام مهما طال الزمن.
    """
    from village import malady as MD

    class R:
        biome = 0

    class S:
        knowledge = set()

    # لا استئناس ولا زحام ولا ماءٌ فاسد ولا سبخة
    p = MD.pressures(S(), R(), set(), 60, 0.0, 1.0, 0.0)
    assert "zoonosis" not in p, "داءُ الماشية بلا ماشية"
    assert "crowd" not in p, "داءُ الزحام في ستّين نفسًا"
    assert "water" not in p, "داءُ الماء وماؤهم نظيف"
    assert "vector" not in p, "داءُ السبخة بلا سبخة"

    p2 = MD.pressures(S(), R(), {"herding"}, 600, 0.5, 1.0, 1.0)
    for fam in ("zoonosis", "crowd", "water", "vector"):
        assert p2.get(fam, 0.0) > 0.0, f"سببٌ قائم ولا يقع داؤه: {fam}"


def test_the_dose_makes_the_poison():
    """
    باراسيلسوس: لا نبتةَ شفاءٍ ولا نبتةَ موت — مقدارٌ فقط. فلكل نبتةٍ
    نافعةٍ حدٌّ ينقلب بعده نفعُها ضرًّا.
    """
    from village import flora as FL
    from village import malady as MD
    mals, plants = MD.build(), FL.build()
    flips = 0
    checked = 0
    for pl in plants[:400]:
        for m in mals:
            d, v = FL.best_dose(pl, m)
            if v > 0.30:
                checked += 1
                h1, x1 = FL.outcome(pl, d, "نيء", m, 0.7)
                h2, x2 = FL.outcome(pl, d * 3.0, "نيء", m, 0.7)
                if (h2 - x2) < (h1 - x1):
                    flips += 1
                break
    assert checked > 5, "لم نجد أدويةً نافعةً لنفحصها"
    assert flips == checked,         f"{checked - flips} نبتةً لا يضرّ إفراطُها — فلا معنى للمقدار"


def test_some_ills_have_no_herb():
    """
    ليس لكل داءٍ دواء. وما بَلِي أو جاء من الدم أو من الهمّ لا تردّه
    ورقة — ومن وعدهم بغير ذلك وعدهم بما ليس عنده.
    """
    from village import flora as FL
    from village import malady as MD
    mals, plants = MD.build(), FL.build()
    hopeless = 0
    for m in mals:
        if m.family not in ("congenital", "degenerative", "melancholy"):
            continue
        best = 0.0
        for pl in plants[:900]:
            _, v = FL.best_dose(pl, m)
            best = max(best, v)
        if best < 0.25:
            hopeless += 1
    assert hopeless >= 15, f"عددُ ما لا دواء له {hopeless} — قليل"


def _run_all():
    ok = fail = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ✓ {name}")
            ok += 1
        except AssertionError as e:
            print(f"  ✗ {name}: {e}")
            fail += 1
        except Exception as e:
            print(f"  ! {name}: {type(e).__name__}: {e}")
            fail += 1
    print(f"\n{ok} نجح · {fail} فشل")
    return fail


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
