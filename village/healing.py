"""
المداواة — وهي **بحثٌ في الظلام**، لا تطبيقُ معرفةٍ أعطيناها لهم.

في هذا العالم دواءٌ لأكثر الأدواء. ونحن نعرفه ولا نقوله. وهم يبدأون من
لا شيء: رجلٌ يرى قريبَه يذوي، فيمدّ يده إلى أوّل نبتةٍ حوله ويسقيه.

## لماذا يصعب هذا عليهم إلى هذا الحدّ

أربع آفاتٍ تعترض كلَّ من يجرّب، وكلُّها قائمة في هذا الكود لا في كلامي:

**١. الشفاء التلقائي.** أكثرُ الأدواء تنقضي من نفسها. فمن سقى مريضًا
ورقةً ثم برئ، رأى بعينه أن الورقة شفته. وهذا أعظم مصدرٍ للطبّ الكاذب
في تاريخ البشر، وهو هنا يعمل بلا استثناء.

**٢. الأعراض تخدع.** الكائن لا يرى الداء، يرى الحُمّى والوهن. وداءان
مختلفان في الآليّة يُعطيان الحُمّى نفسها، فينفع الدواءُ في أحدهما ولا
ينفع في الآخر، فيخرج المجرِّب بأن «الدواء ينفع أحيانًا».

**٣. المقدار.** النبتة النافعة تقتل بضِعف مقدارها. فمن نفعته مرّةً ثم
قتلت مريضَه، ظنّ أنها خانته.

**٤. أدواءٌ لا دواء لها.** ستٌّ وعشرون من مئة لا تُردّ بنبات. ومن جرّب
عليها ألف نبتةٍ خرج بألف خيبة، ولا شيء في الدنيا يخبره أنه يطلب
المستحيل.

## ما نحفظه لهم

`Remedy` — ما يتذكّره الرجل: نبتةٌ، وأعراضٌ رآها، وما جرى بعدها. هذا كلّ
ما عنده. ولا يقرأ من `Plant` إلا اسمَها وموضعها، ولا من `Malady` شيئًا
البتّة. ويحرس ذلك `test_healer_cannot_read_the_cure`.
"""

from . import genome as G
from .flora import PREPS, outcome

#: كم وصفةً يحفظ الرجل الواحد.
MAX_REMEDIES = 14


class Remedy:
    """
    ما يتذكّره المداوي عن نبتة: على أيّ حالٍ جرّبها، وكم مرّةً نفعت.

    ولاحظ أنه **لا يحفظ الداء** — يحفظ العرَض الذي رآه. وهذا هو الفرق
    بين ما نعرفه نحن وما يعرفونه هم.
    """

    __slots__ = ("plant", "sign", "prep", "dose", "good", "bad", "dead",
                 "born", "taught", "src")

    def __init__(self, plant, sign, prep, dose, year, src="جرّبها بنفسه"):
        self.plant = plant        # رقم النبتة
        self.sign = sign          # العرَض الأظهر حين جرّب
        self.prep = prep
        self.dose = dose
        self.good = 0
        self.bad = 0
        self.dead = 0
        self.born = year
        self.taught = 0
        self.src = src

    def trust(self):
        """ثقتُه فيها: ما رآه من نفعٍ مقابل ما رآه من ضرّ."""
        n = self.good + self.bad + self.dead
        if n == 0:
            return 0.30
        return (self.good - self.bad - 2.0 * self.dead + 0.5) / (n + 1.0)

    def label(self, plants):
        return f"{plants[self.plant].name} ({self.prep}، {self.dose:.1f})"


def top_sign(signs, names):
    """أظهرُ ما على المريض. وهو كلُّ ما يملكه المداوي ليصنّف به."""
    best, bv = -1, 0.22
    for i, v in enumerate(signs):
        if v > bv:
            best, bv = i, v
    return best


def pick(healer, sign, rng):
    """
    ماذا يعطي؟ ما جرّبه على هذا العرَض ووثق به، أو شيئًا جديدًا.

    ومن كان أقلَّ استدلالًا لزم ما ورثه، ومن كان أكثرَ جرّب ما لم يُجرَّب
    — وهذا هو الفرق بين ناقلٍ للطبّ وباحثٍ فيه، وكلاهما يقع هنا.
    """
    explore = 0.10 + 0.35 * healer.eg.t[G.OPENNESS]
    fit = [r for r in healer.remedies if r.sign == sign]
    if fit:
        fit.sort(key=lambda r: r.trust(), reverse=True)
        if fit[0].trust() > 0.35 and rng.random() > explore:
            return fit[0], False

    # **وإن لم يكن عنده لهذا العرَض شيء، مدّ يده إلى ما يثق به على كل حال.**
    #
    # كان لا يستعمل إلا ما طابق العرَض، والأعراض عشرة والوصفات أربع عشرة —
    # فلا يكاد يطابق شيء، فيخترع في كل مرّة وصفةً جديدة ولا يُعيد. ولذلك
    # جُرّبت تسعٌ وثمانون في المئة من وصفاتهم **مرّةً واحدة**، ولا يتعلّم
    # من جرّب مرّةً واحدة.
    #
    # والناس تفعل غير ذلك: من وثق بعشبةٍ سقاها لكل علّة — وهو خطأٌ في
    # التخصيص، لكنه يُكثر التجربة فيُصفّي الظنّ. فالعمومُ الخاطئ طريقٌ
    # إلى الصواب، وهذا من مفارقات الطبّ.
    if healer.remedies and rng.random() > explore * 0.7:
        best = max(healer.remedies, key=lambda r: r.trust())
        if best.trust() > 0.25:
            return best, False
    return None, True


def try_on(healer, patient, plant_id, prep, dose, mals, plants, rng, year):
    """
    يُعطى الدواء ويقع أثرُه. **هنا وحدها تُقرأ حقيقةُ النبات** — ولا
    يعود منها إلى عقل أحدٍ إلا ما ظهر على المريض.

    يعيد (نقص السقم، ما زيد من الأذى).
    """
    p = plants[plant_id]
    heal_tot = harm_tot = 0.0
    body = max(0.05, patient.health)
    for k, (mid, left, given) in enumerate(patient.sick):
        h, x = outcome(p, dose, prep, mals[mid], body)
        heal_tot += h
        harm_tot += x
        patient.sick[k] = (mid, max(0.0, left - h * 0.9), given + dose)
    if not patient.sick:
        # دواءٌ لغير داء: لا نفع فيه، والسُّمّ يعمل على كل حال
        _, x = outcome(p, dose, prep, _NOTHING, body)
        harm_tot += x
    p.tried += 1
    patient.health = max(0.0, patient.health - harm_tot * 0.55)
    patient.damage = max(0.0, patient.damage + harm_tot * 0.35)
    return heal_tot, harm_tot


class _Nothing:
    """داءٌ لا آليّة له — لقياس ضرر الدواء على من لا داء به."""
    mech = [0.0] * 8
    stubborn = 0.0


_NOTHING = _Nothing()


def learn(healer, rem, before, after, died, rng, rigour=False):
    """
    ما يستخلصه بعد أن يرى. **وهو لا يرى الحقيقة، يرى الفرق.**

    وقد يبرأ المريض لأن أجل الداء انقضى فيُحسب للدواء، وقد يموت وهو على
    الدواء النافع فيُحسب عليه. ولا نصحّح شيئًا من ذلك.
    """
    if died:
        rem.dead += 1
    elif after < before - 0.06:
        rem.good += 1
    elif after > before + 0.06:
        rem.bad += 1
    else:
        # **لا فرقَ يُذكر — وهذه أكثرُ الحالات وقوعًا، فأكثرُ النبات خامل.**
        #
        # وكان لا يُسجَّل منها شيء في أكثر من نصفها، فتبقى الوصفة على
        # ظنّها الأوّل أبدًا مهما جُرّبت: تسعٌ وثمانون في المئة من
        # وصفاتهم لم يُقيَّد لها أثرٌ واحد. والنتيجةُ الفارغة **خبرٌ
        # أيضًا**، ومن لم يقيّدها لم يتعلّم شيئًا أبدًا.
        #
        # والميل إلى التصديق باقٍ: يعدّها نجاحًا أكثر ممّا يعدّها فشلًا.
        # وميلُ التصديق يُضعفه المنهج: من أحصى ما لم ينفع رأى الحقّ
        p_yes = 0.12 if rigour else 0.45
        if rng.random() < p_yes:
            rem.good += 1
        else:
            rem.bad += 1
    return rem


def remember(healer, rem):
    """يحفظ الوصفة، وإن امتلأ صدرُه أسقط أضعفَ ما عنده ثقةً."""
    healer.remedies.append(rem)
    if len(healer.remedies) > MAX_REMEDIES:
        healer.remedies.sort(key=lambda r: r.trust())
        del healer.remedies[0]


def teach(giver, taker, rng):
    """الوصفة تُلقَّن كما تُلقَّن الحكمة — وتُنقل بثقة المعلّم لا بصدقها."""
    if not giver.remedies or len(taker.remedies) >= MAX_REMEDIES:
        return None
    src = max(giver.remedies, key=lambda r: r.trust())
    if any(r.plant == src.plant and r.sign == src.sign for r in taker.remedies):
        return None
    cp = Remedy(src.plant, src.sign, src.prep, src.dose, src.born,
                src=f"تلقّاها عن {giver.name}")
    # ويرث معها ثقةَ معلّمه مخفّفةً — فتنتقل الخرافة كما ينتقل الصواب
    cp.good = max(0, src.good // 2)
    cp.bad = max(0, src.bad // 2)
    src.taught += 1
    taker.remedies.append(cp)
    return cp


TUNED = {"MAX_REMEDIES": MAX_REMEDIES, "TRUST_PRIOR": 0.30,
         "NOTICE": 0.06, "NULL_CREDIT": 0.45, "NULL_CREDIT_RIGOUR": 0.12, "SIGN_SHOW": 0.22}
