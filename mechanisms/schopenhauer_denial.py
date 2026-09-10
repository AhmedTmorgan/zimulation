"""
إنكار الإرادة — شوبنهاور.

دعواه أن الرغبة نفسها هي مصدر الألم، لا عجزُها عن التحقّق؛ وأن من بلغ
من الألم والتأمّل مبلغًا يرى ذلك، فينصرف عن الإشباع إلى **تعطيل الرغبة**.

وهنا يصير هذا قابلًا للقياس: إن صحّ، فسيظهر في هذه الدنيا قومٌ يقلّ
نسلهم ويقلّ اكتنازهم ويطول تأمّلهم — ولهم **ثمن تطوّري حقيقي**: يورّثون
أقلّ، فتنحسر طباعهم من النسل ما لم تُنقَل بالتعليم.

فإن انقرض الزاهدون دائمًا فالزهد لا يعمّر إلا بالنقل الثقافي، لا بالوراثة.
وهذه نتيجةٌ تُفحص، لا مقولةٌ تُردَّد.
"""

from village import genome as G
from village.emotion import P_GRIEF
from village.plugin import mechanism
from village.psyche import hidden_pull


@mechanism(
    key="denial-of-will",
    ar="إنكار الإرادة",
    source="Schopenhauer, Die Welt als Wille und Vorstellung (1818), الكتاب الرابع",
    claim="من اجتمع له ألمٌ طويل وتأمّلٌ عالٍ ينصرف عن إشباع الرغبة إلى "
          "تعطيلها، فيقلّ نسله واكتنازه ويطول تأمّله — ويدفع ثمنًا تطوّريًا.",
    params={"pain_gate": 1.05, "mind_gate": 0.62, "grip": 0.34, "relief": 0.45},
    hook="yearly",
)
def denial_of_will(sim, a, ctx, rng, P):
    if a.age < 22 or a.stance == "denial":
        return None
    pain = (a.af.p[P_GRIEF] * 0.6 + hidden_pull(a) * 0.7
            + min(1.0, a.hunger) * 0.3 + a.fear_death * 0.4)
    mind = 0.5 * (a.eg.t[G.OPENNESS] + a.eg.t[G.REASONING])
    if pain < P["pain_gate"] or mind < P["mind_gate"]:
        return None
    if rng.random() > P["grip"] * (mind - P["mind_gate"] + 0.2):
        return None

    a.stance = "denial"
    a.title = "الزاهد"
    # تعطيل الرغبة نفسها: يُطفأ ما يدفع إلى الإشباع، لا ما يدفع إلى النفع
    from village.mind import NA, F_BIAS, A_COURT, A_HOARD, A_SEIZE, A_ATTACK, A_CONTEMPLATE
    W = a.prog.W
    off = F_BIAS * NA
    for act, d in ((A_COURT, -2.6), (A_HOARD, -2.2), (A_SEIZE, -2.0),
                   (A_ATTACK, -1.6), (A_CONTEMPLATE, +1.4)):
        i = off + act
        W[i] = max(-6.0, min(6.0, W[i] + d))
    a.apply_shift(G.LUST, -0.30)
    a.apply_shift(G.SEEKING, -0.20)
    # وثمرتُه التي وعد بها: يخفّ الألم فعلًا
    a.despair *= (1.0 - P["relief"])
    a.af.p[P_GRIEF] *= (1.0 - P["relief"])
    sim.chron.add(sim.year, "denial",
                  f"انصرف {a.name} عن الرغبة نفسها لا عن ثمرتها.", 2.2)
    return "denial"
