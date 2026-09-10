"""
ما يقولونه.

هنا خطٌّ صريح لا أتجاوزه: **أنا أكتب النحو، وهم يملؤون المعنى.**

القوالب أدناه تركيبٌ لغوي فارغ — «لأن…»، «إلا من…»، «بعد كذا سنة». وكل
فراغٍ فيها يُملأ من حالة الكائن الفعلية: أثرٌ في ذاكرته له سنةٌ ونوع،
إنسانٌ بينه وبينه رابطة قائمة، مكانٌ سكنه أو جاوره، رقمٌ عدّه بنفسه،
فعلٌ مارسه فعلًا في سنةٍ بعينها.

ولذلك يخرج من كل كائنٍ كلامٌ غير كلام جاره، لأن ذاكرته غير ذاكرته.

وكل جملة تحمل معها `why` — سِجلّ نَسَبها: أي فراغٍ مُلئ من أين. فإن ادّعيتُ
أنهم قالوها، أمكنك أن تفتح النسب وتتحقّق. وما لا نسب له فهو من كتابتي أنا.
"""

from . import genome as G
from .memory import AR_KINDS, KINDS


class Utterance:
    """قولٌ ونَسَبُه."""

    __slots__ = ("text", "why", "author", "year", "kind")

    def __init__(self, text, why, author, year, kind):
        self.text = text
        self.why = why          # [(اسم الفراغ، من أين مُلئ)]
        self.author = author
        self.year = year
        self.kind = kind

    def trace(self):
        return " · ".join(f"{k}←{v}" for k, v in self.why)


# ===================================================== ملء الفراغات من حالته
def _person(a, agents, rng, prefer=None):
    """إنسانٌ بينه وبينه رابطة قائمة فعلًا — لا اسم من عندي."""
    pools = []
    if prefer == "grudge":
        pools = [a.bonds.resentment, a.bonds.affection, a.bonds.trust]
    elif prefer == "love":
        pools = [a.bonds.affection, a.bonds.attraction, a.bonds.trust]
    else:
        pools = [a.bonds.affection, a.bonds.resentment, a.bonds.trust]
    for d in pools:
        live = [k for k in d if k in agents]
        if live:
            best = max(live, key=lambda k: d[k])
            b = agents[best]
            src = ("ضغينة" if d is a.bonds.resentment else
                   "مودّة" if d is a.bonds.affection else "ثقة")
            return b.name, f"{src} قائمة نحو {b.name} بقدر {d[best]:.2f}"
    for k in a.bonds.kin:
        if k in agents:
            return agents[k].name, f"قريبه {agents[k].name}"
    return None, None


def _place(a, world, rng):
    st = world.settlements[a.settlement] if a.settlement < len(world.settlements) else None
    if st is None:
        return None, None
    if rng.random() < 0.45:
        near = world.neighbours(st.x, st.y, 2)
        if near:
            r = rng.choice(near)
            return r.name, f"إقليم يجاور {st.name}"
    return st.name, f"قريته {st.name}"


def _number(a, year, rng):
    """رقمٌ عدّه هو، لا رقمٌ اخترعتُه له."""
    opts = []
    if a.age > 0:
        opts.append((a.age, f"عمره {a.age}"))
    if a.observations >= 1:
        opts.append((int(a.observations), f"ما رصده بنفسه ({a.observations:.0f})"))
    if a.children:
        opts.append((len(a.children), f"عدد ولده {len(a.children)}"))
    dead_kin = sum(1 for t in a.mem.traces if t.kind == KINDS.index("death"))
    if dead_kin:
        opts.append((dead_kin, f"ما يتذكّره من موتى ({dead_kin})"))
    if a.mem.traces:
        t = max(a.mem.traces, key=lambda t: t.strength)
        gap = abs(year - t.year)
        if 1 < gap < 400:
            opts.append((gap, f"ما بينه وبين أقوى ما يتذكّر ({gap} سنة)"))
    if not opts:
        return None, None
    return rng.choice(opts)


def _deed(a, rng, past=False):
    """فعلٌ مارسه هو فعلًا. `past` للإخبار، وإلا فصيغة الأمر."""
    from .mind import ACTIONS, AR_ACTIONS, AR_DEEDS
    tbl = AR_DEEDS if past else AR_ACTIONS
    if a.prog.episodes:
        _, act, tr = rng.choice(a.prog.episodes)
        return tbl[ACTIONS[act]], f"فعلٌ مارسه سنة {tr.year}"
    if a.last_action >= 0:
        return tbl[ACTIONS[a.last_action]], "آخر ما فعل"
    return None, None


def _burden(a, rng, positive=False):
    """أثقلُ ما يحمله في ذاكرته — أو أحلاه."""
    cand = [t for t in a.mem.traces
            if (t.val > 0.25 if positive else t.val < -0.25)]
    if not cand:
        return None, None
    t = max(cand, key=lambda t: t.strength * abs(t.val))
    word = t.tag or AR_KINDS[KINDS[t.kind]]
    src = f"أثرٌ من سنة {t.year} ({AR_KINDS[KINDS[t.kind]]}، قوّته {t.strength:.2f})"
    return word, src


def _vision(a):
    """أقوى ما يتذكّره من المهيب — بذرة كل أسطورة. ولا يُسأل أوقع أم لا."""
    t = a.mem.numinous()
    if t is None:
        return None, None, None
    word = t.tag or AR_KINDS[KINDS[t.kind]]
    src = (f"ذكرى مهيبة من سنة {t.year} ({AR_KINDS[KINDS[t.kind]]}، "
           f"قوّتها {t.strength:.2f}، مصدرها لا يعرفه)")
    return t, word, src


# ===================================================== التبرير عند التعارض
def rationalize(a, key, agents, world, rng, year):
    """
    الدليل ناقضَ عقيدته، فبنى تبريرًا. النحو من عندي، وكل ما فيه من عنده.
    """
    why = []

    def take(fn, *args, **kw):
        v, src = fn(a, *args, **kw)
        return v, src

    person, p_src = _person(a, agents, rng, prefer="grudge")
    place, pl_src = _place(a, world, rng)
    num, n_src = _number(a, year, rng)
    deed, d_src = _deed(a, rng)
    burden, b_src = _burden(a, rng)

    frames = []
    if deed:
        frames.append(("نجا لأنه {deed} قبلها", dict(deed=deed), [("الفعل", d_src)]))
    if person:
        frames.append(("لم يُصِبْنا إلا لأن {person} أخفى ما عنده",
                       dict(person=person), [("المُلام", p_src)]))
        frames.append(("الحدّ يقع على غير {person}، وقد نجا",
                       dict(person=person), [("الشاهد", p_src)]))
    if num:
        frames.append(("يقع بعد {num} سنة لا في حينه",
                       dict(num=num), [("الأجل", n_src)]))
    if place:
        frames.append(("المقصود ليس هذا المكان بل {place}",
                       dict(place=place), [("المكان", pl_src)]))
    if burden:
        frames.append(("أُصبنا لأن فينا {burden} لم يُكفَّر",
                       dict(burden=burden), [("الذنب", b_src)]))
    if deed and person:
        frames.append(("من {deed} كما {person} سلِم، ومن ترك هلك",
                       dict(deed=deed, person=person),
                       [("الفعل", d_src), ("القدوة", p_src)]))
    if not frames:
        return None

    tmpl, slots, prov = rng.choice(frames)
    text = tmpl.format(**slots)
    why = prov + [("العقيدة", key), ("الحال", f"قناعته {a.conv.get(key, 0):.2f}، "
                                              f"استثماره {a.tribute:.2f}")]
    return Utterance(text, why, a.id, year, "rider")


# ===================================================== الأسطورة من ذكرى كاذبة
def myth(a, god, agents, world, rng, year):
    """
    أسطورةٌ تُبنى على أقوى ما يتذكّره ولم يقع. لا يعرف أنه لم يقع.
    """
    t, thing, v_src = _vision(a)
    if t is None:
        return None
    place, pl_src = _place(a, world, rng)
    deed, d_src = _deed(a, rng)
    num, n_src = _number(a, year, rng)
    person, p_src = _person(a, agents, rng, prefer="love")

    good = t.val > 0
    frames = []
    if deed and place:
        frames.append(("من {deed} في {place} " + ("نال" if good else "هلك"),
                       dict(deed=deed, place=place),
                       [("الشعيرة", d_src), ("المكان", pl_src)]))
    if num:
        frames.append(("بعد {num} سنة يُرفع عنّا ما نحمل",
                       dict(num=num), [("الأجل", n_src)]))
    if thing and place:
        frames.append(("{thing} لا يُنسى في {place}، وهناك يُقضى الأمر",
                       dict(thing=thing, place=place),
                       [("الرؤيا", v_src), ("المكان", pl_src)]))
    if person and thing:
        frames.append(("رأى أن {person} يحمل {thing}، وأن نسله عليه علامة",
                       dict(person=person, thing=thing),
                       [("المذكور", p_src), ("الرؤيا", v_src)]))
    if thing:
        frames.append(("ما رآه من {thing} ليس منّا، وإنما من {god}",
                       dict(thing=thing, god=god), [("الرؤيا", v_src)]))
    if not frames:
        return None

    tmpl, slots, prov = rng.choice(frames)
    body = tmpl.format(**slots)
    text = f"حدّث {a.name} أن {body}" if rng.random() < 0.5 else f"قال {a.name}: {body}"
    why = prov + [("مصدر الرؤيا", v_src),
                  ("حاله", f"رهبته {a.mem.awe():.2f}، تصديقه {a.eg.t[G.CREDULITY]:.2f}")]
    return Utterance(text, why, a.id, year, "myth")


# ===================================================== الرواية الشفهية تتغيّر
_SOFTEN = ("يقال إن ", "سمعتُ أن ", "زعموا أن ", "حدّثني من أثق به أن ")
_HARDEN = ("رأيتُ بعيني أن ", "شهدتُ أن ", "كنتُ حاضرًا حين ")


def retell(u, teller, listener, rng, drift, year, agents=None):
    """
    كل نقلٍ يغيّر الرواية: يشتدّ الإسناد عند الواثق ويلين عند الشاكّ،
    ويُبدَّل اسمٌ باسم، ويزيد رقمٌ أو ينقص. فتختلف الروايات بين اثنين
    سمعا من رجلٍ واحد.
    """
    text = u.text
    why = list(u.why)
    t = listener.eg.t

    if rng.random() < drift * 2.2:
        if t[G.CREDULITY] > 0.55:
            text = rng.choice(_HARDEN) + text
            why.append(("تشديد", f"{listener.name} عالي التصديق فرفع الإسناد"))
        else:
            text = rng.choice(_SOFTEN) + text
            why.append(("تليين", f"{listener.name} واطي التصديق فخفّض الإسناد"))

    # الأرقام تكبر في الحكي
    import re
    def bump(m):
        n = int(m.group())
        k = max(1, int(n * rng.uniform(0.75, 1.45)))
        return str(k)
    if rng.random() < drift * 2.0 and re.search(r"\d+", text):
        text = re.sub(r"\d+", bump, text, count=1)
        why.append(("الرقم", "تغيّر في النقل"))

    # ويُبدَّل الاسم باسمٍ يعرفه السامع — فيصير البطل من قومه هو
    if agents and rng.random() < drift * 1.8:
        nm, nsrc = _person(listener, agents, rng)
        if nm and nm not in text:
            import re as _re
            words = [w for w in text.split() if len(w) > 3 and w[0] not in "0123456789"]
            if words:
                old = rng.choice(words)
                text = text.replace(old, nm, 1)
                why.append(("تحريف الاسم", f"{old} ← {nm} ({nsrc})"))

    n = Utterance(text, why, u.author, year, u.kind)
    return n


# ===================================================== الكذب المتعمَّد
# فرقٌ جوهري: الذاكرة الكاذبة لا يعرفها صاحبها، والكذبةُ يعرفها قائلها.
# هنا وحدها يوجد في هذا العالم من يقول ما لا يعتقد، وهو يعلم.

def will_lie(a, rng, stakes=1.0):
    t = a.eg.t
    drive = (t[G.MACHIAVELLIAN] * 1.3 + (1.0 - t[G.HONESTY]) * 1.1
             + t[G.NARCISSISM] * 0.5) * stakes
    if a.is_ruler or a.clergy:
        drive *= 1.5                       # لمن له ما يخسره دافعٌ أكبر
    restraint = t[G.HONESTY] * 1.4 + t[G.AGREEABLE] * 0.5 + a.caught * 0.45
    return rng.random() < min(0.75, 0.30 * drive / (0.45 + restraint))


def lie(a, key, agents, world, rng, year, god):
    """
    يقول ما يعرف أنه غير ما يعتقد. يُبنى القول من حياته هو كأي قولٍ آخر،
    والفرق أنه يُسجَّل في `a.lies` ويُنسَب إليه في ذاكرة من سمعه.
    """
    person, p_src = _person(a, agents, rng, prefer="grudge")
    place, pl_src = _place(a, world, rng)
    num, n_src = _number(a, year, rng)
    deed, d_src = _deed(a, rng)

    frames = []
    frames.append(("رأيتُ بعيني ما لم يره غيري", {},
                   [("الغرض", "ادّعاء شهادةٍ لم تقع")]))
    if person:
        frames.append(("إن {person} هو من جلب علينا هذا",
                       dict(person=person), [("المُتَّهَم", p_src)]))
    if deed:
        frames.append(("ما نجونا إلا لأني {deed} عنكم",
                       dict(deed=deed), [("الفعل المُدّعى", d_src)]))
    if num and place:
        frames.append(("أُخبرتُ أن ما يقع في {place} يقع بعد {num} سنة",
                       dict(place=place, num=num),
                       [("المكان", pl_src), ("الرقم", n_src)]))
    frames.append((f"{god} كلّمني، ولم يكلّم سواي", {},
                   [("الغرض", "احتكار الكلام باسم الإله")]))

    tmpl, slots, prov = rng.choice(frames)
    text = tmpl.format(**slots)
    a.lies += 1
    why = prov + [
        ("يعلم أنه كاذب", f"قناعته بالعقيدة {a.conv.get(key, 0.0):.2f} "
                          f"وأمانته {a.eg.t[G.HONESTY]:.2f}"),
        ("مكسبه", "مكانة وطاعة"),
    ]
    return Utterance(text, why, a.id, year, "lie")


def expose(listener, agents, key, rng):
    """
    ينكشف الكذب من ذاكرة السامع لا من علم المحاكاة: حين يراجع عقيدته
    يستدعي من حدّثه بها، فإن كان حيًّا لحقته الضغينة والفضيحة.
    """
    # لا يفتّش عن «الكاذب» — لا سبيل له إلى ذلك. يفتّش عمّن حدّثه بما
    # كان يعتقده وقد تركه الآن. والانكشاف يقع من هذا الباب وحده.
    told = [t for t in listener.mem.traces
            if t.src == 2 and t.who in agents and not t.repressed]   # S_TOLD
    if not told:
        return None
    t = max(told, key=lambda x: x.strength)
    liar = agents[t.who]
    if liar.lies <= 0:
        return None
    liar.caught += 1
    liar.prestige = max(0.0, liar.prestige - 0.8)
    listener.bonds.bump(listener.bonds.resentment, liar.id, 0.9)
    listener.mem.store(5, listener.mem.traces[0].year if listener.mem.traces else 0,
                       who=liar.id, val=-0.8, strength=1.6, truth=1.0,
                       src=0, tag="انكشف كذبه")
    return liar


# ===================================================== التفاخر
# يعلن الرجل مأثرةً. وثلاثة أضربٍ لا يفرّق السامع بينها:
# صادقةٌ وقعت له، ومنفوخةٌ كبّر رقمها، ومسروقةٌ رآها من غيره فنسبها لنفسه.
# والمكسب واحد في الثلاثة — والفضيحة تنتظر النوعين الأخيرين.

def boast(a, agents, world, rng, year):
    t = a.eg.t
    drive = (t[G.NARCISSISM] * 1.4 + t[G.EXTRAVERSION] * 0.6
             + a.af.s[4] * 0.3)          # E_RESENT: من أُهين يتفاخر
    if rng.random() > min(0.55, 0.16 * drive):
        return None

    deed, d_src = _deed(a, rng, past=True)
    num, n_src = _number(a, year, rng)
    place, pl_src = _place(a, world, rng)
    person, p_src = _person(a, agents, rng, prefer="grudge")

    kind, why = "صادقة", []
    r = rng.random()
    honest = t[G.HONESTY]

    if r > 0.35 + honest * 0.55 and person:
        # مسروقة: فعلٌ رآه من غيره فنسبه إلى نفسه
        kind = "مسروقة"
        why.append(("صاحب الفعل الحقيقي", p_src))
        body = f"{deed or 'فعلتُها'} يوم عجز الناس عنها"
    elif r > 0.20 + honest * 0.45 and num:
        kind = "منفوخة"
        big = int(num * rng.uniform(2.0, 5.0)) + 1
        why.append(("الرقم الحقيقي", n_src), )
        why.append(("ما أعلنه", str(big)))
        body = f"{deed or 'فعلتُ'} ما لم يبلغه {big} من قومي"
    else:
        if not deed:
            return None
        why.append(("الفعل", d_src))
        body = f"{deed} حين لم {'يقدر' if rng.random() < 0.5 else 'يجرؤ'} غيري"
    if place and rng.random() < 0.4:
        body += f"، وذلك في {place}"

    gain = 0.28 * (0.4 + t[G.EXTRAVERSION]) * (1.0 + 0.5 * t[G.NARCISSISM])
    a.prestige = min(12.0, a.prestige + gain)
    if kind != "صادقة":
        a.lies += 1
    why.append(("ضربها", kind))
    why.append(("مكسبه", f"هيبة +{gain:.2f}"))
    return Utterance(body, why, a.id, year, "boast"), kind


def catch_boast(witness, boaster, kind, rng):
    """
    من رأى الفعل يعرف صاحبه. والمنفوخُ يُكشف بمن حضر، والمسروقُ بمن فعل.
    """
    if kind == "صادقة":
        return False
    sharp = (0.2 + witness.eg.t[G.REASONING]) * (0.3 + witness.bonds.resentment.get(boaster.id, 0.0))
    if rng.random() > min(0.6, sharp):
        return False
    boaster.caught += 1
    boaster.prestige = max(0.0, boaster.prestige - 1.4)
    witness.bonds.bump(witness.bonds.resentment, boaster.id, 0.5)
    return True


# ===================================================== أطروحة الرسالة
def thesis(a, st, world, agents, rng, year, concept):
    """
    أطروحةُ رسالةٍ يكتبها. النحو منّي، وكل ما فيها من حاله هو: مفهومه
    الأقوى، وما فقده، وما رصده، ومن يخاصم، وأين يسكن، وكم عدّ.

    وكان هنا قالبٌ واحد بخانةٍ متغيّرة — فخرجت كل الرسائل بجملةٍ واحدة.
    وهذا هو الخطأ نفسه الذي حذّرنا منه: قالبٌ يتنكّر في هيئة فكرة.
    """
    from .mind import AR_DEEDS, ACTIONS
    nm = concept.name
    good = concept.value > 0
    person, p_src = _person(a, agents, rng, prefer="grudge")
    place, pl_src = _place(a, world, rng)
    num, n_src = _number(a, year, rng)
    burden, b_src = _burden(a, rng)
    joy, j_src = _burden(a, rng, positive=True)
    deed, d_src = _deed(a, rng)
    why = [("المفهوم", f"«{nm}» بناه على {concept.evidence} موقفًا "
                       f"(اقترانه {concept.value:+.2f})")]

    F = []
    if burden:
        F.append((f"ما نسمّيه {burden} ليس واحدًا: هو «{nm}» إذا اجتمع، "
                  f"وغيرُه إذا افترق", [("الألم", b_src)]))
    if num and place:
        F.append((f"من عدّ في {place} وجد «{nm}» يعود كل {num}؛ "
                  f"وما عاد على ميقاتٍ فليس بعقاب", [("الرقم", n_src), ("المكان", pl_src)]))
    if person:
        F.append((f"يقول {person} إن «{nm}» عرَضٌ، وأقول إنه أصلٌ "
                  f"وما سواه فرعٌ عليه", [("المخالِف", p_src)]))
    if deed:
        F.append((f"من أراد «{nm}» فليبدأ بأن {deed}؛ فالفعل يسبق الفهم "
                  f"لا يتبعه", [("الفعل", d_src)]))
    if joy:
        F.append((f"ليس {joy} غايةً، وإنما هو أثرٌ يظهر حين يتمّ «{nm}»",
                  [("الخير", j_src)]))
    if a.heretic:
        F.append((f"ما يُنسب إلى غضبٍ له ميقاتٌ يُحصى، و«{nm}» علامةٌ عليه "
                  f"لمن أحصى", [("موقفه", "مُنكِر — كشف الدورة أو قرأها")]))
    if a.stance == "denial":
        F.append((f"«{nm}» بابٌ إلى تعطيل الرغبة لا إلى قضائها، "
                  f"وفي تعطيلها الراحة", [("موقفه", "زاهد")]))
    if a.clergy:
        F.append((f"«{nm}» شرطٌ لا يُبلَغ الرضا بدونه، وقد كُتب فينا "
                  f"قبل أن نُولد", [("موقفه", "كاهن")]))
    if not F:
        F.append((f"«{nm}» {'يجمع' if good else 'يفرّق'} ما ظنناه متفرّقًا",
                  []))

    body, prov = rng.choice(F)
    return body, why + prov
