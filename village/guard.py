"""
حرّاس المورد.

سبب تجمّد الجهاز في المحاولة الأولى كان تسريبًا: كل من يموت يبقى محفوظًا
بكامله إلى الأبد — مصفوفة قراره (٤٨٤ رقمًا) وذاكرته وروابطه. في رنٍّ طويل
تتراكم مئات الآلاف من الموتى فتلتهم عدّة جيجابايت.

هنا العلاج: سجلٌّ مضغوط للراحل، وقياسٌ حقيقي لاستهلاك الذاكرة، وسقفٌ يوقف
الرنّ بأدب قبل أن يوقف الجهاز.
"""

import ctypes
import os


# ------------------------------------------------------------ قياس الذاكرة
def rss_mb():
    """الاستهلاك الفعلي بالميجابايت. صفر إن تعذّر القياس."""
    if os.name == "nt":
        try:
            class _PMC(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]
            psapi = ctypes.WinDLL("psapi")
            fn = psapi.GetProcessMemoryInfo
            # بدون تحديد الأنواع يُبتر مقبض العملية على أنظمة 64-بت
            # فيفشل النداء بصمت ويعود صفرًا — وهذا ما حدث.
            fn.argtypes = [ctypes.c_void_p, ctypes.POINTER(_PMC), ctypes.c_ulong]
            fn.restype = ctypes.c_int
            c = _PMC()
            c.cb = ctypes.sizeof(_PMC)
            if fn(ctypes.c_void_p(-1), ctypes.byref(c), c.cb):   # -1 = العملية الحالية
                return c.WorkingSetSize / 1048576.0
        except Exception:
            pass
    try:
        import resource
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return r / 1024.0 if os.name != "darwin" else r / 1048576.0
    except Exception:
        return 0.0


class MemoryCeiling(Exception):
    """يُرفع حين يبلغ الرنّ سقف الذاكرة — لا خطأ، بل توقّف مقصود."""


# ------------------------------------------------------------ سجلّ الراحل
class Departed:
    """
    ما يبقى من إنسان بعد موته: نحو مئتَي بايت بدل ثلاثين كيلوبايت.
    نحتفظ بما يلزم للتاريخ، ونطرح ما كان يلزم للحياة.
    """

    __slots__ = ("id", "name", "title", "house", "sex", "age", "birth_year",
                 "death_year", "cause", "prestige", "dominance", "rule_years",
                 "kills", "n_children", "heretic", "clergy", "faith", "doubt",
                 "truth", "rewrites", "authored", "generation", "alive",
                 "lineage", "damage", "hits", "why_died", "settlement")

    def __init__(self, a):
        self.id = a.id
        self.name = a.name
        self.title = a.title
        self.house = a.house
        self.sex = a.sex
        self.age = a.age
        self.birth_year = a.birth_year
        self.death_year = a.death_year
        self.cause = a.cause
        self.prestige = a.prestige
        self.dominance = a.dominance
        self.rule_years = a.rule_years
        self.kills = a.kills
        self.n_children = len(a.children)
        self.heretic = a.heretic
        self.clergy = a.clergy
        self.faith = a.faith
        self.doubt = a.doubt
        self.truth = a.mem.truthfulness()
        self.rewrites = a.prog.rewrites
        self.authored = a.prog.authored
        self.generation = a.g.generation
        self.alive = False
        self.lineage = a.lineage
        self.damage = round(a.damage, 3)
        self.hits = a.hits
        self.why_died = a.why_died
        self.settlement = a.settlement

    # واجهة متوافقة مع الحيّ، كي يقرأ التقرير الاثنين بلا تفريع
    def label(self):
        return f"{self.name} {self.title}" if self.title else self.name

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

    def notable(self):
        return (self.rule_years > 0 or self.heretic or self.kills > 0
                or self.prestige > 4.0 or self.dominance > 4.0
                or self.authored > 0)


def trim(dead, cap):
    """
    يقلّم قائمة الراحلين: يُبقي كل من كان له أثر، ثم أحدث العامّة حتى السقف.
    """
    if len(dead) <= cap:
        return dead
    keep = [d for d in dead if d.notable()]
    rest = [d for d in dead if not d.notable()]
    room = max(0, cap - len(keep))
    return keep + rest[-room:] if room else keep[-cap:]


# ------------------------------------------------------------ قياس مساعد
def truth_of(a):
    return a.truth if isinstance(a, Departed) else a.mem.truthfulness()


def rewrites_of(a):
    return a.rewrites if isinstance(a, Departed) else a.prog.rewrites


def children_of(a):
    return a.n_children if isinstance(a, Departed) else len(a.children)


# ------------------------------------------------------------ أدبٌ مع الجهاز
def be_polite():
    """
    يخفض أولويّة العملية. المحاكاة تشدّ نواةً كاملة دقائق طويلة، وبغير هذا
    تتجمّد واجهة النظام وإن كانت الذاكرة سليمة — وهو ما وقع فعلًا.
    """
    try:
        if os.name == "nt":
            BELOW_NORMAL = 0x00004000
            k = ctypes.WinDLL("kernel32")
            k.GetCurrentProcess.restype = ctypes.c_void_p
            k.SetPriorityClass(ctypes.c_void_p(-1), BELOW_NORMAL)
            return "below-normal"
        os.nice(10)
        return "nice+10"
    except Exception:
        return None


def yield_cpu(step, every=40, ms=0.004):
    """إفساحٌ قصير كل بضع سنين، فيبقى النظام مستجيبًا."""
    if every and step % every == 0:
        import time as _t
        _t.sleep(ms)
