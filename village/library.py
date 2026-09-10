"""
المكتبة.

هذا هو الأساس القويّ الذي طُلب — لا بأن نضع فيهم كتبنا، بل بأن نُقدرهم
على الكتابة. الكتب التي نضعها تعطيهم **إجاباتنا**؛ والقدرة على الكتابة
تعطيهم **أسئلتهم**.

وما يفعله الكتاب في هذا العالم ليس رمزيًا:

  **يعبر الموت.** كان المفهوم يموت بصاحبه ما لم يُعلَّم لحيٍّ. والكتاب
  يحمله إلى من لم يولد بعد. فيصير للمعرفة تراكمٌ لا دورة.

  **يحمل الدورة.** من كشف أن الغضب موعدٌ ودوّنه في رسالة، بقي كشفه بعده
  ولو قُتل. وهذا وحده يقلب مصير حضارةٍ كاملة.

  **يُنسَخ ويُحرَق.** النسخُ يقاوم الفقد، والحرقُ يمحو قرونًا في ليلة.
  فتصير حرية القول شرطًا ماديًّا للتقدّم لا شعارًا.

  **يتناقض مع غيره.** رسالتان تختلفان في المفاهيم تصنعان **مدرستين**،
  وقارئوهما يفكّرون بمفرداتٍ مختلفة عن الشيء نفسه.
"""

from . import genome as G

KIND_TREATISE = "رسالة"
KIND_CHRONICLE = "سِيرة"
KIND_CODE = "دستور"
KIND_WAR = "أخبار الحرب"
KIND_TABLES = "زِيج"

_N = [0]


class Book:
    __slots__ = ("id", "kind", "title", "author", "author_name", "born",
                 "concepts", "maxims", "thesis", "period", "copies",
                 "burned", "read_by", "school", "parent", "stance", "split",
                 "topic", "sign", "topic_name", "recipes")

    def __init__(self, kind, title, author, author_name, born,
                 concepts, maxims, thesis, period=None, school=-1, parent=-1,
                 stance="عامّ", topic="", sign=1):
        _N[0] += 1
        self.id = _N[0]
        self.kind = kind
        self.title = title
        self.author = author
        self.author_name = author_name
        self.born = born
        self.concepts = concepts          # نسخٌ من مفاهيم كاتبها
        self.maxims = maxims
        self.thesis = thesis              # أطروحته في جملة
        self.period = period              # الدورة إن كان يعرفها
        self.copies = 1
        self.burned = 0
        self.read_by = 0
        self.school = school              # مدرسته الفكرية
        self.parent = parent              # الرسالة التي بُني عليها
        self.stance = stance              # موقف كاتبها — منه يقع التناقض
        self.split = None                 # اسمُ المدرسة التي انشُقّ عنها
        self.topic = topic                # المسألة التي فيها الكلام
        self.sign = sign                  # جهتُه فيها: مُثبِتٌ أم نافٍ
        self.topic_name = topic           # اسم المسألة كما يُنطق
        self.recipes = []                 # وصفاتُ عقّارٍ إن كان كتابَ طبّ

    def label(self):
        return f"{self.kind} «{self.title}» — {self.author_name}، سنة {self.born:,}"


class Library:
    """ما تحفظه قريةٌ من كتب. يُنسخ ويُحرق ويُقرأ."""

    __slots__ = ("books", "burned_total")

    def __init__(self):
        self.books = []
        self.burned_total = 0

    def add(self, b):
        self.books.append(b)
        return b

    def copy(self, rng, know):
        """النسخ يقاوم الفقد. الورق يُعين، والطباعة تضاعف."""
        if not self.books:
            return 0
        rate = 0.02
        if "paper" in know:
            rate += 0.05
        if "archive" in know:
            rate += 0.06
        if "printing" in know:
            rate += 0.22
        made = 0
        for b in self.books:
            if rng.random() < rate:
                b.copies += 1
                made += 1
        return made

    def burn(self, rng, n=1):
        """الحرق يمحو قرونًا. ما كثرت نسخُه نجا."""
        gone = []
        for _ in range(n):
            live = [b for b in self.books if b.copies > 0]
            if not live:
                break
            # الأقلّ نسخًا أسهل محوًا
            live.sort(key=lambda b: b.copies)
            b = live[0] if rng.random() < 0.6 else rng.choice(live)
            b.copies -= 1
            b.burned += 1
            if b.copies <= 0:
                gone.append(b)
                self.books.remove(b)
                self.burned_total += 1
        return gone

    def decay(self, rng):
        """الرقّ يبلى، والحبر يبهت، ومن لا يُنسخ يضيع."""
        for b in list(self.books):
            if rng.random() < 0.004 * b.copies ** -0.5:
                b.copies -= 1
                if b.copies <= 0:
                    self.books.remove(b)

    def holds_period(self):
        for b in self.books:
            if b.period:
                return b.period
        return None


# ---------------------------------------------------------------- التأليف
def can_write(a, know):
    return ("writing" in know and a.age >= 20
            and a.eg.t[G.REASONING] > 0.5 and len(a.concepts) >= 1)


class School:
    """
    مدرسةٌ فكرية: **جوابٌ بعينه على مسألةٍ بعينها**.

    ليست حزبًا ولا قبيلة. المسألةُ مفهومٌ صاغه أحدُهم، والجوابُ جهةُ
    اقترانه عنده: مُثبِتٌ أنّ هذا يجرّ ذاك، أو نافٍ. ولا تقوم مدرسةٌ
    حيث لا مسألة، ولا ينشقّ أحدٌ إلا عن جوابٍ يخالف جوابَه.
    """

    __slots__ = ("id", "name", "topic", "label", "sign", "stance", "born",
                 "home", "parent", "founder")

    def __init__(self, sid, name, topic, sign, stance, born, home,
                 parent=-1, founder="", label=""):
        self.id = sid
        self.name = name
        self.topic = topic        # هويّة الفكرة: مَن صاغها ومتى
        self.label = label or topic   # واسمُها كما يُنطق
        self.sign = sign
        self.stance = stance
        self.born = born
        self.home = home
        self.parent = parent          # المدرسة التي انشُقّ عنها
        self.founder = founder


def opposes(s1, s2):
    """مدرستان متناقضتان: جوابان مختلفان عن المسألة نفسها."""
    if s1 is None or s2 is None or s1.id == s2.id:
        return False
    if s1.topic == s2.topic and s1.sign != s2.sign:
        return True
    return (s1.stance, s2.stance) in _OPPOSED


def write_treatise(a, st, sim, rng):
    """
    يجمع الرجل ما تفرّق من مفاهيمه وقواعده في بناءٍ واحد له أطروحة.
    هذا هو الفرق بين أن تكون لك آراء وأن تكون لك **منهج**.
    """
    if not can_write(a, st.knowledge):
        return None
    lib = st.library
    # **عمّا يكتب المرء؟**
    #
    # كان يُختار أرسخُ ما عنده (شاهدًا × قوّةَ اقتران). وذلك يقطع
    # الخلاف من أصله: الفكرةُ التي انقلب فيها رأيُه حديثًا اقترانُها
    # قريبٌ من الصفر — لأنها لتوّها عبرت الصفر — فلا تُختار أبدًا.
    # فلا يكتب أحدٌ إلا فيما هو موقنٌ به، ولا يُكتب ردٌّ على أحد.
    #
    # والناس يكتبون ما اضطربوا فيه لا ما اطمأنّوا إليه. فمن انقلب
    # حكمُه كتب في ذلك قبل غيره — وهذا وحده ما يجعل الرسالة تقع
    # **ضدّ** رسالةٍ قبلها.
    strongest = None
    if a.recanted is not None and a.recanted in a.concepts:
        strongest = a.recanted
        a.recanted = None
    if strongest is None:
        strongest = max(a.concepts, key=lambda c: c.evidence * abs(c.value))
    topic = strongest.key()          # لا اسمُه — هويّتُه عبر الأذهان
    sign = 1 if strongest.value > 0 else -1

    # لا يكتب المرءُ الشيءَ مرّتين. لكنه **يكتب ثانيةً إذا تبدّل رأيه** —
    # وهذا هو الشرط الوحيد الذي يستحقّ رسالةً جديدة.
    mine = [b for b in lib.books
            if b.author == a.id and b.kind == KIND_TREATISE]
    if any(b.topic == topic and b.sign == sign for b in mine):
        return None
    if len(mine) >= 3:
        return None

    from .speech import thesis as _thesis
    th, prov = _thesis(a, st, sim.world, sim.agents, rng, sim.year, strongest)
    stn = stance_of(a)
    W = sim.world

    # ------------------------------------------------------- أصل المدرسة
    #
    # المدرسة لا تُرقَّم، تُولَد — ومولدها من **جواب**.
    #   وافق جوابُه جوابًا قائمًا فانتسب إليه ولم يؤسّس شيئًا؛
    #   خالف جوابًا قائمًا في المسألة نفسها فانشقّ وأسّس ضدَّه؛
    #   جاء بمسألةٍ لم يسبق إليها أحد فأسّس بلا خصم.
    #
    # ولهذا لا يقع الانشقاق حيث لا خلاف، ولا يكون التأليفُ وحده تأسيسًا.
    same = opp = None
    for b in lib.books:
        if b.kind != KIND_TREATISE or b.school < 0:
            continue
        s = W.schools.get(b.school)
        if s is None or s.topic != topic:
            continue
        if s.sign == sign and same is None:
            same = s
        elif s.sign != sign and opp is None:
            opp = (s, b)

    parent, split = -1, None
    if same is not None:
        school = same.id
    else:
        school = len(W.schools)
        if opp is not None:
            parent, split = opp[0].id, opp[0].name
        nm = (f"{'مُثبتة' if sign > 0 else 'نافية'} {strongest.name}"
              if opp is not None else f"أهل {strongest.name}")
        W.schools[school] = School(school, nm, topic, sign, stn,
                                   sim.year, st.name, parent, a.name,
                                   label=strongest.name)

    title = f"{'كتاب' if rng.random() < 0.5 else 'رسالة'} {strongest.name}"
    b = Book(KIND_TREATISE, title, a.id, a.name, sim.year,
             [c for c in a.concepts],
             [m for m in a.prog.maxims[:8]],
             th,
             period=st.known_period if a.heretic else None,
             school=school, parent=(opp[1].id if opp else -1), stance=stn,
             topic=topic, sign=sign)
    b.topic_name = strongest.name
    b.split = split
    lib.add(b)
    return b


def write_tables(a, st, sim, rng):
    """زيجٌ يُدوَّن فيه ما رُصد. لا رأي فيه — أرقامٌ تُقارَن بعد قرون."""
    if "calendar" not in st.knowledge or a.observations < 8:
        return None
    lib = st.library
    if any(b.kind == KIND_TABLES and b.author == a.id for b in lib.books):
        return None
    b = Book(KIND_TABLES, f"زِيج {a.name}", a.id, a.name, sim.year,
             [], [], "ما رُصد من مواقيت", period=st.known_period)
    lib.add(b)
    return b


# ---------------------------------------------------------------- القراءة
def read(a, st, rng, sim):
    """
    قراءةُ كتابٍ لمن مات كاتبه. من هنا يعبر الفهم الأجيال.
    وليس كل قارئٍ يفهم: الفهم دالّة في استدلاله وفي بُعد ما قرأ عمّا يعرف.
    """
    from .concept import Concept, MAX_CONCEPTS, transplant
    from .lang import mutate_maxim
    from .mind import NA
    lib = st.library
    if not lib.books or "writing" not in st.knowledge:
        return None
    b = rng.choice(lib.books)
    grasp = (0.15 + a.eg.t[G.REASONING] * 0.9) * (0.4 + a.eg.t[G.OPENNESS])
    if rng.random() > grasp:
        return None
    b.read_by += 1
    got = []

    for c in list(b.concepts):
        if len(a.concepts) >= MAX_CONCEPTS:
            break
        if transplant(c, b.concepts, a, rng) is not None:
            got.append("مفهوم")

    for m in b.maxims[:3]:
        if len(a.prog.maxims) >= 14:
            break
        a.prog.maxims.append(mutate_maxim(m, rng, 0.05))
        got.append("قاعدة")

    # والأثمن: الرقم الذي كشفه ميّت
    if b.period and not a.heretic:
        if a.eg.t[G.REASONING] > 0.55 and rng.random() < 0.45:
            a.heretic = True
            a.doubt = 1.0
            a.faith = max(0.0, a.faith - 0.7)
            a.conv["wrath_is_sin"] = 0.0
            a.title = "المُنكِر"
            if st.known_period is None:
                st.known_period = b.period
            got.append("الدورة")
    return (b, got) if got else None


# ---------------------------------------------------------------- المدارس
STANCES = ("مُنكِر", "كاهن", "زاهد", "عامّ")


def stance_of(a):
    if a.heretic:
        return "مُنكِر"
    if a.stance == "denial":
        return "زاهد"
    if a.clergy:
        return "كاهن"
    return "عامّ"


# ما يناقض ما. الإنكار والكهانة نقيضان، والزهد يخالف العامّة في الغاية
# لا في الأصل — فخلافه أخفّ.
_OPPOSED = {("مُنكِر", "كاهن"), ("كاهن", "مُنكِر"),
            ("زاهد", "كاهن"), ("كاهن", "زاهد")}


def contradicts(b1, b2):
    if b1.school == b2.school:
        return False
    return (b1.stance, b2.stance) in _OPPOSED


def debate(a, b, world, rng):
    """
    لقاءُ رجلين من مدرستين متناقضتين.

    لا يغلب الأصدقُ بل الأرفع مقامًا والأقوى حجّةً — وهذا ليس تشاؤمًا،
    هو ما يُرصد. ومن غُلب لم يقتنع دائمًا: قد ينصرف حانقًا فيشتدّ
    تمسّكه، وهو ما يُسمّى ارتداد النتيجة.
    """
    from . import genome as G
    sa, sb = world.schools.get(a.school), world.schools.get(b.school)
    if not opposes(sa, sb):
        return None
    wa = (0.4 + a.eg.t[G.REASONING]) * (0.5 + a.prestige / 4.0) \
        * (0.6 + a.eg.t[G.EXTRAVERSION])
    wb = (0.4 + b.eg.t[G.REASONING]) * (0.5 + b.prestige / 4.0) \
        * (0.6 + b.eg.t[G.EXTRAVERSION])
    win, lose = (a, b) if wa * rng.gauss(1.0, 0.3) > wb else (b, a)

    # ومن كان استثماره في مدرسته عظيمًا لم يتركها وإن غُلب
    hold = 0.25 + 0.5 * lose.eg.t[G.CREDULITY] + 0.3 * min(1.0, lose.prestige / 5.0)
    if rng.random() > hold:
        lose.school = win.school
        lose.bonds.bump(lose.bonds.trust, win.id, 0.25)
        return ("تحوّل", win, lose)
    lose.bonds.bump(lose.bonds.resentment, win.id, 0.45)
    win.bonds.bump(win.bonds.resentment, lose.id, 0.20)
    return ("تصلّب", win, lose)


def schools_in(st, agents):
    from collections import Counter
    c = Counter()
    for m in st.members:
        x = agents.get(m)
        if x is not None and x.school >= 0:
            c[x.school] += 1
    return c


def persuaded(a, bk, world, rng):
    """
    هل يتّبع القارئُ ما قرأ؟

    من كان له في المسألة جوابٌ يخالف ما في الكتاب لم يتركه لأنه قرأه —
    يحتاج أن يُهزم رأيُه، وذلك يحتاج عقلًا يزن (لا تصديقًا يقبل كل
    شيء، فالتصديق يشدّ صاحبَه إلى ما هو عليه بقدر ما يجرّه إلى غيره).
    ومن لا جواب له عنده يميل مع أوّل ما قرأ.
    """
    from . import genome as G
    s = world.schools.get(bk.school)
    if s is None:
        return False
    his = world.schools.get(a.school)
    if his is not None and his.id == s.id:
        return False
    if opposes(his, s):
        p = 0.04 + 0.24 * a.eg.t[G.REASONING] * a.eg.t[G.OPENNESS]
    elif his is None:
        p = 0.42 + 0.30 * a.eg.t[G.CREDULITY]
    else:
        p = 0.14 + 0.26 * a.eg.t[G.CREDULITY]
    # ومن وافق موقفُه موقفَ الكاتب في الدين مال إليه في المسألة أيضًا
    if stance_of(a) == bk.stance:
        p += 0.12
    return rng.random() < p


def taught_school(giver, taker, idea, world, rng):
    """
    المذهب يُورَّث بالتلقين لا بالكتاب وحده.

    كان الانتساب لا يقع إلا بقراءة رسالة، والقراءة نادرة: فبقيت المدارس
    أفرادًا، وسيطُ أتباعها **واحد**، فلا يلتقي في قريةٍ رجلان على
    مسألةٍ ليختلفا فيها — ولذلك لم تقع مناظرةٌ واحدة في ثلاثة آلاف سنة.

    وليس هكذا تنتشر المذاهب: تنتشر بأن يأخذ التلميذُ عن شيخه الفكرةَ
    **وحكمَه فيها معًا**. فمن لُقِّن «كذا يجرّ كذا» لُقِّن معها أنّ
    القول قولُ فلان، فصار من أهله وإن لم يقرأ سطرًا.

    والمخالِف لا يترك مذهبه لتلقين — يحتاج حجّةً تُهزَم بها حجّتُه.
    """
    from . import genome as G
    if giver.school < 0 or taker.school == giver.school:
        return False
    s = world.schools.get(giver.school)
    if s is None or s.topic != idea.key():
        return False                      # يلقّنه في مسألته لا في غيرها
    his = world.schools.get(taker.school)
    if opposes(his, s):
        return False
    p = 0.30 + 0.35 * taker.eg.t[G.CREDULITY] + 0.25 * taker.bonds.feel(giver.id)
    if taker.school < 0:
        p += 0.20
    if rng.random() >= min(0.92, p):
        return False
    taker.school = giver.school
    return True



KIND_HERBAL = "عقّار"


def write_herbal(a, st, sim, rng):
    """
    يدوّن المداوي ما جرّب. ومن هنا يعبر الطبُّ الأجيال — لا من الأفواه
    وحدها، لأن الفم ينسى والصدر يموت.

    ويُكتب **ما وثق به** لا ما صحّ: فتُخلَّد الخرافة كما يُخلَّد الصواب،
    وتُقرأ بعد قرنٍ فيُعمل بها. وهذا ما وقع في كتب العقاقير كلها.
    """
    if "writing" not in st.knowledge or len(a.remedies) < 3:
        return None
    lib = st.library
    if any(b.kind == KIND_HERBAL and b.author == a.id for b in lib.books):
        return None
    good = [r for r in a.remedies if r.trust() > 0.2]
    if len(good) < 2:
        return None
    good.sort(key=lambda r: r.trust(), reverse=True)
    lines = "؛ ".join(
        f"لِـ{sim.mal_signs[r.sign]}: {sim.plants[r.plant].name} "
        f"{r.prep} بمقدار {r.dose:.1f}" for r in good[:5])
    b = Book(KIND_HERBAL, f"عقّار {a.name}", a.id, a.name, sim.year,
             [], [], lines)
    b.recipes = [(r.plant, r.sign, r.prep, r.dose,
                  r.good, r.bad, r.dead) for r in good[:6]]
    lib.add(b)
    return b
