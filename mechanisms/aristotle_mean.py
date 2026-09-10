"""
الوسط — أرسطو.

دعواه في «الأخلاق النيقوماخية» أن الفضيلة وسطٌ بين طرفين، وأن الطرفين
كليهما رذيلة: الشجاعة بين التهوّر والجبن، والكرم بين التبذير والشحّ.

وهنا تصير الدعوى قابلة للقياس مباشرةً: إن صحّت، فمن كان في طرفٍ من أي
صفة — عاليًا كان أو واطئًا — يجب أن **يعيش أقلّ وينجب أقلّ** ممن كان في
الوسط. وإن لم يظهر ذلك في الأرقام فالدعوى لا تصمد في هذه الدنيا.

والأثر هنا صغيرٌ عن قصد (بضعة بالمئة في السنة) كي يُقاس على الأجيال لا
أن يُفرض في الجيل الواحد. عطّلها بـ `disable("golden-mean")` وقارن.
"""

from village import genome as G
from village.plugin import mechanism

# الصفات التي لها طرفان مؤذيان — لا كلّ صفة كذلك
_TWO_ENDED = (G.AGREEABLE, G.CONSCIENT, G.EXTRAVERSION, G.NEUROTIC,
              G.RAGE, G.FEAR, G.CARE, G.SEEKING, G.CREDULITY, G.DOMINANCE)


@mechanism(
    key="golden-mean",
    ar="الوسط الذهبي",
    source="Aristotle, Ἠθικὰ Νικομάχεια (نحو 340 ق.م)، الكتاب الثاني",
    claim="طرفا كل صفةٍ مؤذيان لا طرفٌ واحد؛ فمن بعُد عن الوسط في صفاته "
          "يعيش أقلّ وينجب أقلّ ممن قارَبه — على الأجيال لا في الجيل.",
    params={"cost": 0.020, "reach": 0.30},
    hook="yearly",
)
def golden_mean(sim, a, ctx, rng, P):
    if a.age < 12:
        return None
    excess = 0.0
    for i in _TWO_ENDED:
        d = abs(a.eg.t[i] - 0.5)
        if d > P["reach"]:
            excess += (d - P["reach"])
    if excess <= 0.0:
        return None
    # ثمنٌ صغير في الصحّة والخصوبة معًا — يظهر أثره في مئة سنة لا في سنة
    a.health = max(0.0, a.health - P["cost"] * excess)
    return None
