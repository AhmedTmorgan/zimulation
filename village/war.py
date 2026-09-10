"""
التدبير العسكري.

كان الغزو عندنا اندفاعًا: جوعٌ وجارٌ قريب فتقع الغارة. وهذا ليس تفكيرًا
عسكريًّا، هو شجار. والفرق بينهما أربعة أشياء يملكها القائد المدبِّر ولا
يملكها المندفع:

  **الاختيار** — لا يغزو الأقرب بل الأضعف الأغنى، ويحسب من وراءه.
  **التوقيت** — ينتظر حتى يُصاب جارُه بغضبٍ أو ثورةٍ أو جدب.
  **التحصين** — يبني قبل أن يُهاجَم لا بعده.
  **الحلف** — يجمع من يشترك معه في عدوّ.

وأهمّ من ذلك كلّه: **التدبير يُكتَب فيُورَّث.** من غزا وكتب ما نفعه، قرأه
قائدٌ بعد قرنٍ فبدأ من حيث انتهى. ولهذا تتفوّق الأمم التي تدوّن حروبها
على التي تنساها — لا لأن رجالها أشجع.

فقدرة القائد هنا = عقلُه + ما قرأ. والثاني يتراكم، والأول لا.
"""

from . import genome as G


def doctrine_level(st, ruler, agents):
    """
    ما بلغه القائد من تدبير: عقلُه، وما قرأه من أخبار الحروب، وما بلغته
    قريته من صنعة الحرب.
    """
    from .library import KIND_WAR
    lvl = 0.30 + 0.70 * ruler.eg.t[G.REASONING]
    accounts = sum(1 for b in st.library.books if b.kind == KIND_WAR)
    lvl += min(0.9, 0.16 * accounts)          # ما دُوّن يتراكم
    if "law" in st.knowledge:
        lvl += 0.10                            # جندٌ يُنظَّم لا يُحشَد
    if "wheel" in st.knowledge:
        lvl += 0.10
    if "coin" in st.knowledge:
        lvl += 0.12                            # يُموَّل، فيُطال أمده
    return min(2.6, lvl)


def strength(st, agents, cfg, know_leth):
    """قوّةُ قريةٍ على القتال: رجالها وصنعتها وجدارها."""
    s = 0.0
    for m in st.members:
        a = agents.get(m)
        if a is None or a.age < cfg.adult_age or a.age > 55:
            continue
        s += (0.4 + a.eg.t[G.VIGOR]) * (0.5 + a.skills[2])
    return s * (1.0 + know_leth), st.walls * 0.35


def weakness(sim, st):
    """
    ما يُغري بالغزو: جوعٌ، وسخط، وقلّة سلاح، وأثرُ نكبةٍ حديثة.
    وهذا هو **التوقيت**: لا يُقاس الجار بحاله دائمًا بل بحاله الآن.
    """
    need = sim._need(st)
    hunger = max(0.0, 1.0 - st.granary / max(1.0, need))
    recent = 0.0
    y = sim.year
    if st.wrath_seen and y - st.wrath_seen[-1] <= 4:
        recent += 0.45                       # أُصيبوا بغضبٍ لتوّهم
    if sim.last_revolt.get(st.id, -99) >= y - 5:
        recent += 0.35                       # وثاروا على حاكمهم
    return min(1.6, hunger * 0.8 + st.unrest * 0.4 + recent)


def allies_of(sim, st):
    return [s for s in sim.world.settlements
            if s.id != st.id and st.relations.get(s.id, 0.4) > 0.75
            and s.pop() >= 8]


def plan(sim, st, ruler, cfg):
    """
    خطّةُ غزو، أو لا خطّة. يعيد (الهدف، الحلفاء، سببُ الاختيار) أو None.

    المدبِّر يزن: ما يُغنَم، وضعفَ الهدف الآن، وبُعدَ الطريق، ومن وراءه.
    والمندفع لا يزن شيئًا — ولذلك يخسر وإن كان أقوى.
    """
    lvl = doctrine_level(st, ruler, sim.agents)
    reach = 3 + int(lvl)                     # التدبير يُطيل مدى الحملة
    cand = [s for s in sim.world.settlements
            if s.id != st.id and s.pop() >= 8
            and abs(s.x - st.x) + abs(s.y - st.y) <= reach]
    if not cand:
        return None

    mine, _ = strength(st, sim.agents, cfg, 0.0)
    best, bscore, why = None, 0.0, ""
    for t in cand:
        theirs, wall = strength(t, sim.agents, cfg, 0.0)
        w = weakness(sim, t)
        dist = abs(t.x - st.x) + abs(t.y - st.y)
        spoils = t.granary + 6.0 * len(t.knowledge - st.knowledge)
        backers = sum(s.pop() for s in allies_of(sim, t))
        # التقدير: ما يُرجى مقسومًا على ما يُخشى
        risk = (theirs + wall + backers * 0.5) * (1.0 + 0.18 * dist)
        score = (spoils * (0.5 + w)) / max(1.0, risk)
        # قليلُ التدبير يخلط الرغبة بالحساب
        score *= (0.35 + 0.65 * (lvl / 2.6)) + (1.0 - lvl / 2.6) * \
            (0.5 - 0.5 * st.relations.get(t.id, 0.4))
        if score > bscore:
            best, bscore = t, score
            why = ("ضعفٌ حادث" if w > 0.6 else
                   "غنيمةٌ ترجى" if spoils > 40 else "قربٌ وسهولة")
    if best is None:
        return None
    # لا يُقدِم المدبِّر إلا إذا رجحت كفّته
    theirs, wall = strength(best, sim.agents, cfg, 0.0)
    helpers = [s for s in allies_of(sim, st)
               if best.relations.get(s.id, 0.4) < 0.5]
    ours = mine + sum(strength(s, sim.agents, cfg, 0.0)[0] * 0.45 for s in helpers)
    margin = ours / max(1.0, theirs + wall)
    need_margin = 1.05 + 0.35 * (lvl / 2.6)      # المدبِّر يطلب هامشًا
    if margin < need_margin:
        return None
    return best, helpers, why, lvl, margin


def should_fortify(sim, st, ruler, cfg):
    """
    التحصين قبل الحاجة. المندفع يبني بعد أن يُهاجَم، والمدبِّر قبل.
    """
    lvl = doctrine_level(st, ruler, sim.agents)
    threat = 0.0
    for s in sim.world.settlements:
        if s.id == st.id:
            continue
        d = abs(s.x - st.x) + abs(s.y - st.y)
        if d > 4:
            continue
        rel = st.relations.get(s.id, 0.4)
        if rel < 0.3:
            threat += (0.4 - rel) * (s.pop() / 60.0) / (1.0 + 0.3 * d)
    return threat * lvl > 0.35


def record(sim, st, ruler, won, target_name, toll):
    """
    يُدوَّن الخبر فيُقرأ بعد قرن. وهذا وحده ما يجعل التدبير يتراكم.
    """
    from .library import Book, KIND_WAR
    if "writing" not in st.knowledge:
        return None
    b = Book(KIND_WAR, f"أخبار {target_name}", ruler.id, ruler.name, sim.year,
             [], [],
             (f"غزونا {target_name} فظفرنا؛ والذي نفع: أن ضربناهم وهم موهونون"
              if won else
              f"غزونا {target_name} فرُددنا؛ والذي ضرّ: أننا أقدمنا بلا فضل قوّة"))
    st.library.add(b)
    return b
