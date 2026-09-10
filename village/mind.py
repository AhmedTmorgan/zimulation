"""
العقل: الكود الذي يعيد الكائن كتابته بنفسه.

ثلاث طبقات، كل واحدة أعمق من التي قبلها:
  (١) أوزان — مصفوفة قرار ابتدائية تصنعها الغرائز الموروثة.
  (٢) بنية — الكائن يفتح وصلات ويغلق أخرى أثناء التأمّل.
  (٣) لغة — حِكَم يؤلّفها الكائن بنفسه، تُقرأ وتُورَّث وتُعلَّم (انظر lang.py).

والقاعدة التي يقوم عليها المشروع كله:
  التعلّم يقرأ من الذاكرة، لا من الواقع.
كل تعديل يجريه الكائن على كوده مصدره أثرٌ في ذاكرته — وقد يكون هذا الأثر
مزروعًا أو محلومًا أو مُختلَقًا. الكائن لا يملك وسيلة للتمييز.
"""

import math
import random as _random

from . import genome as G
from .lang import eval_expr, compose_maxim, mutate_maxim

FEATURES = (
    "bias", "hunger", "sick", "tired", "lonely", "crowded", "threat", "grief",
    "lust", "grudge", "scarcity", "surplus", "young", "old", "kin_need",
    "leisure", "awe", "humiliated", "ruled", "powerful", "wrath_near", "doubt",
    "dread", "want", "despair",
)
NF = len(FEATURES)
(
    F_BIAS, F_HUNGER, F_SICK, F_TIRED, F_LONELY, F_CROWDED, F_THREAT, F_GRIEF,
    F_LUST, F_GRUDGE, F_SCARCITY, F_SURPLUS, F_YOUNG, F_OLD, F_KIN_NEED,
    F_LEISURE, F_AWE, F_HUMILIATED, F_RULED, F_POWERFUL, F_WRATH_NEAR, F_DOUBT,
    F_DREAD, F_WANT, F_DESPAIR,
) = range(NF)

AR_FEATURES = {
    "bias": "دائمًا", "hunger": "جوع", "sick": "مرض", "tired": "إعياء",
    "lonely": "وحدة", "crowded": "زحام", "threat": "خطر", "grief": "فَقْد",
    "lust": "شهوة", "grudge": "ضغينة", "scarcity": "شُحّ", "surplus": "فائض",
    "young": "صِبا", "old": "شيخوخة", "kin_need": "قريبٌ محتاج",
    "leisure": "فراغ", "awe": "رهبة", "humiliated": "مهانة",
    "ruled": "تحت حاكم", "powerful": "بيدي سلطة",
    "wrath_near": "الغضب قريب", "doubt": "شكّ",
    "dread": "رهبة الموت", "want": "خوف العوز", "despair": "يأس",
}

ACTIONS = (
    "forage", "farm", "herd", "build", "craft", "rest", "socialize", "court",
    "tend", "teach", "learn", "quarrel", "attack", "reconcile", "contemplate",
    "ritual", "preach", "scheme", "seize", "observe", "wander", "hoard",
)
NA = len(ACTIONS)
(
    A_FORAGE, A_FARM, A_HERD, A_BUILD, A_CRAFT, A_REST, A_SOCIALIZE, A_COURT,
    A_TEND, A_TEACH, A_LEARN, A_QUARREL, A_ATTACK, A_RECONCILE, A_CONTEMPLATE,
    A_RITUAL, A_PREACH, A_SCHEME, A_SEIZE, A_OBSERVE, A_WANDER, A_HOARD,
) = range(NA)

AR_ACTIONS = {
    "forage": "اجمع", "farm": "ازرع", "herd": "ارعَ الماشية", "build": "ابنِ",
    "craft": "اصنع", "rest": "نَم", "socialize": "خالِط", "court": "تقرّب",
    "tend": "داوِ", "teach": "علّم", "learn": "تعلّم", "quarrel": "خاصِم",
    "attack": "اضرب", "reconcile": "صالِح", "contemplate": "تأمّل",
    "ritual": "تعبّد", "preach": "اخطُب باسم الإله", "scheme": "تآمر",
    "seize": "استولِ على الأمر", "observe": "ارصُد وأحصِ", "wander": "ارتحل",
    "hoard": "اكنز",
}

# صيغة الإخبار — غير صيغة الأمر. «اجمع» أمرٌ، و«جمعتُ» خبر.
AR_DEEDS = {
    "forage": "جمعتُ", "farm": "زرعتُ", "herd": "رعيتُ", "build": "بنيتُ",
    "craft": "صنعتُ", "rest": "نمتُ", "socialize": "خالطتُ", "court": "تقرّبتُ",
    "tend": "داويتُ", "teach": "علّمتُ", "learn": "تعلّمتُ", "quarrel": "خاصمتُ",
    "attack": "ضربتُ", "reconcile": "صالحتُ", "contemplate": "تأمّلتُ",
    "ritual": "تعبّدتُ", "preach": "خطبتُ", "scheme": "دبّرتُ",
    "seize": "أخذتُ الأمر", "observe": "رصدتُ وأحصيتُ", "wander": "ارتحلتُ",
    "hoard": "كنزتُ",
}

# أفعال لا يمارسها إلا من بلغ
ADULT_ONLY = frozenset((A_COURT, A_PREACH, A_SCHEME, A_SEIZE, A_ATTACK, A_HOARD))
# أفعال منتجة للطعام
PRODUCTIVE = frozenset((A_FORAGE, A_FARM, A_HERD))


# بناء المصفوفة يستهلك ٤٨٤ عيّنة عشوائية لكل مولود. توليدها واحدةً واحدة
# كان يلتهم خُمس زمن المحاكاة، فنسحب من بِركةٍ ثابتة بإزاحة عشوائية واحدة:
# نفس التوزيع، ونفس الحتمية، وجزءٌ من التكلفة.
_POOL = [_random.Random(0x5EED).gauss(0.0, 1.0) for _ in range(8192)]
_PLEN = len(_POOL)


def _noise(rng, count, sigma):
    o = rng.randrange(_PLEN)
    if o + count <= _PLEN:
        return [v * sigma for v in _POOL[o:o + count]]
    return [_POOL[(o + i) % _PLEN] * sigma for i in range(count)]


# --------------------------------------------------------------- الغرائز
def innate(g, rng):
    """
    المصفوفة الابتدائية: ما لم يتعلّمه أحد وإنما وُلد به.
    بدون هذه الغرائز يموت الجميع في خمس سنين ولا يحدث تطوّر أصلًا.
    """
    t = g.t
    W = _noise(rng, NF * NA, 0.05)

    def w(f, a, v):
        W[f * NA + a] += v

    # الجوع يدفع للإنتاج
    for a in (A_FORAGE, A_FARM, A_HERD):
        w(F_HUNGER, a, 3.4 + 0.9 * t[G.SEEKING])
    w(F_SCARCITY, A_FORAGE, 1.1)
    w(F_SCARCITY, A_FARM, 1.0)
    w(F_SCARCITY, A_HERD, 0.9)
    w(F_HUNGER, A_HOARD, 0.5 * (1.0 - t[G.HONESTY]))
    w(F_SCARCITY, A_HOARD, 0.7 * (1.0 - t[G.HONESTY]) + 0.4 * t[G.NARCISSISM])
    w(F_SCARCITY, A_WANDER, 0.6 + 0.5 * t[G.OPENNESS])
    w(F_SCARCITY, A_ATTACK, 0.5 * t[G.CALLOUSNESS] + 0.4 * t[G.RAGE])

    # الجسد
    w(F_TIRED, A_REST, 1.9)
    w(F_SICK, A_REST, 1.5)
    w(F_SICK, A_RITUAL, 0.6 * t[G.CREDULITY])
    w(F_OLD, A_TEACH, 0.9 + 0.6 * t[G.CARE])
    w(F_OLD, A_CONTEMPLATE, 0.6 + 0.7 * t[G.OPENNESS])
    w(F_YOUNG, A_LEARN, 1.4)
    w(F_YOUNG, A_SOCIALIZE, 0.8 + 0.6 * t[G.PLAY])

    # الخطر
    w(F_THREAT, A_WANDER, 1.0 + 1.1 * t[G.FEAR])
    w(F_THREAT, A_ATTACK, 0.9 * t[G.RAGE] + 0.7 * t[G.DOMINANCE] - 0.6 * t[G.FEAR])
    w(F_THREAT, A_BUILD, 0.5 + 0.5 * t[G.CONSCIENT])

    # الوصل والقطع
    w(F_LONELY, A_SOCIALIZE, 1.5 * (0.4 + t[G.EXTRAVERSION]))
    w(F_LONELY, A_COURT, 0.9 * (0.2 + t[G.LUST]))
    w(F_LUST, A_COURT, 1.9 * (0.3 + t[G.LUST]))
    w(F_CROWDED, A_QUARREL, 0.6 * (1.0 - t[G.AGREEABLE]))
    w(F_CROWDED, A_WANDER, 0.4)
    w(F_KIN_NEED, A_TEND, 1.5 * (0.3 + t[G.CARE]))
    w(F_GRIEF, A_RITUAL, 0.9 * t[G.CREDULITY] + 0.4)
    w(F_GRIEF, A_CONTEMPLATE, 0.7 + 0.5 * t[G.OPENNESS])
    w(F_GRIEF, A_TEND, 0.5 * t[G.CARE])

    # الضغينة والمهانة — محرّك الثأر
    w(F_GRUDGE, A_QUARREL, 1.0 * (1.0 - t[G.AGREEABLE]) + 0.5 * t[G.RAGE])
    w(F_GRUDGE, A_ATTACK, 2.3 * t[G.RAGE] * (0.4 + t[G.CALLOUSNESS]))
    w(F_GRUDGE, A_RECONCILE, 1.2 * (t[G.AGREEABLE] + t[G.HONESTY]) * 0.6)
    w(F_GRUDGE, A_SCHEME, 0.9 * t[G.MACHIAVELLIAN])
    w(F_HUMILIATED, A_ATTACK, 2.2 * t[G.NARCISSISM] * (0.3 + t[G.RAGE]))
    w(F_HUMILIATED, A_SCHEME, 1.1 * t[G.MACHIAVELLIAN] + 0.5 * t[G.NARCISSISM])
    w(F_HUMILIATED, A_SEIZE, 0.8 * t[G.DOMINANCE] * t[G.NARCISSISM] * 2.0)
    w(F_HUMILIATED, A_CONTEMPLATE, 0.6 * t[G.OPENNESS])

    # الفراغ — الشرط الذي بدونه لا تأمّل ولا اختراع ولا دين
    lei = 0.9
    w(F_LEISURE, A_CONTEMPLATE, lei * (0.5 + 1.5 * t[G.OPENNESS]))
    w(F_LEISURE, A_CRAFT, lei * (0.4 + 1.2 * t[G.CONSCIENT]))
    w(F_LEISURE, A_SOCIALIZE, lei * (0.4 + t[G.EXTRAVERSION]))
    w(F_LEISURE, A_TEACH, lei * 0.6 * t[G.CARE])
    w(F_LEISURE, A_OBSERVE, lei * (0.3 + 2.6 * t[G.OPENNESS] * t[G.REASONING]))
    w(F_BIAS, A_OBSERVE, 1.5 * t[G.REASONING] * t[G.OPENNESS] - 0.5)
    w(F_SURPLUS, A_BUILD, 0.9 + 0.6 * t[G.CONSCIENT])
    w(F_SURPLUS, A_CRAFT, 0.8)
    w(F_SURPLUS, A_RITUAL, 0.5 * t[G.CREDULITY])
    w(F_SURPLUS, A_SCHEME, 0.6 * t[G.MACHIAVELLIAN] * t[G.DOMINANCE] * 2.0)

    # الرهبة والعقيدة
    w(F_AWE, A_RITUAL, 1.15 * (0.3 + t[G.CREDULITY]))
    w(F_AWE, A_PREACH, 1.0 * t[G.EXTRAVERSION] * (0.3 + t[G.NARCISSISM]) * 1.6)
    w(F_AWE, A_CONTEMPLATE, 0.6 * t[G.OPENNESS])
    w(F_WRATH_NEAR, A_RITUAL, 1.5 * (0.2 + t[G.CREDULITY]))
    w(F_WRATH_NEAR, A_HOARD, 0.9 * (1.0 - t[G.HONESTY]) + 0.4)
    w(F_WRATH_NEAR, A_PREACH, 0.9 * t[G.MACHIAVELLIAN] + 0.5 * t[G.CREDULITY])
    w(F_WRATH_NEAR, A_WANDER, 0.5 * t[G.FEAR])

    # الشكّ — بذرة العلم، ومصدر الهرطقة
    w(F_DOUBT, A_OBSERVE, 1.4 * (0.2 + t[G.REASONING]) * (0.3 + t[G.OPENNESS]) * 1.8)
    w(F_DOUBT, A_CONTEMPLATE, 1.0 * t[G.OPENNESS])
    w(F_DOUBT, A_RITUAL, -0.8 * (1.0 - t[G.CREDULITY]))
    w(F_DOUBT, A_PREACH, -0.5)

    # السلطة
    w(F_RULED, A_SCHEME, 0.8 * t[G.DOMINANCE] * (0.3 + t[G.MACHIAVELLIAN]) * 1.7)
    w(F_RULED, A_SEIZE, 0.5 * t[G.DOMINANCE] * t[G.NARCISSISM] * 2.2)
    w(F_RULED, A_RITUAL, 0.3 * t[G.CREDULITY])
    w(F_POWERFUL, A_PREACH, 0.8 + 0.7 * t[G.MACHIAVELLIAN])
    w(F_POWERFUL, A_HOARD, 0.9 * (1.0 - t[G.HONESTY]))
    w(F_POWERFUL, A_ATTACK, 0.6 * t[G.CALLOUSNESS])
    w(F_POWERFUL, A_BUILD, 0.7 * t[G.NARCISSISM])   # الطاغية يبني ليُذكَر

    # رهبة الموت — إدارة الرعب: التشبّث بما يَعِد بالبقاء
    w(F_DREAD, A_RITUAL, 1.6 * (0.25 + t[G.CREDULITY]))
    w(F_DREAD, A_TEND, 0.8 * t[G.CARE])
    w(F_DREAD, A_COURT, 0.7 * t[G.LUST])          # النسل ردٌّ على الفناء
    w(F_DREAD, A_BUILD, 0.6 * t[G.NARCISSISM])    # وكذلك الحجر الذي يُذكَر
    w(F_DREAD, A_CONTEMPLATE, 0.7 * t[G.OPENNESS])
    w(F_DREAD, A_ATTACK, -0.8 * t[G.FEAR])

    # خوف العوز
    w(F_WANT, A_HOARD, 2.0 * (1.0 - t[G.HONESTY]) + 0.6)
    w(F_WANT, A_FORAGE, 1.3)
    w(F_WANT, A_FARM, 1.2)
    w(F_WANT, A_SCHEME, 0.8 * t[G.MACHIAVELLIAN])
    w(F_WANT, A_QUARREL, 0.6 * (1.0 - t[G.AGREEABLE]))
    w(F_WANT, A_WANDER, 0.5 + 0.4 * t[G.OPENNESS])

    # اليأس يشلّ
    w(F_DESPAIR, A_REST, 1.4)
    w(F_DESPAIR, A_CONTEMPLATE, 1.1 * (0.3 + t[G.OPENNESS]))
    w(F_DESPAIR, A_SOCIALIZE, 0.7 * t[G.EXTRAVERSION])
    for _a in (A_FORAGE, A_FARM, A_HERD, A_BUILD, A_CRAFT, A_TEACH, A_COURT):
        w(F_DESPAIR, _a, -1.0)

    # الميل الأساسي
    w(F_BIAS, A_FORAGE, 0.95)
    w(F_BIAS, A_FARM, 0.35)
    w(F_BIAS, A_HERD, 0.30)
    w(F_BIAS, A_ATTACK, -1.35)
    w(F_BIAS, A_SEIZE, -3.2)
    w(F_BIAS, A_QUARREL, -0.7)
    w(F_BIAS, A_SCHEME, -1.6)
    w(F_BIAS, A_PREACH, -1.4)
    w(F_BIAS, A_HOARD, -1.5)
    w(F_BIAS, A_RITUAL, -1.5)
    w(F_BIAS, A_WANDER, -0.9)
    w(F_BIAS, A_SOCIALIZE, 0.35 + 0.5 * t[G.EXTRAVERSION])
    w(F_BIAS, A_REST, 0.30)
    w(F_BIAS, A_COURT, -0.8)
    w(F_BIAS, A_LEARN, 0.25 + 0.4 * t[G.OPENNESS])
    return W


class Program:
    """كود الكائن: أوزان + حِكَم مؤلَّفة."""

    __slots__ = ("W", "maxims", "episodes", "rewrites", "authored",
                 "derived", "kept")

    def __init__(self, W, maxims=None):
        self.W = W
        self.maxims = maxims if maxims is not None else []
        self.episodes = []     # (سِمات، فعل، أثرُ ذاكرة)
        self.rewrites = 0      # كم مرة أعاد كتابة نفسه
        self.authored = 0      # كم حكمة ألّفها
        self.derived = 0       # كم قاعدة استنتجها ولم يعشها
        self.kept = 0          # كم نيّة أوفى بها

    def complexity(self):
        n = sum(1 for x in self.W if abs(x) > 0.25)
        return n + 6 * len(self.maxims)


# --------------------------------------------------------------- القرار
def decide(prog, f, rng, temperature, adult=True, blocked=None, intent=None):
    """
    f: قائمة كثيفة بطول NF.
    يعيد فعلًا واحدًا. القيد هنا مقصود: فعل واحد في المرة، مهما تزاحمت
    الدوافع — عنق الزجاجة الذي يجبر الكائن على ترتيب ذاته.
    """
    W = prog.W
    scores = W[F_BIAS * NA: F_BIAS * NA + NA][:]
    for fi in range(1, len(f)):          # ما بعد NF مفاهيمُ صنعها هو
        if (fi + 1) * NA > len(W):
            break
        v = f[fi]
        if v <= 0.001:
            continue
        off = fi * NA
        for a in range(NA):
            scores[a] += W[off + a] * v

    for m in prog.maxims:
        act = eval_expr(m.expr, f)
        if act > 0.05:
            scores[m.action] += m.weight * act

    if not adult:
        for a in ADULT_ONLY:
            scores[a] -= 6.0
    if blocked:
        for a in blocked:
            scores[a] -= blocked[a]
    if intent is not None:
        scores[intent[0]] += intent[1]   # النيّة تقاوم دوافع اللحظة

    mx = max(scores)
    inv = 1.0 / max(0.15, temperature)
    tot = 0.0
    ws = [0.0] * NA
    for a in range(NA):
        e = math.exp((scores[a] - mx) * inv)
        ws[a] = e
        tot += e
    r = rng.random() * tot
    acc = 0.0
    for a in range(NA):
        acc += ws[a]
        if r <= acc:
            return a
    return NA - 1


# ------------------------------------------------------ إعادة كتابة الذات
def reflect(agent, cfg, rng, year, ressentiment=0.0, high_acts=()):
    """
    التأمّل. الكائن يستعرض ما يتذكّره من نتائج أفعاله ويعدّل كوده.

    لاحظ من أين تأتي إشارة التعلّم: من `trace.val * trace.strength` —
    أي من الأثر الباقي في الذاكرة، بعد التلاشي والتشويه والاختلاق.
    إن كان الأثر ملفّقًا تعلّم الكائن منه كما يتعلّم من الحقيقة تمامًا،
    ولا سبيل عنده لمعرفة الفرق.
    """
    prog = agent.prog
    eps = prog.episodes
    if not eps:
        return 0

    live = [(f, a, tr) for (f, a, tr) in eps if tr is not None and tr.strength > 0.05]
    if not live:
        prog.episodes = []
        return 0

    vals = [tr.val * min(1.5, tr.strength) for (_, _, tr) in live]
    base = sum(vals) / len(vals)
    lr = cfg.learn_rate * (0.5 + agent.g.t[G.REASONING])
    W = prog.W
    touched = 0

    for (fs, a, tr), v in zip(live, vals):
        adv = v - base
        if abs(adv) < 0.02:
            continue
        step = lr * adv
        for fi, fv in fs:
            i = fi * NA + a
            W[i] += step * fv
            if W[i] > 6.0:
                W[i] = 6.0
            elif W[i] < -6.0:
                W[i] = -6.0
        touched += 1

    # تعديل بنيوي: فتح وصلة أو قطعها
    if rng.random() < cfg.rewrite_rate * (0.4 + agent.g.t[G.OPENNESS]):
        fi = rng.randrange(NF)
        a = rng.randrange(NA)
        i = fi * NA + a
        if abs(W[i]) > 0.3 and rng.random() < 0.45:
            W[i] = 0.0                       # قطعُ عادة
        else:
            W[i] += rng.gauss(0.0, 0.55)     # فتحُ ميلٍ جديد
        prog.rewrites += 1

    # تأليف حكمة: الطبقة التي يكتبها الكائن بلسانه
    if rng.random() < cfg.invent_rule_rate * (0.3 + agent.g.t[G.OPENNESS] + agent.g.t[G.REASONING]):
        m = compose_maxim(live, rng, agent.id, year, ressentiment, high_acts)
        if m is not None and len(prog.maxims) < 14:
            prog.maxims.append(m)
            prog.authored += 1

    # لا تُمسح الحوادث بعد التأمّل: تبقى سنوات، فيتآكل أثرها ويتشوّه،
    # ويعود الكائن يتعلّم من النسخة المتآكلة لا من الأصل.
    prog.episodes = [e for e in live[-16:]]
    return touched


def inherit(pa, pb, g, rng, cfg):
    """
    الابن يرث كودًا مخلوطًا من أبويه *بعد* ما تعلّماه، ممزوجًا بغرائزه هو.
    هذا افتراض لاماركي مقصود: الطلب كان أن يطوّر الكود نفسه عبر الأجيال،
    لا أن تعيد كل ولادة العدّاد إلى الصفر.
    """
    base = innate(g, rng)
    L = cfg.lamarck
    inv = 1.0 - L
    jit = _noise(rng, NF * NA, 0.03)
    W = [inv * b + L * 0.5 * (x + y) + j
         for b, x, y, j in zip(base, pa.W, pb.W, jit)]

    maxims = []
    for m in (pa.maxims + pb.maxims):
        if rng.random() < 0.35:
            maxims.append(mutate_maxim(m, rng, cfg.meme_drift))
        if len(maxims) >= 8:
            break
    return Program(W, maxims)


# ------------------------------------------------------------- بناء السِمات
def build_features(a, ctx):
    """يبني القائمة الكثيفة. ctx قاموس يجهّزه المحرّك مرة لكل قرية."""
    f = [0.0] * NF
    f[F_BIAS] = 1.0
    if a.hunger > 0.03:
        f[F_HUNGER] = min(1.0, a.hunger)
    if a.illness > 0.02:
        f[F_SICK] = min(1.0, a.illness)
    f[F_TIRED] = min(1.0, a.fatigue)
    af = a.af
    from .emotion import (P_RAGE, P_FEAR, P_GRIEF, P_LUST,
                          E_RESENT, E_HUMIL, E_AWE)
    if af.p[P_GRIEF] > 0.1:
        f[F_GRIEF] = min(1.0, af.p[P_GRIEF] * 0.6)
    if af.p[P_LUST] > 0.1:
        f[F_LUST] = min(1.0, af.p[P_LUST] * 0.6)
    if af.s[E_RESENT] > 0.1:
        f[F_GRUDGE] = min(1.0, af.s[E_RESENT] * 0.55)
    if af.s[E_HUMIL] > 0.1:
        f[F_HUMILIATED] = min(1.0, af.s[E_HUMIL] * 0.6)
    f[F_AWE] = min(1.0, af.s[E_AWE] * 0.45 + a.mem.awe() * 0.30)
    thr = ctx["threat"] + af.p[P_FEAR] * 0.35
    if thr > 0.02:
        f[F_THREAT] = min(1.0, thr)
    if a.bonds.close_count() == 0:
        f[F_LONELY] = 0.8
    elif a.bonds.close_count() < 2:
        f[F_LONELY] = 0.35
    f[F_CROWDED] = ctx["crowding"]
    f[F_SCARCITY] = ctx["scarcity"]
    f[F_SURPLUS] = ctx["surplus"]
    if a.age < 14:
        f[F_YOUNG] = 1.0 - a.age / 14.0
    if a.age > 42:
        f[F_OLD] = min(1.0, (a.age - 42) / 25.0)
    f[F_KIN_NEED] = a.kin_need
    # الفراغ: ما يتبقّى بعد سدّ الحاجات — شرط التأمّل
    press = max(f[F_HUNGER], f[F_SICK], f[F_TIRED], f[F_THREAT])
    f[F_LEISURE] = max(0.0, 1.0 - press) * ctx["provision"]
    f[F_RULED] = ctx["ruled"] if not a.is_ruler else 0.0
    f[F_POWERFUL] = a.power
    f[F_WRATH_NEAR] = a.wrath_expectation
    f[F_DOUBT] = a.doubt
    f[F_DREAD] = a.fear_death
    f[F_WANT] = a.fear_want
    f[F_DESPAIR] = min(1.0, a.despair)
    if a.fear_revolt > 0.2:
        f[F_THREAT] = min(1.0, f[F_THREAT] + 0.5 * a.fear_revolt)
    return f


def sparse(f):
    return [(i, v) for i, v in enumerate(f) if v > 0.02]
