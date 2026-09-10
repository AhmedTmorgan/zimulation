"""
الذاكرة.

كل أثر يحمل حقلًا اسمه `truth`. هذا الحقل موجود من أجل المراقب فقط:
لا توجد دالة واحدة في هذا الملف تسمح للكائن بقراءته أو بالتصرّف بناءً عليه.
الكائن يتعامل مع الأثر الملفّق بنفس الطريقة تمامًا التي يتعامل بها مع المعاش.

مصادر الأثر خمسة: معاش، مزروع (وُضع فيه قبل أن يبدأ)، مسموع (حكاية الغير
التُقطت كتجربة ذاتية)، محلوم، ومُختلَق (سدّ فجوة أثناء الاسترجاع).
"""

KINDS = (
    "hunger", "feast", "birth", "death", "love", "betrayal", "violence",
    "reconcile", "wonder", "vision", "journey", "craft", "teaching",
    "plague", "ritual",
)
NK = len(KINDS)
(
    K_HUNGER, K_FEAST, K_BIRTH, K_DEATH, K_LOVE, K_BETRAYAL, K_VIOLENCE,
    K_RECONCILE, K_WONDER, K_VISION, K_JOURNEY, K_CRAFT, K_TEACHING,
    K_PLAGUE, K_RITUAL,
) = range(NK)

AR_KINDS = {
    "hunger": "جوع", "feast": "وليمة", "birth": "ولادة", "death": "موت",
    "love": "حبّ", "betrayal": "خيانة", "violence": "عنف", "reconcile": "مصالحة",
    "wonder": "دهشة", "vision": "رؤيا", "journey": "رحلة", "craft": "صنعة",
    "teaching": "تعليم", "plague": "وباء", "ritual": "طقس",
}

SOURCES = ("lived", "implanted", "told", "dreamt", "confabulated")
S_LIVED, S_IMPLANT, S_TOLD, S_DREAM, S_CONFAB = range(5)
AR_SOURCES = {
    "lived": "معاش", "implanted": "مزروع", "told": "مسموع",
    "dreamt": "محلوم", "confabulated": "مُختلَق",
}

# الأنواع التي تنزع للطابع المهيب — تقاوم التلاشي وتغذّي الأسطورة
NUMINOUS = (K_VISION, K_WONDER, K_RITUAL)


class Trace:
    __slots__ = ("kind", "year", "who", "val", "strength", "truth", "src", "tag",
                 "repressed", "buried")

    def __init__(self, kind, year, who, val, strength, truth, src, tag):
        self.kind = kind
        self.year = year
        self.who = who          # معرّف كائن آخر، أو -1
        self.val = val          # قيمة وجدانية [-1, 1]
        self.strength = strength
        self.truth = truth      # 1 حقيقي، 0 ملفّق — للمراقب فقط
        self.src = src
        self.tag = tag
        self.repressed = False   # مدفون: يغيب عن الاسترجاع ويبقى فاعلًا
        self.buried = 0.0        # قوّته يوم دُفن، ليعود بها


class MemoryBank:
    __slots__ = ("traces", "cap", "fidelity", "raw")

    def __init__(self, cap, fidelity):
        self.traces = []
        # ما عيشَ حديثًا ولم يُستخلص منه درسٌ بعد.
        #
        # كان العقل لا يتعلّم إلا من الكدح — لأن الكدح وحده كان يُسجَّل
        # موقفًا يُقاس عليه. فكانت كل مفاهيمهم من جنسٍ واحد: «هذان
        # يجتمعان فيأتي الخير»، وليس فيهم من صاغ «هذان يجتمعان فيأتي
        # الشرّ» ولا مرّة في ثلاثمئة مفهوم. فلا خوفَ مُصاغ ولا محرَّم
        # مُستنبَط ولا خلافَ ممكن — إذ لا يختلف اثنان وكلاهما يُثبت.
        #
        # فصار كلُّ ما يُعاش يمرّ من هنا: الشجارُ والمهانةُ والمرضُ
        # وفقدُ الولد كما الحصاد. والدرسُ يُستخلص بعدها بحول.
        self.raw = []
        self.cap = cap
        self.fidelity = fidelity   # 0..1 — ترفعها صفة الذاكرة وتقنية الكتابة

    # ---------------------------------------------------------------- تخزين
    def store(self, kind, year, who=-1, val=0.0, strength=1.0,
              truth=1.0, src=S_LIVED, tag=""):
        v = -1.0 if val < -1.0 else (1.0 if val > 1.0 else val)
        t = Trace(kind, year, who, v, strength, truth, src, tag)
        self.traces.append(t)
        if src == S_LIVED and len(self.raw) < 10:
            self.raw.append(t)
        if len(self.traces) > self.cap + 12:
            self._prune()
        return t

    def _prune(self):
        self.traces.sort(key=lambda t: t.strength, reverse=True)
        # ما يسقط يُصفَّر، كي يعرف العقل أن ما كان يتعلّم منه لم يعد موجودًا
        for t in self.traces[self.cap:]:
            t.strength = 0.0
        del self.traces[self.cap:]

    # ---------------------------------------------------------------- تلاشٍ
    def age(self, decay_base, numinous_bonus):
        keep = []
        ap = keep.append
        for t in self.traces:
            # الشدّة الوجدانية تحمي، والمهيب يُحمى أكثر
            if t.repressed:
                continue         # المدفون لا يتلاشى — لذلك يعود كما كان
            protect = 0.35 * abs(t.val) + (numinous_bonus * 8 if t.kind in NUMINOUS else 0.0)
            d = decay_base * (1.35 - self.fidelity) * (1.0 - min(0.8, protect))
            t.strength *= (1.0 - d)
            if t.strength > 0.06:
                ap(t)
            else:
                t.strength = 0.0
        self.traces = keep
        if len(self.traces) > self.cap:
            self._prune()

    # ------------------------------------------------------------ استرجاع
    def recall(self, rng, year, kind=None, tag=None, who=None, k=4, confab_rate=0.0):
        out = []
        for t in self.traces:
            if t.repressed:          # المدفون لا يُستدعى
                continue
            if kind is not None and t.kind != kind:
                continue
            if tag and t.tag != tag:
                continue
            if who is not None and t.who != who:
                continue
            out.append(t)
        out.sort(key=lambda t: t.strength, reverse=True)
        out = out[:k]
        for t in out:
            t.strength = min(2.2, t.strength * 1.05)   # الاسترجاع يثبّت

        # الفجوة تُسدّ باختلاق، والكائن لا يعلم أنه اختلق
        if confab_rate and len(self.traces) >= 4 and rng.random() < confab_rate * (1.3 - self.fidelity):
            a = rng.choice(self.traces)
            b = rng.choice(self.traces)
            new = self.store(
                kind if kind is not None else a.kind, year,
                who=a.who if rng.random() < 0.5 else b.who,
                val=0.6 * (a.val + b.val),
                strength=0.85 * max(a.strength, b.strength),
                truth=0.0, src=S_CONFAB, tag=(a.tag or b.tag),
            )
            out.append(new)
        return out

    def dream(self, rng, year, store_rate):
        """النوم يعيد تركيب الشظايا. أحيانًا يخرج التركيب من النوم كذكرى."""
        if len(self.traces) < 3:
            return None
        a = rng.choice(self.traces)
        b = rng.choice(self.traces)
        if rng.random() >= store_rate:
            return None
        kind = K_VISION if rng.random() < 0.42 else (a.kind if rng.random() < 0.5 else b.kind)
        val = 0.5 * (a.val + b.val) + rng.gauss(0.0, 0.35)
        return self.store(kind, year, who=a.who, val=val,
                          strength=0.75 + 0.5 * abs(val), truth=0.0,
                          src=S_DREAM, tag="رؤيا" if kind == K_VISION else (a.tag or b.tag))

    # -------------------------------------------------------------- قياسات
    def felt(self, kind):
        """شدّة ما يتذكّره من نوعٍ ما — لا ما وقع له."""
        s = 0.0
        for t in self.traces:
            if t.kind == kind:
                s += t.strength * abs(t.val)
        return s

    def signed(self, kind):
        s = 0.0
        for t in self.traces:
            if t.kind == kind:
                s += t.strength * t.val
        return s

    def attitude(self, who):
        s = 0.0
        n = 0.0
        for t in self.traces:
            if t.who == who:
                s += t.strength * t.val
                n += t.strength
        return s / n if n > 0.001 else 0.0

    def awe(self):
        s = 0.0
        for t in self.traces:
            if t.kind in NUMINOUS:
                s += t.strength * max(0.0, t.val)
        return min(1.0, s * 0.28)

    def numinous(self):
        """
        أقوى ما يتذكّره من المهيب. لا يسأل: أوقع هذا أم لم يقع؟ — إذ لا
        سبيل له إلى السؤال. وإنما تنزع الذكريات المهيبة إلى البقاء، وأكثرُها
        بقاءً في الغالب ما زُرع فيه أو حلمه، فتخرج الأسطورة من هناك بلا
        أن يعلم أحد لماذا.
        """
        best = None
        for t in self.traces:
            if t.repressed or t.kind not in NUMINOUS or t.val <= 0.0:
                continue
            if best is None or t.strength * t.val > best.strength * best.val:
                best = t
        return best

    def strongest_false(self):
        """للمراقب وحده: أقوى ما يتذكّره ولم يقع."""
        best = None
        for t in self.traces:
            if t.truth < 0.5 and t.val > 0.0:
                if best is None or t.strength > best.strength:
                    best = t
        return best

    # ------------------------------------------------------ مقاييس المراقب
    def truthfulness(self):
        w = sum(t.strength for t in self.traces)
        if w < 1e-6:
            return 1.0
        return sum(t.strength * t.truth for t in self.traces) / w

    def source_mix(self):
        m = [0.0] * 5
        for t in self.traces:
            m[t.src] += t.strength
        tot = sum(m) or 1.0
        return [x / tot for x in m]
