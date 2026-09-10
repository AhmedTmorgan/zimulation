"""
السببية.

كان في هذا العالم أرقامٌ مفروضة بلا علّة: `base_lifespan = 44` رقمٌ
كتبتُه، فإذا سُئل «لماذا يعيشون أربعًا وأربعين؟» لم يكن الجواب إلا
«لأني كتبتُ ذلك». وهذا عيبٌ في النمذجة لا تفصيلًا فيها: النموذج الذي
تُفرَض نتائجه لا يفسّر شيئًا.

فهنا يصير العمر **نتيجةً** لا معاملًا:

    أذًى يتراكم  −  إصلاحٌ يتناقص  =  الموت

وكل طرفٍ منهما مشتقٌّ من متغيّراتٍ في العالم لا من رقمٍ عندي. فإذا سُئل
«لماذا قلّت الوفيات؟» كان الجواب: لأن الغلّة زادت فقلّ الجوع، أو لأن
الطبّ رفع الإصلاح، أو لأن الماء طاب. وإذا سُئل «لماذا ظهر السرطان؟»
كان الجواب أعمق: **لأنهم كفّوا عن الموت بغيره.**

المراجع:
  الجسد المُستهلَك (Kirkwood 1977) — الصيانة والنسل يتنازعان موردًا واحدًا،
  فمن أكثر النسل قلّت صيانته. وبهذا تصير الشيخوخة مقايضةً لا قدرًا.

  نموذج الإصابات المتعدّدة (Armitage & Doll 1954) — الورم يحتاج تراكم
  إصاباتٍ في الخليّة، فيرتفع وقوعه بأُسٍّ من العمر. ولهذا لا يُرى إلا
  حيث طال العمر.
"""

from . import genome as G
from .mind import (A_FORAGE, A_FARM, A_HERD, A_BUILD, A_CRAFT, A_ATTACK,
                   A_REST, A_CONTEMPLATE)

# ما يُنهك الجسد من الأفعال — الكدح سببٌ للأذى كالجوع
TOIL = {A_FARM: 1.00, A_BUILD: 0.95, A_HERD: 0.75, A_FORAGE: 0.70,
        A_CRAFT: 0.45, A_ATTACK: 0.85, A_REST: -0.35, A_CONTEMPLATE: -0.10}

CANCER_HITS = 5          # كم إصابةً يلزم تراكمها قبل أن يستقلّ الورم


def toil_of(act):
    return TOIL.get(act, 0.15)


# ------------------------------------------------------------ الماء
def foul(region, pop, know):
    """
    فساد الماء. سببه مزدحمٌ يسكن ودخانُ صنعةٍ يُصرَف — لا قدرٌ يهبط.
    والرَّي يزيده لأنه يُركّد، والفخّار يقلّله لأنه يُغلي ويُخزّن.
    """
    # الكثافة تُشبع: مدينةٌ من ألفٍ ليست أقذر عشر مرّاتٍ من قريةٍ من مئة،
    # لأن مَن كثُروا حفروا وصرّفوا. فالجذر لا الخطّ.
    dens = min(1.0, (pop / 400.0) ** 0.5)
    craft = 0.0
    if "copper" in know:
        craft += 0.10
    if "bronze" in know:
        craft += 0.12
    if "iron" in know:
        craft += 0.16
    if "irrigation" in know:
        craft += 0.10
    relief = 0.0
    if "pottery" in know:
        relief += 0.10          # يُغلى ويُخزَّن
    if "granary" in know:
        relief += 0.04
    if "law" in know:
        relief += 0.08          # تنظيمُ المصارف
    if "wheel" in know:
        relief += 0.05          # نقلُ الماء من بعيد
    if "geometry" in know:
        relief += 0.10          # قنواتٌ تُمَدّ بميلٍ محسوب
    if "medicine" in know:
        relief += 0.24
    if "method" in know:
        relief += 0.12
    return max(0.0, min(1.0, dens * 0.55 + craft - relief))


# ------------------------------------------------------------ الإصلاح
def repair_capacity(a, cfg, nutrition, medicine):
    """
    ما يصلحه الجسد في السنة.

    يتناقص بالسنّ (الشيخوخة)، وبالنسل (الجسد المُستهلَك: ما أُنفق على
    الخلف لا يُنفق على الصيانة)، ويرتفع بالغذاء وبالطبّ.
    """
    base = 0.135 + 0.26 * a.g.t[G.VIGOR] + 0.095 * a.g.t[G.LONGEVITY]
    # الشيخوخة: انحدارٌ يبدأ بعد العشرين ويتسارع
    age = a.age
    senesce = 1.0 if age <= 22 else max(0.06, 1.0 - 0.0125 * (age - 22) ** 1.22)
    # المقايضة: كل ولدٍ ثمنُه صيانةٌ لم تُنفَق
    soma = (max(0.55, 1.0 - 0.028 * len(a.children))
            if getattr(cfg, 'cause_soma', True) else 1.0)
    return base * senesce * soma * (0.55 + 0.55 * nutrition) * (1.0 + medicine)


def wear(a, ctx, know, region, cfg, rng, medicine):
    """
    ما يقع على الجسد في السنة، وكل مصدرٍ منه له اسمٌ يُسأل عنه.
    يعيد (صافي الأذى، أكبر مصدرٍ فيه).
    """
    src = {}
    src["الأيض"] = 0.055
    h = min(1.0, a.hunger)
    if h > 0.02:
        src["الجوع"] = 0.155 * h
    if a.illness > 0.02:
        src["السقم"] = 0.185 * a.illness
    t = toil_of(a.last_action)
    if t > 0 and getattr(cfg, "cause_toil", True):
        src["الكدح"] = 0.048 * t * (1.4 - a.g.t[G.VIGOR])
    if getattr(cfg, "cause_water", True):
        w = foul(region, ctx.get("pop", 0), know)
        if w > 0.05:
            src["الماء"] = 0.115 * w
    if a.pregnant or (a.sex == 1 and a.age < 45 and len(a.children) > 0):
        src["الحمل"] = 0.020 * min(6, len(a.children))

    gross = sum(src.values())
    rep = repair_capacity(a, cfg, ctx.get("provision", 1.0), medicine)
    net = gross - rep
    a.damage = max(0.0, a.damage + net)
    if t < 0:
        a.damage = max(0.0, a.damage + 0.030 * t)     # الراحة تُصلح

    # الإصابات الجسدية تتراكم بقدر ما يقع على الجسد — لا بقدر السنّ وحده
    # المعدّل معايَرٌ ليبلغ خمس إصاباتٍ نحو الستين لمن سلِم — فيظهر
    # الورم حيث طال العمر وحده، ولا يُرى في مجتمعٍ يموت شبابه.
    # ويُفصَل ما يُبلي الجسدَ عمّا يُراكم الطفرات: السقمُ الحادّ يُنهك
    # ولا يُسرطن، والمزمنُ يفعل الاثنين.
    mut = gross - src.get("السقم", 0.0) + 0.30 * getattr(a, "inflam", 0.0)
    if rng.random() < 0.030 + 0.16 * max(0.0, mut):
        a.hits += 1

    top = max(src.items(), key=lambda kv: kv[1])[0] if src else "الأيض"
    return net, top


# ------------------------------------------------------------ الموت
def hazard(a, cfg, rng):
    """
    احتمال الموت في هذه السنة، وسببُه.

    لا عمرَ مفروض هنا: الشيخوخة تظهر لأن الإصلاح ينحدر، والورم يظهر
    لأن الإصابات تتراكم — ولا يُرى إلا عند من طال عمره.
    """
    # الورم: يحتاج تراكمًا، فلا يصيب شابًّا إلا نادرًا
    if a.hits >= CANCER_HITS and getattr(cfg, 'cause_tumour', True):
        # منحنى أرميتاج-دول: شديد الانحدار، فلا يكاد يُرى قبل الأربعين
        # ثم يرتفع بأُسٍّ. ولذلك يبقى نادرًا حيث يقصر العمر لأسبابٍ أخرى،
        # ويظهر فجأةً حين يطول — وهو ما وقع في تاريخ البشر فعلًا.
        p = 0.016 * (a.hits - CANCER_HITS + 1) ** 1.9
        if rng.random() < min(0.40, p):
            return True, "ورم", f"تراكمت {a.hits} إصابة"

    if a.damage > 1.0:
        p = min(0.75, 0.28 * (a.damage - 1.0) ** 0.85 + 0.05)
        if rng.random() < p:
            why = "وهنٌ" if a.age > 40 else "إنهاك"
            return True, why, f"أذًى {a.damage:.2f} فوق ما يُصلَح"

    # حوادث لا تُعزى إلى تراكم: وقوعٌ وغرقٌ ولدغ
    acc = 0.0030 * (1.3 - a.g.t[G.VIGOR]) * (1.0 + 0.5 * toil_of(a.last_action))
    if rng.random() < acc:
        return True, "حادث", "لا تراكم فيه"
    return False, None, None


# ------------------------------------------------------------ الجهل
def literacy(st, agents, cfg):
    """
    نصيبُ من يقرأ. ينتشر الجهل حين تُحرق الكتب أو يموت المعلّمون أو
    يتفرّق الناس — ويقلّ حين تكثر النسخ وتُطبَع.
    """
    if "writing" not in st.knowledge:
        return 0.0
    n = max(1, st.pop())
    teachers = sum(1 for m in st.members
                   if m in agents and agents[m].prestige > 2.0)
    books = sum(b.copies for b in st.library.books)
    lit = 0.06 + 0.35 * min(1.0, books / (n * 0.35)) + 0.30 * min(1.0, teachers / (n * 0.10))
    if "paper" in st.knowledge:
        lit += 0.08
    if "printing" in st.knowledge:
        lit += 0.22
    if "archive" in st.knowledge:
        lit += 0.08
    return max(0.0, min(0.95, lit))


# ------------------------------------------------------------ التفسير
def explain(a):
    """سلسلةُ سببٍ لموتة بعينها — لا وسمٌ مجرّد."""
    parts = []
    if a.hits:
        parts.append(f"إصابات متراكمة: {a.hits}")
    parts.append(f"أذًى صافٍ: {a.damage:.2f}")
    parts.append(f"ولدٌ أنفق عليه صيانته: {len(a.children)}")
    if a.age:
        parts.append(f"بلغ {a.age}")
    return " · ".join(parts)


# ------------------------------------------------------------ الوباء
def outbreak_pressure(sim):
    """
    ظهور ممرضٍ جديد. كان احتمالًا ثابتًا كتبتُه — وهذا يخالف قاعدة
    «لا حدث بلا سبب». فهنا يُشتقّ من ثلاثةٍ كلُّها في العالم:

      **مخالطة الحيوان** — أكثر أوبئة البشر جاءت من الماشية. فمن استأنس
      فتح بابًا لم يكن مفتوحًا (Diamond 1997؛ Wolfe et al. 2007).

      **الكثافة** — الممرض يحتاج عائلًا يجد غيره قبل أن يموت. ودون عتبةٍ
      من العدد ينطفئ (حجم المجتمع الحَرِج، Bartlett 1957).

      **الاتصال** — الطريق الذي ينقل الحَبّ ينقل السقم. فالتجارة تُغني
      وتُعدي معًا.
    """
    total = sim.population()
    if total < 60:
        return 0.0
    animals = 0.0
    connect = 0.0
    dens = 0.0
    n = max(1, len(sim.world.settlements))
    for st in sim.world.settlements:
        pop = st.pop() + sim.mass.get(st.id, 0)
        if "herding" in st.knowledge:
            animals += 0.30
        if "farming" in st.knowledge:
            animals += 0.10          # فأرُ المخزن وذبابُ الحقل
        for k, v in (("wheel", 0.10), ("sail", 0.14), ("coin", 0.10),
                     ("printing", 0.08)):
            if k in st.knowledge:
                connect += v
        dens += min(1.0, pop / 400.0)
    animals /= n
    connect /= n
    dens /= n
    hygiene = 0.0
    k0 = sim.world.settlements[0].knowledge
    if "medicine" in k0:
        hygiene += 0.35
    if "method" in k0:
        hygiene += 0.20
    if "law" in k0:
        hygiene += 0.08
    crit = min(1.0, (total / 900.0) ** 0.6)      # عتبة حجمٍ حرجة
    p = 0.0075 * crit * (0.35 + animals) * (0.45 + dens) * (0.55 + connect)
    return max(0.0, p * (1.0 - hygiene))


# ------------------------------------------------------------ الخصوبة
def fecundity(a, cfg, provision):
    """
    احتمال الحمل. كان رقمًا ثابتًا، وله في الواقع ثلاثة أسباب:

      **الرضاعة** — أعظم كابحٍ للنسل قبل الحداثة. المرضع لا تحمل غالبًا
      (انقطاع الطمث الإرضاعي)، ومدّةُ الإرضاع تطول حيث يقلّ الطعام —
      فتقلّ الولادات حيث يقلّ القوت، بلا قرارٍ من أحد.

      **حال الجسد** — الجوع والأذى المتراكم يخفضان الخصوبة قبل أن يقتلا
      (Frisch 1978: عتبةُ كتلةٍ للإخصاب).

      **السنّ** — انحدارٌ يتسارع بعد الخامسة والثلاثين.

    فتصير المباعدة بين الولادات نتيجةً لا معاملًا.
    """
    if a.nursing > 0:
        return 0.02                       # لا ينقطع تمامًا، ويكاد
    p = 0.92 * (0.40 + a.g.t[G.FERTILITY])
    p *= max(0.15, 1.0 - 0.55 * min(1.0, a.hunger))
    p *= max(0.25, 1.0 - 0.40 * min(1.0, a.damage))
    p *= (0.55 + 0.45 * min(1.0, provision))
    if a.age > 35:
        p *= max(0.10, 1.0 - 0.085 * (a.age - 35))
    return max(0.0, min(0.95, p))


def nursing_years(mother, provision, know):
    """
    كم تُرضع. تطول حيث يقلّ الطعام — فيتباعد النسل من غير قرار.
    والفطام يُبكَّر حيث كثُر القوت أو عُرف الحليب المستأنس.
    """
    y = 3.3 - 1.0 * min(1.0, provision)
    if "herding" in know:
        y -= 0.35                          # لبنُ الماشية يُفطم به
    if "granary" in know:
        y -= 0.15
    if "medicine" in know:
        y -= 0.20
    return max(1.1, y)
