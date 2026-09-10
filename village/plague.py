"""الأوبئة: ممرضات تتحوّر، ومناعة تُورَّث وتُكتسب."""

_N = [0]

_NAMES = ("السُّخام", "الحُمّى الزرقاء", "الذُّبال", "نَفَس الرمل", "السُّقام",
          "الطاعون الأسود", "الرِّعدة", "القَحّة", "الصُّفار", "الوَرَم")


class Pathogen:
    __slots__ = ("id", "name", "virulence", "transmit", "antigen", "born", "toll")

    def __init__(self, name, virulence, transmit, antigen, born):
        _N[0] += 1
        self.id = _N[0]
        self.name = name
        self.virulence = virulence
        self.transmit = transmit
        self.antigen = antigen
        self.born = born
        self.toll = 0


def spawn(rng, year, n_antigen):
    return Pathogen(rng.choice(_NAMES),
                    max(0.05, min(0.85, rng.gauss(0.30, 0.16))),
                    max(0.08, min(0.9, rng.gauss(0.40, 0.16))),
                    rng.randrange(n_antigen), year)


def mutate(p, rng, n_antigen, year):
    q = Pathogen(p.name + "٢", p.virulence * rng.gauss(1.0, 0.25),
                 p.transmit * rng.gauss(1.0, 0.22), p.antigen, year)
    q.virulence = max(0.05, min(0.9, q.virulence))
    q.transmit = max(0.05, min(0.95, q.transmit))
    if rng.random() < 0.5:
        q.antigen = rng.randrange(n_antigen)   # تجاوز المناعة المكتسبة
    return q


def resistance(agent, p):
    r = 0.0
    if p.antigen in agent.immunity:
        r += 0.75
    r += 0.25 * agent.eg.t[17]           # VIGOR
    return min(0.95, r)
