"""
واجهة الآليات.

الفيلسوف لا يكتب بايثون، والمطوّر لا يقرأ الفلسفة. هذه الواجهة تجعل
المساهمة **تصريحًا** قبل أن تكون شفرة: من يضيف آلية يلزمه أن يعلن
أربعة أشياء قبل سطر الكود الأول —

    المصدر   : من قال هذا، وأين. لا آلية بلا مرجع.
    الدعوى   : جملة واحدة قابلة للتكذيب. «إن صحّت هذه الآلية فسنرى كذا».
    المعاملات: كل ثابتٍ حرّ فيها. تُحصى ولا تُخفى.
    المِعوَل  : كيف يُبطَل أثرها لتُقارن الدنيا بها وبدونها.

والسبب في التشدّد بسيط: نموذجٌ بمئتَي معامل حرّ يقدر أن ينتج أي تاريخٍ
تطلبه منه، فلا يتنبّأ بشيء. عدّادُ المعاملات هنا هو ضمير المشروع —
`manifest()` يطبعه كاملًا في أي لحظة، ولا سبيل إلى إخفاء واحد.

مثال:

    from village.plugin import mechanism

    @mechanism(
        key="denial-of-will", ar="إنكار الإرادة",
        source="Schopenhauer, Die Welt als Wille und Vorstellung (1818), كتاب IV",
        claim="من طال ألمه وارتفع تأمّله ينزع إلى تعطيل الرغبة لا إشباعها، "
              "فيقلّ نسله ويقلّ اكتنازه.",
        params={"threshold": 1.15, "strength": 0.35},
        hook="yearly",
    )
    def denial(sim, a, ctx, rng, P):
        ...
"""

import inspect

HOOKS = ("yearly", "on_action", "on_birth", "on_death", "on_wrath", "on_speech")


class Mechanism:
    __slots__ = ("key", "ar", "source", "claim", "params", "hook", "fn",
                 "enabled", "fired")

    def __init__(self, key, ar, source, claim, params, hook, fn):
        self.key = key
        self.ar = ar
        self.source = source
        self.claim = claim
        self.params = dict(params or {})
        self.hook = hook
        self.fn = fn
        self.enabled = True
        self.fired = 0

    def __call__(self, *args):
        self.fired += 1
        return self.fn(*args, self.params)


REGISTRY = {}
_BY_HOOK = {h: [] for h in HOOKS}


def mechanism(key, ar, source, claim, params=None, hook="yearly"):
    """يسجّل آلية. يرفض ما لا مرجع له ولا دعوى قابلة للتكذيب."""
    if hook not in HOOKS:
        raise ValueError(f"مِشْبك غير معروف: {hook} — المتاح {HOOKS}")
    if not source or len(source) < 8:
        raise ValueError(f"«{key}»: لا آلية بلا مرجع صريح")
    if not claim or len(claim) < 20:
        raise ValueError(f"«{key}»: لا آلية بلا دعوى قابلة للتكذيب")

    def deco(fn):
        sig = inspect.signature(fn)
        if len(sig.parameters) != 5:
            raise ValueError(
                f"«{key}»: التوقيع يجب أن يكون (sim, agent, ctx, rng, P)")
        m = Mechanism(key, ar, source, claim, params, hook, fn)
        if key in REGISTRY:
            raise ValueError(f"«{key}» مسجّلة من قبل")
        REGISTRY[key] = m
        _BY_HOOK[hook].append(m)
        return m
    return deco


def fire(hook, sim, agent, ctx, rng):
    """يُشغّل ما سُجّل على هذا المِشْبك. الأخطاء تُبتلع كي لا تُسقط الرنّ."""
    out = []
    for m in _BY_HOOK.get(hook, ()):
        if not m.enabled:
            continue
        try:
            r = m(sim, agent, ctx, rng)
            if r:
                out.append((m.key, r))
        except Exception as e:      # آليةٌ مساهِمة لا تُسقط العالم
            m.enabled = False
            if hasattr(sim, "chron"):
                sim.chron.add(sim.year, "mechanism_failed",
                              f"عُطّلت آلية «{m.ar}»: {type(e).__name__}", 1.0)
    return out


def disable(*keys):
    """المِعوَل: يُبطل آليات بعينها لتُقارن الدنيا بها وبدونها."""
    for k in keys:
        if k in REGISTRY:
            REGISTRY[k].enabled = False


def enable_only(*keys):
    for k, m in REGISTRY.items():
        m.enabled = k in keys


def free_parameters():
    """كم معاملًا حرًّا أضافته الآليات المسجّلة."""
    return sum(len(m.params) for m in REGISTRY.values())


def manifest(core_params=None):
    """
    ضمير المشروع: كل آلية ومرجعها ودعواها ومعاملاتها، وعدّادٌ إجمالي.
    اطبعه في كل ورقة أو تقرير يخرج من هذه المحاكاة.
    """
    import importlib
    import pathlib
    import pkgutil
    import dataclasses as _dc
    from .config import Config as _C
    if core_params is None:
        core_params = len(_dc.fields(_C))     # يُحصى ولا يُكتب بيدي

    # كلُّ وحدةٍ تُعلن ما ضبطتُه فيها بيدي في `TUNED`. وما لم يُعلن
    # يُسمّى هنا صراحةً — فالرقم الذي يُخفي شيئًا أسوأ من رقمٍ كبير.
    import village as _pkg
    declared, silent = {}, []
    for mod in sorted(m.name for m in pkgutil.iter_modules(_pkg.__path__)):
        try:
            m = importlib.import_module(f".{mod}", _pkg.__name__)
        except Exception:
            continue
        t = getattr(m, "TUNED", None)
        if isinstance(t, dict) and t:
            declared[mod] = len(t)
        else:
            silent.append(mod)
    n_declared = sum(declared.values())

    lines = ["# الآليات المسجّلة", ""]
    lines.append(f"معاملات القلب: **{core_params}** (حقول `Config`)")
    lines.append(f"مضبوطات مُعلَنة في الوحدات: **{n_declared}** — "
                 + "، ".join(f"`{k}` {v}" for k, v in sorted(declared.items())))
    lines.append(f"آليات مضافة: **{len(REGISTRY)}** · "
                 f"معاملاتها الحرّة: **{free_parameters()}**")
    tot = core_params + n_declared + free_parameters()
    lines.append("")
    lines.append(f"**المجموع المُعلَن: {tot} معاملًا حرًّا.** "
                 f"كلّما زاد هذا الرقم قلّت قدرة النموذج على التنبّؤ.")
    lines.append("")
    lines.append("> يُحصى هذا العدد آليًّا من الكود لا يُكتب بيدٍ.")
    if silent:
        # ما لم يُعلَن يُقدَّر ولا يُترك مجهولًا: يُعدّ في مصدر كل وحدة
        # كلُّ عددٍ عشريّ كتبتُه بيدي (عدا 0 و1، فهما بنيةٌ لا معايرة).
        # وهو تقديرٌ **أعلى** لا رقمٌ دقيق — لكنه أصدق من السكوت.
        import ast as _ast
        est, rows = 0, []
        for mod in silent:
            try:
                src = pathlib.Path(
                    importlib.import_module(
                        f".{mod}", _pkg.__name__).__file__).read_text(
                            encoding="utf-8")
                n = len({v.value for v in _ast.walk(_ast.parse(src))
                         if isinstance(v, _ast.Constant)
                         and isinstance(v.value, float)
                         and v.value not in (0.0, 1.0)})
            except Exception:
                n = 0
            est += n
            rows.append((mod, n))
        rows.sort(key=lambda r: -r[1])
        lines.append(">")
        lines.append(f"> **ووحداتٌ لم تُعلن مضبوطاتها بعد** — وفيها نحو "
                     f"**{est}** عددًا مضبوطًا غير مُحصًى (تقديرٌ أعلى: كلُّ "
                     f"عددٍ عشريّ مميَّز في مصدرها عدا 0 و1). وهذا نقصٌ "
                     f"يُذكر ولا يُخبّأ، ومعناه أن المجموع الحقيقي أقرب إلى "
                     f"**{tot + est}** منه إلى {tot}:")
        lines.append(">")
        lines.append("> " + "، ".join(f"`{m}` {n}" for m, n in rows if n))
        bare = [m for m, n in rows if not n]
        if bare:
            lines.append("> ")
            lines.append("> (وبلا أعدادٍ مضبوطة: "
                         + "، ".join(f"`{m}`" for m in bare) + ")")
    lines.append("")
    for m in REGISTRY.values():
        lines.append(f"## {m.ar} (`{m.key}`) — {'مفعّلة' if m.enabled else 'معطّلة'}")
        lines.append(f"- **المصدر:** {m.source}")
        lines.append(f"- **الدعوى:** {m.claim}")
        lines.append(f"- **المِشْبك:** `{m.hook}` · **اشتغلت:** {m.fired:,} مرة")
        if m.params:
            lines.append("- **معاملاتها:** " +
                         "، ".join(f"`{k}={v}`" for k, v in m.params.items()))
        lines.append("")
    return "\n".join(lines)


def count_core_params(cfg):
    """يحصي معاملات الإعدادات — الرقم الذي يجب ألّا يُخفى."""
    return sum(1 for k in vars(cfg) if not k.startswith("_")
               and k not in ("seed", "years"))
