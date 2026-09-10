"""
الأربعة والثلاثون.

خمسة بيوت، وثلاثة أجيال، وأنساب متشابكة. لكل واحد قصّة وطبع ومقام،
وكلهم يحملون كل الصفات البشرية — الرحمة والقسوة والغرور والصبر —
والفرق بينهم في المعايرة لا في الوجود.

ما لم يُذكر من الصفات يُسحب عشوائيًا، فلا اثنان متطابقان حتى لو تشابها.
"""

from . import genome as G

M, F = 0, 1

FOUNDERS = [
    # ---------------------------------------------------- بيت الرماد
    dict(n="نَهار", sex=M, age=54, house="الرماد", craft="حافظ الحكاية", stance="devout",
         tr=dict(conscientiousness=.82, care=.72, credulity=.86, openness=.22,
                 honesty=.74, dominance=.48, recall=.70, reasoning=.44),
         story="شيخ البيت الأكبر وحافظ حكاية الهبوط. يرويها كل ليلة بالكلمات نفسها، "
               "ويعدّ تغيير كلمة واحدة فيها خيانة. لم يسأل نفسه مرّة: من أخبرني؟"),

    dict(n="غَيْلان", sex=M, age=46, house="الرماد", craft="كاهن الغضب", stance="cleric",
         tr=dict(machiavellianism=.88, credulity=.18, extraversion=.84, honesty=.16,
                 narcissism=.72, reasoning=.66, care=.30, dominance=.70),
         story="كاهن الغضب. يعرف في قرارة نفسه أنه لم يرَ شيئًا قطّ، لكنه يعرف "
               "متى يرتجف صوته فيصمت الناس. يؤمن بالطقس ولا يؤمن بالإله."),

    dict(n="خَنْساء", sex=F, age=43, house="الرماد", craft="نائحة", stance="devout",
         tr=dict(grief=.92, neuroticism=.78, care=.74, credulity=.70, recall=.80,
                 openness=.34, play=.12),
         story="دفنت ثلاثة من أبنائها في غضبٍ واحد. تعدّ أسماءهم كل ليلة قبل النوم، "
               "وتخاف أن تنساهم أكثر مما تخاف الموت."),

    dict(n="زُهْرة", sex=F, age=20, house="الرماد", craft="ناسجة", stance="skeptic",
         tr=dict(reasoning=.80, credulity=.08, honesty=.84, openness=.72,
                 agreeableness=.44, neuroticism=.50, dominance=.40),
         story="ابنة الكاهن. رأت أباه يتمرّن على البكاء خلف الخيمة قبل الخطبة، "
               "فما عادت تصدّق أحدًا — ولا حتى نفسها حين تبكي."),

    dict(n="بَلْج", sex=M, age=26, house="الرماد", craft="راوٍ", stance="devout",
         tr=dict(conscientiousness=.76, openness=.16, agreeableness=.72, credulity=.84,
                 recall=.74, reasoning=.34, dominance=.24),
         story="ابن نهار. يحفظ الحكاية كما يحفظها أبوه، حرفًا بحرف، ولا يسأل. "
               "يقول: السؤال ثقب في الإناء."),

    dict(n="مَيّ", sex=F, age=33, house="الرماد", craft="ناسجة", stance="wavering",
         tr=dict(openness=.86, play=.70, care=.60, credulity=.44, recall=.72,
                 extraversion=.54, reasoning=.58),
         story="تضع في كل ثوب تنسجه خيطًا لا يفهمه أحد. تقول إنه اسم من مات في "
               "تلك السنة. لم يطلب منها أحد ذلك، ولا تعرف من أين جاءتها الفكرة."),

    # ---------------------------------------------------- بيت النخلة
    dict(n="عَثْم", sex=M, age=59, house="النخلة", craft="شيخ", stance="devout",
         tr=dict(recall=.10, credulity=.88, care=.68, openness=.30, longevity=.80,
                 vigor=.30, reasoning=.38, honesty=.66),
         story="أكبر الأحياء. ذاكرته ثقبٌ يملؤه بما يشبه الحقيقة. يقسم أنه رأى "
               "وادي النخلات السبع بعينيه — والوادي غرق قبل مولده بألفٍ وتسعمئة سنة."),

    dict(n="سَلْمى", sex=F, age=48, house="النخلة", craft="قابلة", stance="skeptic",
         tr=dict(care=.94, reasoning=.78, credulity=.20, conscientiousness=.86,
                 vigor=.62, honesty=.80, neuroticism=.34, openness=.60),
         story="القابلة. أخرجت من الأرحام أكثر مما دفنت — بقليل. لا تصلّي أثناء "
               "الولادة، تعمل. وحين ماتت ثلاث نساء في موسم واحد لم تلُم أحدًا: عدّت."),

    dict(n="رُقَيّة", sex=F, age=23, house="النخلة", craft="قابلة متعلّمة", stance="wavering",
         tr=dict(care=.80, fear=.72, neuroticism=.62, conscientiousness=.70,
                 credulity=.52, reasoning=.60),
         story="تتعلّم من أمّها وتخاف أن تصير مثلها: امرأة رأت كثيرًا فما عادت "
               "تستطيع أن تُعزّي أحدًا بكذبة."),

    dict(n="وَرْدان", sex=M, age=39, house="النخلة", craft="زارع", stance="wavering",
         tr=dict(honesty=.18, conscientiousness=.84, fear=.74, seeking=.76,
                 agreeableness=.30, credulity=.46, narcissism=.50),
         story="يزرع أكثر مما يأكل ويخبّئ الباقي في حفرة لا يعرفها إلا هو. "
               "لا يثق بأحد لأنه يعرف بماذا يفكّر هو نفسه في سنوات الجوع."),

    dict(n="نُعْم", sex=F, age=16, house="النخلة", craft="جامعة", stance="wavering",
         tr=dict(play=.84, openness=.78, dominance=.56, extraversion=.72,
                 credulity=.34, vigor=.80),
         story="أسرع قدمين في القرية، ولا تحبّ أن يُمسك بها أحد — لا في اللعب "
               "ولا في غيره. تذهب حيث لا يُؤذَن، وتعود قبل أن يُسأل عنها."),

    dict(n="قَطْن", sex=M, age=18, house="النخلة", craft="زارع", stance="devout",
         tr=dict(lust=.78, fear=.70, agreeableness=.76, extraversion=.28,
                 credulity=.66, honesty=.72, narcissism=.22),
         story="يحبّ زهرة منذ ثلاث سنين ولم يقل. يظنّ أن الإله يعاقب من يشتهي، "
               "فيصلّي كلما رآها، ثم يخجل من صلاته."),

    dict(n="أُمامة", sex=F, age=12, house="النخلة", craft="—", stance="skeptic",
         tr=dict(openness=.94, reasoning=.82, credulity=.14, play=.66,
                 agreeableness=.50, extraversion=.60),
         story="طفلة تسأل أسئلة تُسكِت الكبار. سألت مرّة: إن كان الإله غاضبًا منذ "
               "ألفي سنة، فمتى يتعب؟ فضُربت، ولم تنسَ أن أحدًا لم يجب."),

    # ---------------------------------------------------- بيت الحجر
    dict(n="مِرْداس", sex=M, age=32, house="الحجر", craft="مقاتل", stance="wavering",
         tr=dict(dominance=.92, narcissism=.88, honesty=.12, rage=.74, vigor=.90,
                 callousness=.66, machiavellianism=.60, care=.24, credulity=.36),
         story="أقوى ذراع وأقسى لسان. يرى أن أباه صار شيخًا لأنه هرم لا لأنه "
               "يستحق، ويقول ذلك في وجهه. ينتظر — وهو رجل لا يجيد الانتظار."),

    dict(n="دَرْغام", sex=M, age=37, house="الحجر", craft="مقاتل", stance="devout",
         tr=dict(rage=.78, conscientiousness=.74, reasoning=.26, agreeableness=.48,
                 credulity=.72, dominance=.54, vigor=.82, openness=.18),
         story="يقاتل حين يُؤمر ولا يسأل لماذا، ويعدّ ذلك فضيلة. قال مرّة: "
               "من يسأل قبل أن يضرب يموت وهو يسأل."),

    dict(n="صَفِيّة", sex=F, age=15, house="الحجر", craft="—", stance="wavering",
         tr=dict(dominance=.76, callousness=.54, narcissism=.62, vigor=.70,
                 care=.28, agreeableness=.30, credulity=.40),
         story="ابنة مرداس. تعلّمت منه أن الرحمة ضعف قبل أن تتعلّم المشي، "
               "وهي تختبر ذلك على الصغار لترى إن كان صحيحًا."),

    dict(n="هَجْر", sex=M, age=21, house="الحجر", craft="بنّاء", stance="wavering",
         tr=dict(conscientiousness=.92, extraversion=.16, openness=.44,
                 agreeableness=.60, credulity=.44, care=.40, reasoning=.62),
         story="يبني الجدران ويحبّها أكثر مما يحبّ الناس. يقول إن الحجر لا يكذب: "
               "إن أسأتَ وضعه سقط في وجهك في حينه، لا بعد أجيال."),

    dict(n="لُبَابة", sex=F, age=29, house="الحجر", craft="مصلحة", stance="wavering",
         tr=dict(agreeableness=.94, honesty=.86, care=.82, extraversion=.68,
                 rage=.14, narcissism=.14, credulity=.50, reasoning=.64),
         story="تمشي بين المتخاصمين حتى تُتعِب نفسها ولا يشكرها أحد. "
               "أصلحت بين مرداس وأبيه ثلاث مرّات، وتعرف أن الرابعة لن تُصلَح."),

    dict(n="عَوْف", sex=M, age=13, house="الحجر", craft="—", stance="devout",
         tr=dict(narcissism=.58, dominance=.62, credulity=.68, openness=.28,
                 play=.54, vigor=.66),
         story="ابن مرداس الأصغر. يقلّد أباه في كل شيء حتى في المشية وفي طريقة "
               "الصمت قبل الغضب. لم يقرّر بعد إن كان يحبّه أو يخافه."),

    # ---------------------------------------------------- بيت المِلح
    dict(n="أَشْرَم", sex=M, age=29, house="المِلح", craft="راصد", stance="skeptic",
         tr=dict(reasoning=.94, openness=.90, credulity=.06, recall=.84,
                 conscientiousness=.78, neuroticism=.56, extraversion=.30,
                 agreeableness=.52, honesty=.82),
         story="يعدّ. يعدّ الأيام والمواسم والموتى وأضلاع الظلّ عند الظهيرة. "
               "سُمّي على الذي مات في الحكاية لأنه أحصى النجوم — ويعرف ذلك، "
               "ويعدّ رغم ذلك. لم يخبر أحدًا بعد بما لاحظه عن سنوات الغضب."),

    dict(n="سُلاف", sex=F, age=27, house="المِلح", craft="راحلة", stance="wavering",
         tr=dict(openness=.88, seeking=.86, extraversion=.80, fear=.24,
                 credulity=.30, dominance=.50, play=.62),
         story="ترتحل أبعد مما يُسمح وتعود بأشياء لا يعرفها أحد: حجر يجذب الحديد، "
               "بذرة لا تنبت هنا. لا أحد يسألها من أين، لأن السؤال يفتح بابًا."),

    dict(n="جَذْل", sex=M, age=8, house="المِلح", craft="—", stance="devout",
         tr=dict(play=.86, openness=.70, credulity=.80, fear=.40),
         story="ابن سلاف. يجمع الحصى ويرتّبه صفوفًا ويسمّي كل صفّ باسم جدّ لم يره."),

    dict(n="مَرْوان", sex=M, age=44, house="المِلح", craft="تاجر", stance="cleric",
         tr=dict(machiavellianism=.86, honesty=.14, reasoning=.76, extraversion=.66,
                 narcissism=.64, credulity=.24, callousness=.52, dominance=.66),
         story="يبيع ويشتري، ويعرف ثمن كل إنسان في القرية بالحبّة. يساند الكاهن "
               "علنًا ويضحك منه سرًّا، وقد حسب أن الطقوس أرخص من الحرّاس."),

    dict(n="رَمْدان", sex=M, age=24, house="المِلح", craft="تاجر", stance="skeptic",
         tr=dict(callousness=.78, honesty=.08, narcissism=.80, machiavellianism=.70,
                 agreeableness=.18, credulity=.16, rage=.58, fear=.30),
         story="ابن مروان، وأخفّ منه ضميرًا. لا يؤمن بشيء ولا يخفي ذلك إلا حين "
               "يفيده الإخفاء. يقول: الإله الذي يقتل ثلثنا كل جيل ليس غاضبًا، إنه جائع."),

    dict(n="آسِية", sex=F, age=30, house="المِلح", craft="—", stance="wavering",
         tr=dict(machiavellianism=.82, extraversion=.20, reasoning=.80, recall=.88,
                 honesty=.36, care=.44, credulity=.34, dominance=.44),
         story="تعرف أسرار الجميع وتصمت. سكوتها أثقل من كلام غيرها، والكل يجاملها "
               "لسبب لا يستطيع أن يسمّيه."),

    dict(n="فَيْروز", sex=F, age=17, house="المِلح", craft="مغنّية", stance="devout",
         tr=dict(recall=.96, play=.80, openness=.74, extraversion=.78,
                 credulity=.66, care=.58, reasoning=.52),
         story="تغنّي، وأغانيها تحفظ ما لا يحفظه الشيوخ — الأسماء والسنوات "
               "والفواصل بينها. لا تعرف أنها تحمل سجلّ القرية في حنجرتها."),

    # ---------------------------------------------------- بيت الريح
    dict(n="شَبيب", sex=M, age=34, house="الريح", craft="راعٍ", stance="wavering",
         tr=dict(extraversion=.14, openness=.50, credulity=.28, dominance=.18,
                 agreeableness=.56, care=.46, seeking=.40, fear=.30),
         story="يرعى بعيدًا ويعود قليلًا. لا يعنيه من يحكم ولا من يصلّي. "
               "سُئل مرّة عن الإله فقال: لم يكلّمني، ولم أكلّمه."),

    dict(n="حَلِيمة", sex=F, age=36, house="الريح", craft="راعية", stance="devout",
         tr=dict(conscientiousness=.80, grief=.84, extraversion=.12, care=.70,
                 credulity=.74, neuroticism=.58, honesty=.78),
         story="أرملة. مات زوجها في الغضب قبل تسع سنين وهو يحمل قربانه إلى الكاهن. "
               "تعمل ولا تتكلّم، وتصلّي أكثر من الجميع."),

    dict(n="مِسْعَر", sex=M, age=19, house="الريح", craft="راعٍ", stance="wavering",
         tr=dict(rage=.86, agreeableness=.34, play=.68, conscientiousness=.28,
                 credulity=.42, vigor=.74, narcissism=.54, openness=.56),
         story="يغضب في لحظة وينسى في لحظة، ولا يفهم لماذا لا ينسى الناس مثله. "
               "خصومه أكثر من أصدقائه، وهو يظنّ العكس."),

    dict(n="ظَمْياء", sex=F, age=14, house="الريح", craft="—", stance="devout",
         tr=dict(credulity=.92, openness=.84, neuroticism=.72, recall=.60,
                 extraversion=.62, care=.58, reasoning=.36),
         story="تحلم أحلامًا ثقيلة وتحكيها في الصباح كأنها وقعت. يصدّقها الصغار، "
               "وبدأ بعض الكبار يصدّق. لا تكذب — هي فعلًا لا تعرف الفرق."),

    dict(n="كَرْدَم", sex=M, age=41, house="الريح", craft="راعٍ", stance="skeptic",
         tr=dict(credulity=.04, grief=.88, rage=.66, reasoning=.68, honesty=.76,
                 agreeableness=.40, neuroticism=.64, openness=.52),
         story="كان أشدّهم إيمانًا. ثم مات ابنه في الغضب وهو راكع يدعو، فوقف "
               "ولم يركع بعدها. يحضر الطقوس ويصمت فيها، وصمته يزعج الكاهن أكثر من الإنكار."),

    dict(n="رَيْحانة", sex=F, age=11, house="الريح", craft="—", stance="wavering",
         tr=dict(agreeableness=.78, care=.66, openness=.58, credulity=.56, play=.72),
         story="ابنة لبابة. ورثت عن أمّها أنها تقف بين المتخاصمين، وورثت عن أبيها "
               "أنها تبكي بعدها وحدها."),

    dict(n="غُصْن", sex=M, age=6, house="الريح", craft="—", stance="devout",
         tr=dict(play=.88, credulity=.86, openness=.66, fear=.52),
         story="ابن كردم. يسأل أباه لماذا لا يركع، ولا يحصل على جواب."),

    dict(n="هالة", sex=F, age=2, house="النخلة", craft="—", stance="devout",
         tr=dict(vigor=.70, play=.80, credulity=.90),
         story="رضيعة رُقَيّة. أول من وُلد في هذه القرية بعد الغضب الأخير، "
               "ويقول نهار إنها علامة."),
]

# (ابن، أم، أب) — بالأسماء
KIN = [
    ("بَلْج", "خَنْساء", "نَهار"),
    ("زُهْرة", "مَيّ", "غَيْلان"),
    ("رُقَيّة", "سَلْمى", "وَرْدان"),
    ("سَلْمى", None, "عَثْم"),
    ("وَرْدان", None, "عَثْم"),
    ("حَلِيمة", None, "عَثْم"),
    ("نُعْم", "سَلْمى", "وَرْدان"),
    ("قَطْن", None, "وَرْدان"),
    ("أُمامة", "مَيّ", None),
    ("مِرْداس", "خَنْساء", "نَهار"),
    ("صَفِيّة", "لُبَابة", "مِرْداس"),
    ("عَوْف", "لُبَابة", "مِرْداس"),
    ("هَجْر", None, "دَرْغام"),
    ("كَرْدَم", None, "دَرْغام"),
    ("جَذْل", "سُلاف", "شَبيب"),
    ("فَيْروز", "سُلاف", None),
    ("رَمْدان", None, "مَرْوان"),
    ("آسِية", None, "مَرْوان"),
    ("شَبيب", None, "غَيْلان"),
    ("مِسْعَر", "حَلِيمة", "شَبيب"),
    ("ظَمْياء", "حَلِيمة", None),
    ("رَيْحانة", "لُبَابة", None),
    ("غُصْن", None, "كَرْدَم"),
    ("هالة", "رُقَيّة", "قَطْن"),
    ("أَشْرَم", None, "قَطْن"),   # عمّ الفتى، من جيل سابق سُمّي كذلك
]

# أزواج قائمون عند سنة الصفر
UNIONS = [("نَهار", "خَنْساء"), ("عَثْم", None), ("وَرْدان", "سَلْمى"),
          ("مِرْداس", "لُبَابة"), ("شَبيب", "حَلِيمة"), ("غَيْلان", "مَيّ")]

STANCE_FAITH = {"devout": 0.88, "cleric": 0.55, "wavering": 0.45, "skeptic": 0.12}

_KEY = {name: i for i, name in enumerate(G.TRAITS)}


def trait_overrides(d):
    return {_KEY[k]: v for k, v in d.get("tr", {}).items() if k in _KEY}


def by_name():
    return {p["n"]: i for i, p in enumerate(FOUNDERS)}
