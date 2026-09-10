"""
الأصول: لماذا سُمّي الشيء بما سُمّي.

لا شيء في حياة البشر بلا أصل. «أغسطس» رجلٌ حكم، و«سبتمبر» رقمٌ سبعةٌ في
تقويمٍ زُحزح فبقي الاسم وضاع المعنى، وموسمُ الفيضان عند المصريين عُلِّق
بشروق نجمٍ لاحظوه يسبقه.

فهنا: كل مسمّى يُسجَّل بمن سمّاه، وفي أي سنة، وعلى أي شيء، ولماذا.
ثم — وهذا هو المهمّ — يبقى الاسم ويُنسى سببه.

والأصل قد يكون كاذبًا: إن كان أقوى ما في ذاكرتهم الجمعية حدثًا لم يقع،
فقد يصير هو مبدأ تقويمهم. فيؤرّخون قرونًا من سنةٍ لم تكن.
"""

from .memory import AR_KINDS, KINDS

KIND_EPOCH = "مبدأ التقويم"
KIND_MONTH = "شهر"
KIND_STAR = "نجم"
KIND_FEAST = "موسم"
KIND_PLAGUE = "سقم"
KIND_LAW = "شريعة"
KIND_UNIT = "مكيال"


class Named:
    """مسمّى وأصله."""

    __slots__ = ("kind", "name", "year", "namer", "after", "why",
                 "origin_lost", "forms")

    def __init__(self, kind, name, year, namer, after, why):
        self.kind = kind
        self.name = name
        self.year = year
        self.namer = namer          # اسم من سمّاه
        self.after = after          # على أي شيء سُمّي
        self.why = why              # سببٌ من واقعهم، صادقًا كان أو كاذبًا
        self.origin_lost = False    # هل نُسي السبب؟
        self.forms = [(year, name)]  # كيف تغيّر نُطقه عبر القرون

    def drift_to(self, new, year):
        self.forms.append((year, new))
        self.name = new

    def tale(self):
        s = f"{self.kind} «{self.name}»"
        if self.origin_lost:
            s += f" — سُمّي سنة {self.year:,} ولم يعد أحد يعرف لماذا"
        else:
            s += f" — سمّاه {self.namer} سنة {self.year:,} على {self.after}؛ {self.why}"
        if len(self.forms) > 1:
            s += " (" + " ← ".join(f for _, f in self.forms) + ")"
        return s


# --------------------------------------------------------------- الاشتقاق
_SUF = ("ان", "ون", "ية", "ين", "ات", "ى", "اء", "وس", "ار", "يم")
_PRE = ("ذو ", "أبو ", "بيت ", "عين ", "رأس ")


def derive(source, rng):
    """يُشتقّ الاسم من مصدره كما تُشتقّ أسماء البشر: بقصٍّ وإلحاق."""
    s = source.strip()
    if not s:
        return None
    r = rng.random()
    if r < 0.30 and len(s) > 3:
        return s[:max(3, len(s) - 1)] + rng.choice(_SUF)
    if r < 0.50:
        return rng.choice(_PRE) + s
    if r < 0.70 and len(s) > 4:
        return s[: len(s) // 2 + 1] + rng.choice(_SUF)
    return s


# ------------------------------------------------------ الانجراف الصوتي
_SHIFT = (("ث", "ت"), ("ذ", "د"), ("ق", "ء"), ("ظ", "ض"), ("ة", "ه"),
          ("او", "و"), ("اي", "ي"), ("ّ", ""), ("ْ", ""))


def drift(name, rng):
    """قرنٌ يمرّ فيلين حرفٌ ويسقط آخر — كما تنجرف كل الألسنة."""
    out = name
    for a, b in _SHIFT:
        if a in out and rng.random() < 0.30:
            out = out.replace(a, b, 1)
    if len(out) > 4 and rng.random() < 0.18:
        i = rng.randrange(1, len(out) - 1)
        out = out[:i] + out[i + 1:]
    return out


class Registry:
    def __init__(self):
        self.items = []
        self.by_kind = {}

    def add(self, n):
        self.items.append(n)
        self.by_kind.setdefault(n.kind, []).append(n)
        return n

    def get(self, kind):
        return self.by_kind.get(kind, [])

    def age(self, year, rng, forget_after=250):
        """
        تمرّ القرون: يتغيّر النطق، ثم يُنسى السبب. الاسم يعيش أطول من معناه.
        """
        for n in self.items:
            if year - n.year > 60 and rng.random() < 0.012:
                d = drift(n.name, rng)
                if d and d != n.name:
                    n.drift_to(d, year)
            if not n.origin_lost and year - n.year > forget_after:
                if rng.random() < 0.02:
                    n.origin_lost = True


# ================================================== لحظات التسمية
def name_epoch(sim, st, rng):
    """
    مبدأ التقويم. يُعلَّق بأقوى ما في الذاكرة الجمعية — وقد لم يقع.
    """
    reg = sim.names
    if reg.get(KIND_EPOCH):
        return None
    # ما يجتمع الناس على تذكّره: أقوى الآثار عند أهل القرية
    tally = {}
    for m in st.members[:80]:
        a = sim.agents.get(m)
        if a is None:
            continue
        for t in a.mem.traces:
            if t.strength < 0.9:
                continue
            k = (t.kind, t.year // 20 * 20)
            e = tally.setdefault(k, [0.0, 0.0, 0])
            e[0] += t.strength
            e[1] += t.truth * t.strength
            e[2] += 1
    if not tally:
        return None
    (kind, yr), (w, tw, cnt) = max(tally.items(), key=lambda kv: kv[1][0])
    truth = tw / w if w else 1.0
    namer = sim.agents.get(st.ruler)
    namer = namer.name if namer else (sim.agents[st.members[0]].name
                                      if st.members else "مجهول")
    label = AR_KINDS[KINDS[kind]]
    n = Named(KIND_EPOCH, f"عام {label}", sim.year, namer,
              f"ما يتذكّره {cnt} منهم عن سنة {yr}",
              f"أقوى ما اجتمعت عليه ذاكرتهم" +
              ("" if truth > 0.5 else " — ولم يقع منه شيء"))
    sim.epoch_year = yr
    sim.epoch_true = truth
    reg.add(n)
    sim.chron.add(sim.year, "epoch",
                  f"جعلوا مبدأ تأريخهم «{n.name}» — {n.why}.", 4.5)
    return n


def name_months(sim, st, rng, count=12):
    """
    يقسمون السنة ويسمّون أقسامها. المصادر أربعة، كلها من واقعهم:
    حاكمٌ حيّ، وميتٌ يُذكَر، وموسمٌ لاحظوه، وأسطورةٌ يحملونها.
    """
    reg = sim.names
    if reg.get(KIND_MONTH):
        return []
    made = []
    pool = []

    ruler = sim.agents.get(st.ruler)
    if ruler is not None:
        pool.append((ruler.name, f"حاكمهم يوم قُسِّمت السنة", ruler.name))
    for d in sim.dead[-400:]:
        if d.rule_years > 3 or d.prestige > 4.0:
            pool.append((d.name, f"من حكم أو رُفع قدره ومات", d.name))
    d = st.doctrine
    if d is not None:
        pool.append((d.god, "إلههم", "الكهنة"))
        for t in list(d.tenets.values())[:6]:
            w = t.text.split()[0] if t.text else None
            if w and len(w) > 2:
                pool.append((w, "من عقيدتهم", "الكهنة"))
    for w in sim.world.wrath.history[-6:]:
        pool.append((w[1], f"ما وقع بهم سنة {w[0]}", "الشيوخ"))
    reg_star = reg.get(KIND_STAR)
    for s in reg_star:
        pool.append((s.name, "نجمٌ رصدوه", s.namer))

    if len(pool) < 3:
        return []
    rng.shuffle(pool)
    seen = set()
    i = 0
    while len(made) < count and i < len(pool) * 3:
        src, why, namer = pool[i % len(pool)]
        i += 1
        nm = derive(src, rng)
        if not nm or nm in seen:
            continue
        seen.add(nm)
        made.append(reg.add(Named(KIND_MONTH, nm, sim.year, namer, src, why)))
    if made:
        sim.chron.add(sim.year, "months",
                      "قسّموا السنة وسمّوا أقسامها: " +
                      "، ".join(m.name for m in made) + ".", 4.0)
    return made


def name_star(sim, a, st, sign, rng):
    """
    نجمٌ يُسمّى لأنه لوحظ يسبق شيئًا. إن صحّ الارتباط صار أداةَ تنبّؤ.
    """
    reg = sim.names
    base = a.name if rng.random() < 0.4 else (
        st.name if rng.random() < 0.5 else sign)
    nm = derive(base, rng) or base
    n = Named(KIND_STAR, nm, sim.year, a.name, base,
              f"لاحظ أنه يطلع قبل {sign}")
    reg.add(n)
    sim.chron.add(sim.year, "star",
                  f"سمّى {a.name} نجمًا «{nm}» لأنه رآه يطلع قبل {sign}.", 3.8)
    return n


def name_plague(sim, p, victim, st, rng):
    reg = sim.names
    src = victim.name if (victim is not None and rng.random() < 0.5) else st.name
    nm = derive(src, rng) or src
    n = Named(KIND_PLAGUE, nm, sim.year,
              victim.name if victim else "الناس", src,
              "أوّل من عُرف به" if victim else "المكان الذي ظهر فيه")
    reg.add(n)
    return n


def name_law(sim, ruler, st, rng):
    reg = sim.names
    nm = derive(ruler.name, rng) or ruler.name
    n = Named(KIND_LAW, nm, sim.year, ruler.name, ruler.name,
              f"من فرضها على أهل {st.name}")
    reg.add(n)
    sim.chron.add(sim.year, "law",
                  f"دُوّنت شريعة «{nm}» باسم {ruler.name}.", 3.5)
    return n


def name_feast(sim, a, st, myth_text, rng):
    reg = sim.names
    src = (myth_text.split()[-1] if myth_text else a.name)
    nm = derive(src, rng) or src
    n = Named(KIND_FEAST, nm, sim.year, a.name, src, "موسمٌ من حكايةٍ حملوها")
    reg.add(n)
    return n
