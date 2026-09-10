"""
الكائن.

جسد له جوع وإعياء ومرض، وذاكرة لا يعرف صدقها، ووجدان، وروابط،
وموقع في سُلّم، وكود يعيد كتابته. ويموت.
"""

from . import genome as G
from .emotion import Affect
from .memory import MemoryBank

MALE, FEMALE = 0, 1


class Bonds:
    """الروابط. الحبّ والكره يُخزَّنان منفصلين لأنهما يجتمعان في شخصٍ واحد."""

    __slots__ = ("affection", "resentment", "attraction", "trust",
                 "kin", "reared_with", "partner", "faction")

    def __init__(self):
        self.affection = {}
        self.resentment = {}
        self.attraction = {}
        self.trust = {}
        self.kin = set()          # أقارب الدم
        self.reared_with = set()  # من نشأ معه — يكبح الانجذاب (فسترمارك)
        self.partner = -1
        self.faction = -1

    def close_count(self):
        n = 0
        for v in self.affection.values():
            if v > 0.40:
                n += 1
        return n

    def feel(self, who):
        return self.affection.get(who, 0.0) - self.resentment.get(who, 0.0)

    def bump(self, d, who, amt, cap=3.0):
        v = d.get(who, 0.0) + amt
        d[who] = 0.0 if v < 0.0 else (cap if v > cap else v)

    def decay(self, bond_decay, grudge_decay, patience):
        for d, r in ((self.affection, bond_decay),
                     (self.attraction, bond_decay * 1.6),
                     (self.trust, bond_decay * 0.6)):
            dead = []
            for k in d:
                d[k] *= (1.0 - r)
                if d[k] < 0.03:
                    dead.append(k)
            for k in dead:
                del d[k]
        # التغاضي: الصبر يُذيب الضغينة أسرع
        gr = grudge_decay * (0.5 + patience)
        dead = []
        for k in self.resentment:
            self.resentment[k] *= (1.0 - gr)
            if self.resentment[k] < 0.03:
                dead.append(k)
        for k in dead:
            del self.resentment[k]

    def worst(self):
        best, bv = -1, 0.45
        for k, v in self.resentment.items():
            if v > bv:
                best, bv = k, v
        return best

    def dearest(self):
        best, bv = -1, 0.40
        for k, v in self.affection.items():
            if v > bv:
                best, bv = k, v
        return best


class Agent:
    __slots__ = (
        "id", "name", "house", "g", "eg", "prog", "mem", "af", "bonds",
        "sex", "age", "birth_year", "death_year", "alive", "cause",
        "hunger", "fatigue", "illness", "health", "kin_need",
        "pregnant", "pregnancy_by", "children", "mother", "father",
        "settlement", "prestige", "dominance", "power", "is_ruler", "rule_years",
        "faith", "doubt", "wrath_expectation", "clergy", "heretic",
        "conv", "riders",
        "skills", "immunity", "infection", "title", "backstory",
        "observations", "shift", "deeds", "last_action", "kills", "tribute",
        "fear_death", "fear_want", "fear_revolt", "despair", "lies", "caught",
        "said", "stance", "star_log", "longing", "knows", "lineage",
        "concepts", "intention", "damage", "hits", "why_died", "nursing",
        "school", "last_fs", "recanted", "sick", "remedies", "smelt", "inflam",
    )

    def __init__(self, aid, name, house, g, prog, sex, age, birth_year, cfg, rng):
        self.id = aid
        self.name = name
        self.house = house
        self.g = g
        self.eg = G.Genome(list(g.t), g.antigens, g.generation)  # الصفات المعبَّر عنها
        self.prog = prog
        self.mem = MemoryBank(cfg.memory_cap, 0.30 + 0.55 * g.t[G.RECALL])
        self.af = Affect()
        self.bonds = Bonds()

        self.sex = sex
        self.age = age
        self.birth_year = birth_year
        self.death_year = None
        self.alive = True
        self.cause = None

        self.hunger = 0.0
        self.fatigue = 0.0
        self.illness = 0.0
        self.health = 0.65 + 0.35 * g.t[G.VIGOR]
        self.kin_need = 0.0

        self.pregnant = 0          # شهور الحمل المتبقية (بوحدة سنوية جزئية)
        self.pregnancy_by = -1
        self.children = []
        self.mother = -1
        self.father = -1

        self.settlement = 0
        self.prestige = 0.0        # مكانة مكتسبة بالكفاءة — يُتبع طوعًا
        self.dominance = 0.0       # مكانة مأخوذة بالبطش — يُتبع خوفًا
        self.power = 0.0
        self.is_ruler = False
        self.rule_years = 0

        self.faith = 0.35 + 0.5 * g.t[G.CREDULITY]
        self.doubt = 0.0
        self.wrath_expectation = 0.0
        self.clergy = False
        self.heretic = False
        # القناعة فردية: لكلٍّ عقيدته هو، وتبريراته هو.
        # ما تراه القرية «عقيدةً» ليس إلا متوسطًا مرجّحًا لهذه القناعات.
        self.conv = {}
        self.riders = []

        self.skills = [0.0, 0.0, 0.0, 0.0]   # زرع، صنعة، قتال، رصد
        self.immunity = set(g.antigens)
        self.infection = None
        self.title = ""
        self.backstory = ""
        self.observations = 0.0
        self.shift = [0.0] * G.NT
        self.deeds = []
        self.last_action = -1
        self.kills = 0
        self.tribute = 0.0
        self.fear_death = 0.0
        self.fear_want = 0.0
        self.fear_revolt = 0.0
        self.despair = 0.0
        self.lies = 0            # ما قاله وهو يعلم أنه غير ما يعتقد
        self.caught = 0          # ما انكشف منه
        self.said = []           # أقوالٌ ألّفها بنفسه
        self.stance = None       # جوابه على العبث حين واجهه
        self.star_log = []       # ما رصده من (طلوع النجم، خصب العام)
        self.longing = 0.0       # حنينٌ إلى ما يتذكّره ولو لم يكن
        self.knows = 1.0         # ما يبلغه عن حال الناس — لا حالهم
        self.lineage = aid       # جدّه الأوّل من الجيل المؤسّس
        self.concepts = []       # سِماتٌ صنعها هو، لم تكن في قائمتي
        self.intention = None    # التزامٌ يقاوم دوافع اللحظة
        self.damage = 0.0        # أذًى تراكم فوق ما أُصلح
        self.hits = 0            # إصاباتٌ جسدية متراكمة
        self.why_died = ""       # سلسلة السبب، لا وسمٌ مجرّد
        self.nursing = 0.0       # ما بقي من إرضاعٍ يكبح الحمل
        self.school = -1         # مدرسته الفكرية إن انتسب
        self.last_fs = ()        # الموقف الذي كان فيه حين فعل
        self.recanted = None     # فكرةٌ انقلب حكمُه فيها ولمّا يكتب
        self.sick = []           # (رقم العلّة، ما بقي منها، ما سُقي)
        self.remedies = []       # ما يظنّ أنه دواء — لا ما هو دواء
        self.smelt = 0.0         # ما باشره من صهرٍ يسمّم صاحبَه
        self.inflam = 0.0        # التهابٌ مزمن — وهو وحده يُسرطن

    # ------------------------------------------------------------------
    def t(self, i):
        return self.eg.t[i]

    def apply_shift(self, i, amount):
        """
        انزياح في الصفة المعبَّر عنها لا الموروثة.
        هكذا تفعل السلطة فعلها: الجينوم ثابت، والسلوك يتغيّر.
        """
        self.shift[i] += amount
        v = self.g.t[i] + self.shift[i]
        self.eg.t[i] = 0.02 if v < 0.02 else (0.98 if v > 0.98 else v)

    def status(self):
        return self.prestige + self.dominance

    def adult(self, cfg):
        return self.age >= cfg.adult_age

    def fertile(self, cfg):
        if not self.alive or self.age < cfg.menarche:
            return False
        lim = cfg.fertile_until_f if self.sex == FEMALE else cfg.fertile_until_m
        return self.age <= lim

    def can_pair(self, other, cfg):
        """تجنّب المحارم: فسترمارك — من نشأت معه لا تشتهيه."""
        if other.id == self.id or other.sex == self.sex:
            return False
        if other.id in self.bonds.reared_with or other.id in self.bonds.kin:
            return False
        if other.mother != -1 and other.mother == self.mother:
            return False
        return self.fertile(cfg) and other.fertile(cfg)

    def label(self):
        if self.title:
            return f"{self.name} {self.title}"
        return self.name

    def creed(self):
        if self.heretic:
            return "مُنكِر"
        if self.clergy:
            return "كاهن"
        if self.faith > 0.7:
            return "مؤمن"
        if self.faith < 0.3:
            return "شاكّ"
        return "متردّد"
