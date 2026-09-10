"""
العقيدة — على مستويين.

  (١) قناعة فردية: `a.conv[key]` — ما يعتقده هذا الإنسان بعينه، وتبريراته
      هو في `a.riders`. هذه وحدها هي التي تحكم سلوكه.
  (٢) أرثوذكسية عامة: `tenet.strength` — متوسطٌ مرجّح لقناعات أهل القرية،
      والوزن للمكانة والكهنوت والحكم. أي أن القويّ يعرّف «الصواب»،
      لكنه لا يغيّر ما في الصدور إلا بالخطابة والتعليم والعقاب.

لا شيء يقفز من فردٍ إلى الجميع. الانتقال يمرّ دائمًا عبر النقل — انحياز
الهيبة وانحياز الأغلبية (Henrich) — ولذلك يمكن أن تجد في قريةٍ واحدة
كاهنًا موقنًا وفلّاحًا نصف مصدّق ورجلًا لا يصدّق شيئًا.

الإله غير موجود في فيزياء هذا العالم. لكن الغضب يقع، والتفسير يصير سلطة.
وحين يصطدم الاعتقاد بالدليل يُحسم بواحدٍ من ثلاثة (فستنجر): مراجعة، أو
تبرير، أو تجنّب. ومن ضحّى كثيرًا في سبيل العقيدة أقلُّ الناس استعدادًا
لمراجعتها — يزداد يقينًا كلما كذّبها الواقع.
"""

from . import genome as G
from .emotion import awe_strike, E_AWE

REVISE, RATIONALIZE, AVOID = 0, 1, 2
AR_ROUTE = {REVISE: "مراجعة", RATIONALIZE: "تبرير", AVOID: "تجنّب"}


class Tenet:
    """نصّ العقدة + أرثوذكسيتها العامة. القناعة الفردية ليست هنا."""

    __slots__ = ("key", "text", "strength", "tested", "confirmed",
                 "disconfirmed", "riders", "true_in_world", "born")

    def __init__(self, key, text, strength, true_in_world, born=0):
        self.key = key
        self.text = text
        self.strength = strength     # أرثوذكسية عامة — تُحسب ولا تُكتب مباشرة
        self.tested = 0
        self.confirmed = 0
        self.disconfirmed = 0
        self.riders = []             # التبريرات التي صارت عامّة
        self.true_in_world = true_in_world
        self.born = born


class Doctrine:
    __slots__ = ("god", "name", "tenets", "sect", "born", "parent",
                 "complexity", "ritual_debt", "prophecies", "martyrs",
                 "persecutions", "schisms")

    def __init__(self, god, name, tenets, born, sect=0, parent=-1):
        self.god = god
        self.name = name
        self.tenets = {t.key: t for t in tenets}
        self.sect = sect
        self.born = born
        self.parent = parent
        self.complexity = float(len(tenets))
        self.ritual_debt = 0.0
        self.prophecies = []
        self.martyrs = 0
        self.persecutions = 0
        self.schisms = 0

    def fork(self, name, year, sect):
        ts = []
        for t in self.tenets.values():
            n = Tenet(t.key, t.text, t.strength, t.true_in_world, year)
            n.riders = list(t.riders)
            ts.append(n)
        d = Doctrine(self.god, name, ts, year, sect, self.sect)
        d.complexity = self.complexity
        d.prophecies = list(self.prophecies)   # الوعد وفشلُه يُورَثان مع المذهب
        self.schisms += 1
        return d


def founding_tenets(god):
    return [
        Tenet("wrath_is_sin",
              f"الغضب عقابٌ من {god} على خطيئتنا، ويُدفَع بالطقس والقربان", 1.0, False),
        Tenet("white_mountain", "الجبل الأبيض محرّم؛ من صعده هلك", 1.0, False),
        Tenet("counting_stars", "من أحصى النجوم مرض ولم يقم", 0.9, False),
        Tenet("stranger_plague", "الغريب يحمل السقم في يده", 0.8, True),
        Tenet("return_promise",
              "بعد سبعة أجيال يعود الماء ونرجع إلى الوادي", 1.0, False),
    ]


# ------------------------------------------------------- القناعة الفردية
def seed_conviction(a, doc, rng):
    """
    قناعة المولود الأولى. تنبع من تصديقه الموروث ومن قوة ما زُرع فيه —
    ولذلك يختلف اثنان وُلدا في اليوم نفسه اختلافًا حقيقيًا.
    """
    if doc is None:
        return
    cred = a.g.t[G.CREDULITY]
    for key in doc.tenets:
        base = 0.25 + 0.85 * cred + a.mem.awe() * 0.4
        a.conv[key] = max(0.0, min(1.6, base * rng.gauss(1.0, 0.30)))


def inherit_conv(child, mother, father, rng, drift=0.18, doc=None):
    """
    الأبناء يرثون قناعات أبويهم — ولا يرثونها وحدها.

    كان الميراث وحده يجعل القناعة تنحدر انحدارًا أحاديًّا: كل جيلٍ يبدأ
    من متوسّطٍ متآكل، فتبلغ الصفر بعد قرون ولا تعود. وهذا خطأ في النمذجة:
    الاعتقاد في الناس يُولَد من جديد في كل طفل — من التنشئة والرهبة —
    لا يُنقَل ناقصًا كما يُنقَل المال.

    فهنا مصدرٌ وميراث: نصفٌ ممّا عند أبويه، ونصفٌ من تصديقه هو.
    """
    keys = set(mother.conv) | set(father.conv)
    if doc is not None:
        keys |= set(doc.tenets)
    cred = child.g.t[G.CREDULITY]
    fresh = 0.20 + 0.95 * cred          # ما يولد به من استعدادٍ للتصديق
    for k in keys:
        mid = 0.5 * (mother.conv.get(k, 0.0) + father.conv.get(k, 0.0))
        v = 0.55 * mid * (0.45 + 1.1 * cred) + 0.45 * fresh
        child.conv[k] = max(0.0, min(1.6, v * rng.gauss(1.0, drift)))
    for r in (mother.riders + father.riders):
        if rng.random() < 0.30 and len(child.riders) < 8:
            child.riders.append(r)


def wrath_conviction(a, doc, rng):
    """
    الغضب نفسه يُنشئ اعتقادًا. من نجا ورأى الموت يعمّ ثم يتوقّف يخرج
    منه بيقينٍ أشدّ لا أقلّ — وهذا مقيسٌ في الناس بعد الكوارث.
    """
    if doc is None or a.heretic:
        return
    k = (0.10 + 0.45 * a.eg.t[G.CREDULITY]) * (0.4 + a.fear_death)
    for key in doc.tenets:
        a.conv[key] = min(1.6, a.conv.get(key, 0.0) + k * rng.gauss(1.0, 0.35))
    a.faith = min(1.0, a.faith + k * 0.6)


def conviction(a, key):
    return a.conv.get(key, 0.0)


def investment(a):
    """كم ضحّى في سبيل العقيدة. الاستثمار يقاوم المراجعة."""
    return min(3.0, a.tribute * 0.5 + (2.0 if a.clergy else 0.0) +
               a.af.s[E_AWE] * 0.4 + a.faith * 1.2)


def resolve(a, key, weight, rng, cfg, year, tenet=None):
    """
    دليلٌ ضدّ عقيدة — عند هذا الإنسان وحده.
    لا يمسّ أحدًا غيره: يغيّر `a.conv[key]` و`a.riders` فقط.
    يعيد (المسار، نصّ التبرير إن وُجد).
    """
    t = a.eg.t
    inv = investment(a)
    cur = a.conv.get(key, 0.0)
    w_rev = (0.25 + t[G.REASONING] * 1.6 + t[G.OPENNESS] * 0.8) * \
            (1.6 - t[G.CREDULITY]) / (0.5 + inv)
    w_rat = (0.30 + t[G.CREDULITY] * 1.4 + t[G.NEUROTIC] * 0.4) * (0.5 + inv) * (0.3 + cur)
    w_avo = (0.20 + a.af.s[E_AWE] * 0.8 + t[G.FEAR] * 0.9)
    tot = w_rev + w_rat + w_avo
    r = rng.random() * tot

    if tenet is not None:
        tenet.tested += 1
        tenet.disconfirmed += 1

    if r < w_rev:
        a.conv[key] = max(0.0, cur - 0.30 * weight)
        a.doubt = min(1.0, a.doubt + 0.20 * weight * (0.4 + t[G.REASONING]))
        a.faith = max(0.0, a.faith - 0.12 * weight)
        return REVISE, None

    if r < w_rev + w_rat:
        # التبرير نفسه يؤلّفه الكائن من حياته — انظر speech.rationalize.
        # لم يعد هنا نصٌّ مكتوب سلفًا يختار منه.
        a.conv[key] = min(1.6, cur + 0.09 * weight)
        a.faith = min(1.0, a.faith + 0.06 * weight)
        a.doubt = max(0.0, a.doubt - 0.05 * weight)
        return RATIONALIZE, None

    a.doubt = max(0.0, a.doubt - 0.02)
    return AVOID, None


# --------------------------------------------------- الأرثوذكسية العامة
def _weight(a):
    w = 1.0 + a.prestige * 0.45 + a.dominance * 0.35
    if a.clergy:
        w += 3.0
    if a.is_ruler:
        w += 4.0
    return w


#: ما لا يبلغه أحدٌ في صدره يسقط من العقيدة.
FORGET = 0.035
#: كم عقدةً تحمل ملّةٌ شفاهية، وكم تُضيف الكتابة.
CREED_ORAL = 22.0
CREED_WRITTEN = 130.0
#: ولا تُنسى عقدةٌ قبل أن يُتاح لها جيل.
CREED_GRACE = 30
#: وتُمهَل الأسطورة سنينَ قلائل لتنتشر، ثم تُزاحم على مكانها كسائرها.
CREED_SPREAD = 5

#: وما ذهب من صدر الرجل يُمحى من ذهنه لا يبقى صفرًا مسجّلًا.
DROP = 0.02
#: وما سقط من الملّة يخفت في الصدر ولا يثبت.
LAPSE = 0.72

#: ما ضبطتُه بيدي في هذا الملفّ — يُحصى في البيان.
TUNED = {"FORGET": FORGET, "DROP": DROP, "LAPSE": LAPSE,
         "CREED_ORAL": CREED_ORAL, "CREED_WRITTEN": CREED_WRITTEN,
         "CREED_GRACE": CREED_GRACE, "CREED_SPREAD": CREED_SPREAD}


def creed_capacity(st, agents, cfg):
    """
    كم عقدةً تحمل ملّة؟ **بقدر ما يُحفَظ ويُعلَّم، لا أكثر.**

    كانت العُقَد تتراكم بلا حدّ — كلُّ أسطورةٍ تُروى تصير مادّةً في
    الملّة إلى الأبد — حتى بلغت ثمانين ومئتين في القرية الواحدة،
    ومتوسّط رسوخها نصف: أي أنها كلّها معتقَدة حقًّا، وذلك محال.

    والحدُّ ليس عددًا أضعه، هو **سعةُ النقل**: ملّةٌ شفاهية لا تحمل إلا
    ما تحفظه الصدور وتسعه مواسمُ التعليم؛ فإذا جاءت الكتابة ارتفع
    السقف لأن اللوح يحفظ ما لا يحفظه الصدر (Goody 1977؛ وBartlett 1932
    فيما يسقط من الرواية المتكرّرة).

    وثمرتُه دعوى تُكذَّب: **الأمم الكاتبة عقائدها أعقد.** ومن أحرق
    كتبَها ردّها إلى الشفاهية فسقط أكثرُ ملّتها في جيل.
    """
    from .causes import literacy
    return CREED_ORAL + CREED_WRITTEN * literacy(st, agents, cfg)


def recompute_orthodoxy(st, agents, year=0, cfg=None):
    """
    ما تعلنه القرية عقيدةً: متوسطٌ مرجّح لما في الصدور، والوزن للسلطة.
    تتحرك ببطء — الأرثوذكسية لا تقفز مع كل شكٍّ فردي.

    **والعقيدة تنسى.** كانت العُقَد تتراكم بلا حدّ حتى بلغت مئتين
    وأربعين في القرية الواحدة، وصار لكل رجلٍ رأيٌ في ثلاثمئة مسألة.
    وهذا لا يقع: ما لا يُعلَّم ولا يُقام عليه شعيرةٌ ولا يبقى في صدر
    أحدٍ يسقط من الملّة، ولا يبقى منه إلا اسمُه في كتابٍ إن كُتب
    (Bartlett 1932 — ما لا يُستعمل من الذاكرة الجمعية يُختصر ثم يُفقد).

    وثمرةُ ذلك مزدوجة: عقيدةٌ لها قلبٌ محدود يُدافَع عنه، ورنٌّ لا
    يثقل مع القرون — وكلاهما مطلوب.
    """
    d = st.doctrine
    if d is None:
        return
    people = [agents[m] for m in st.members if m in agents]
    if not people:
        return
    ws = [_weight(a) for a in people]
    den = sum(ws) or 1.0
    pairs = list(zip(people, ws))
    dead = []
    for key, t in d.tenets.items():
        num = 0.0
        for a, w in pairs:
            num += w * a.conv.get(key, 0.0)
        target = num / den
        t.strength += 0.30 * (target - t.strength)   # جمود مؤسسي
        # لا تُنسى عقدةٌ قبل أن يُتاح لها جيل، ولا تُنسى وهي مكتوبة
        if (t.strength < FORGET and target < FORGET
                and year - t.born > 45 and not t.riders):
            dead.append(key)
    for key in dead:
        del d.tenets[key]

    # وما زاد على سعة النقل يسقط، والأضعفُ رسوخًا أوّلُ ما يُنسى.
    if cfg is not None:
        cap = creed_capacity(st, agents, cfg)
        over = len(d.tenets) - int(cap)
        if over > 0:
            # تُمهَل الأسطورة سنينَ قلائل لا جيلًا. وكانت المهلة جيلًا
            # فوقعت الفأس على **قلب الملّة** دون الأساطير الطارئة: تُحمى
            # أسطورةٌ لم يصدّقها إلا قائلُها، وتسقط عقدةٌ عليها بُني
            # الدين. والصواب عكسُه — ما لم يلتقطه أحدٌ هو أوّل ما يذهب.
            young = year - CREED_SPREAD
            drop = sorted((t for t in d.tenets.values() if t.born < young),
                          key=lambda t: t.strength)[:over]
            for t in drop:
                del d.tenets[t.key]
                dead.append(t.key)
    return len(dead)


def share(st, agents, key, threshold=0.5):
    """كم نسبة من يعتقد هذه العقدة فعلًا (لا من يظهرها)."""
    n = held = 0
    for m in st.members:
        a = agents.get(m)
        if a is None:
            continue
        n += 1
        if a.conv.get(key, 0.0) >= threshold:
            held += 1
    return held / n if n else 0.0


# ------------------------------------------------------------- الانتقال
def transmit(speaker, listener, rng, pull=0.10):
    """
    انحياز الهيبة: نأخذ عقائد من نَجَح، لا عقائد من أقنَع.
    """
    if not speaker.conv:
        return
    prestige = 1.0 + speaker.prestige * 0.35 + (1.5 if speaker.clergy else 0.0)
    k = pull * prestige * (0.20 + listener.eg.t[G.CREDULITY]) * (1.0 - 0.6 * listener.doubt)
    k = min(0.45, k)
    for key, v in speaker.conv.items():
        cur = listener.conv.get(key, 0.0)
        listener.conv[key] = max(0.0, min(1.6, cur + k * (v - cur)))
    if speaker.riders and rng.random() < k and len(listener.riders) < 10:
        r = rng.choice(speaker.riders)
        if r not in listener.riders:
            listener.riders.append(r)


def _erode(a, doc, t_):
    """
    تآكل ما لا دليل عليه — تناسبيّ لا مطلق. الفرق مهمّ: الطرح المطلق
    يسوّي الناس عند صفرٍ واحد، والضربُ يُبقي بينهم فروقًا.

    ويُمشَّط هنا ما في الصدر لا ما في الملّة: فما ذهب يُمحى، ولا يبقى
    في ذهن الرجل قيدٌ بصفرٍ عن مسألةٍ لم يعد يعرفها أحد.
    """
    e = 0.055 * (0.15 + t_[G.REASONING]) * (1.15 - t_[G.CREDULITY])         * (0.4 + t_[G.OPENNESS])
    conv = a.conv
    tenets = doc.tenets
    for key in list(conv):
        cur = conv[key]
        if key in tenets:
            cur *= (1.0 - e)
        else:
            # عقدةٌ سقطت من الملّة فلم يعد أحدٌ يذكرها ولا يُثاب عليها.
            # كانت تبقى في الصدر بقيمتها إلى الأبد، فيحمل الرجلُ رأيًا
            # في ثلاثمئة مسألةٍ نسيها قومُه. ولا تُنسى دفعةً — تخفت.
            cur *= LAPSE
        if cur < DROP:
            del conv[key]
        else:
            conv[key] = cur
    if e > 0.030:
        a.doubt = min(1.0, a.doubt + 0.004 * (e / 0.05))


def conform(a, doc, rate=0.05, circle=None):
    """
    قوّتان متضادّتان في كل سنة:
      انحياز الأغلبية — يجذب إلى ما يُعلَن أنه الصواب.
      وتآكل ما لا دليل عليه — يخفض القناعة عند من يطلب الدليل.

    بغير الثانية لا شيء يُنقص الاعتقاد سوى الدليل، والدليل قد يكون محرّمًا،
    فيقفل المجتمع على نفسه إلى الأبد. وبوجودها يستقرّ توزيعٌ حقيقي:
    عالي التصديق يشبع عند اليقين، وطالبُ الدليل ينجرف نحو الشكّ.
    """
    if doc is None:
        return
    t_ = a.eg.t
    k = rate * (0.3 + t_[G.AGREEABLE]) * (0.3 + t_[G.CREDULITY]) * (1.0 - a.doubt)

    # الامتثال لمن يعرفه لا لمتوسّطٍ لا يراه أحد. كان الشدّ إلى الأرثوذكسية
    # العامّة — وهي نفسها متوسّط الجميع — فانهار التباين إلى نقطة واحدة:
    # الكلّ يُشدّ إلى المتوسّط والمتوسّط يُشدّ إلى الكلّ.
    if circle:
        # يُمرّ على الدائرة مرّةً واحدة لا مرّةً لكل عقدة. وكان الأوّل
        # يقرأ صدرَ كل جارٍ في كل مسألة — سبعةَ عشر مليون قراءةٍ في
        # خمسٍ وعشرين سنة.
        den = 0.0
        acc = {}
        tenets = doc.tenets
        for b, w in circle:
            den += w
            for key, v in b.conv.items():
                if key in tenets:
                    acc[key] = acc.get(key, 0.0) + w * v
        if den <= 0:
            return
        conv = a.conv
        for key in tenets:
            tgt = acc.get(key, 0.0)
            cur = conv.get(key, 0.0)
            if tgt == 0.0 and cur == 0.0:
                continue
            conv[key] = max(0.0, min(1.6, cur + k * (tgt / den - cur)))
        _erode(a, doc, t_)
        return
    erode = 0.030 * (0.15 + t_[G.REASONING]) * (1.15 - t_[G.CREDULITY])         * (0.4 + t_[G.OPENNESS])
    for key, t in doc.tenets.items():
        cur = a.conv.get(key, 0.0)
        v = cur + k * (t.strength - cur) - erode
        a.conv[key] = max(0.0, min(1.6, v))
    if erode > 0.022:
        a.doubt = min(1.0, a.doubt + 0.004 * (erode / 0.03))


def prophecy_failed(doc, believers, rng, cfg, year):
    """
    فشل النبوءة. النتيجة المضادة للحدس والمثبتة تجريبيًا: المستثمرون بشدّة
    يزدادون يقينًا ويخرجون للدعوة، والمتردّدون هم من ينفضّون.
    """
    zealots, leavers = [], []
    for a in believers:
        inv = investment(a)
        cur = a.conv.get("return_promise", 0.0)
        if inv > 1.5 and rng.random() < 0.55 + 0.2 * a.eg.t[G.CREDULITY]:
            a.faith = min(1.0, a.faith + 0.22)
            a.conv["return_promise"] = min(1.6, cur + 0.35)
            awe_strike(a.af, a.eg, 0.8)
            zealots.append(a)
        elif rng.random() < 0.45 * (1.4 - a.eg.t[G.CREDULITY]):
            a.faith = max(0.0, a.faith - 0.30)
            a.conv["return_promise"] = max(0.0, cur - 0.55)
            a.doubt = min(1.0, a.doubt + 0.30)
            leavers.append(a)
    doc.complexity += cfg.doctrine_growth * 2.0
    return zealots, leavers


def wrath_expectation(a, doc, years_since, mean_gap):
    if a.heretic and mean_gap:
        phase = years_since / max(1.0, mean_gap)
        return max(0.0, min(1.0, phase ** 3))
    base = 0.15 + 0.5 * a.faith
    if doc is not None:
        base += 0.15 * min(1.0, doc.ritual_debt)
    return max(0.0, min(1.0, base * (0.4 + years_since / 30.0)))


def detect_period(records, reasoning, has_calendar):
    """
    هل يكفي السجلّ لكشف الدورية؟ ستّ وقائع مدوّنة على الأقل، وتقويم يثبّت
    الأرقام، وعقل يقارن. الشفهي وحده لا يكفي: الأجيال تنسى الفواصل
    وتحتفظ بالرعب.
    """
    if not has_calendar or len(records) < 6:
        return None
    gaps = [records[i + 1] - records[i] for i in range(len(records) - 1)]
    if not gaps:
        return None
    mean = sum(gaps) / len(gaps)
    if mean <= 0:
        return None
    var = sum((x - mean) ** 2 for x in gaps) / len(gaps)
    cv = (var ** 0.5) / mean            # معامل الاختلاف: كم يخفي الضجيجُ الدورية

    # كان القياس نسبةَ المتوسط إلى الانحراف، وهي كبيرةٌ دائمًا هنا
    # (سبعٌ وعشرون على خمسة)، فكان الكشف يقع بأي عقلٍ تقريبًا — وهو قلب
    # هذه المحاكاة فلا ينبغي أن يكون بهذه السهولة.
    #
    # فالميزان الآن: كم من الضجيج يحتمله العقل قبل أن يعمى عن النظم.
    # وما كان نظمُه تامًّا يراه كلُّ أحد — وذلك صواب.
    # تشويشُ العالم الفعلي نحو 0.185 من المتوسط. فمن دون استدلالٍ
    # يقارب الثلثين لا يرى فيه نظمًا — والكشف قلبُ هذه المحاكاة.
    tolerance = 0.06 + 0.205 * max(0.0, min(1.0, reasoning))
    if cv <= tolerance:
        return mean
    return None
    mean = sum(gaps) / len(gaps)
    var = sum((x - mean) ** 2 for x in gaps) / len(gaps)
    sd = var ** 0.5
    snr = mean / max(1.0, sd)
    if snr * (0.4 + reasoning) > 2.1:
        return mean
    return None
