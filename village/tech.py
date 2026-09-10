"""
المعرفة.

الابتكار هنا ليس عبقرية فرد، بل دالّة في حجم السكان الفعّال واتصالهم —
فرضية «الدماغ الجمعي» (Muthukrishna & Henrich). قرية من أربعة وثلاثين
إنسانًا لا تكتشف الكهرباء مهما بلغ ذكاء أفرادها: المعرفة تحتاج عددًا
يحملها وشبكة تنقلها وسجلًا يحفظها من الموت.

ولهذا السبب بالذات يصبح سؤال «يقتتلون أم يتّحدون؟» سؤالًا فيزيائيًا
داخل هذا العالم، لا سؤالًا أخلاقيًا.
"""

# key, اسم, متطلبات, أدنى عدد فعّال, أدنى رصيد معرفي, الأثر
TECHS = [
    ("fire",       "حفظ النار",        [],                              0,   0,  {"food": 0.06, "mort": -0.03}),
    ("cord",       "الحبل والسلّة",     [],                              0,   0,  {"food": 0.05}),
    ("stone",      "الأداة الحجرية",    [],                              0,   0,  {"food": 0.08, "leth": 0.05}),
    ("shelter",    "المأوى",           ["cord"],                        0,   1,  {"mort": -0.05, "cap": 0.06}),
    ("herding",    "الاستئناس",        ["cord", "stone"],               24,  2,  {"food": 0.16, "cap": 0.10}),
    ("farming",    "الزراعة",          ["stone", "fire"],               30,  2,  {"food": 0.42, "cap": 0.45}),
    ("pottery",    "الفخّار",           ["fire"],                        30,  3,  {"food": 0.08, "cap": 0.06}),
    ("granary",    "المخزن",           ["pottery", "farming"],          62,  5,  {"cap": 0.22, "buffer": 0.35}),
    ("weaving",    "النسيج",           ["cord"],                        56,  4,  {"mort": -0.04}),
    ("irrigation", "الرَّي",            ["farming"],                     98,  7,  {"food": 0.34, "cap": 0.35}),
    ("counting",   "الإحصاء",          ["granary"],                     84,  7,  {"insight": 0.20}),
    ("writing",    "الكتابة",          ["counting", "pottery"],         180,  10, {"fidelity": 0.30, "record": 1.0, "teach": 0.30}),
    ("copper",     "النحاس",           ["fire", "pottery"],             112,  10, {"food": 0.10, "leth": 0.10}),
    ("wheel",      "العجلة",           ["copper", "cord"],              180,  12, {"food": 0.10, "connect": 0.15}),
    ("calendar",   "التقويم",          ["counting", "writing"],         200, 14, {"food": 0.12, "insight": 0.35}),
    ("law",        "الشريعة المدوّنة",  ["writing"],                     220, 15, {"order": 0.30, "cap": 0.10}),
    ("bronze",     "البرونز",          ["copper"],                      240, 16, {"food": 0.10, "leth": 0.18}),
    ("sail",       "الشراع",           ["weaving", "wheel"],            240, 17, {"connect": 0.28}),
    ("coin",       "النقد",            ["law", "bronze"],               480, 20, {"connect": 0.22, "cap": 0.10}),
    ("iron",       "الحديد",           ["bronze"],                      544, 23, {"food": 0.14, "leth": 0.24, "cap": 0.12}),
    ("astronomy",  "علم الفلك",        ["calendar"],                    512, 24, {"insight": 0.45}),
    ("geometry",   "الهندسة",          ["counting", "writing"],         512, 24, {"insight": 0.30, "cap": 0.08}),
    ("medicine",   "الطبّ",            ["writing", "astronomy"],        608, 28, {"mort": -0.22, "birth": -0.40}),
    ("paper",      "الورق",            ["writing", "weaving"],          640, 30, {"record": 1.0, "teach": 0.30}),
    ("archive",    "دار السجلّات",      ["paper", "law", "calendar"],    736, 34, {"record": 2.0, "insight": 0.30}),
    ("glass",      "الزجاج",           ["fire", "pottery", "iron"],     736, 36, {"insight": 0.12}),
    ("printing",   "الطباعة",          ["paper", "coin"],               832, 40, {"teach": 0.60, "record": 1.5, "connect": 0.25}),
    ("optics",     "البصريات",         ["glass", "geometry"],           864, 44, {"insight": 0.35}),
    ("mechanics",  "علم الحِيَل",       ["geometry", "iron", "wheel"],   896, 46, {"food": 0.16, "insight": 0.20}),
    ("clock",      "الساعة",           ["mechanics", "astronomy"],      960, 50, {"insight": 0.30}),
    ("method",     "المنهج التجريبي",   ["printing", "optics", "clock"], 1024, 56, {"insight": 0.90, "free": 1.0}),
    ("chemistry",  "الكيمياء",         ["method", "glass"],             1088, 62, {"mort": -0.10, "insight": 0.30}),
    ("elements",   "العناصر",          ["chemistry"],                   1152, 68, {"insight": 0.35}),
    ("steam",      "البخار",           ["mechanics", "method", "iron"], 1216, 72, {"food": 0.30, "cap": 0.35}),
    ("magnetism",  "المغناطيسية",      ["method", "elements"],          1280, 78, {"insight": 0.30}),
    ("battery",    "العمود الكهربي",    ["elements", "chemistry"],       1344, 84, {"insight": 0.35}),
    ("current",    "التيار",           ["battery", "magnetism"],        1440, 90, {"insight": 0.40}),
    ("electro",    "الكهرومغناطيسية",   ["current"],                     1536, 98, {"insight": 0.50}),
    ("waves",      "الموجات",          ["electro", "optics", "method"], 1664, 108, {"insight": 0.60}),
]

BY_KEY = {t[0]: t for t in TECHS}
ORDER = {t[0]: i for i, t in enumerate(TECHS)}
LANDMARKS = ("farming", "writing", "calendar", "law", "printing",
             "method", "elements", "current", "electro", "waves")

# ما تحجبه المحرّمات المزروعة في تاريخهم
TABOO_BLOCKS = {
    # إحصاء الحَبّ في المخزن ليس إحصاء النجوم: تمرّ الأرقام والكتابة،
    # ويبقى المحرّم قائمًا على رفع البصر إلى السماء وعدّ ما فيها.
    "counting_stars": ("astronomy", "calendar"),
}


def yields(know):
    f = 1.0
    for k in know:
        e = BY_KEY.get(k)
        if e:
            f += e[5].get("food", 0.0)
    return f


def effect(know, key):
    v = 0.0
    for k in know:
        e = BY_KEY.get(k)
        if e:
            v += e[5].get(key, 0.0)
    return v


def available(know, blocked):
    out = []
    for key, name, pre, pop, kn, eff in TECHS:
        if key in know or key in blocked:
            continue
        ok = True
        for p in pre:
            if p not in know:
                ok = False
                break
        if ok:
            out.append((key, name, pop, kn))
    return out


def innovation_pressure(n_eff, connect, leisure, openness, know_n, cfg):
    """
    معدّل الابتكار. الأُسّ على العدد أقلّ من واحد: مضاعفة السكان لا تضاعف
    الاكتشاف، لكن تقليصهم إلى النصف يوقفه تقريبًا.
    """
    if n_eff < 8:
        return 0.0
    base = (n_eff ** cfg.collective_brain_exp) / 40.0
    return (cfg.invention_scale * base * (0.35 + connect) *
            (0.15 + leisure) * (0.30 + openness) * (1.0 + know_n * 0.045))


def try_invent(st, n_eff, connect, leisure, openness, blocked, cfg, rng):
    cands = available(st.knowledge, blocked)
    if not cands:
        return None
    p = innovation_pressure(n_eff, connect, leisure, openness, len(st.knowledge), cfg)
    if p <= 0.0:
        return None
    # كان هنا شرطُ رصيدٍ معرفيّ صارم أوقع الشجرة في فجوة مغلقة: كل ما بقي
    # يطلب عشرين معرفة وهم عند ثمانية عشر، ولا شيء متاح بينهما. والمتطلّبات
    # وحدها تكفي لفرض الترتيب، ورصيدُ المعرفة يعمل في المعدّل لا في البوّابة.
    ready = [c for c in cands if n_eff >= c[2]]
    if not ready:
        return None
    ready.sort(key=lambda c: ORDER[c[0]])
    ready = ready[:6]                     # الأقرب في الشجرة أرجح
    # الأقرب متطلبًا أسهل
    key, name, need_pop, need_kn = rng.choice(ready)
    # كلّما عمُقت المعرفة صعُب ما بعدها: الزراعة تأتي في قرون، والكهرباء
    # لا تأتي إلا بعد آلاف السنين ومئات الألوف من الرؤوس المتّصلة.
    depth = 1.0 + ORDER[key] * 0.30
    chance = min(0.40, p * 0.035 * (1.0 + 0.6 * (n_eff / max(1, need_pop) - 1.0)) / depth)
    if rng.random() < chance:
        st.knowledge.add(key)
        return (key, name)
    return None
