"""
العلل — مئةٌ منها، ولكلٍّ سببٌ في العالم لا في يدي.

كان السقم عندهم رقمًا واحدًا: `illness` يرتفع فينحلّ الجسد. فإذا سُئل
«ممّ مرض هذا؟» لم يكن الجواب إلا «لأن الرقم ارتفع». وذلك ليس علّة.

فصار السقم **علّةً مسمّاة لها مَنشأ**. ولا تقع علّةٌ إلا إذا وُجد
سببُها في الدنيا: لا يقع داءُ الماشية قبل أن يستأنسوا، ولا داءُ الزحام
قبل أن يبلغ العدد حدَّه، ولا داءُ الماء حيث الماء نظيف. **والعلل
تُخلَق من الأسباب لا تُوزَّع على الناس.**

## الأسر الاثنتا عشرة، ولكلٍّ مرجع

| الأسرة | من أين تجيء | المرجع |
|---|---|---|
| `zoonosis` | من الحيوان المستأنس إلى الإنسان | Diamond 1997؛ Wolfe et al. 2007 |
| `crowd` | لا تبقى إلا في تجمّعٍ يفوق حدَّ المجتمع الحرج | Bartlett 1957؛ Black 1966 |
| `water` | برازٌ يعود إلى الفم عبر الماء | Snow 1855 |
| `vector` | سبخةٌ ودفءٌ وحشرةٌ ناقلة | — |
| `deficiency` | قوتٌ واحدٌ لا يكفي الجسد | Lind 1753 (الأسقربوط) |
| `wound` | جرحٌ يتعفّن بعد ضربٍ أو كدح | — |
| `birth` | ولادةٌ تُعطب أو مولودٌ لا يقوى | Loudon 1992 |
| `degenerative` | إصلاحٌ ينحدر فيتراكم الأذى | Kirkwood 1977 |
| `congenital` | قرابةٌ في الدم بين الأبوين | Bittles & Black 2010 |
| `toxic` | صنعةٌ تسمّم صاحبها: نحاسٌ ورصاصٌ وغبار | Ramazzini 1700 |
| `melancholy` | يأسٌ يطول فيُنهك الجسد | — |
| `contagion` | لمسٌ ونفَسٌ بين الناس بلا حيوان |  — |

## ما لا يعرفونه

الكائن لا يقرأ اسم علّته ولا أسرتها ولا آليّتها. **يرى الأعراض وحدها**:
حُمّى، سعال، طفح، إسهال، وهن، ألم، تورّم، يرقان، رعشة، هزال. وعلّتان
مختلفتان تُعطيان أعراضًا متشابهة فتُخلَطان — وهذا هو سبب أن الطبّ احتاج
آلاف السنين. ولا نلمّح لهم أبدًا.
"""

import random

# ------------------------------------------------------------- الأعراض
SIGNS = ("حُمّى", "سُعال", "طفح", "إسهال", "وهن",
         "ألم", "تورّم", "يرقان", "رعشة", "هزال")
NS = len(SIGNS)

# ----------------------------------------------------------- الآليّات
# ما الذي يفعله الداء بالجسد. ومنه — لا من اسمه — يُعرف ما ينفعه.
MECHANISMS = ("عفن", "حُمّى", "سُمّ", "نقص", "احتقان",
              "نزف", "تشنّج", "هزال")
NM = len(MECHANISMS)
M_ROT, M_FEVER, M_POISON, M_LACK, M_CONGEST, M_BLEED, M_SPASM, M_WASTE = range(NM)

FAMILIES = ("zoonosis", "crowd", "water", "vector", "deficiency", "wound",
            "birth", "degenerative", "congenital", "toxic", "melancholy",
            "contagion")
AR_FAMILY = {
    "zoonosis": "من الماشية", "crowd": "من الزحام", "water": "من الماء",
    "vector": "من السبخة", "deficiency": "من القوت", "wound": "من الجرح",
    "birth": "من الولادة", "degenerative": "من البِلى",
    "congenital": "من الدم", "toxic": "من الصنعة",
    "melancholy": "من الهمّ", "contagion": "من المخالطة",
}

#: كم علّةً من كل أسرة. المجموع مئة.
QUOTA = {
    "zoonosis": 14, "crowd": 11, "water": 10, "vector": 7,
    "deficiency": 8, "wound": 8, "birth": 6, "degenerative": 12,
    "congenital": 6, "toxic": 7, "melancholy": 4, "contagion": 7,
}

#: طبعُ كل أسرة: (آليّاتها الغالبة، شدّتها، مدّتها، عدواها، حدُّ ظهورها)
_TEMPER = {
    "zoonosis":     ((M_FEVER, M_ROT), 0.55, 3.0, 0.55, "herd"),
    "crowd":        ((M_FEVER, M_CONGEST), 0.50, 2.2, 0.75, "dense"),
    "water":        ((M_ROT, M_WASTE), 0.45, 2.0, 0.35, "foul"),
    "vector":       ((M_FEVER, M_SPASM), 0.50, 4.5, 0.0, "marsh"),
    "deficiency":   ((M_LACK, M_BLEED), 0.35, 6.0, 0.0, "diet"),
    "wound":        ((M_ROT, M_FEVER), 0.60, 1.5, 0.0, "hurt"),
    "birth":        ((M_BLEED, M_ROT), 0.70, 1.2, 0.0, "birth"),
    "degenerative": ((M_WASTE, M_CONGEST), 0.30, 9.0, 0.0, "old"),
    "congenital":   ((M_LACK, M_WASTE), 0.45, 12.0, 0.0, "kin"),
    "toxic":        ((M_POISON, M_SPASM), 0.40, 5.0, 0.0, "craft"),
    "melancholy":   ((M_WASTE, M_LACK), 0.25, 4.0, 0.0, "despair"),
    "contagion":    ((M_ROT, M_FEVER), 0.35, 2.5, 0.60, "touch"),
}

_A = ("سَ", "زُ", "قِ", "دَ", "نُ", "بِ", "مَ", "حُ", "طِ", "خَ", "رُ", "شِ",
      "غَ", "ثُ", "لِ", "كَ")
_B = ("ام", "ول", "اث", "ين", "اد", "وم", "ير", "اس", "ان", "اح", "وث",
      "اف", "يم", "ال", "ون", "اق")


def _coin(rng):
    return rng.choice(_A) + rng.choice(_B)


class Malady:
    """
    علّةٌ بعينها. اسمُها وأسرتُها وآليّتها **للمراقب**؛ ولا يقرأ الكائنُ
    منها إلا ما يظهر على الجسد.
    """

    __slots__ = ("id", "key", "name", "family", "mech", "signs", "severity",
                 "years", "transmit", "gate", "onset", "chronic", "toll",
                 "stubborn")

    def __init__(self, i, key, name, family, mech, signs, severity, years,
                 transmit, gate, chronic):
        self.id = i
        self.key = key
        self.name = name          # اسمٌ للمراقب — وهم يسمّونها بأنفسهم
        self.family = family
        self.mech = mech          # متّجه الآليّة — سرٌّ تامّ
        self.signs = signs        # ما يُرى منها
        self.severity = severity
        self.years = years
        self.transmit = transmit
        self.gate = gate          # الشرط الذي لا تقع قبله
        self.chronic = chronic
        self.stubborn = 0.0       # سرّ: ما لا يبلغه النبات منها
        self.toll = 0             # كم قتلت — للمراقب

    def visible(self):
        """ما يراه الناظر: الأعراض فوق حدّ الظهور، لا أكثر."""
        return tuple(SIGNS[i] for i, v in enumerate(self.signs) if v > 0.30)


def build(seed=20260910):
    """
    يُبنى جدولُ العلل مرّةً واحدة، وهو **ثابتٌ بين الرنّات**: بيولوجيا
    هذا العالم واحدة، والذي يختلف هو ما يكتشفونه منها. ولو تغيّرت مع
    كل بذرة لما أمكن أن يُقارَن رنٌّ برنّ.
    """
    rng = random.Random(seed)
    out = []
    i = 0
    for fam in FAMILIES:
        mechs, sev0, yrs0, tr0, gate = _TEMPER[fam]
        for k in range(QUOTA[fam]):
            mech = [0.0] * NM
            for m in mechs:
                mech[m] = 0.55 + 0.45 * rng.random()
            # ولكل علّةٍ شذوذُها: آليّةٌ ثالثة تجعلها تخالف أخواتها
            mech[rng.randrange(NM)] += 0.30 * rng.random()
            s = sum(mech) or 1.0
            mech = [x / s for x in mech]

            # الأعراض تتبع الآليّة ولا تطابقها — ولهذا تُخلَط العلل
            signs = [0.0] * NS
            for m, w in enumerate(mech):
                if w <= 0.02:
                    continue
                for sgn in _SIGN_OF[m]:
                    signs[sgn] += w * (0.6 + 0.8 * rng.random())
            for j in range(NS):
                signs[j] = min(1.0, signs[j] + rng.gauss(0.0, 0.06))

            sev = max(0.05, sev0 * rng.gauss(1.0, 0.30))
            yrs = max(0.4, yrs0 * rng.gauss(1.0, 0.35))
            tr = max(0.0, tr0 * rng.gauss(1.0, 0.25))
            m_ = Malady(i, f"{fam}{k}", _coin(rng), fam, mech, signs,
                        sev, yrs, tr, gate, yrs > 5.0)
            # **ما لا يبلغه النبات.**
            #
            # ليس كلُّ داءٍ له في الأرض دواء. العفن والحُمّى والنقص
            # تُدفَع بورقةٍ أو جذر؛ وأمّا مفصلٌ بَلِي، أو دمٌ جاء معتلًّا
            # من الأبوين، أو همٌّ أقعد صاحبَه — فلا تردّه عشبة. ومن ظنّ
            # أن لكل داءٍ دواءً فقد وعد الناسَ بما ليس عنده.
            #
            # وهذا هو أقسى ما في المسألة عليهم: يجرّبون ويجرّبون على
            # داءٍ لا يُجرَّب له، فيموت المريض ويبقى الظنّ أنهم قصّروا.
            m_.stubborn = _STUBBORN.get(fam, 0.0) * rng.gauss(1.0, 0.18)
            m_.stubborn = max(0.0, min(0.97, m_.stubborn))
            out.append(m_)
            i += 1
    return out


#: كم يعصى الداءُ على النبات، بحسب أسرته.
_STUBBORN = {
    "congenital": 0.94,     # دمٌ جاء هكذا — لا تردّه ورقة
    "degenerative": 0.88,   # ما بَلِي لا يُعاد بعُشب
    "melancholy": 0.72,     # يُخفَّف ولا يُرفَع
    "birth": 0.55,          # يُعان عليه، وأكثرُه بيد القابلة لا بالدواء
    "toxic": 0.45,          # يُوقَف إن تُرك السبب، وإلا فلا
    "vector": 0.30,
    "crowd": 0.22,
    "zoonosis": 0.20,
    "contagion": 0.18,
    "water": 0.12,
    "wound": 0.10,
    "deficiency": 0.05,     # نقصٌ يُسدّ بما نقص — أيسرُها وأخفاها
}

#: أيُّ عرَضٍ يصحب أيَّ آليّة. هذا هو الجسر الوحيد بين ما يقع وما يُرى.
_SIGN_OF = {
    M_ROT:     (0, 3, 6),      # حمّى، إسهال، تورّم
    M_FEVER:   (0, 4, 8),      # حمّى، وهن، رعشة
    M_POISON:  (5, 8, 3),      # ألم، رعشة، إسهال
    M_LACK:    (9, 4, 2),      # هزال، وهن، طفح
    M_CONGEST: (1, 0, 4),      # سعال، حمّى، وهن
    M_BLEED:   (7, 4, 9),      # يرقان، وهن، هزال
    M_SPASM:   (8, 5, 0),      # رعشة، ألم، حمّى
    M_WASTE:   (9, 4, 5),      # هزال، وهن، ألم
}

TUNED = {"QUOTA_TOTAL": sum(QUOTA.values()), "SIGN_SHOW": 0.30,
         "MECH_ODD": 0.30, "SIGN_NOISE": 0.06}


# ==================================================== متى يقع الداء
#: حدُّ المجتمع الحرج: تحته لا تبقى أدواءُ الزحام لأنها تُفني عائلها
#: أو تُمنّعه فتنقطع سلسلتها (Bartlett 1957؛ Black 1966 في الحصبة).
CRITICAL_COMMUNITY = 240.0

def by_family(mals):
    idx = {f: [] for f in FAMILIES}
    for m in mals:
        idx[m.family].append(m)
    return idx


def pressures(st, region, know, pop, foul_v, climate, marsh_near):
    """
    ضغطُ كل أسرةٍ في هذه القرية هذه السنة. **يُحسب مرّةً للقرية لا لكل
    نفس**، وإلا أثقل الرنّ.

    ولا يقع داءٌ لم يُصنَع سببُه: من لم يستأنس لم يصبه داءُ الماشية،
    ومن لم يزدحم لم يصبه داءُ الزحام، ومن ماؤه نظيفٌ سلِم من داء الماء.
    """
    p = {}
    if "herding" in know:
        # الاستئناسُ يفتح الباب، والكثافةُ تُبقيه مفتوحًا
        p["zoonosis"] = 0.010 + 0.020 * min(1.0, pop / 120.0)
    if pop > CRITICAL_COMMUNITY:
        # تحت الحدّ الحرج تنقطع السلسلة، وفوقه تستوطن
        p["crowd"] = 0.018 * min(2.0, (pop - CRITICAL_COMMUNITY) / CRITICAL_COMMUNITY)
    if foul_v > 0.05:
        p["water"] = 0.040 * foul_v
    if marsh_near > 0.0:
        # الناقل يحتاج ماءً راكدًا ودفئًا
        p["vector"] = 0.030 * marsh_near * max(0.0, min(1.6, climate))
    if pop > 8:
        p["contagion"] = 0.006 + 0.010 * min(1.0, pop / 200.0)
    return p


def roll(a, pres, idx, rng, sick_share):
    """
    هل يقع على هذا الجسد داءٌ هذه السنة، وأيُّه؟

    الأسبابُ العامّة تأتي من القرية، والخاصّةُ من حاله هو: جوعُه وجرحُه
    وسنُّه وصنعتُه وهمُّه. ومن كان أوهنَ أُصيب أكثر — لا لأن الداء يختار
    بل لأن المقاومة تقلّ.
    """
    from . import genome as G
    frail = 1.0 + 0.9 * min(1.0, a.hunger) - 0.5 * a.g.t[G.VIGOR]
    frail = max(0.25, frail)

    r = dict(pres)
    # المخالطة: بقدر من حولك من المرضى
    if "contagion" in r:
        r["contagion"] *= (0.4 + 2.2 * sick_share)
    if "crowd" in r:
        r["crowd"] *= (0.4 + 1.8 * sick_share)

    if a.hunger > 0.25:
        r["deficiency"] = 0.030 * (a.hunger - 0.25)
    if a.health < 0.55:
        r["wound"] = 0.045 * (0.55 - a.health)
    if a.damage > 0.8 and a.age > 35:
        r["degenerative"] = 0.012 * (a.damage - 0.8) * (1.0 + (a.age - 35) / 40.0)
    if getattr(a, "despair", 0.0) > 0.45:
        r["melancholy"] = 0.030 * (a.despair - 0.45)
    if getattr(a, "smelt", 0.0) > 0.0:
        r["toxic"] = 0.022 * min(1.0, a.smelt)

    for fam, rate in r.items():
        if rng.random() < rate * frail:
            pool = idx.get(fam)
            if pool:
                return pool[rng.randrange(len(pool))]
    return None


def intensity(m):
    """
    ما يحمله الجسدُ من الداء **في السنة الواحدة**.

    والشدّةُ المكتوبة في الداء هي جملتُه لا سنويّتُه: فالحادّ يصبّها في
    عامٍ أو عامين، والمزمنُ يفرّقها على عشرة. وكان يُؤخذ المكتوب كما هو
    فيبقى صاحبُ الداء المزمن في ذروة السقم **اثنتي عشرة سنة** بلا
    انقطاع — فلا يحتمله جسد، وانقرض القوم في مئةٍ وثمانين سنة.

    والحقّ أن طولَ الداء وشدّته يتعاكسان: ما طال خفّ، وما اشتدّ قصُر.
    """
    return m.severity * (2.0 / (1.0 + m.years))


def burden(a, mals):
    """ما تُحدثه العلل القائمة من سقمٍ ظاهر — وهو ما يراه الناس."""
    tot = 0.0
    for mid, left, _ in a.sick:
        tot += intensity(mals[mid]) * (0.55 + 0.45 * min(1.0, left))
    return min(1.0, tot)


def signs_of(a, mals):
    """الأعراض المجتمعة كما تُرى على الجسد. لا اسمَ فيها ولا أسرة."""
    v = [0.0] * NS
    for mid, left, _ in a.sick:
        m = mals[mid]
        w = 0.55 + 0.45 * min(1.0, left)
        for i in range(NS):
            v[i] = max(v[i], m.signs[i] * w)
    return v


def progress(a, mals, rng, repair):
    """
    تمرّ سنةٌ على ما به. يعيد قائمة ما شُفي منه وما بقي.

    وأكثرُ الأدواء تنقضي من نفسها — **وهذه هي الآفة التي تخدع كلَّ من
    يجرّب دواءً**: يشرب المريض ورقةً ثم يبرأ لأن أجلَ الداء انقضى، فيُنسب
    الشفاء إلى الورقة. ولا سبيل إلى تمييز ذلك إلا بعدٍّ طويلٍ ومقارنة.
    """
    healed = []
    keep = []
    for mid, left, dose in a.sick:
        m = mals[mid]
        left -= (1.0 / max(0.4, m.years)) * (0.75 + 0.5 * repair)
        if left <= 0.0:
            healed.append(mid)
        else:
            keep.append((mid, left, dose))
    a.sick = keep
    return healed


TUNED["CRITICAL_COMMUNITY"] = CRITICAL_COMMUNITY
