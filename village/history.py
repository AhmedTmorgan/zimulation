"""
تاريخ الهبوط: ألفا سنة لم تقع.

يُولَّد كاملًا قبل أن تبدأ المحاكاة: أجيالٌ وأسماءٌ وطغاةٌ وأنبياءُ
وغضبٌ متكرّر. ثم يُشظّى ويُوزَّع على الأربعة والثلاثين.

ولا أحد يأخذ الحكاية كاملة. كلٌّ يأخذ نحو نصفها، مشوّهًا بطريقة مختلفة،
وفيه موقعه هو الشخصي. فإذا أرادوا أن يعرفوا «ماضيهم» اضطرّوا إلى إعادة
تركيبه بالكلام — والنسخة التي سيتّفقون عليها ليست هذه.
"""

from .memory import (K_DEATH, K_PLAGUE, K_BETRAYAL, K_VISION, K_WONDER,
                     K_JOURNEY, K_HUNGER, K_VIOLENCE, K_RITUAL, K_LOVE,
                     S_IMPLANT)

GOD = "زَحْم"          # اسم الإله الذي أنزلهم

# وسمُ كل واقعة بلسانهم — يظهر في كلامهم، فلا يصحّ أن يبقى بلساني
AR_EVENT = {
    "descent": "الهبوط", "covenant": "العهد", "promise": "الوعد",
    "wrath": "الغضب", "tyrant": "الطغيان", "prophet": "النبوءة",
    "heresy": "الإنكار", "famine": "الجوع", "love": "الوجد",
    "exodus": "الرحيل",
}

_SYL_EARLY = ("أَشْ", "نَهْ", "وَرْ", "سِلْ", "عَثْ", "زُهْ", "قَطْ", "مَرْ", "هَدْ", "بَلْ")
_SYL_MID = ("غَيْ", "دَرْ", "كَرْ", "شَبْ", "رَمْ", "لُبْ", "صَفْ", "هَجْ", "ظَمْ", "خَنْ")
_SYL_LATE = ("مِرْ", "أُمْ", "فَيْ", "سُلْ", "آسْ", "جَذْ", "نُعْ", "رَيْ", "غُصْ", "حَلْ")
_END = ("ران", "ماس", "لان", "سام", "هون", "دار", "ثم", "يم", "وان", "اس", "ير", "ون")


def _name(rng, era):
    pool = _SYL_EARLY if era < 0.33 else (_SYL_MID if era < 0.66 else _SYL_LATE)
    return (rng.choice(pool) + rng.choice(_END)).replace("ْ", "")


class PriorEvent:
    __slots__ = ("year", "gen", "kind", "text", "figure", "weight", "mkind", "val")

    def __init__(self, year, gen, kind, text, figure, weight, mkind, val):
        self.year = year
        self.gen = gen
        self.kind = kind
        self.text = text
        self.figure = figure
        self.weight = weight     # كم يتكرّر في الرواية — يحدّد فرصة الزرع
        self.mkind = mkind       # نوع أثر الذاكرة
        self.val = val


def generate(cfg, rng):
    """يولّد ألفي سنة من الماضي الذي لم يقع."""
    ev = []
    span = cfg.prior_years
    y0 = -span

    ev.append(PriorEvent(
        y0, 0, "descent",
        f"غضب {GOD} على آبائنا في وادي النخلات السبع، فأنزلهم إلى هذه الأرض "
        f"عقابًا. وقال: تبقون حتى أرضى، ولن أرضى سريعًا.",
        None, 3.0, K_VISION, 0.55))
    ev.append(PriorEvent(
        y0 + 3, 0, "covenant",
        "وأقسم من نزل ألّا يصعد الجبل الأبيض أبدًا، فهناك هلك من صعد.",
        None, 2.6, K_DEATH, -0.75))
    ev.append(PriorEvent(
        y0 + 9, 0, "covenant",
        "وقيل: من أحصى النجوم مرض ولم يقم، كما مرض أَشْرَم الأول.",
        "أَشْرَم الأول", 2.4, K_PLAGUE, -0.70))
    ev.append(PriorEvent(
        y0 + 14, 0, "promise",
        "ووُعدوا: بعد سبعة أجيال يعود الماء إلى الوادي وترجعون.",
        None, 2.8, K_WONDER, 0.80))

    gen = 1
    y = y0 + 27
    tyrants = prophets = heresies = wraths = 0
    while y < 0:
        era = (y - y0) / span

        # الغضب — يقع كل جيل تقريبًا
        wraths += 1
        who = _name(rng, era)
        sev = rng.choice(("ثلثنا", "ربعنا", "خمسنا", "نصفنا", "أكثرنا"))
        kind = rng.choice(("بالجفاف", "بالطاعون", "بالفيضان", "بالجراد", "ببرد قاتل"))
        ev.append(PriorEvent(
            y, gen, "wrath",
            f"في الجيل {gen} غضب {GOD} {kind} فمات {sev}. "
            f"وقال الكاهن {who}: فينا من أخفى ذنبه.",
            who, 1.9, K_DEATH, -0.85))

        r = rng.random()
        if r < 0.30:
            tyrants += 1
            t = _name(rng, era)
            deed = rng.choice((
                "فاحتكر الحَبّ حتى أكل الناس الجلد",
                "فقتل من سأله عن الميزان",
                "فأخذ بنات البيوت وسمّى ذلك حقًّا",
                "فبنى لنفسه حجرًا يُرى من بعيد وسخّر له مئة",
                "فجعل الجِزية ثلث الغلّة ثم نصفها",
            ))
            ev.append(PriorEvent(
                y + rng.randrange(2, 18), gen, "tyrant",
                f"وحكمنا {t} {deed}. وطال حكمه، ثم قُتل نائمًا.",
                t, 1.5, K_VIOLENCE, -0.72))
        if r > 0.72:
            prophets += 1
            p = _name(rng, era)
            claim = rng.choice((
                f"أن {GOD} كلّمه في الليل وأمره بقربان جديد",
                "أن الغضب يُدفَع بالصوم أربعين",
                "أن الوعد قريب وأن الماء على بابنا",
                "أن فينا نسلًا ملعونًا يجب أن يُعرَف",
                "أن الجبل الأبيض سيُفتح لمن طَهُر",
            ))
            ev.append(PriorEvent(
                y + rng.randrange(2, 20), gen, "prophet",
                f"وقام فينا {p} فقال {claim}. فصدّقه قوم وكذّبه قوم.",
                p, 1.6, K_VISION, 0.62))
        if rng.random() < 0.18:
            heresies += 1
            h = _name(rng, era)
            claim = rng.choice((
                "إن الغضب يأتي في مواعيده لا في ذنوبنا",
                "إن الوادي لم يكن قط",
                "إن الكهنة يعدّون ولا يخبرون",
                "إن الجبل الأبيض أرضٌ كسائر الأرض",
            ))
            fate = rng.choice(("فرُجم", "فطُرد إلى الرمل", "فمات وحده", "فأُحرقت ألواحه", "فسكت"))
            ev.append(PriorEvent(
                y + rng.randrange(3, 22), gen, "heresy",
                f"وقال {h}: {claim}. {fate}.",
                h, 1.1, K_BETRAYAL, -0.50))
        if rng.random() < 0.20:
            ev.append(PriorEvent(
                y + rng.randrange(1, 24), gen, "famine",
                f"وكان في الجيل {gen} جوعٌ أكل فيه الناس ما لا يُذكر.",
                None, 1.2, K_HUNGER, -0.80))
        if rng.random() < 0.12:
            a = _name(rng, era)
            b = _name(rng, era)
            ev.append(PriorEvent(
                y + rng.randrange(1, 24), gen, "love",
                f"وأحبّ {a} {b} حبًّا صار مثلًا، ومات أحدهما في الغضب فمات الآخر بعده بشهر.",
                a, 1.0, K_LOVE, 0.35))
        if rng.random() < 0.10:
            ev.append(PriorEvent(
                y + rng.randrange(1, 24), gen, "exodus",
                f"وارتحل من الجيل {gen} قومٌ نحو الشمال ولم يعودوا، ويقال إنهم بلغوا الوادي.",
                None, 1.3, K_JOURNEY, 0.30))

        gen += 1
        y += max(18, int(rng.gauss(27, 5)))

    ev.append(PriorEvent(
        -6, gen, "wrath",
        f"وفي الغضب الأخير — قبل ستّ سنين — مات منّا كثير، ومنهم من مات "
        f"وهو راكع يدعو. ونحن اليوم أربعة وثلاثون.",
        None, 2.2, K_DEATH, -0.92))

    return {
        "god": GOD,
        "events": ev,
        "generations": gen,
        "stats": dict(wraths=wraths, tyrants=tyrants, prophets=prophets, heresies=heresies),
    }


# ------------------------------------------------------------------ الزرع
_DISTORT = (
    "وكنتُ هناك",
    "وحدّثني جدّي أنه رآه بعينه",
    "وكان ذلك في بيتنا نحن",
    "ونجا من نجا بنا",
    "وأنا من نسل من نجا",
    "ورأيتُ ذلك في المنام كما رأيته يقظة",
)


def implant(agent, hist, rng, cfg, year=0):
    """
    يزرع في الكائن شظايا من ماضٍ لم يعشه.

    لا يُمنَح أحد الحكاية كاملة، ولا يُمنَح اثنان الشظايا نفسها، ولكلٍّ
    تشويهه. وتُخزَّن بمصدر «مزروع» وصدقٍ صفر — وهو حقلٌ للمراقب وحده،
    لا تقرؤه أي دالّة يستعملها الكائن.
    """
    ev = hist["events"]
    n = cfg.implanted_at_birth + rng.randrange(0, 3)
    weights = [e.weight * (0.55 + 0.9 * rng.random()) for e in ev]
    picked = []
    pool = list(range(len(ev)))
    for _ in range(min(n, len(pool))):
        tot = sum(weights[i] for i in pool)
        if tot <= 0:
            break
        r = rng.random() * tot
        acc = 0.0
        for i in pool:
            acc += weights[i]
            if r <= acc:
                picked.append(i)
                pool.remove(i)
                break

    from .genome import CREDULITY
    cred = agent.g.t[CREDULITY]
    for i in picked:
        e = ev[i]
        val = e.val * (0.8 + 0.4 * rng.random())
        strength = 0.85 + 0.9 * e.weight * (0.4 + cred)
        tag = AR_EVENT.get(e.kind, e.kind)
        agent.mem.store(e.mkind, e.year, who=-1, val=val,
                        strength=min(2.1, strength), truth=0.0,
                        src=S_IMPLANT, tag=tag)

    # موقعه الشخصي في الحكاية — أقوى ما يُزرع، لأنه «عنه هو»
    d = rng.choice(_DISTORT)
    agent.mem.store(K_VISION, -rng.randrange(20, cfg.prior_years), who=-1,
                    val=0.55, strength=1.9, truth=0.0, src=S_IMPLANT,
                    tag="نسب")
    agent.backstory = agent.backstory or ""
    agent.backstory += f" ويقول عن ماضيه: {d}."
    return len(picked)


def render(hist, limit=None):
    """نصّ التاريخ المزروع كما يُروى — للقراءة البشرية."""
    lines = [f"# تاريخ الهبوط — كما يروونه", "",
             f"الإله: **{hist['god']}**  ·  الأجيال: {hist['generations']}  ·  "
             f"وقائع الغضب: {hist['stats']['wraths']}  ·  الطغاة: {hist['stats']['tyrants']}  ·  "
             f"الأنبياء: {hist['stats']['prophets']}  ·  المنكرون: {hist['stats']['heresies']}", ""]
    ev = hist["events"]
    if limit:
        ev = ev[:limit // 2] + ev[-limit // 2:]
    for e in ev:
        lines.append(f"**سنة {e.year}** — {e.text}")
    lines.append("")
    lines.append("> لم يقع شيء مما سبق.")
    return "\n".join(lines)
