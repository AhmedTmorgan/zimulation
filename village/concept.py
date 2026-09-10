"""
المفاهيم، والاستنتاج، والنيّة.

هنا يُرفع السقف الذي كنتُ أنا فيه أضع كل شيء.

قبل هذا الملف كان الكائن يفكّر بخمسٍ وعشرين سِمةً سمّيتُها أنا، ويختار
من اثنين وعشرين فعلًا حدّدتُها أنا. يعيد ترتيب الأوزان بينها كما يشاء،
لكنّه لا يستطيع أن يصنع **مفهومًا** لم يكن في قائمتي. فكانت أنطولوجيا
عالمه أنطولوجيتي.

ثلاثة أشياء هنا:

**المفهوم** — يلاحظ الكائن اقترانًا في بياناته هو، فيصوغ منه سِمةً
جديدة تنضمّ إلى متّجهه. لا أعرف اسمها ولا مضمونها قبل أن يصنعها.
وتُسمّى وتُعلَّم، فإن انتشرت صارت من لغة القوم.

**الاستنتاج** — من قاعدتين يملكهما يشتقّ ثالثة **لم يعشها قط**. هذا هو
الفرق بين التعلّم بالارتباط والاستدلال: نتيجةٌ بلا تجربة تسندها. ونحن
نَسِمُها `derived` فنستطيع أن نسأل بعد ألف سنة: كم ممّا يعتقدونه لم
يُجرَّب أصلًا؟

**النيّة** — التزامٌ يعقده على سنين فيقاوم به جوعه وخوفه اللحظيَّين حتى
ينكسر أو يبلغ. الفرق بين أن تُدفَع وأن تدفع نفسك.

ولا شيء من هذا وعي. لكنّ السقف لم يعد سقفي.
"""

from . import genome as G
from .lang import eval_expr, render

MAX_CONCEPTS = 9          # سعة الذهن — ولا بدّ من سعةٍ يقوم فيها بناء
MIN_EVIDENCE = 6          # كم مرّة يلزم أن يلاحظ الاقتران قبل أن يصوغه
MAX_DEPTH = 4
#: كم موقفًا يُمشَّط، وكم سمةً من كل موقف — حدُّ الانتباه لا حدُّ العالم.
SCAN_EPISODES = 16
SCAN_FEATURES = 9
#: كم موضعًا في الذهن **يُحجَز لما يأتي من غيره**.
#
# كان الذهن يمتلئ بما يصوغه صاحبُه وحده في شبابه، فإذا قرأ كتابًا بعد
# ذلك لم يسعه منه شيء: `read()` تقف عند الامتلاء. فكانت الكتب تُقرأ
# ولا تُورِث فكرةً واحدة، ولا يلتقي كاتبان على مسألة، ولا يقع خلاف.
#
# فصار في كل ذهنٍ نصيبٌ **لا يملؤه إلا غيرُه**: لا يعقد المرء من عنده
# فوق ستّ، والثلاثةُ الباقية لمن علّمه أو لكتابٍ قرأه. ومن عاش وحده
# بقيت فارغة — وذلك حقٌّ فيه: عالَمُ المنعزل أضيق.
RESERVED = 3
#: وكم موضعًا **لا يملؤه إلا هو**.
#
# الحجز كان في جهةٍ واحدة: حُفظ للآخرين نصيبٌ ولم يُحفظ له نصيب، فامتلأ
# الذهن بما أخذه عن الناس حتى لم يبقَ موضعٌ يسكّ فيه لفظًا من عنده —
# فهبط ما يصوغه القوم بأنفسهم إلى ثلاثة في المئة. والحقّ أن الجهتين
# محفوظتان: لا يُقصى صوتُ الجماعة من الذهن، ولا يُقصى صوتُ صاحبه.
SELF_ROOM = 3

#: ما ضبطتُه بيدي في هذا الملفّ — يُحصى في البيان.
TUNED = {"MAX_CONCEPTS": MAX_CONCEPTS, "MAX_DEPTH": MAX_DEPTH,
         "SCAN_EPISODES": SCAN_EPISODES, "SCAN_FEATURES": SCAN_FEATURES,
         "REVISE_FIRE": 0.15, "REVISE_WEIGHT": 2.5, "REVISE_MAX": 0.45,
         "RESERVED": RESERVED, "SELF_ROOM": SELF_ROOM, "COIN_RISE": 0.28,
         "MIN_EVIDENCE": MIN_EVIDENCE, "COIN_FLOOR": 0.55}             # أقصى طبقات التجريد — بلا حدٍّ تتوالد بلا معنى


class Concept:
    """سِمةٌ صنعها كائن، لم تكن في قائمتي."""

    __slots__ = ("expr", "name", "author", "born", "taught", "evidence",
                 "value", "derived", "uses", "depth")

    def __init__(self, expr, name, author, born, evidence, value, depth=1):
        self.expr = expr          # شجرةٌ فوق السِمات الأساسية (lang)
        self.name = name
        self.author = author
        self.born = born
        self.taught = 0
        self.evidence = evidence  # كم موقفًا بُني عليه
        self.value = value        # ما اقترن به من خير أو شرّ
        self.derived = False
        self.uses = 0
        self.depth = depth        # طبقة التجريد: مفهومٌ عن مفاهيم

    def holds(self, f):
        """
        المفهوم متى صيغ صار وحدةً في الذهن لا مجموعَ أجزائه.

        وكان يُحسب عطفًا محضًا فيضمُر بكل طبقة (أصغرُ الطرفين، ثم أصغر
        منه...) حتى يستحيل بناء طبقةٍ ثالثة. والحدُّ من التضاؤل هو ما
        يجعل التجريد ممكنًا: الكلمة تُستدعى كاملةً، لا مجزّأة.
        """
        v = eval_expr(self.expr, f)
        return v ** 0.55 if v > 0.0 else 0.0

    def key(self):
        """
        هويّةُ الفكرة عبر الأذهان.

        الاسمُ وحده لا يكفي، والتعبيرُ لا يُنقَل (مواضعُه تخصّ صاحبه).
        وما يبقى ثابتًا في كل نسخةٍ هو **مَن صاغها ومتى**: فالفكرة هي
        «ما صاغه فلانٌ سنة كذا وسمّاه كذا»، ومن أخذها عنه أخذ هويّتها
        معها وإن خالفه في حكمها بعد ذلك.

        وبغير هذه الهويّة لا خلافَ ممكن: كلُّ رجلٍ يسمّي فكرتَه اسمًا
        من عنده فلا يلتقي اثنان على مسألةٍ واحدة أبدًا.
        """
        return f"{self.author}:{self.born}:{self.name}"

    def render(self, concepts=None):
        s = f"«{self.name}» = {render(self.expr, concepts)}"
        return s + (f" [طبقة {self.depth}]" if self.depth > 1 else "")


# ------------------------------------------------------------- التسمية
_A = ("سَ", "نَ", "مَ", "طَ", "زُ", "رَ", "لَ", "هَ", "دَ", "كَ", "شَ", "بَ")
_B = ("وم", "ان", "ير", "اث", "َل", "ون", "اء", "ين", "َر", "اس", "َم", "ود")


_DIAC = "ًٌٍَُِّْ"


def _bare(s):
    return "".join(ch for ch in s if ch not in _DIAC)


def _coin(rng, seed_word=None):
    """
    اسمٌ للمفهوم. يُشتقّ ممّا في يده إن وجد، وإلا نُحت نحتًا.
    ويُجرَّد من الحركات قبل القصّ، وإلا خرجت أسماءٌ ككَل وزحاَم.
    """
    if seed_word:
        b = _bare(seed_word)
        if len(b) > 2 and rng.random() < 0.55:
            return _bare(b[:3] + rng.choice(_B))
    return _bare(rng.choice(_A) + rng.choice(_B))


# --------------------------------------------------- تكوين المفهوم
def form(agent, rng, year, nf):
    """
    يلمح الكائن أن حالين يجتمعان في مواقفه، ويقترنان بأثرٍ ثابت — فيصوغ
    منهما شيئًا واحدًا يسمّيه. هذا ما لم أضعه في قائمتي.

    الشاهد كله من حوادثه هو: السِمات التي كانت قائمة، والأثر الذي بقي
    في ذاكرته بعدها. ولا يُسأل: أوقع ذلك حقًّا؟
    """
    eps = [(fs, a, tr) for (fs, a, tr) in agent.prog.episodes
           if tr is not None and tr.strength > 0.05]
    if len(eps) < MIN_EVIDENCE:
        return None
    mine = sum(1 for x in agent.concepts if x.author == agent.id)
    if (len(agent.concepts) >= MAX_CONCEPTS
            or mine >= MAX_CONCEPTS - RESERVED):
        return None

    # يبحث عن زوجٍ من السِمات يتلازم، ويقترن بأثرٍ ذي اتجاه واضح
    # لا يُمشَّط كلُّ ما عاشه ولا كلُّ ما كان حاضرًا في الموقف: **الأحدثُ
    # والأبرز**. وهذا ليس اختصارًا للحساب وحده — هو كيف يقع الاستنتاج
    # فعلًا: لا يقارن المرء كل شيءٍ بكل شيء، يقارن ما بقي ظاهرًا في
    # ذهنه. وبغير هذا الحدّ يكبر الذهن حتى يثقل الرنّ ويقف.
    pair_stat = {}
    for fs, act, tr in eps[-SCAN_EPISODES:]:
        v = tr.val * min(1.5, tr.strength)
        act_f = [i for i, x in fs if x > 0.25 and i != 0]
        if len(act_f) > SCAN_FEATURES:
            act_f = [i for i, _ in sorted(
                ((i, x) for i, x in fs if x > 0.25 and i != 0),
                key=lambda p: p[1], reverse=True)[:SCAN_FEATURES]]
        n_f = len(act_f)
        for i in range(n_f):
            fi = act_f[i]
            for j in range(i + 1, n_f):
                k = (fi, act_f[j])
                e = pair_stat.setdefault(k, [0, 0.0])
                e[0] += 1
                e[1] += v
    if not pair_stat:
        return None

    # من ملك كلمةً فكّر بها. فالمفاهيم التي صاغها تُرجَّح على السِمات
    # الخام حين يبني ما فوقها — وبغير هذا الترجيح تبقى الطبقة الأولى
    # سقفًا، إذ السِمات الخام أكثر عددًا وأشدّ حضورًا فتغلب دائمًا.
    from .mind import NF as _NF
    best, score = None, 0.0
    for k, (n, tot) in pair_stat.items():
        if n < 3:
            continue
        s = abs(tot / n) * (n ** 0.5)
        made = (1 if k[0] >= _NF else 0) + (1 if k[1] >= _NF else 0)
        s *= (1.0 + 0.85 * made)
        if s > score:
            best, score = k, s
    # وكلّما كثُر ما **سكَّه هو** صعُب أن يسكّ غيره: من وضع ستّ كلمات
    # فسّر بها ما يلقاه، ومن لم يضع شيئًا سكّ من أوّل شبهٍ يلمحه.
    #
    # والعبرة بما سكَّه لا بما يحمل. وكان الحدُّ على المجموع، فكان من
    # تعلّم من الناس ثمانيةً يُمنَع أن يضع واحدًا — أي أن **الأخذ عن
    # الغير يخنق الوضع**، وذلك عكسُ ما يقع: من ملك ألفاظًا أكثر بنى
    # فوقها أسهل. وبلغ المنقولُ ثمانيةً وثمانين في المئة لهذا السبب.
    if best is None or score < 0.55 * (1.0 + 0.28 * mine):
        return None

    n, tot = pair_stat[best]
    mean = tot / n
    op = 2 if mean > 0 else 3       # ما اقترن بخيرٍ يُعقَد عطفًا، والشرّ فصلًا
    expr = (op, (0, best[0]), (0, best[1]))

    # الطرفان قد يكونان مفهومَين صنعهما هو — فيُبنى تجريدٌ فوق تجريد.
    # وهذا هو العمق: طبقةٌ ثانية ثم ثالثة، ولكلٍّ اسمٌ مشتقّ ممّا تحته.
    from .mind import AR_FEATURES, FEATURES, NF
    def _label(i):
        if i < NF:
            return AR_FEATURES[FEATURES[i]], 0
        j = i - NF
        if j < len(agent.concepts):
            return agent.concepts[j].name, agent.concepts[j].depth
        return None, 0
    s0, d0 = _label(best[0])
    s1, d1 = _label(best[1])
    if s0 is None or s1 is None:
        return None
    depth = 1 + max(d0, d1)
    if depth > MAX_DEPTH:
        return None
    # لا يصوغ المرء اسمين لمعنًى واحد في ذهنه هو. (وأمّا أن يختلف اسمُه
    # عن اسم جاره لنفس المعنى فذاك شأن آخر — وهو واقع، وهو المترادفات.)
    if any(x.expr == expr for x in agent.concepts):
        return None
    c = Concept(expr, _coin(rng, s0), agent.id, year, n, mean, depth)
    agent.concepts.append(c)
    agent.prog.W.extend([0.0] * nf_actions())   # صفٌّ جديد في مصفوفته
    return c


def nf_actions():
    from .mind import NA
    return NA


def evaluate(agent, f):
    """قيم المفاهيم المصنوعة، تُلحَق بمتّجه السِمات الأساسي."""
    if not agent.concepts:
        return f
    out = list(f)
    for c in agent.concepts:
        v = c.holds(f)
        if v > 0.02:
            c.uses += 1
        out.append(v)
    return out


def revise(agent):
    """
    يراجع المرءُ ما صاغه على ما عاشه **بعد** أن صاغه.

    وكان الحكم يُثبَّت مرّةً واحدة فلا يتغيّر أبدًا: من رأى في الخامسة
    والعشرين أن هذين يجتمعان فيأتي الخير مات عليه في السبعين مهما
    رأى بعدها. وذلك ليس تعلّمًا، وهو أيضًا يقطع الخلاف من أصله — إذ
    نسخةُ الفكرة تحمل حكمَ مُعطيها إلى الأبد، فلا يختلف تلميذان.

    فالحكم الآن يتحرّك بالشاهد، **وثِقلُ الشاهد الجديد يقلّ كلّما كثُر
    القديم** — فمن بنى فكرته على أربعين موقفًا لا يقلبها موقفان.
    ومن انقلب حكمُه فقد غيّر رأيه، وهذا يقع ويُدوَّن.
    """
    if not agent.concepts:
        return None
    eps = [e for e in agent.prog.episodes[-SCAN_EPISODES:]
           if e[2] is not None and e[2].strength > 0.05]
    if len(eps) < 4:
        return None
    from .mind import NF
    n = NF + len(agent.concepts)
    dense = []
    for fs, _act, tr in eps:
        f = [0.0] * n
        for i, x in fs:
            if i < n:
                f[i] = x
        dense.append((f, tr.val * min(1.5, tr.strength)))

    flipped = None
    for cc in agent.concepts:
        num = den = 0.0
        for f, v in dense:
            w = cc.holds(f)
            if w > 0.15:
                num += w * v
                den += w
        if den < 0.6:
            continue                      # لم يحضر مفهومُه في شيء
        obs = num / den
        old = cc.value
        k = min(0.45, 2.5 / (cc.evidence + 2.5))
        cc.value = old + k * (obs - old)
        cc.evidence += 1
        if (old > 0.0) != (cc.value > 0.0) and abs(cc.value) > 0.05:
            flipped = cc
    return flipped


# ------------------------------------------------------- النقل
def _borrowed_full(taker):
    """أبلغ المنقولُ حدَّه؟ فلا يُزاحم ما يسكّه صاحبُ الذهن."""
    got = sum(1 for x in taker.concepts if x.author != taker.id)
    return got >= MAX_CONCEPTS - SELF_ROOM


def transplant(src, owner_concepts, taker, rng=None):
    """
    نقلُ مفهومٍ من ذهنٍ إلى ذهن.

    ومؤشّرات المفاهيم **ليست قابلة للنقل**: الموضع الثاني في ذهن المؤلّف
    غير الموضع الثاني في ذهن السامع. فنقلُ التعبير كما هو يجعل المفهوم
    يشير إلى غير ما وُضع له — بل قد يشير إلى نفسه.

    فيُنقَل هنا مع **ما بُني عليه**: تُستنسخ المفاهيم التي يتألّف منها
    أوّلًا، ثم يُعاد ترقيم مواضعها في ذهن الآخذ. ومن لم يتّسع ذهنه لما
    تحته لم يأخذه — فبعض الأفكار لا تُنقَل إلا إلى من هُيّئ لها.
    """
    from .mind import NA, NF
    # من ملك المعنى لم يحتج إلى موضعٍ ثانٍ له وإن سمع له اسمًا آخر.
    # (والاسمان لمعنًى واحد بين شخصين مترادفان — وذاك واقع يُبقى عليه.)
    if any(x.expr == src.expr for x in taker.concepts):
        return None
    mapping = {}

    def _need(cc):
        """
        ينسخ ما تحته أوّلًا، ويعيد موضعه الجديد.

        والمقارنة تقع بعد إعادة الترقيم لا قبلها: تعبيرُ المُعطي بلغته
        هو، فلا يُقارَن بتعابير الآخذ إلا بعد أن يُترجَم إليها.
        """
        sub = _remap(cc.expr)
        if sub is None:
            return None
        for k, v in enumerate(taker.concepts):
            if v.expr == sub:
                return NF + k
        if len(taker.concepts) >= MAX_CONCEPTS:
            return None
        cp = Concept(sub, cc.name, cc.author, cc.born,
                     cc.evidence, cc.value, cc.depth)
        cp.taught = cc.taught + 1
        cc.taught += 1
        taker.concepts.append(cp)
        taker.prog.W.extend([0.0] * NA)
        return NF + len(taker.concepts) - 1

    def _remap(e):
        if e[0] == 0:
            i = e[1]
            if i < NF:
                return e
            j = i - NF
            if j >= len(owner_concepts):
                return None
            got = _need(owner_concepts[j])
            return None if got is None else (0, got)
        if e[0] == 1:
            s = _remap(e[1])
            return None if s is None else (1, s)
        a = _remap(e[1])
        b = _remap(e[2])
        if a is None or b is None:
            return None
        if a == b:
            return a                    # لا عبارةَ تكرّر نفسها
        return (e[0], a, b)

    if _borrowed_full(taker):
        return None
    expr = _remap(src.expr)
    if expr is None or len(taker.concepts) >= MAX_CONCEPTS:
        return None
    cp = Concept(expr, src.name, src.author, src.born,
                 src.evidence, src.value, src.depth)
    cp.taught = src.taught + 1
    src.taught += 1
    taker.concepts.append(cp)
    taker.prog.W.extend([0.0] * nf_actions())
    return cp


# ------------------------------------------------------- الاستنتاج
def derive(agent, rng, year):
    """
    من قاعدةٍ ومفهومٍ يشتقّ قاعدةً لم يعشها.

    إن كانت عنده «إذا (سِمة س) فافعل ف»، وكان عنده مفهومٌ «م» تدخل فيه
    «س» — فقد يستنتج «إذا م فافعل ف». والنتيجة لا تسندها تجربة واحدة:
    هي مشتقّة لا مكتسبة. وتُوسَم كذلك.
    """
    from .lang import Maxim
    if not agent.concepts or not agent.prog.maxims:
        return None
    if len(agent.prog.maxims) >= 14:
        return None
    m = rng.choice(agent.prog.maxims)
    base = _leaves(m.expr)
    if not base:
        return None
    cands = [c for c in agent.concepts if set(_leaves(c.expr)) & set(base)]
    if not cands:
        return None
    c = rng.choice(cands)
    ci = agent.concepts.index(c)
    from .mind import NF
    new = Maxim((0, NF + ci), m.action, m.weight * 0.85, agent.id, year)
    new.derived = True
    agent.prog.maxims.append(new)
    agent.prog.derived += 1
    return new


def _leaves(e):
    if e[0] == 0:
        return [e[1]]
    if e[0] == 1:
        return _leaves(e[1])
    return _leaves(e[1]) + _leaves(e[2])


# ------------------------------------------------------------ النيّة
class Intention:
    """التزامٌ على سنين يقاوم دوافع اللحظة."""

    __slots__ = ("action", "years", "why", "born", "strength", "broke")

    def __init__(self, action, years, why, born, strength):
        self.action = action
        self.years = years
        self.why = why
        self.born = born
        self.strength = strength
        self.broke = False


def intend(agent, rng, year):
    """
    يعقد نيّة أثناء تأمّله. مصدرها أقوى ما يتذكّر، ومداها من عزمه
    (الضمير)، وقوّتها ممّا يقاوم به الجوع والخوف.
    """
    if agent.intention is not None:
        return None
    t = agent.eg.t
    if rng.random() > 0.06 * (0.2 + t[G.CONSCIENT]) * (0.3 + t[G.OPENNESS]):
        return None
    live = [(fs, a, tr) for (fs, a, tr) in agent.prog.episodes
            if tr is not None and tr.strength > 0.05]
    if not live:
        return None
    fs, act, tr = max(live, key=lambda e: e[2].val * e[2].strength)
    if tr.val <= 0.15:
        return None
    yrs = 2 + int(6 * t[G.CONSCIENT] * rng.random())
    st = 1.6 + 2.4 * t[G.CONSCIENT]
    agent.intention = Intention(act, yrs, f"أثرٌ من سنة {tr.year}", year, st)
    return agent.intention


def press(agent):
    """أثر النيّة على الاختيار — تُضاف كعلاوةٍ تقاوم دوافع اللحظة."""
    it = agent.intention
    if it is None:
        return None
    return it.action, it.strength


def tick(agent, ctx):
    """
    تمرّ سنة على النيّة. تنكسر إن اشتدّ الجوع فوق ما تحتمل — فليس هذا
    عزمًا مطلقًا، بل عزمٌ له حدّ. ومن انكسرت نيّته حمل أثر ذلك.
    """
    it = agent.intention
    if it is None:
        return None
    from .emotion import P_GRIEF, P_LUST
    strain = (min(1.0, agent.hunger) * 1.6 + agent.fear_death * 0.9
              + agent.fear_want * 0.7 + agent.af.p[P_GRIEF] * 0.6
              + agent.af.p[P_LUST] * 0.4 + agent.despair * 0.8)
    it.strength *= 0.94          # العزم يبلى بطول المدّة
    if strain > it.strength * 0.42:
        it.broke = True
        agent.intention = None
        agent.af.social(4, 0.5)          # E_RESENT — على نفسه
        return "broke"
    it.years -= 1
    if it.years <= 0:
        agent.intention = None
        agent.prog.kept += 1
        return "kept"
    return None
