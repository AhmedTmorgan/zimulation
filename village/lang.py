"""
اللغة الصغيرة التي يكتب بها الكائن كودَه.

حكمة = «إذا <شرط> فـ<فعل>» بوزن.
الشرط شجرة صغيرة: سِمة، أو نفيها، أو عطف/فصل بين اثنتين.

الحِكَم تُؤلَّف أثناء التأمّل من ارتباطٍ يلمحه الكائن بين موقفٍ يتذكّره
ونتيجةٍ يتذكّرها. ثم تُعلَّم وتُورَّث، وتتشوّه في كل نقل — فتنجرف
المعاني عبر القرون كما تنجرف اللغات. وكلها قابلة للقراءة بالعربية،
فيمكننا أن نفتح أي سنة ونقرأ حرفيًا: ما الذي اخترعته هذه القرية.
"""

_NEXT = [1]


def _fresh():
    _NEXT[0] += 1
    return _NEXT[0]


class Maxim:
    __slots__ = ("id", "expr", "action", "weight", "author", "born", "taught",
                 "lineage", "derived")

    def __init__(self, expr, action, weight, author, born, lineage=None):
        self.id = _fresh()
        self.expr = expr
        self.action = action
        self.weight = weight
        self.author = author
        self.born = born
        self.taught = 0
        self.lineage = lineage if lineage is not None else self.id
        self.derived = False     # مشتقّة لا مكتسبة: لم تسندها تجربة


def eval_expr(e, f):
    op = e[0]
    if op == 0:            # سِمة
        i = e[1]
        # قاعدةٌ تُشير إلى مفهومٍ لا يحمله من ورثها: لا تجد ما تستند إليه
        # فلا تعمل. وهكذا تموت أفكارٌ لأن حاملها لم يفهم ما بُنيت عليه.
        return f[i] if i < len(f) else 0.0
    if op == 1:            # نفي
        return 1.0 - eval_expr(e[1], f)
    if op == 2:            # عطف
        a = eval_expr(e[1], f)
        b = eval_expr(e[2], f)
        return a if a < b else b
    a = eval_expr(e[1], f)  # فصل
    b = eval_expr(e[2], f)
    return a if a > b else b


def render(e, concepts=None):
    from .mind import FEATURES, AR_FEATURES, NF
    op = e[0]
    if op == 0:
        i = e[1]
        if i < NF:
            return AR_FEATURES[FEATURES[i]]
        # ما بعد السِمات الأساسية مفاهيمُ صاغوها هم
        if concepts and i - NF < len(concepts):
            return "«" + concepts[i - NF].name + "»"
        return "مفهومٌ لا يحمله"
    if op == 1:
        return "لا " + render(e[1], concepts)
    if op == 2:
        return "(" + render(e[1], concepts) + " و" + render(e[2], concepts) + ")"
    return "(" + render(e[1], concepts) + " أو " + render(e[2], concepts) + ")"


def render_maxim(m, concepts=None):
    from .mind import ACTIONS, AR_ACTIONS, NF
    verb = AR_ACTIONS[ACTIONS[m.action]]
    body = render(m.expr, concepts)
    s = f"إذا {body} فلا ت{verb}" if m.weight < 0 else f"إذا {body} فـ{verb}"
    return s + (" [مستنتَجة]" if m.derived else "")


def compose_maxim(episodes, rng, author, year, ressentiment=0.0, high_acts=()):
    """
    الكائن يلمح ارتباطًا بين موقفٍ يتذكّره وأثرٍ يتذكّره — فيصوغه قاعدة.
    وقد يكون الأثر الذي بنى عليه لم يقع قط.
    """
    if len(episodes) < 2:
        return None
    scored = sorted(episodes, key=lambda e: abs(e[2].val * e[2].strength), reverse=True)
    fs, action, tr = scored[0]
    if not fs:
        return None
    signal = tr.val * min(1.5, tr.strength)
    if abs(signal) < 0.25:
        return None

    fs2 = sorted(fs, key=lambda p: p[1], reverse=True)[:3]
    fi = fs2[0][0]
    if fi == 0 and len(fs2) > 1:
        fi = fs2[1][0]
    expr = (0, fi)

    other = next((p[0] for p in fs2 if p[0] != fi), None)
    r = rng.random()
    if r < 0.28 and other is not None:
        expr = (2, expr, (0, other))              # عطف
    elif r < 0.40 and other is not None:
        expr = (3, expr, (0, other))              # فصل
    elif r < 0.50:
        expr = (1, expr)                          # نفي

    w = max(-2.2, min(2.2, signal * 1.6))

    # قلبُ القيم (نيتشه): من طال احتقاره ولم يقدر على الانتقام لم يبقَ له
    # إلا أن يعيد تعريف الفضيلة، فيجعل ما يرفع أصحاب المقام مذمومًا.
    # لا نكتب له ما يقول: نجعله يذمّ الفعل الذي به عَلا خصومه فعلًا.
    if ressentiment > 0.45 and high_acts and rng.random() < min(0.8, ressentiment):
        action = rng.choice(tuple(high_acts))
        w = -abs(w) * 1.35

    return Maxim(expr, action, w, author, year)


def mutate_maxim(m, rng, drift):
    """كل نقل يشوّه المعنى قليلًا — انجراف ثقافي في مستوى الكود نفسه."""
    from .mind import NF, NA
    expr = m.expr
    action = m.action
    weight = m.weight * (1.0 + rng.gauss(0.0, drift))

    r = rng.random()
    if r < drift:
        action = rng.randrange(NA)                        # تحريف الأمر
    elif r < drift * 2:
        expr = (1, expr) if expr[0] != 1 else expr[1]     # انقلاب الشرط
    elif r < drift * 3 and expr[0] == 0:
        expr = (0, rng.randrange(NF))                     # استبدال السِمة
    elif r < drift * 3.6 and expr[0] in (2, 3):
        expr = (5 - expr[0], expr[1], expr[2])            # و ↔ أو

    if expr[0] in (2, 3) and expr[1] == expr[2]:
        expr = expr[1]                            # «زحام وزحام» ليست عبارة
    n = Maxim(expr, action, weight, m.author, m.born, m.lineage)
    n.taught = m.taught + 1
    n.derived = m.derived
    return n
