"""
النفس: ما يخافه الإنسان، وما يدفنه، وما قد يُنهيه.

ثلاثة مخاوف مسمّاة، لكلٍّ منها مصدرٌ في الواقع وأثرٌ في السلوك:
  الموت   — يشتدّ برؤية الموتى وبالسقم وبالسنّ وباقتراب الغضب.
  الفقر   — يشتدّ بالجوع وبخلوّ المخزن وبثقل الجِزية.
  الثورة  — يشتدّ عند الحاكم بالسخط، وعند الجميع بعد كل انتفاضة.

ونظرية إدارة الرعب (Terror Management): الوعي بالموت يدفع إلى التشبّث
بما يمنح البقاء رمزيًا — فالخوف من الفناء يرفع التديّن ويقوّي التعصّب
للجماعة. وهذا ما يجعل الغضب الدوري يصنع دينًا لا يهدمه.

والكبت (فرويد): الأثر الذي يفوق احتماله لا يُمحى — يُدفن. يغيب عن
الاسترجاع، ويبقى يوجّه السلوك من حيث لا يُرى، ويعود في المنام.

والانتحار على تصنيف دوركهايم في «الانتحار»: دالّةٌ في الاندماج
الاجتماعي والضبط المعياري، طرفاهما قاتلان كوسطهما نافع.
"""

from . import genome as G
from .emotion import P_FEAR, P_GRIEF, E_HUMIL, E_AWE, E_SHAME, E_GUILT

# أنواع دوركهايم الأربعة
EGOISTIC, ANOMIC, ALTRUISTIC, FATALISTIC = range(4)
AR_SUICIDE = {
    EGOISTIC: "انفراد",      # اندماج أقلّ من اللازم
    ANOMIC: "انفلات",        # ضبط أقلّ من اللازم — انهيار المعنى
    ALTRUISTIC: "فداء",      # اندماج أكثر من اللازم
    FATALISTIC: "قهر",       # ضبط أكثر من اللازم
}


# ------------------------------------------------------------- المخاوف
def update_fears(a, st, ctx, doc, rng):
    """يُستدعى مرة كل سنة قبل القرار."""
    t = a.eg.t
    base = 0.25 + 0.9 * t[G.FEAR]

    # الموت: ما يراه ويحمله في جسده وما يتوقّعه
    seen = min(1.0, a.mem.felt(2) * 0.05)          # آثار الموت في ذاكرته
    body = 0.6 * a.illness + 0.5 * max(0.0, (a.age - 35) / 30.0)
    a.fear_death = min(1.0, base * (0.35 * seen + body + 0.45 * a.wrath_expectation
                                    + 0.30 * a.af.p[P_GRIEF]))

    # الفقر: الجوع وخلوّ المخزن وثقل ما يُؤخذ منه
    a.fear_want = min(1.0, base * (0.9 * min(1.0, a.hunger) + 0.7 * ctx["scarcity"]
                                   + 0.5 * min(1.0, a.tribute)))

    # الثورة: يخافها الحاكم من رعيّته، ويخافها الرعيّة من الفوضى
    unrest = min(1.0, st.unrest)
    if a.is_ruler:
        a.fear_revolt = min(1.0, (0.4 + t[G.NEUROTIC]) * (0.5 * unrest + 0.5 * ctx["scarcity"]))
    else:
        a.fear_revolt = min(1.0, base * 0.55 * unrest)

    # إدارة الرعب: من اشتدّ خوفه من الفناء تشبّث بما يَعِد بالبقاء
    if a.fear_death > 0.45 and not a.heretic:
        grip = 0.05 * (a.fear_death - 0.45) * (0.4 + t[G.CREDULITY])
        a.faith = min(1.0, a.faith + grip)
        if doc is not None:
            for k in doc.tenets:
                a.conv[k] = min(1.6, a.conv.get(k, 0.0) + grip * 0.8)
        a.af.social(E_AWE, grip * 2.0)


# ------------------------------------------------------------- الكبت
def repress(a, rng):
    """
    ما يفوق الاحتمال يُدفن ولا يُمحى: يغيب عن الاسترجاع ويبقى فاعلًا.
    شرطه ألمٌ شديد يقترن بخجلٍ أو ذنب — لا مجرّد ألم.
    """
    load = a.af.s[E_SHAME] + a.af.s[E_GUILT] + a.af.s[E_HUMIL]
    if load < 0.9:
        return None
    cand = [t for t in a.mem.traces if t.val < -0.55 and not t.repressed]
    if not cand:
        return None
    t = max(cand, key=lambda t: t.strength * -t.val)
    if rng.random() > 0.35 * (0.4 + a.eg.t[G.NEUROTIC]) * min(1.0, load / 2.0):
        return None
    t.repressed = True
    t.buried = t.strength
    t.strength *= 0.12          # يغيب عن الاسترجاع، ولا يُحذف
    return t


def return_of_repressed(a, rng, year):
    """
    المدفون يعود: في المنام، أو تحت ضغطٍ يشبه ما دُفن من أجله.
    """
    hidden = [t for t in a.mem.traces if t.repressed]
    if not hidden:
        return None
    stress = a.fear_death + a.fear_want + a.af.p[P_FEAR] * 0.5
    p = 0.04 + 0.10 * min(1.0, stress)
    if rng.random() > p:
        return None
    t = rng.choice(hidden)
    t.repressed = False
    t.strength = min(2.2, t.buried * 1.15)      # يعود أشدّ مما دُفن
    return t


def hidden_pull(a):
    """
    أثر المدفون على السلوك وهو مدفون: انقباضٌ عامّ لا يعرف صاحبه سببه.
    """
    s = 0.0
    for t in a.mem.traces:
        if t.repressed:
            s += t.buried * -t.val
    return min(1.0, s * 0.22)


# ------------------------------------------------------------- اليأس
def integration(a, agents):
    """الاندماج الاجتماعي: كم رابطًا حيًّا يشدّه إلى الناس."""
    s = 0.0
    for k, v in a.bonds.affection.items():
        if k in agents and v > 0.3:
            s += min(1.0, v)
    s += 0.6 * sum(1 for k in a.bonds.kin if k in agents)
    if a.bonds.partner in agents:
        s += 1.4
    s += 0.5 * len([c for c in a.children if c in agents])
    return min(3.0, s * 0.42)


def regulation(a, st, doc, agents):
    """الضبط المعياري: كم من القواعد يحكم حياته — من العقيدة ومن السلطة."""
    r = 0.0
    if doc is not None:
        r += 0.5 * sum(a.conv.get(k, 0.0) for k in doc.tenets) / max(1, len(doc.tenets))
        r += 0.35 * min(1.0, doc.complexity / 12.0)
    ruler = agents.get(st.ruler)
    if ruler is not None and not a.is_ruler:
        r += 0.55 * min(1.0, ruler.dominance / 6.0)
        r += 0.35 * min(1.0, a.tribute)
    return min(3.0, r)


def despair(a, st, doc, agents, cfg):
    """
    دالّة اليأس على منطق دوركهايم: طرفا الاندماج قاتلان، وطرفا الضبط كذلك.
    تعيد (الشدّة، النوع) أو (0، None).
    """
    I = integration(a, agents)
    R = regulation(a, st, doc, agents)
    t = a.eg.t
    frail = (0.25 + t[G.NEUROTIC] * 1.1) * (1.3 - t[G.EXTRAVERSION] * 0.5)
    pain = (a.af.p[P_GRIEF] * 0.55 + a.af.s[E_HUMIL] * 0.35
            + hidden_pull(a) * 0.6 + min(1.0, a.hunger) * 0.3
            + a.fear_want * 0.25)

    scores = []
    if I < 0.75:                              # انفراد
        scores.append(((0.75 - I) * 1.5 * frail + pain * 0.5, EGOISTIC))
    if I > 2.35 and a.faith > 0.75:           # فداء
        scores.append(((I - 2.35) * 0.9 * a.faith, ALTRUISTIC))
    if R < 0.45:                              # انفلات — انهيار المعنى
        anom = (0.45 - R) * 1.8 * frail
        if a.heretic:
            anom *= 1.6                       # من رأى أن لا عقاب ولا موعد
        scores.append((anom + pain * 0.6, ANOMIC))
    if R > 2.2:                               # قهر
        scores.append(((R - 2.2) * 1.3 * frail + pain * 0.7, FATALISTIC))

    if not scores:
        return 0.0, None
    v, kind = max(scores)
    # ما يمسك المرء: ولدٌ يحتاجه، وأملٌ في القادم
    hold = 0.55 * len([c for c in a.children if c in agents]) + 0.4 * t[G.SEEKING]
    return max(0.0, v - hold), kind


def absurd_response(a, rng):
    """
    من عرف أن الغضب موعدٌ لا عقاب، ثم بقي الموت على حاله: ثلاثة أبواب
    (كامو). ليس هذا نصًّا يُقتبَس، بل ثلاثة مسارات يرجّح بينها طبعُه.
    """
    t = a.eg.t
    w_leap = (0.3 + t[G.CREDULITY] * 1.6) * (0.4 + a.fear_death)
    w_end = (0.15 + t[G.NEUROTIC] * 1.2) * (0.3 + a.af.p[P_GRIEF])
    w_revolt = (0.35 + t[G.SEEKING] + t[G.REASONING] * 0.8) * (1.2 - t[G.NEUROTIC] * 0.4)
    tot = w_leap + w_end + w_revolt
    r = rng.random() * tot
    if r < w_leap:
        return "leap"        # قفزة إيمانية رغم الدليل
    if r < w_leap + w_end:
        return "end"
    return "revolt"          # يكمل وهو عارف
