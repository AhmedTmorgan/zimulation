"""
الجينوم.

كل كائن يحمل *كل* الصفات البشرية — الرحمة والقسوة والغرور والتواضع.
الفرق بينهم في المعايرة لا في الوجود. لا يوجد كائن "شرير" وآخر "طيّب":
يوجد كائن عتبة غضبه واطية وآخر عالية، وموقف يفتح الباب أو يقفله.

الأساس: HEXACO (ستّة عوامل، بينها الأمانة-التواضع التي يقيس قطبها المنخفض
الاستحقاق والاستغلال)، والثالوث المظلم (نرجسية/ميكيافيلية/قسوة)،
والتوجّه للهيمنة الاجتماعية، وأنظمة بانكسيب الوجدانية الأولية السبعة.
"""

TRAITS = (
    # HEXACO
    "openness", "conscientiousness", "extraversion", "agreeableness",
    "neuroticism", "honesty",
    # الثالوث المظلم
    "narcissism", "machiavellianism", "callousness",
    # التوجّه للهيمنة الاجتماعية
    "dominance",
    # أنظمة بانكسيب الأولية — قابلية التنشيط لا الحالة
    "seeking", "rage", "fear", "lust", "care", "grief", "play",
    # جسدي/معرفي
    "vigor", "fertility", "longevity", "recall", "reasoning", "credulity",
)
NT = len(TRAITS)
(
    OPENNESS, CONSCIENT, EXTRAVERSION, AGREEABLE, NEUROTIC, HONESTY,
    NARCISSISM, MACHIAVELLIAN, CALLOUSNESS,
    DOMINANCE,
    SEEKING, RAGE, FEAR, LUST, CARE, GRIEF, PLAY,
    VIGOR, FERTILITY, LONGEVITY, RECALL, REASONING, CREDULITY,
) = range(NT)

AR = {
    "openness": "الانفتاح", "conscientiousness": "الضمير", "extraversion": "الانبساط",
    "agreeableness": "الوداعة", "neuroticism": "العصابية", "honesty": "الأمانة-التواضع",
    "narcissism": "النرجسية", "machiavellianism": "الميكيافيلية", "callousness": "القسوة",
    "dominance": "نزعة الهيمنة",
    "seeking": "السعي", "rage": "الغيظ", "fear": "الخوف", "lust": "الشهوة",
    "care": "الرعاية", "grief": "الفَقْد", "play": "اللعب",
    "vigor": "العافية", "fertility": "الخصوبة", "longevity": "طول العمر",
    "recall": "متانة الذاكرة", "reasoning": "الاستدلال", "credulity": "التصديق",
}

# قابلية التوريث التقريبية من أدبيات الوراثة السلوكية.
# الباقي بيئة: متوسط القرية + تشويش — فالثقافة تعيد تشكيل توزيع الطباع.
H2 = [0.0] * NT
for _i, _h in (
    (OPENNESS, 0.55), (CONSCIENT, 0.45), (EXTRAVERSION, 0.52), (AGREEABLE, 0.42),
    (NEUROTIC, 0.48), (HONESTY, 0.45),
    (NARCISSISM, 0.50), (MACHIAVELLIAN, 0.35), (CALLOUSNESS, 0.45),
    (DOMINANCE, 0.35),
    (SEEKING, 0.45), (RAGE, 0.45), (FEAR, 0.45), (LUST, 0.40),
    (CARE, 0.40), (GRIEF, 0.40), (PLAY, 0.40),
    (VIGOR, 0.60), (FERTILITY, 0.35), (LONGEVITY, 0.28),
    (RECALL, 0.50), (REASONING, 0.55), (CREDULITY, 0.35),
):
    H2[_i] = _h

N_ANTIGEN = 32


def _clip(v):
    return 0.02 if v < 0.02 else (0.98 if v > 0.98 else v)


class Genome:
    __slots__ = ("t", "antigens", "generation")

    def __init__(self, t, antigens, generation=0):
        self.t = t
        self.antigens = antigens
        self.generation = generation

    @classmethod
    def seedling(cls, rng, bias=None):
        t = [_clip(rng.gauss(0.5, 0.16)) for _ in range(NT)]
        if bias:
            for i, v in bias.items():
                t[i] = _clip(v)
        return cls(t, frozenset(rng.sample(range(N_ANTIGEN), 3)), 0)

    @classmethod
    def conceive(cls, a, b, rng, sigma, env_mean=None):
        """
        نموذج الوراثة المزدوجة: h² من متوسط الأبوين، والباقي من البيئة
        (متوسط القرية) زائد تشويش فردي. يعني القرية تصنع طباع أبنائها جزئيًا.
        """
        t = []
        for i in range(NT):
            mid = 0.5 * (a.t[i] + b.t[i])
            h = H2[i]
            shared = env_mean[i] if env_mean else 0.5

            # البيئة **غير المشتركة**: لكل مولودٍ نصيبُه هو، لا متوسّطُ قريته.
            #
            # كان الجزء غير الموروث يُسحب إلى متوسّطٍ واحدٍ للجميع، فينهار
            # تباين الطباع إلى النصف في خمسين سنة ولا يعود. وذلك خطأ في
            # وراثة السلوك: أكثرُ ما لا يُورَّث ليس مشتركًا بين الإخوة بل
            # خاصًّا بكل واحد (Plomin & Daniels 1987 — لماذا يختلف أبناء
            # البيت الواحد؟). فبغير هذا التباين لا يبقى في القوم عقلٌ
            # نادر ولا شكٌّ نادر ولا شيءٌ نادر أصلًا.
            env = 0.55 * shared + 0.45 * 0.5 + rng.gauss(0.0, 0.155)
            v = h * mid + (1.0 - h) * env
            v += rng.gauss(0.0, sigma * (1.0 + (1.0 - h)))
            t.append(_clip(v))
        pool = list(a.antigens | b.antigens)
        ant = set(rng.sample(pool, min(3, len(pool)))) if pool else set()
        if rng.random() < 0.09:
            ant.add(rng.randrange(N_ANTIGEN))
        return cls(t, frozenset(ant), max(a.generation, b.generation) + 1)

    # مركّبات مشتقّة يستخدمها بقية النظام -----------------------------
    def dark(self):
        return (self.t[NARCISSISM] + self.t[MACHIAVELLIAN] + self.t[CALLOUSNESS]) / 3.0

    def warmth(self):
        return (self.t[AGREEABLE] + self.t[CARE] + self.t[HONESTY]) / 3.0

    def distance(self, other):
        return sum(abs(x - y) for x, y in zip(self.t, other.t)) / NT
