"""
الوجدان.

طبقتان:
  (١) الأنظمة الأولية عند بانكسيب — سبعة، تنشط سريعًا وتخمد سريعًا،
      وقابلية تنشيط كل واحد منها صفة موروثة.
  (٢) العواطف الاجتماعية العليا — تُشتقّ بالتقييم (OCC): من المسؤول؟
      هل انتُهك عُرف؟ ماذا حدث لمكانتي؟

والمزاج دائرة راسل: قيمة (سار/مؤلم) × استثارة. بطيء، ويتلوّن بما يتذكّره
الكائن لا بما جرى له.
"""

from . import genome as G

PRIMARY = ("seeking", "rage", "fear", "lust", "care", "grief", "play")
NP = 7
P_SEEK, P_RAGE, P_FEAR, P_LUST, P_CARE, P_GRIEF, P_PLAY = range(NP)
AR_PRIMARY = {
    "seeking": "السعي", "rage": "الغيظ", "fear": "الخوف", "lust": "الشهوة",
    "care": "الرعاية", "grief": "الفَقْد", "play": "اللعب",
}

SOCIAL = ("pride", "shame", "envy", "gratitude", "resentment",
          "contempt", "guilt", "awe", "humiliation")
NS = 9
E_PRIDE, E_SHAME, E_ENVY, E_GRATITUDE, E_RESENT, E_CONTEMPT, E_GUILT, E_AWE, E_HUMIL = range(NS)
AR_SOCIAL = {
    "pride": "الكِبر", "shame": "الخجل", "envy": "الحسد", "gratitude": "الامتنان",
    "resentment": "الضغينة", "contempt": "الاحتقار", "guilt": "الذنب",
    "awe": "الرهبة", "humiliation": "المهانة",
}

_DECAY_P = 0.55   # الأنظمة الأولية تخمد بسرعة
_DECAY_S = 0.82   # الاجتماعية تدوم


class Affect:
    __slots__ = ("p", "s", "valence", "arousal", "mood")

    def __init__(self):
        self.p = [0.0] * NP
        self.s = [0.0] * NS
        self.valence = 0.0
        self.arousal = 0.2
        self.mood = 0.0        # مزاج بطيء

    def fire(self, idx, amount, gain=1.0):
        v = self.p[idx] + amount * gain
        self.p[idx] = 0.0 if v < 0 else (2.5 if v > 2.5 else v)

    def social(self, idx, amount):
        v = self.s[idx] + amount
        self.s[idx] = 0.0 if v < 0 else (2.5 if v > 2.5 else v)

    def settle(self, g):
        """خمود + إعادة حساب المزاج."""
        for i in range(NP):
            self.p[i] *= _DECAY_P
        for i in range(NS):
            self.s[i] *= _DECAY_S
        pos = self.p[P_SEEK] + self.p[P_CARE] + self.p[P_PLAY] + self.s[E_PRIDE] + self.s[E_GRATITUDE] + self.s[E_AWE]
        neg = self.p[P_RAGE] + self.p[P_FEAR] + self.p[P_GRIEF] + self.s[E_SHAME] + self.s[E_RESENT] + self.s[E_HUMIL] + self.s[E_ENVY]
        self.valence = max(-1.0, min(1.0, 0.30 * (pos - neg)))
        self.arousal = max(0.0, min(1.0, 0.22 * (pos + neg)))
        # العصابية تبطّئ التعافي من المزاج السيّئ
        pull = 0.14 * (1.0 - 0.5 * g.t[G.NEUROTIC]) if self.valence > self.mood else 0.14
        self.mood += pull * (self.valence - self.mood)

    def dominant(self):
        bi, bv = -1, 0.28
        for i in range(NP):
            if self.p[i] > bv:
                bi, bv = i, self.p[i]
        best = ("primary", bi, bv) if bi >= 0 else None
        bi2, bv2 = -1, 0.28
        for i in range(NS):
            if self.s[i] > bv2:
                bi2, bv2 = i, self.s[i]
        if bi2 >= 0 and (best is None or bv2 > bv):
            return ("social", bi2, bv2)
        return best

    def label(self):
        d = self.dominant()
        if d is None:
            return "هادئ"
        kind, i, _ = d
        return AR_PRIMARY[PRIMARY[i]] if kind == "primary" else AR_SOCIAL[SOCIAL[i]]


# ----------------------------------------------------------------- التقييم
def appraise(af, g, *, congruence=0.0, blame_other=0.0, blame_self=0.0,
             norm_violation=0.0, status_delta=0.0, other_gain=0.0,
             threat=0.0, loss=0.0, novelty=0.0, tenderness=0.0, allure=0.0):
    """
    حدث → مركّبات تقييم → تنشيط عاطفي.
    كل مسار مضروب في قابلية التنشيط الموروثة، فنفس الحدث يولّد عند اثنين
    شيئين مختلفين تمامًا.
    """
    t = g.t
    if congruence > 0:
        af.fire(P_SEEK, congruence * 0.9, 0.6 + t[G.SEEKING])
        af.fire(P_PLAY, congruence * 0.4, 0.4 + t[G.PLAY])
    if threat > 0:
        af.fire(P_FEAR, threat, 0.5 + t[G.FEAR] * 1.4)
    if loss > 0:
        af.fire(P_GRIEF, loss, 0.5 + t[G.GRIEF] * 1.4)
    if allure > 0:
        af.fire(P_LUST, allure, 0.4 + t[G.LUST] * 1.5)
    if tenderness > 0:
        af.fire(P_CARE, tenderness, 0.4 + t[G.CARE] * 1.5)
    if novelty > 0:
        af.fire(P_SEEK, novelty * 0.7, 0.4 + t[G.OPENNESS])

    # الغيظ: إسناد اللوم للغير + انتهاك عُرف — تُضخّمه النرجسية
    if blame_other > 0:
        amp = 0.45 + t[G.RAGE] * 1.3 + t[G.NARCISSISM] * 0.5
        af.fire(P_RAGE, (blame_other + 0.6 * norm_violation), amp)
        af.social(E_RESENT, blame_other * (0.5 + 0.8 * (1.0 - t[G.AGREEABLE])))
        af.social(E_CONTEMPT, blame_other * 0.5 * (0.3 + t[G.CALLOUSNESS]))

    if blame_self > 0:
        af.social(E_GUILT, blame_self * (0.25 + t[G.HONESTY] + t[G.CARE]) * 0.6)
        af.social(E_SHAME, blame_self * (0.3 + t[G.NEUROTIC]) * 0.7)

    # المكانة: الكِبر مقابل المهانة. النرجسية تضاعف الاتجاهين.
    if status_delta > 0:
        af.social(E_PRIDE, status_delta * (0.4 + 1.2 * t[G.NARCISSISM]))
    elif status_delta < 0:
        h = -status_delta * (0.4 + 1.4 * t[G.NARCISSISM])
        af.social(E_HUMIL, h)
        # المهانة تتحوّل غيظًا — وهي بذرة الثأر
        af.fire(P_RAGE, h * 0.75, 0.4 + t[G.RAGE])

    if other_gain > 0:
        af.social(E_ENVY, other_gain * (0.25 + t[G.NARCISSISM] * 0.9 + (1.0 - t[G.HONESTY]) * 0.5))
    elif other_gain < 0:
        af.social(E_GRATITUDE, -other_gain * (0.3 + t[G.AGREEABLE] + t[G.HONESTY]) * 0.5)


def awe_strike(af, g, intensity):
    """الرهبة: ما يفتح باب العقيدة."""
    af.social(E_AWE, intensity * (0.35 + g.t[G.CREDULITY] * 1.2 + g.t[G.OPENNESS] * 0.4))
    af.fire(P_FEAR, intensity * 0.5, 0.4 + g.t[G.FEAR])
