"""
السلطة.

مساران للمكانة لا مسار واحد (Henrich & Gil-White):
  الهيبة — تُمنح طوعًا لمن ينفع ويعلّم ويُطعم.
  الهيمنة — تُنتزع بالبطش والاحتكار والتخويف.
كلاهما يوصل إلى الحكم، والفرق بينهما هو الفرق بين زعيمٍ وطاغية.

ومفارقة السلطة (Keltner): مجرّد الإمساك بالسلطة يزيح السلوك — يقلّ
التعاطف، وترتفع النرجسية المعبَّر عنها، ويقلّ الكفّ. فالطاغية في هذا
العالم يُصنَع ولا يُولد: يمكن لأنقى الأربعة والثلاثين أن يصير أسوأهم
بعد عشرين سنة على الكرسي.
"""

from . import genome as G
from .emotion import appraise, E_HUMIL


def prestige_gain(a, amount):
    a.prestige = min(12.0, a.prestige + amount)


def dominance_gain(a, amount):
    a.dominance = min(12.0, a.dominance + amount)


def legitimacy(st, ruler, doc, agents):
    """شرعية الحاكم: بركة الكهنة + الإطعام + الخوف."""
    if ruler is None:
        return 0.0
    divine = 0.6 if ruler.clergy else 0.0
    for m in st.members[:40]:
        a = agents.get(m)
        if a is not None and a.clergy and a.bonds.feel(ruler.id) > 0.3:
            divine += 0.25
            break
    provision = min(1.0, st.granary / max(1.0, 0.6 * st.pop()))
    fear = min(1.0, ruler.dominance / 8.0)
    return max(0.0, min(2.0, 0.55 * divine + 0.75 * provision + 0.45 * fear))


def choose_ruler(st, agents, cfg, rng, year):
    """
    من يحكم؟ من يجمع أعلى (مكانة × سند تحالفه).
    السند يقاس بمن يحبّه أو يخافه من أهل القرية.
    """
    best, bv = None, 0.0
    pool = [agents[m] for m in st.members if m in agents]
    adults = [a for a in pool if a.age >= cfg.adult_age]
    if len(adults) < 3:
        return None
    for a in adults:
        support = 0.0
        for b in adults:
            if b.id == a.id:
                continue
            f = b.bonds.feel(a.id)
            if f > 0.25:
                support += f
            fear = min(1.0, a.dominance / 6.0) * (0.3 + b.eg.t[G.FEAR])
            support += fear * 0.55
        v = (a.prestige + 1.3 * a.dominance) * (0.4 + support / max(1, len(adults)))
        v *= (0.7 + a.eg.t[G.DOMINANCE])
        v *= rng.gauss(1.0, 0.12)
        if v > bv:
            best, bv = a, v
    return best


def install(st, a, agents, year):
    old = agents.get(st.ruler)
    if old is not None and old is not a:
        old.is_ruler = False
        old.title = "المخلوع"
        appraise(old.af, old.eg, status_delta=-1.4, blame_other=0.8)
    st.ruler = a.id
    a.is_ruler = True
    a.rule_years = 0
    a.title = "الحاكم" if a.prestige >= a.dominance else "الطاغية"
    appraise(a.af, a.eg, status_delta=1.6, congruence=0.8)


def corrupt(a, cfg):
    """
    ما تفعله السلطة بمن يمسكها. الجينوم لا يتغيّر — المعبَّر عنه يتغيّر.
    وكودُه يتغيّر معه: يزداد ميله للبطش والاكتناز والخطابة، ويقلّ للمداواة.
    """
    k = cfg.power_corrupts
    a.apply_shift(G.NARCISSISM, k)
    a.apply_shift(G.CALLOUSNESS, k * 0.8)
    a.apply_shift(G.DOMINANCE, k * 0.7)
    a.apply_shift(G.AGREEABLE, -k * 0.9)
    a.apply_shift(G.HONESTY, -k * 0.7)
    a.apply_shift(G.CARE, -k * 0.5)

    from .mind import (NA, F_POWERFUL, A_ATTACK, A_HOARD, A_PREACH,
                       A_TEND, A_RECONCILE, A_BUILD)
    W = a.prog.W
    off = F_POWERFUL * NA
    for act, d in ((A_ATTACK, k * 2.2), (A_HOARD, k * 2.0), (A_PREACH, k * 1.6),
                   (A_BUILD, k * 1.4), (A_TEND, -k * 1.8), (A_RECONCILE, -k * 1.6)):
        i = off + act
        W[i] = max(-6.0, min(6.0, W[i] + d))


def tyranny_index(st, agents):
    r = agents.get(st.ruler)
    if r is None:
        return 0.0
    tot = r.prestige + r.dominance
    if tot < 0.1:
        return 0.0
    return r.dominance / tot


def grievance(st, agents, cfg):
    """الغبن المتراكم: جوع + جِزية + مهانة + ضغائن تجاه الحاكم."""
    r = agents.get(st.ruler)
    if r is None:
        return 0.0
    g = 0.0
    n = 0
    for m in st.members:
        a = agents.get(m)
        if a is None or a.id == r.id or a.age < cfg.adult_age:
            continue
        n += 1
        g += min(1.0, a.hunger) * 0.9
        g += a.bonds.resentment.get(r.id, 0.0) * 0.7
        g += a.af.s[E_HUMIL] * 0.35
        g += a.tribute * 0.25
    if n == 0:
        return 0.0
    return g / n


def attempt_revolt(st, agents, cfg, rng, year):
    """
    الثورة. تنجح إذا فاق الغبن × حجم التحالف قدرةَ الحاكم على القمع.
    تعيد (نجحت؟، القائد، عدد القتلى).
    """
    ruler = agents.get(st.ruler)
    if ruler is None:
        return None
    gr = grievance(st, agents, cfg)
    if gr < cfg.revolt_threshold:
        return None

    rebels = []
    for m in st.members:
        a = agents.get(m)
        if a is None or a.id == ruler.id or a.age < cfg.adult_age:
            continue
        drive = (a.bonds.resentment.get(ruler.id, 0.0) * 0.8 + a.hunger * 0.6 +
                 a.af.s[E_HUMIL] * 0.5 + a.eg.t[G.DOMINANCE] * 0.4 -
                 a.eg.t[G.FEAR] * 0.7 - a.faith * 0.35 * (1.0 if ruler.clergy else 0.4))
        if drive > 0.35:
            rebels.append((drive, a))
    if len(rebels) < 3:
        return None

    rebels.sort(key=lambda p: p[0], reverse=True)
    leader = rebels[0][1]
    force = sum(d * (0.4 + a.eg.t[G.VIGOR]) for d, a in rebels)
    guard = (1.5 + ruler.dominance) * (1.0 + 0.6 * legitimacy(st, ruler, st.doctrine, agents))
    guard += 0.05 * st.walls

    dead = []
    if force > guard * rng.gauss(1.0, 0.18):
        # سقط
        toll = max(1, int(len(rebels) * 0.12 * rng.random()))
        for _, a in rebels[-toll:]:
            dead.append(a)
        dead.append(ruler)
        install(st, leader, agents, year)
        st.unrest = max(0.0, st.unrest - 0.6)
        return (True, leader, dead)
    else:
        toll = max(1, int(len(rebels) * (0.25 + 0.35 * ruler.eg.t[G.CALLOUSNESS])))
        for _, a in rebels[:toll]:
            dead.append(a)
        ruler.kills += toll
        dominance_gain(ruler, 1.2)
        st.unrest = min(2.0, st.unrest + 0.35)
        for m in st.members:
            a = agents.get(m)
            if a is not None and a.id != ruler.id:
                appraise(a.af, a.eg, threat=0.7, blame_other=0.5, status_delta=-0.3)
                a.bonds.bump(a.bonds.resentment, ruler.id, 0.35)
        return (False, leader, dead)
