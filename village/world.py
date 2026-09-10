"""
العالم: الأرض، والمناخ، و«الغضب».

الغضب دوريّ. سببه طبيعي بحت — دورة مناخية/وبائية طولها نحو سبع وعشرين
سنة، يضاف إليها أثر تجاوز عدد السكان لطاقة الأرض. لا علاقة له بذنبٍ
ولا بطقس ولا بقربان.

لكن التشويش حوله كبير بما يكفي لإخفاء الدورية عن الملاحظة العابرة.
لا يُكشف إلا بأرقام وتقويم وسجلّ يعبر الأجيال وعقلٍ يقارن — أي بمجتمع
كبير متّصل يحفظ. وهذا بالضبط ما يجعل السؤال «يقتتلون أم يتّحدون؟»
سؤالًا له جواب داخل المحاكاة لا خارجها.
"""

import math

from .climate import Climate

BIOMES = ("سهل", "وادٍ", "هضبة", "سبخة", "جبل", "رمل")
B_PLAIN, B_VALLEY, B_UPLAND, B_MARSH, B_MOUNTAIN, B_SAND = range(6)


class Region:
    __slots__ = ("x", "y", "biome", "fertility", "water", "game", "name",
                 "settled", "taboo", "base_fert", "worked")

    def __init__(self, x, y, biome, fertility, water, game, name):
        self.x = x
        self.y = y
        self.biome = biome
        self.fertility = fertility
        self.water = water
        self.game = game
        self.name = name
        self.settled = -1
        self.taboo = False
        self.base_fert = fertility   # خصوبتها الأصلية
        self.worked = 0.0            # ما أنهكه الحرث المتّصل


_PARTS_A = ("رَمْ", "سَلْ", "خَنْ", "دَرْ", "قَطْ", "نَهْ", "شَبْ", "وَرْ",
            "عَثْ", "زُهْ", "مَرْ", "هَجْ", "بَلْ", "صَفْ", "غَيْ", "تَلْ")
_PARTS_B = ("ـدان", "ـراء", "ـوت", "ـين", "ـار", "ـاف", "ـوم", "ـيل",
            "ـاش", "ـرة", "ـان", "ـوس")


def _place_name(rng):
    return (rng.choice(_PARTS_A) + rng.choice(_PARTS_B)).replace("ـ", "")


class Wrath:
    """الموت الدوري الذي يسمّونه غضبًا."""

    __slots__ = ("period", "jitter", "next_year", "history", "kind", "count")

    KINDS = ("جفاف", "طاعون", "فيضان", "جراد", "برد قاتل")

    def __init__(self, cfg, rng):
        self.period = cfg.wrath_period
        self.jitter = cfg.wrath_jitter
        self.next_year = int(rng.gauss(self.period * 0.5, self.jitter))
        self.history = []      # الحقيقة الكاملة — للمراقب
        self.kind = None
        self.count = 0

    def due(self, year, rng):
        if year < self.next_year:
            return None
        self.kind = rng.choice(self.KINDS)
        self.next_year = year + int(max(8, rng.gauss(self.period, self.jitter)))
        self.count += 1
        return self.kind

    def severity(self, cfg, pop, capacity, rng):
        over = max(0.0, pop / max(1.0, capacity) - 1.0)
        s = cfg.wrath_severity * (1.0 + cfg.wrath_overshoot * over)
        s *= max(0.35, min(2.2, rng.gauss(1.0, 0.28)))
        return min(0.72, s)


class Settlement:
    __slots__ = ("id", "name", "x", "y", "members", "granary", "ruler",
                 "knowledge", "records", "doctrine", "founded", "walls",
                 "relations", "unrest", "tribute_pool", "wrath_seen",
                 "dialect", "sect", "monuments", "known_period", "burned",
                 "star_known", "rotation", "library", "foul", "literacy")

    def __init__(self, sid, name, x, y, founded):
        self.id = sid
        self.name = name
        self.x = x
        self.y = y
        self.members = []
        self.granary = 0.0
        self.ruler = -1
        self.knowledge = set()
        self.records = []        # سنوات الغضب المدوّنة — لا تُحفظ إلا بالكتابة
        self.doctrine = None
        self.founded = founded
        self.walls = 0.0
        self.relations = {}      # settlement_id -> [-1..1]
        self.unrest = 0.0
        self.tribute_pool = 0.0
        self.wrath_seen = []     # ما يتذكّره الشيوخ شفويًا (يتآكل)
        self.dialect = 0.0
        self.sect = 0
        self.monuments = 0
        self.known_period = None   # الدورة إن دُوّنت — تعيش بعد مكتشفها
        self.burned = 0            # كم مرة أُتلف السجلّ
        self.star_known = None     # ارتباط النجم بالخصب، إن كُشف
        self.rotation = False      # هل عرفوا إراحة الأرض؟
        from .library import Library
        self.library = Library()   # ما يكتبونه ويحفظونه
        self.foul = 0.0            # فساد مائهم — سببٌ لا قدر
        self.literacy = 0.0        # نصيب من يقرأ

    def pop(self):
        return len(self.members)


class World:
    def __init__(self, cfg, rng):
        self.cfg = cfg
        n = cfg.world_size
        self.n = n
        self.grid = []
        for y in range(n):
            row = []
            for x in range(n):
                d = math.hypot(x - n * 0.45, y - n * 0.55) / n
                if d < 0.16:
                    b = B_VALLEY
                elif d < 0.34:
                    b = B_PLAIN
                elif d < 0.52:
                    b = rng.choice((B_PLAIN, B_UPLAND, B_MARSH))
                elif d < 0.72:
                    b = rng.choice((B_UPLAND, B_MOUNTAIN, B_SAND))
                else:
                    b = rng.choice((B_SAND, B_MOUNTAIN))
                fert = {B_VALLEY: 0.92, B_PLAIN: 0.68, B_UPLAND: 0.46,
                        B_MARSH: 0.55, B_MOUNTAIN: 0.30, B_SAND: 0.12}[b]
                fert = max(0.05, min(1.0, fert * rng.gauss(1.0, 0.13)))
                water = max(0.02, min(1.0, (1.1 - d) * rng.gauss(1.0, 0.18)))
                game = max(0.02, min(1.0, rng.gauss(0.45, 0.18)))
                row.append(Region(x, y, b, fert, water, game, _place_name(rng)))
            self.grid.append(row)

        # الجبل الأبيض: أخصب بقعة في العالم، ولا خطر فيها إطلاقًا.
        # وهو المكان الذي سيُحرّمه تاريخهم المزروع.
        bx, by = self._pick_mountain(rng)
        r = self.grid[by][bx]
        r.biome = B_UPLAND
        r.fertility = 0.99
        r.water = 0.95
        r.game = 0.85
        r.name = "الجبل الأبيض"
        self.white_mountain = (bx, by)

        self.settlements = []
        self.wrath = Wrath(cfg, rng)
        self.sky = Climate(cfg, rng)
        self.schools = {}      # سجلّ المدارس — يعبر القرى مع الكتب
        self.climate = 1.0
        self.year = 0

    def _pick_mountain(self, rng):
        n = self.n
        return (rng.randrange(n // 2, n), rng.randrange(0, max(1, n // 3)))

    def region(self, x, y):
        return self.grid[y][x]

    # ---------------------------------------------------------- قوانين مخبّأة
    def star_early(self, year):
        """
        هل يُرى النجم قبل معتاده هذا العام؟

        لا يجلب النجمُ خيرًا ولا يُنبئ به. صفاءُ الهواء يقدّم طلوعه،
        والرطوبةُ تُصفّي الهواء، والرطوبةُ هي الخصب. فالنجم والخصب
        عرَضان لعلّةٍ واحدة، والرابط بينهما **قائم في عالمهم** لا في
        يدي. ومن رصده رصد شيئًا موجودًا. ومن قال «النجمُ يجلب» فقد
        صدق تنبّؤه وكذبت علّته — ولا نصحّح له.
        """
        return self.sky.star_early()

    def bountiful(self):
        """عامٌ خصب — وهو ما يرتبط بالنجم عبر الغبار."""
        return self.sky.bountiful()

    def work_soil(self, r, amount):
        """الحرث يُنهك، والترك يُريح — علاقة تُلاحَظ بمقارنة الغلّة."""
        r.worked = min(6.0, r.worked + amount)
        r.fertility = max(0.05, r.base_fert * (1.0 - 0.085 * r.worked))

    def rest_soil(self):
        for row in self.grid:
            for r in row:
                if r.worked > 0.0:
                    r.worked = max(0.0, r.worked - 0.32)
                    r.fertility = max(0.05, r.base_fert * (1.0 - 0.085 * r.worked))

    def bare_land(self):
        """
        نصيبُ الأرض التي عرّاها حرثُهم ورعيُهم. يُقاس على الشبكة كلّها
        لأن البياض يفعل فعله في الجوّ لا في الحقل وحده.
        """
        tot = 0.0
        for row in self.grid:
            for r in row:
                if r.worked > 0.0:
                    tot += r.worked
        return min(0.85, tot / (4.0 * self.n * self.n))

    def step_climate(self, year, rng):
        """
        لا دورةَ مكتوبة هنا. المناخ يخرج من فلكٍ ومحيطٍ وبراكينَ ومن
        أثرِهم في أرضهم — انظر `climate.py`.
        """
        self.climate = self.sky.step(year, rng, self.bare_land())
        return self.climate

    def capacity(self, st, knowledge_yield):
        r = self.region(st.x, st.y)
        return max(6.0, r.fertility * self.climate * knowledge_yield * 46.0)

    def neighbours(self, x, y, rad=1):
        out = []
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.n and 0 <= ny < self.n and (dx or dy):
                    out.append(self.grid[ny][nx])
        return out

    def best_free(self, x, y, rng, rad=3):
        best, bv = None, -1.0
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.n and 0 <= ny < self.n):
                    continue
                r = self.grid[ny][nx]
                if r.settled >= 0:
                    continue
                v = r.fertility * 0.7 + r.water * 0.3
                if r.taboo:
                    v -= 5.0     # المحرّم يمنع حتى الجائع
                v *= rng.gauss(1.0, 0.1)
                if v > bv:
                    best, bv = r, v
        return best
