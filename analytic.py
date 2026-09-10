#!/usr/bin/env python
"""
قياس الآلية معزولةً عن البيئة.

القياس داخل المحاكاة ملوَّثٌ دائمًا: أي سببِ موتٍ تُزيله يرفع العدد،
فيعود الشحّ بما ذهب. ولذلك يُقاس هنا **الجسدُ وحده**: كائنٌ صناعي ثابت
الصفات، تغذيةٌ وزحامٌ وتقنيةٌ مثبّتة، ويُسأل: في أي سنةٍ يعبر الأذى
قدرةَ الإصلاح؟

فيُفصَل بذلك أثرُ الآلية عن أثر الإيكولوجيا. والفرقُ بين الرقمين هو
تعويض مالتوس مقاسًا لا مزعومًا.
"""
import sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

from village.config import Config
from village import causes as CA
from village import genome as G
from village.mind import A_FARM


class _Body:
    """جسدٌ صناعي: كل صفاته وسطٌ، وبيئته ثابتة."""
    def __init__(self, kids=3):
        self.g = type("g", (), {"t": [0.5] * G.NT})()
        self.eg = self.g
        self.age = 0
        self.hunger = 0.10
        self.illness = 0.04
        self.pregnant = 0
        self.sex = 0
        self.children = [0] * kids
        self.last_action = A_FARM
        self.damage = 0.0
        self.hits = 0


def age_at_failure(cfg, pop=300, med=0.0, kids=3, cap=120):
    import random
    rng = random.Random(4242)
    b = _Body(kids)
    know = {"fire", "cord", "stone", "farming", "pottery", "granary", "copper"}
    reg = type("r", (), {})()
    ctx = dict(pop=pop, provision=0.9)
    for y in range(1, cap):
        b.age = y
        CA.wear(b, ctx, know, reg, cfg, rng, med)
        if b.damage > 1.0:
            return y
    return cap


def main():
    base = Config()
    print("عمر انهيار الجسد الصناعي — البيئة مثبّتة، الفارق آليةٌ واحدة\n")
    b0 = age_at_failure(base)
    print(f"{'الحالة':<26}{'عمر الانهيار':>14}{'الفارق':>9}")
    print("-" * 50)
    print(f"{'— الأصل —':<26}{b0:>14}{'':>9}")
    for k, lab in (("cause_water", "بلا أذى الماء"),
                   ("cause_toil", "بلا إنهاك الكدح"),
                   ("cause_soma", "بلا مقايضة النسل")):
        cfg = Config(); setattr(cfg, k, False)
        v = age_at_failure(cfg)
        print(f"{lab:<26}{v:>14}{v - b0:>+9}")
    print()
    print("وأثر ما ليس آليةً في الجسد بل في العالم:")
    for lab, kw in (("زحام 1200 بدل 300", dict(pop=1200)),
                    ("طبٌّ (إصلاح +25٪)", dict(med=0.25)),
                    ("بلا ولد", dict(kids=0)),
                    ("ثمانية أولاد", dict(kids=8))):
        v = age_at_failure(base, **kw)
        print(f"  {lab:<24}{v:>12}{v - b0:>+9}")


if __name__ == "__main__":
    main()
