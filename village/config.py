"""كل مقابض العالم في مكان واحد."""

from dataclasses import dataclass


@dataclass
class Config:
    # -- الزمن والحجم -------------------------------------------------
    seed: int = 20260909
    years: int = 10000
    prior_years: int = 2000           # تاريخ الهبوط المزروع (لم يحدث)
    world_size: int = 12
    founders: int = 34
    max_named: int = 300              # كائنات بمحاكاة معرفية كاملة
    settlement_split_at: int = 90

    # -- الجسد --------------------------------------------------------
    base_lifespan: float = 44.0
    adult_age: int = 15
    elder_age: int = 45
    menarche: int = 14
    fertile_until_f: int = 45
    fertile_until_m: int = 62
    yearly_food_need: float = 1.0
    child_food_ratio: float = 0.55
    gestation_penalty: float = 0.35   # خطر الوفاة أثناء الولادة قبل الطبّ
    infant_mortality: float = 0.155   # خطر سنويّ دون الخامسة قبل الطبّ
                                      # (يعطي نحو 30٪ وفياتٍ قبل الخامسة)

    # -- الذاكرة ------------------------------------------------------
    memory_cap: int = 56
    implanted_at_birth: int = 4
    dream_store_rate: float = 0.30
    contagion_rate: float = 0.22
    confab_rate: float = 0.16
    decay_base: float = 0.055
    numinous_bonus: float = 0.045

    # -- العقل --------------------------------------------------------
    learn_rate: float = 0.055
    rewrite_rate: float = 0.10        # تعديل بنيوي للقواعد
    invent_rule_rate: float = 0.05    # تأليف تعبيرة جديدة في اللغة الصغيرة
    temperature: float = 0.42
    lamarck: float = 0.45             # ما يرثه الابن من كود أبويه المتعلَّم

    # -- الفلك ---------------------------------------------------------
    # طورُ ترنّح المحور عند بدء العالم. **هذا شرطٌ ابتدائي مفروض** —
    # لا يُشتقّ من شيء لأنه موضعُ الكوكب في مداره حين بدأنا النظر.
    # اخترتُ لهم طورًا بعد ذروة الرطوبة بقليل، فينحدر الموسم عبر
    # عشرة آلاف سنة كما انحدر في الصحراء الكبرى حقيقةً.
    orbit_phase: float = 1.15

    # مَعاوِلُ السماء: يُطفأ كلُّ سببٍ وحده فتُقارَن الدنيا به وبدونه.
    # فمن قال «الجدب من الفلك» أو «الجدب من رعيهم» فله ما يُكذّبه.
    sky_orbit: bool = True        # ترنّح المحور
    sky_ocean: bool = True        # مرجّح الشحن والتفريغ (التأخير)
    sky_volcano: bool = True      # الرماد
    sky_albedo: bool = True       # أثرُ عريِ الأرض في المطر

    # -- الغضب (الموت الدوري) -----------------------------------------
    wrath_period: float = 27.0        # الدورة الحقيقية بالسنين
    wrath_jitter: float = 5.0         # تشويش يخفي الدورية
    wrath_severity: float = 0.16      # نسبة الموتى الأساسية
    wrath_overshoot: float = 0.35     # ما يضيفه تجاوز الطاقة الاستيعابية

    # -- العاطفة والروابط ---------------------------------------------
    contacts_per_year: int = 6
    grudge_decay: float = 0.075
    bond_decay: float = 0.06
    infidelity_base: float = 0.06
    jealousy_violence: float = 0.30
    violence_lethality: float = 0.16

    # -- السلطة -------------------------------------------------------
    power_corrupts: float = 0.030     # انزياح سنوي في السلوك المعبَّر لمن يحكم
    revolt_threshold: float = 1.05
    tribute_rate: float = 0.16        # ما يقتطعه الحاكم من الغلّة

    # -- الوراثة ------------------------------------------------------
    mutation_sigma: float = 0.05

    # -- الثقافة والعقيدة ---------------------------------------------
    myth_threshold: float = 0.60
    meme_drift: float = 0.09
    schism_threshold: float = 0.55
    doctrine_growth: float = 0.35     # تعقّد العقيدة مع كل تبرير

    # -- الوباء -------------------------------------------------------
    outbreak_chance: float = 0.014
    pathogen_mutate: float = 0.07
    max_strains: int = 10             # السلالات المتداولة — بلا سقفٍ تتكاثر أسّيًا

    # -- مِعاوِل السببية: أطفئ سببًا وقارن الدنيا به وبدونه ---------
    cause_water: bool = True          # فساد الماء يؤذي
    cause_toil: bool = True           # الكدح يُنهك
    cause_soma: bool = True           # النسل ينافس الصيانة (كيركوود)
    cause_tumour: bool = True         # الإصابات تتراكم فتستقلّ

    # -- التقنية ------------------------------------------------------
    invention_scale: float = 0.24
    collective_brain_exp: float = 0.55  # أُسّ حجم السكان في معدّل الابتكار

    # -- حدود المورد (الدرس المستفاد من تجمّد الجهاز) ------------------
    dead_cap: int = 60000             # كم راحلًا نحفظ سجلّه المضغوط
    event_cap: int = 40000            # سقف وقائع السجلّ
    mem_limit_mb: int = 1200          # يقف الرنّ بأدب قبل أن يقف الجهاز
    housekeep_every: int = 25

    # -- التشغيل ------------------------------------------------------
    snapshot_every: int = 20
    verbose_every: int = 250
