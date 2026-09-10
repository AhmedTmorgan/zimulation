"""
المحرّك: سنة واحدة في كل خطوة.

الترتيب مقصود — المناخ يسبق الإنتاج، والإنتاج يسبق التوزيع، والتوزيع
يصنع الجوع الذي يصنع الغبن الذي يصنع الثورة. والغضب يقع فوق ذلك كله
في مواعيده، غير عابئ بمن صلّى ومن لم يصلِّ.
"""

from . import genome as G
from . import mind as M
from . import tech as T
from . import faith as FA
from . import power as PW
from . import plague as PL
from . import flora as FL
from . import healing as HL
from . import history as HI
from . import malady as MD
from . import people as PE
from . import guard as GD
from . import speech as SP
from . import psyche as PS
from . import naming as NM
from . import concept as CN
from . import library as LB
from . import causes as CA
from . import war as WR
from . import plugin as PG
from .agent import Agent, MALE, FEMALE
from .chronicle import Chronicle
from .emotion import appraise, awe_strike, P_LUST, E_AWE
from .lang import mutate_maxim
from .memory import (S_LIVED, S_TOLD, S_CONFAB, K_FEAST, K_HUNGER, K_DEATH, K_LOVE,
                     K_BETRAYAL, K_VIOLENCE, K_RECONCILE, K_WONDER, K_VISION,
                     K_JOURNEY, K_CRAFT, K_TEACHING, K_PLAGUE, K_RITUAL, K_BIRTH)
from .mind import Program, innate, inherit, build_features, decide, reflect, sparse
from .rng import Streams
from .world import World, Settlement


class Sim:
    def __init__(self, cfg):
        self.cfg = cfg
        self.rs = Streams(cfg.seed)
        self.rng = self.rs.get("core")
        self.world = World(cfg, self.rs.get("world"))
        self.history = HI.generate(cfg, self.rs.get("history"))
        self.chron = Chronicle()
        self.agents = {}
        self.mass = {}
        self.pathogens = []
        # بيولوجيا هذا العالم: مئةُ علّةٍ وثلاثةُ آلافِ نبتة. تُبنى مرّةً
        # وهي واحدةٌ في كل رنّ — والذي يختلف هو ما يعرفونه منها.
        self.maladies = MD.build()
        self.mal_signs = MD.SIGNS
        self.mal_fam = MD.by_family(self.maladies)
        self.plants = FL.build()
        self.flora_at = FL.by_biome(self.plants)
        self.doctrines = {}
        self.next_id = 1
        self.next_sect = 1
        self.year = 0
        self.dead = []
        self.last_revolt = {}
        self.last_war = {}
        self.war_log = []
        self._natural = set()
        self.names = NM.Registry()
        self.epoch_year = None
        self.epoch_true = 1.0
        self.stats = dict(births=0, deaths=0, murders=0, wraths=0, revolts=0,
                          persecutions=0, schisms=0, wars=0, suicides=0,
                          lies=0, exposed=0, repressed=0)
        self._found()

    # ================================================================ التأسيس
    def _found(self):
        cfg, rng = self.cfg, self.rs.get("found")
        w = self.world
        x, y = w.n // 2, w.n // 2
        r = w.region(x, y)
        st = Settlement(0, "القرية", x, y, 0)
        r.settled = 0
        w.settlements.append(st)
        self.mass[0] = 0

        # المحرّم يقع على الجبل الأبيض: أخصب بقعة في العالم
        bx, by = w.white_mountain
        w.region(bx, by).taboo = True

        god = self.history["god"]
        doc = FA.Doctrine(god, f"عهد {god}", FA.founding_tenets(god), 0, sect=0)
        st.doctrine = doc
        self.doctrines[0] = doc

        name_idx = {}
        for i, p in enumerate(PE.FOUNDERS):
            ov = PE.trait_overrides(p)
            g = G.Genome.seedling(rng, ov)
            prog = Program(innate(g, rng))
            a = Agent(self.next_id, p["n"], p["house"], g, prog,
                      p["sex"], p["age"], -p["age"], cfg, rng)
            self.next_id += 1
            a.settlement = 0
            a.backstory = p["story"]
            a.title = p["craft"] if p["craft"] != "—" else ""
            a.faith = PE.STANCE_FAITH[p["stance"]]
            if p["stance"] == "cleric":
                a.clergy = True
            if p["stance"] == "skeptic":
                a.doubt = 0.35 + 0.3 * rng.random()
            a.prestige = 0.4 * (a.age / 20.0) + 2.0 * g.t[G.CONSCIENT] * (a.age > 20)
            a.dominance = 2.4 * g.t[G.DOMINANCE] * (a.age > 16)
            self.agents[a.id] = a
            st.members.append(a.id)
            name_idx[p["n"]] = a.id

        # الأنساب
        for child, mother, father in PE.KIN:
            ci = name_idx.get(child)
            if ci is None:
                continue
            c = self.agents[ci]
            for who, attr in ((mother, "mother"), (father, "father")):
                if who and who in name_idx:
                    pid = name_idx[who]
                    setattr(c, attr, pid)
                    par = self.agents[pid]
                    par.children.append(ci)
                    c.bonds.kin.add(pid)
                    par.bonds.kin.add(ci)
                    c.bonds.reared_with.add(pid)
                    par.bonds.reared_with.add(ci)
                    c.bonds.bump(c.bonds.affection, pid, 1.5)
                    par.bonds.bump(par.bonds.affection, ci, 1.8)
        # الإخوة
        for a in self.agents.values():
            for b in self.agents.values():
                if a.id >= b.id:
                    continue
                if (a.mother != -1 and a.mother == b.mother) or \
                   (a.father != -1 and a.father == b.father):
                    a.bonds.kin.add(b.id); b.bonds.kin.add(a.id)
                    a.bonds.reared_with.add(b.id); b.bonds.reared_with.add(a.id)
                    a.bonds.bump(a.bonds.affection, b.id, 1.0)
                    b.bonds.bump(b.bonds.affection, a.id, 1.0)

        for x_, y_ in PE.UNIONS:
            if y_ and x_ in name_idx and y_ in name_idx:
                i, j = name_idx[x_], name_idx[y_]
                self.agents[i].bonds.partner = j
                self.agents[j].bonds.partner = i
                self.agents[i].bonds.bump(self.agents[i].bonds.affection, j, 1.6)
                self.agents[j].bonds.bump(self.agents[j].bonds.affection, i, 1.6)

        # زرع الماضي الذي لم يقع
        ri = self.rs.get("implant")
        for a in self.agents.values():
            HI.implant(a, self.history, ri, cfg, 0)
            FA.seed_conviction(a, doc, ri)
            if a.doubt > 0.2:                      # الشكّاك يبدأ أقلّ قناعة
                for k in a.conv:
                    a.conv[k] *= (1.0 - 0.7 * a.doubt)

        # معرفة البداية
        st.knowledge |= {"fire", "cord", "stone", "shelter"}
        st.granary = self._need(st) * 1.35
        self.chron.add(0, "founding",
                       f"أربعة وثلاثون إنسانًا في قرية واحدة، يحملون ذاكرة ألفي سنة "
                       f"لم يعشها أحد منهم. إلههم {god}، وغضبه — كما يقولون — عقاب.", 4.0)

    # ================================================================ الحلقة
    def run(self, years, on_year=None):
        cfg = self.cfg
        for _ in range(years):
            self.step()
            if on_year:
                on_year(self)
            if self.year % cfg.housekeep_every == 0:
                self.housekeep()
            if self.population() <= 0:
                self.chron.add(self.year, "extinction", "لم يبقَ أحد.", 5.0)
                break
        return self

    def housekeep(self):
        """تقليم ما يتراكم، ثم قياس الذاكرة الحقيقية والتوقّف عند السقف."""
        cfg = self.cfg
        if len(self.dead) > cfg.dead_cap * 1.25:
            self.dead = GD.trim(self.dead, cfg.dead_cap)
        ev = self.chron.events
        if len(ev) > cfg.event_cap * 1.25:
            keep = [e for e in ev if e.weight >= 2.0]
            minor = [e for e in ev if e.weight < 2.0]
            room = max(0, cfg.event_cap - len(keep))
            self.chron.events = sorted(keep + (minor[-room:] if room else []),
                                       key=lambda e: e.year)
        if cfg.mem_limit_mb:
            mb = GD.rss_mb()
            if mb and mb > cfg.mem_limit_mb:
                raise GD.MemoryCeiling(
                    f"بلغ الرنّ {mb:.0f} ميجابايت عند سنة {self.year:,} "
                    f"(السقف {cfg.mem_limit_mb}). تُوقف المحاكاة سالمةً.")
        return GD.rss_mb()

    def step(self):
        self.year += 1
        y = self.year
        cfg = self.cfg
        w = self.world
        w.step_climate(y, self.rs.get("climate"))

        for st in list(w.settlements):
            if st.pop() == 0 and self.mass.get(st.id, 0) == 0:
                continue
            ctx = self._context(st)
            self._actions(st, ctx)
            self._distribute(st)
            self._social(st)
            self._mating(st, ctx)
            self._multitude(st, ctx)
            self._politics(st)
            self._faith_phase(st)
            self._naturalism(st, self.rs.get('nat'))
            r_ = self.world.region(st.x, st.y)
            st.foul = CA.foul(r_, st.pop() + self.mass.get(st.id, 0), st.knowledge)
            st.literacy = CA.literacy(st, self.agents, cfg)

        self._trade()
        self._invent()
        self._disease()
        self._maladies(y)
        self._war()
        self._wrath()
        self._lifecycle()
        self._diffuse()
        w.rest_soil()
        self.names.age(y, self.rs.get('names'))
        rl = self.rs.get('books')
        for st in w.settlements:
            st.library.copy(rl, st.knowledge)
            st.library.decay(rl)
        for st in list(w.settlements):
            self._split(st)

        if y % cfg.snapshot_every == 0:
            self._snapshot()

    # ================================================================ السياق
    def _context(self, st):
        cfg = self.cfg
        pop = st.pop() + self.mass.get(st.id, 0)
        cap = self.world.capacity(st, T.yields(st.knowledge))
        need = self._need(st)
        # ما يُستورد يرفع ما تحتمله القرية فوق ما تنبته أرضها
        if st.granary > need:
            cap = max(cap, need * 1.15)
        provision = min(1.4, st.granary / max(0.6, need))
        ruler = self.agents.get(st.ruler)
        return dict(
            threat=min(1.0, st.unrest * 0.5 + max(0.0, pop / max(1.0, cap) - 1.0) * 0.5),
            crowding=min(1.0, pop / max(1.0, cap)),
            scarcity=max(0.0, min(1.0, 1.0 - provision)),
            surplus=max(0.0, min(1.0, provision - 1.0) * 2.5),
            provision=min(1.0, provision),
            ruled=1.0 if ruler is not None else 0.0,
            land=min(1.0, (cap / max(1.0, pop)) ** 0.45),
            cap=cap, pop=pop, ruler=ruler,
        )

    def _need(self, st):
        cfg = self.cfg
        n = 0.0
        for m in st.members:
            a = self.agents.get(m)
            if a is None:
                continue
            n += cfg.yearly_food_need if a.age >= cfg.adult_age else cfg.yearly_food_need * cfg.child_food_ratio
        n += self.mass.get(st.id, 0) * cfg.yearly_food_need * 0.9
        return max(0.5, n)

    # ================================================================ الأفعال
    def _actions(self, st, ctx):
        cfg = self.cfg
        rng = self.rs.get("act")
        enforce = self._enforcement(st)
        produced = 0.0
        for m in list(st.members):
            a = self.agents.get(m)
            if a is None or not a.alive:
                continue
            a.kin_need = self._kin_need(a)
            a.wrath_expectation = self._expectation(a, st)
            PS.update_fears(a, st, ctx, st.doctrine, rng)
            a.longing = self._longing(a)
            PG.fire('yearly', self, a, ctx, rng)   # آليات المساهمين
            if a.fertile(cfg):
                drive = (0.55 + 0.95 * a.eg.t[G.LUST]) * (1.0 - 0.5 * min(1.0, a.hunger))                     * (1.0 - 0.6 * a.illness)
                if a.bonds.partner in self.agents:
                    drive *= 0.55          # المرتبط أقلّ سعيًا لا معدومه
                a.af.fire(P_LUST, drive)
            # ما عاشه منذ قرارِه الأخير يُقيَّد الآن على **ذلك** الموقف
            # لا على موقف اليوم — فالنتيجة تتلو الفعل ولا تسبقه.
            if a.mem.raw:
                if a.last_fs:
                    room = 26 - len(a.prog.episodes)
                    for tr in a.mem.raw[:room]:
                        a.prog.episodes.append((a.last_fs, a.last_action, tr))
                a.mem.raw.clear()
            f = CN.evaluate(a, build_features(a, ctx))
            fs = sparse(f)
            a.last_fs = fs
            intent = CN.press(a)
            blocked = self._blocked_for(a, st, enforce)
            if a.longing > 0.30:                    # الحنين يحرّك القدم
                blocked = dict(blocked or {})
                blocked[M.A_WANDER] = blocked.get(M.A_WANDER, 0.0) - 1.7 * a.longing
                blocked[M.A_CONTEMPLATE] = blocked.get(M.A_CONTEMPLATE, 0.0) - 0.8 * a.longing
            adult = a.age >= cfg.adult_age
            n_acts = 3 if adult else 1
            for k in range(n_acts):
                act = decide(a.prog, f, rng, cfg.temperature, adult, blocked, intent)
                produced += self._do(a, act, st, ctx, fs, (1.0, 0.70, 0.45)[k], rng)
                a.last_action = act
        # الجماهير غير المسمّاة: تُحاكى إحصائيًا لكنها تنتج فعلًا
        m = self.mass.get(st.id, 0)
        if m:
            reg = self.world.region(st.x, st.y)
            per = 1.25 * reg.fertility * self.world.climate * T.yields(st.knowledge)
            produced += m * per * ctx["land"]
        st.granary += produced

    def _enforcement(self, st):
        """قدرة القرية على معاقبة من يخرق المحرّم — لا علاقة لها بما يعتقده هو."""
        d = st.doctrine
        if d is None:
            return 0.0
        n = max(1, st.pop())
        clergy = sum(1 for m in st.members
                     if m in self.agents and self.agents[m].clergy)
        ruler = self.agents.get(st.ruler)
        e = 0.5 * (clergy / n) * 6.0
        if ruler is not None:
            e += 0.5 * ruler.eg.t[G.CALLOUSNESS] * (0.4 + ruler.dominance / 6.0)
        return min(1.6, e)

    def _dissonance(self, a, key, weight, rng, tenet=None):
        """
        دليلٌ ناقض عقيدةً عنده. يحسم، وإن برّر ألّف تبريره من حياته هو،
        وإن راجع استدعى من حدّثه بها — فقد ينكشف كاذب.
        """
        route, _ = FA.resolve(a, key, weight, rng, self.cfg, self.year, tenet=tenet)
        if route == FA.RATIONALIZE:
            u = SP.rationalize(a, key, self.agents, self.world, rng, self.year)
            if u is not None:
                if len(a.riders) < 10 and u.text not in a.riders:
                    a.riders.append(u.text)
                a.said.append(u)
                if len(a.said) > 6:
                    del a.said[0]
        elif route == FA.REVISE:
            liar = SP.expose(a, self.agents, key, rng)
            if liar is not None:
                self.stats["exposed"] += 1
                self.chron.add(self.year, "exposed",
                               f"راجع {a.name} ما كان يعتقد، فانكشف أن "
                               f"{liar.name} حدّثه بما لا يعتقده هو.", 2.8)
        return route

    def _blocked_for(self, a, st, enforce):
        """
        ما يمتنع عنه *هذا* الإنسان: قناعته هو، زائد خوفه هو من العقاب.
        فالجَسور قليل الإيمان يخرق المحرّم بينما يلتزم به جاره.
        """
        d = st.doctrine
        if d is None:
            return None
        out = {}
        fear = enforce * (0.25 + a.eg.t[G.FEAR])
        for key, act, k in (("counting_stars", M.A_OBSERVE, 2.4),
                            ("white_mountain", M.A_WANDER, 0.8)):
            if key not in d.tenets:
                continue
            pen = k * a.conv.get(key, 0.0) + 1.4 * fear * (d.tenets[key].strength > 0.4)
            if pen > 0.15:
                out[act] = pen
        return out or None

    def _ressentiment(self, a, st):
        """
        كم يعلوه غيره، وكم يحمل عليهم. رقمٌ من الواقع لا من عندي.
        """
        pool = [self.agents[m] for m in st.members[:60] if m in self.agents]
        if len(pool) < 4:
            return 0.0, ()
        above = [b for b in pool if b.status() > a.status() + 1.2]
        if not above:
            return 0.0, ()
        share = len(above) / len(pool)
        borne = sum(a.bonds.resentment.get(b.id, 0.0) for b in above) / len(above)
        r = min(1.0, share * (0.35 + borne) * (0.5 + a.eg.t[G.NARCISSISM]) * 1.6)
        # الأفعال التي بها عَلَوا فعلًا — لا التي أظنّها أنا رفيعة
        acts = set()
        for b in above[:8]:
            if b.last_action >= 0:
                acts.add(b.last_action)
            if b.is_ruler:
                acts.add(M.A_SEIZE)
            if b.tribute < 0:
                acts.add(M.A_HOARD)
        return r, tuple(acts)

    def _longing(self, a):
        """
        الحنين إلى أقوى ما يتذكّره من خير — ولو لم يقع قط.
        وكلّما بعُد في الزمن صار أحلى: هكذا تشتدّ الرغبة في العودة إلى
        وادٍ لم يوجد، فتُحمَل الأقدام إلى حيث لا شيء.
        """
        best = None
        for t in a.mem.traces:
            if t.repressed or t.val < 0.5 or t.strength < 1.0:
                continue
            if best is None or t.strength * t.val > best.strength * best.val:
                best = t
        if best is None:
            return 0.0
        gone = max(1, self.year - best.year)
        return min(1.0, best.strength * best.val * (0.45 + min(1.0, gone / 320.0)))

    def _kin_need(self, a):
        n = 0.0
        for k in a.bonds.kin:
            b = self.agents.get(k)
            if b is not None and b.alive and (b.illness > 0.25 or b.hunger > 0.45):
                n += 0.4
        return min(1.0, n)

    def _expectation(self, a, st):
        gap = self._mean_gap(st)
        since = self.year - (st.records[-1] if st.records else
                             (st.wrath_seen[-1] if st.wrath_seen else 0))
        return FA.wrath_expectation(a, st.doctrine, since, gap)

    def _mean_gap(self, st):
        r = st.records or st.wrath_seen
        if len(r) < 2:
            return None
        gaps = [r[i + 1] - r[i] for i in range(len(r) - 1)]
        return sum(gaps) / len(gaps)

    # ---------------------------------------------------------------- تنفيذ
    def _do(self, a, act, st, ctx, fs, w, rng):
        cfg = self.cfg
        y = self.year
        reg = self.world.region(st.x, st.y)
        clim = self.world.climate
        food = 0.0
        kind, val, tag = None, 0.0, ""
        vg = (0.40 + 0.60 * a.eg.t[G.VIGOR]) * (0.55 + 0.45 * a.health)
        if a.age < cfg.adult_age:
            vg *= 0.20 + 0.62 * (a.age / cfg.adult_age)
        know = st.knowledge

        if act == M.A_FORAGE:
            food = 3.45 * reg.fertility * clim * vg * (1.0 + 0.4 * T.effect(know, "food"))
            kind, val = (K_FEAST, 0.25) if food > 0.9 else (K_HUNGER, -0.15)
        elif act == M.A_FARM:
            if "farming" in know:
                food = 6.00 * reg.fertility * clim * vg * T.yields(know) * (0.6 + 0.5 * a.skills[0])
                if st.star_known:
                    food *= 1.18          # يزرعون في وقته لأنهم قرأوا السماء
                self.world.work_soil(reg, 0.030)
                a.skills[0] = min(1.0, a.skills[0] + 0.03)
                kind, val = K_CRAFT, 0.30
            else:
                food = 1.90 * reg.fertility * clim * vg
                kind, val = K_HUNGER, -0.05
        elif act == M.A_HERD:
            if "herding" in know:
                food = 4.40 * (0.4 + reg.game) * clim * vg * T.yields(know)
                kind, val = K_CRAFT, 0.22
            else:
                food = 2.40 * reg.game * clim * vg
                kind, val = K_JOURNEY, 0.10
        elif act == M.A_BUILD:
            st.walls += 0.25 * vg
            if a.is_ruler:
                st.monuments += 0.15
            PW.prestige_gain(a, 0.05 * w)
            kind, val = K_CRAFT, 0.20
        elif act == M.A_CRAFT:
            a.skills[1] = min(1.0, a.skills[1] + 0.04)
            food = 0.55 * vg
            PW.prestige_gain(a, 0.04 * w)
            # من صهر المعدن تنفّس دخانه. ولا يظهر أثرُه في سنةٍ ولا في
            # عشر — يظهر بعد عمرٍ من الصنعة، فلا يربط أحدٌ بينهما.
            # (Ramazzini 1700 في أمراض أهل الحِرَف.)
            heat = sum(1 for k in ("copper", "bronze", "iron", "glass")
                       if k in know)
            if heat:
                a.smelt = min(1.0, a.smelt + 0.012 * heat)
            kind, val = K_CRAFT, 0.25
        elif act == M.A_REST:
            a.fatigue = max(0.0, a.fatigue - 0.55 * w)
            tr = a.mem.dream(rng, y, cfg.dream_store_rate)
            if tr is not None and tr.kind == K_VISION:
                awe_strike(a.af, a.eg, 0.35)
            kind, val = None, 0.0
        elif act == M.A_SOCIALIZE:
            other = self._pick(st, a, rng)
            if other is not None:
                self._talk(a, other, rng, st)
                if a.school >= 0 and other.school >= 0 and a.school != other.school:
                    d = LB.debate(a, other, self.world, rng)
                    if d is not None:
                        kindd, win, lose = d
                        self.stats["debates"] = self.stats.get("debates", 0) + 1
                        if kindd == "تحوّل":
                            self.stats["converts"] = self.stats.get("converts", 0) + 1
                        else:
                            self.stats["hardened"] = self.stats.get("hardened", 0) + 1
                bo = SP.boast(a, self.agents, self.world, rng, y)
                if bo is not None:
                    u, bkind = bo
                    a.said.append(u)
                    if len(a.said) > 6:
                        del a.said[0]
                    self.stats["boasts"] = self.stats.get("boasts", 0) + 1
                    if SP.catch_boast(other, a, bkind, rng):
                        self.stats["boast_caught"] = self.stats.get("boast_caught", 0) + 1
                        self.chron.add(y, "exposed",
                                       f"كذّب {other.name} ما تفاخر به {a.name}.", 2.2)
                kind, val, tag = K_LOVE, 0.18, "صحبة"
        elif act == M.A_COURT:
            kind, val = self._court(a, st, rng)
        elif act == M.A_TEND:
            tgt = self._neediest(a, st)
            if tgt is not None:
                self._dose(a, tgt, st, rng, y)
                heal = 0.30 * (0.4 + a.eg.t[G.CARE]) * (1.0 + T.effect(know, "mort") * -1.0)
                tgt.illness = max(0.0, tgt.illness - heal)
                tgt.bonds.bump(tgt.bonds.affection, a.id, 0.45)
                appraise(tgt.af, tgt.eg, congruence=0.5, other_gain=-0.4, tenderness=0.4)
                PW.prestige_gain(a, 0.10 * w)
                kind, val, tag = K_LOVE, 0.35, "رعاية"
        elif act == M.A_TEACH:
            kind, val = self._teach(a, st, rng)
        elif act == M.A_LEARN:
            kind, val = self._learn(a, st, rng)
        elif act == M.A_QUARREL:
            other = self._pick(st, a, rng, hostile=True)
            if other is not None:
                self._quarrel(a, other, rng)
                kind, val, tag = K_BETRAYAL, -0.30, "خصام"
        elif act == M.A_ATTACK:
            # حين يجتمع فرقُ القوّة وقلّةُ الاكتراث قد يقع الإكراه بدل الضرب
            if (a.age >= cfg.adult_age and a.eg.t[G.CALLOUSNESS] > 0.55
                    and a.eg.t[G.LUST] > 0.5 and a.eg.t[G.HONESTY] < 0.4
                    and rng.random() < 0.16):
                self._coerce(a, st, rng)
                kind, val = K_VIOLENCE, 0.20
            else:
                kind, val = self._attack(a, st, rng)
        elif act == M.A_RECONCILE:
            other = a.bonds.worst()
            if other is not None and other in self.agents:
                b = self.agents[other]
                drop = 0.55 * (0.3 + a.eg.t[G.AGREEABLE] + a.eg.t[G.HONESTY])
                a.bonds.bump(a.bonds.resentment, other, -drop)
                b.bonds.bump(b.bonds.resentment, a.id, -drop * 0.7)
                b.bonds.bump(b.bonds.affection, a.id, 0.22)
                appraise(a.af, a.eg, congruence=0.4)
                appraise(b.af, b.eg, congruence=0.35, other_gain=-0.25)
                kind, val, tag = K_RECONCILE, 0.42, "تغاضٍ"
        elif act == M.A_CONTEMPLATE:
            res, high = self._ressentiment(a, st)
            reflect(a, cfg, rng, y, res, high)
            flip = CN.revise(a)
            if flip is not None:
                a.recanted = flip
                self.stats["mind_changed"] = self.stats.get("mind_changed", 0) + 1
                self.chron.add(
                    y, "recant",
                    f"غيّر {a.name} رأيه في «{flip.name}»: كان يراه "
                    f"{'خيرًا فصار شرًّا' if flip.value < 0 else 'شرًّا فصار خيرًا'}"
                    f" بعد {flip.evidence} موقفًا.", 3.2)
            made = CN.form(a, rng, y, M.NF)
            if made is not None:
                self.chron.add(y, "concept",
                               f"صاغ {a.name} مفهومًا جديدًا: {made.render()}", 3.6)
            CN.derive(a, rng, y)
            if len(a.remedies) >= 3 and rng.random() < 0.05:
                hb = LB.write_herbal(a, st, self, rng)
                if hb is not None:
                    self.chron.add(y, "herbal",
                                   f"دوّن {a.name} ما جرّب من العقاقير: "
                                   f"{hb.thesis[:90]}", 3.4)
                    self.stats["herbals"] = self.stats.get("herbals", 0) + 1
            urge = 0.05 + (0.30 if a.recanted is not None else 0.0)
            if LB.can_write(a, st.knowledge) and rng.random() < urge * a.eg.t[G.REASONING]:
                bk = LB.write_treatise(a, st, self, rng)
                if bk is not None:
                    a.school = bk.school
                    if bk.split:
                        self.chron.add(
                            y, "schism",
                            f"انشقّ {a.name} عن {bk.split} في مسألة «{bk.topic_name}»: "
                            f"يقول {'بل هي كذلك' if bk.sign > 0 else 'ليست كذلك'} — "
                            f"{bk.thesis}", 6.0)
                        self.stats["schisms"] = self.stats.get("schisms", 0) + 1
                    self.chron.add(y, "book",
                                   f"كتب {a.name} [{bk.stance}] {bk.kind} "
                                   f"«{bk.title}»: {bk.thesis}.", 4.0)
            it = CN.intend(a, rng, y)
            if it is not None:
                self.chron.add(y, "intention",
                               f"عقد {a.name} نيّةً على {it.years} سنين.", 1.8)
            a.fatigue = max(0.0, a.fatigue - 0.1)
            if a.mem.awe() > 0.35 and rng.random() < 0.06 * a.eg.t[G.CREDULITY]:
                self._new_myth(a, st, rng)
            kind, val, tag = K_WONDER, 0.20, "تأمّل"
        elif act == M.A_RITUAL:
            cost = 0.16 * (1.0 + (st.doctrine.complexity * 0.02 if st.doctrine else 0))
            st.granary = max(0.0, st.granary - cost)
            a.tribute += cost
            if st.doctrine:
                st.doctrine.ritual_debt += 0.03
            a.faith = min(1.0, a.faith + 0.02)
            a.af.s[E_AWE] *= 0.42      # الرِّيتة تُفرِغ الرهبة، فلا تدوم الحاجة إليها
            st.unrest = max(0.0, st.unrest - 0.03)   # الطقس المكلف يشدّ العصب فعلًا
            kind, val, tag = K_RITUAL, 0.28, "طقس"
        elif act == M.A_PREACH:
            kind, val = self._preach(a, st, rng)
        elif act == M.A_SCHEME:
            kind, val = self._scheme(a, st, rng)
        elif act == M.A_SEIZE:
            kind, val = self._seize(a, st, rng)
        elif act == M.A_OBSERVE:
            kind, val = self._observe(a, st, rng)
        elif act == M.A_WANDER:
            kind, val = self._wander(a, st, rng)
        elif act == M.A_HOARD:
            take = min(st.granary * 0.10, 0.5)
            st.granary -= take
            a.tribute -= take * 0.4
            a.hunger = max(0.0, a.hunger - 0.2)
            kind, val, tag = K_FEAST, 0.15, "كنز"

        a.fatigue = min(1.5, a.fatigue + 0.22 * w)

        if kind is not None:
            a.mem.store(kind, y, val=val, strength=0.9 + 0.5 * abs(val),
                        truth=1.0, src=S_LIVED, tag=tag)
        return food * w * ctx["land"]

    # ---------------------------------------------------------------- مساعِد
    def _pick(self, st, a, rng, hostile=False):
        n = len(st.members)
        if n < 2:
            return None
        for _ in range(6):
            oid = st.members[rng.randrange(n)]
            if oid == a.id:
                continue
            b = self.agents.get(oid)
            if b is None or not b.alive:
                continue
            if hostile:
                if a.bonds.resentment.get(oid, 0.0) > 0.25 or rng.random() < 0.35:
                    return b
                continue
            return b
        return None

    def _dose(self, healer, patient, st, rng, y):
        """
        يمدّ يده إلى نبتةٍ ويسقيها. **هذا هو كلُّ الطبّ عندهم في أوّله.**

        لا يعرف ما بالمريض — يرى أظهرَ عرَضٍ عليه. ولا يعرف ما في النبتة
        — يعرف ما رآه منها من قبل، إن كان رآه. والباقي رمية.
        """
        if not patient.sick:
            return None
        signs = MD.signs_of(patient, self.maladies)
        sign = HL.top_sign(signs, MD.SIGNS)
        if sign < 0:
            return None

        rem, fresh = HL.pick(healer, sign, rng)
        if rem is None:
            here = self.flora_at[self.world.region(st.x, st.y).biome]
            if not here:
                return None
            pl = here[rng.randrange(len(here))]
            # المقدار في أوّل مرّةٍ حَدْس، وكفُّه يزن ولا يكيل
            dose = 0.25 + 1.15 * rng.random()
            prep = FL.PREPS[rng.randrange(len(FL.PREPS))]
            rem = HL.Remedy(pl.id, sign, prep, dose, y)
            new_one = True
        else:
            new_one = False
            # ويميل إلى ما جرّب، ويزيد المقدار قليلًا إن لم يرَ نفعًا
            dose = rem.dose * (1.0 + (0.20 if rem.trust() < 0.1 else 0.0))

        before = MD.burden(patient, self.maladies)
        HL.try_on(healer, patient, rem.plant, rem.prep, dose,
                  self.maladies, self.plants, rng, y)
        after = MD.burden(patient, self.maladies)
        died = patient.health <= 0.0
        # **المنهج التجريبي يغيّر ما يُستخلَص من التجربة نفسها.**
        #
        # قبله: من لم يرَ فرقًا عدّه نجاحًا في أكثر الأحيان — وهو ميل
        # التصديق. وبعده: تُقيَّد النتيجة الفارغة فارغةً. ولهذا لم يصر
        # الطبُّ علمًا إلا بعد أن صار في القوم منهجٌ يُحصي ما لم ينفع
        # كما يُحصي ما نفع.
        HL.learn(healer, rem, before, after, died, rng,
                 rigour=("method" in st.knowledge))
        if new_one:
            HL.remember(healer, rem)
        self.stats["doses"] = self.stats.get("doses", 0) + 1
        if died:
            self.stats["killed_by_cure"] = self.stats.get("killed_by_cure", 0) + 1
            self._kill(patient, "دواء")
        return rem

    def _neediest(self, a, st=None):
        """
        من يداويه؟ قريبَه أوّلًا — ثم أيَّ مريضٍ في قريته.

        وكان لا يداوي إلا قريبًا، فكانت الجرعات ألفًا ومئة في سبعمئة
        سنة مقابل تسعة آلاف إصابة: أي أن تسعة أعشار المرضى لا يُداوَون
        أصلًا، فلا تجربةَ ولا تعلّم. والمداوي في القرية يُدعى إلى غير
        أهله، ومن هنا يصير له باعٌ يُذكر.
        """
        best, bv = None, 0.2
        for k in a.bonds.kin:
            b = self.agents.get(k)
            if b is not None and b.alive and b.illness > bv:
                best, bv = b, b.illness
        if best is None and st is not None:
            for m in st.members:
                b = self.agents.get(m)
                if (b is not None and b.alive and b.id != a.id
                        and b.illness > bv):
                    best, bv = b, b.illness
        return best

    def _talk(self, a, b, rng, st):
        """الحديث ينقل الحكايات — وأحيانًا تُلتقط حكاية الغير كتجربة ذاتية."""
        cfg = self.cfg
        sim = 1.0 - a.g.distance(b.g)
        warmth = 0.30 * (a.eg.t[G.AGREEABLE] + b.eg.t[G.AGREEABLE]) * sim
        a.bonds.bump(a.bonds.affection, b.id, warmth)
        b.bonds.bump(b.bonds.affection, a.id, warmth * 0.9)
        a.bonds.bump(a.bonds.trust, b.id, warmth * 0.5)
        appraise(a.af, a.eg, congruence=0.25, tenderness=warmth)
        appraise(b.af, b.eg, congruence=0.22)

        if b.concepts and len(a.concepts) < CN.MAX_CONCEPTS                 and rng.random() < 0.10 * (0.3 + a.eg.t[G.CREDULITY]):
            # صاحبُ المذهب يتكلّم في مذهبه. وكان يُنقل عنه واحدٌ من
            # تسعةٍ بالقرعة، فيندر أن يقع على المسألة التي له فيها
            # قول — فلا يُورَّث المذهب ولا يجتمع عليه اثنان.
            src = None
            if b.school >= 0:
                s = self.world.schools.get(b.school)
                if s is not None and rng.random() < 0.62:
                    for cc in b.concepts:
                        if cc.key() == s.topic:
                            src = cc
                            break
            if src is None:
                src = rng.choice(b.concepts)
            if CN.transplant(src, b.concepts, a, rng) is not None:
                # ومن أخذ الفكرة أخذ معها حكمَ من لقّنه إيّاها
                if LB.taught_school(b, a, src, self.world, rng):
                    self.stats["joined"] = self.stats.get("joined", 0) + 1
        # الرواية تنتقل فتتغيّر: يشتدّ إسنادها عند الواثق ويلين عند
        # الشاكّ، ويكبر رقمُها، ويصير بطلُها من معارف السامع. فلا يبقى
        # لدى اثنين سمعا من رجلٍ واحد خبرٌ واحد.
        if b.said and len(a.said) < 6 and rng.random() < 0.14 * (0.3 + a.eg.t[G.CREDULITY]):
            src_u = rng.choice(b.said)
            a.said.append(SP.retell(src_u, b, a, rng, cfg.meme_drift,
                                    self.year, self.agents))
            self.stats["retold"] = self.stats.get("retold", 0) + 1
        if b.mem.traces and rng.random() < cfg.contagion_rate * (0.3 + a.eg.t[G.CREDULITY]):
            src = max(b.mem.traces, key=lambda t: t.strength * (0.5 + abs(t.val)))
            # تُخزَّن كأنها حدثت له هو
            a.mem.store(src.kind, src.year, who=src.who, val=src.val * 0.85,
                        strength=src.strength * 0.7, truth=0.0,
                        src=S_TOLD, tag=src.tag)

    def _court(self, a, st, rng):
        cfg = self.cfg
        if a.age < cfg.menarche:
            return None, 0.0
        best, bv = None, 0.0
        n = len(st.members)
        for _ in range(min(9, n + 2)):
            b = self.agents.get(st.members[rng.randrange(n)])
            if b is None or not b.alive or not a.can_pair(b, cfg):
                continue
            v = (0.5 + b.eg.t[G.VIGOR]) * (0.4 + a.bonds.affection.get(b.id, 0.0))
            v *= (0.6 + 0.5 * b.status() / 6.0)
            v *= rng.gauss(1.0, 0.25)
            if v > bv:
                best, bv = b, v
        if best is None:
            return None, 0.0
        b = best
        mutual = (0.55 + b.eg.t[G.LUST]) \
            * (0.55 + b.bonds.affection.get(a.id, 0.0)
               + 0.5 * b.bonds.attraction.get(a.id, 0.0)) \
            * (0.65 + a.status() / 8.0)
        a.bonds.bump(a.bonds.attraction, b.id, 0.5)
        appraise(a.af, a.eg, allure=0.6)
        if mutual * rng.gauss(1.0, 0.3) > 0.34:
            a.af.p[P_LUST] *= 0.25
            b.af.p[P_LUST] *= 0.45
            b.bonds.bump(b.bonds.attraction, a.id, 0.45)
            a.bonds.bump(a.bonds.affection, b.id, 0.35)
            b.bonds.bump(b.bonds.affection, a.id, 0.35)
            appraise(b.af, b.eg, allure=0.5, congruence=0.3)
            # الغيرة
            for who in (a.bonds.partner, b.bonds.partner):
                p = self.agents.get(who)
                if p is not None and p.id not in (a.id, b.id) and rng.random() < 0.55:
                    appraise(p.af, p.eg, blame_other=0.8, status_delta=-0.7,
                             norm_violation=0.6)
                    rival = b.id if who == a.bonds.partner else a.id
                    p.bonds.bump(p.bonds.resentment, rival, 0.7)
                    p.mem.store(K_BETRAYAL, self.year, who=rival, val=-0.7,
                                strength=1.5, truth=1.0, src=S_LIVED, tag="غيرة")
            if a.bonds.partner not in self.agents and b.bonds.partner not in self.agents:
                a.bonds.partner = b.id
                b.bonds.partner = a.id
            return K_LOVE, 0.55
        appraise(a.af, a.eg, status_delta=-0.25)
        return K_LOVE, -0.15

    def _teach(self, a, st, rng):
        pupil = None
        n = len(st.members)
        for _ in range(5):
            b = self.agents.get(st.members[rng.randrange(n)])
            if b is not None and b.alive and b.id != a.id and b.age < a.age:
                pupil = b
                break
        if pupil is None:
            return None, 0.0
        boost = 1.0 + T.effect(st.knowledge, "teach")
        # نقل حكمة — مع تشويه
        if a.prog.maxims and len(pupil.prog.maxims) < 14:
            m = rng.choice(a.prog.maxims)
            if rng.random() < 0.55 * boost * (0.3 + pupil.eg.t[G.CREDULITY]):
                pupil.prog.maxims.append(mutate_maxim(m, rng, self.cfg.meme_drift))
        # نقل الوصفات — وبها وحدها يتراكم الطبّ.
        #
        # بغير هذا يبدأ كلُّ مداوٍ من الصفر ويموت وما عنده، فيبقى طبُّهم
        # بعد تسعمئة سنة **لا أنفعَ من رميةٍ عشوائية** (قِسناه: 0.04
        # مقابل 0.06). والمعرفة التي لا تُنقل ليست معرفةَ قوم.
        if a.remedies and rng.random() < 0.60 * boost:
            got = HL.teach(a, pupil, rng)
            if got is not None:
                self.stats["recipes_taught"] =                     self.stats.get("recipes_taught", 0) + 1
        # نقل مهارة وعقيدة
        for i in range(4):
            pupil.skills[i] = max(pupil.skills[i], a.skills[i] * 0.65)
        if a.concepts and len(pupil.concepts) < CN.MAX_CONCEPTS                 and rng.random() < 0.70 * (0.3 + pupil.eg.t[G.CREDULITY]):
            src = rng.choice(a.concepts)
            CN.transplant(src, a.concepts, pupil, rng)
        pupil.faith += (a.faith - pupil.faith) * 0.12 * (0.3 + pupil.eg.t[G.CREDULITY])
        FA.transmit(a, pupil, rng, pull=0.07)
        pupil.bonds.bump(pupil.bonds.affection, a.id, 0.30)
        PW.prestige_gain(a, 0.14)
        pupil.mem.store(K_TEACHING, self.year, who=a.id, val=0.3,
                        strength=1.0, truth=1.0, src=S_LIVED, tag="تعلّم")
        return K_TEACHING, 0.30

    def _learn(self, a, st, rng):
        tutor, bv = None, 0.0
        n = len(st.members)
        for _ in range(5):
            b = self.agents.get(st.members[rng.randrange(n)])
            if b is None or not b.alive or b.id == a.id:
                continue
            v = b.prestige + 0.5 * b.status()      # انحياز الهيبة (Henrich)
            if v > bv:
                tutor, bv = b, v
        if tutor is None:
            return None, 0.0
        if st.library.books and rng.random() < 0.35:
            got = LB.read(a, st, rng, self)
            if got is not None:
                bk, what = got
                if bk.kind == LB.KIND_HERBAL and bk.recipes:
                    for (pl, sg, pr, ds, gd, bd, dd) in bk.recipes:
                        if len(a.remedies) >= HL.MAX_REMEDIES:
                            break
                        if any(r.plant == pl and r.sign == sg
                               for r in a.remedies):
                            continue
                        rm = HL.Remedy(pl, sg, pr, ds, bk.born,
                                       src=f"قرأها في «{bk.title}»")
                        rm.good, rm.bad = gd // 2, bd // 2
                        a.remedies.append(rm)
                        self.stats["recipes_read"] =                             self.stats.get("recipes_read", 0) + 1
                if (bk.kind == LB.KIND_TREATISE and a.school != bk.school
                        and LB.persuaded(a, bk, self.world, rng)):
                    a.school = bk.school
                    self.stats["joined"] = self.stats.get("joined", 0) + 1
                if "الدورة" in what:
                    self.chron.add(self.year, "discovery",
                                   f"قرأ {a.name} {bk.label()} فعرف ما كشفه "
                                   f"صاحبه ومات دونه.", 4.6)
        for i in range(4):
            a.skills[i] = max(a.skills[i], tutor.skills[i] * 0.6)
        if tutor.prog.maxims and len(a.prog.maxims) < 14 and rng.random() < 0.45:
            a.prog.maxims.append(mutate_maxim(rng.choice(tutor.prog.maxims),
                                              rng, self.cfg.meme_drift))
        a.faith += (tutor.faith - a.faith) * 0.10 * (0.3 + a.eg.t[G.CREDULITY])
        FA.transmit(tutor, a, rng, pull=0.06)
        # قراءة السجلّ: ما دُوّن يمكن أن يُفهم، ومن فهمه لم يعد يصدّق العقاب
        if st.known_period and not a.heretic and "writing" in st.knowledge:
            grasp = (0.25 + a.eg.t[G.REASONING]) * (1.2 - a.eg.t[G.CREDULITY]) * 0.30
            if rng.random() < grasp:
                a.heretic = True
                a.doubt = 1.0
                a.faith = max(0.0, a.faith - 0.7)
                a.conv["wrath_is_sin"] = 0.0
                a.conv["counting_stars"] = 0.0
                a.title = "المُنكِر"
            elif a.eg.t[G.CREDULITY] > 0.58 and rng.random() < 0.28:
                # قرأ الرقم نفسه فازداد يقينًا. الدليل لا يُقنع وحده.
                a.faith = min(1.0, a.faith + 0.16)
                a.doubt = max(0.0, a.doubt - 0.20)
                for key in a.conv:
                    a.conv[key] = min(1.6, a.conv[key] + 0.18)
        return K_TEACHING, 0.22

    def _coerce(self, a, st, rng):
        """
        فعلُ إكراهٍ بين بالغَين. يُسجَّل كحدثٍ ونتائجه فقط: أثرُ صدمةٍ
        في ذاكرة من وقع عليه، وضغينةٌ ودمٌ بين بيتين، وأبوّةٌ قد تلتبس،
        وخطرُ انكشافٍ يهوي بمقام الفاعل. لا وصف ولا تفصيل.
        """
        cfg = self.cfg
        if a.age < cfg.adult_age:
            return None
        pool = [self.agents[m] for m in st.members if m in self.agents]
        cand = [b for b in pool
                if b.id != a.id and b.sex != a.sex and b.age >= cfg.adult_age]
        if not cand:
            return None
        b = rng.choice(cand)
        power = (a.dominance + a.prestige) - (b.dominance + b.prestige)
        if power < 1.0:
            return None
        appraise(b.af, b.eg, threat=1.0, blame_other=1.0, status_delta=-0.9,
                 norm_violation=1.0, loss=0.6)
        b.bonds.bump(b.bonds.resentment, a.id, 1.4)
        b.mem.store(K_VIOLENCE, self.year, who=a.id, val=-0.95, strength=2.1,
                    truth=1.0, src=S_LIVED, tag="إكراه")
        b.health -= 0.10
        for k in b.bonds.kin:
            kin = self.agents.get(k)
            if kin is not None and kin.alive:
                kin.bonds.bump(kin.bonds.resentment, a.id, 1.0)
                appraise(kin.af, kin.eg, blame_other=1.0, status_delta=-0.5)
        if b.sex == FEMALE and b.fertile(cfg) and b.pregnant == 0                 and rng.random() < 0.20:
            b.pregnant = 1
            b.pregnancy_by = a.id
        self.stats["coercion"] = self.stats.get("coercion", 0) + 1
        # ينكشف أحيانًا فيسقط مقامه، ويُفلت أحيانًا
        if rng.random() < 0.35 + 0.3 * (1.0 - a.dominance / 8.0):
            a.prestige = max(0.0, a.prestige - 1.2)
            st.unrest = min(2.0, st.unrest + 0.10)
            self.chron.add(self.year, "coercion",
                           f"أكرَه {a.name} {b.name}، وعُرف ذلك.", 2.6)
        return b

    def _quarrel(self, a, b, rng):
        wins = (a.status() + a.eg.t[G.DOMINANCE] * 3) > \
               (b.status() + b.eg.t[G.DOMINANCE] * 3) * rng.gauss(1.0, 0.3)
        win, lose = (a, b) if wins else (b, a)
        appraise(win.af, win.eg, status_delta=0.35, congruence=0.2)
        appraise(lose.af, lose.eg, status_delta=-0.55, blame_other=0.6, norm_violation=0.3)
        lose.bonds.bump(lose.bonds.resentment, win.id, 0.45)
        win.bonds.bump(win.bonds.resentment, lose.id, 0.15)
        PW.dominance_gain(win, 0.12)
        lose.mem.store(K_BETRAYAL, self.year, who=win.id, val=-0.45,
                       strength=1.2, truth=1.0, src=S_LIVED, tag="مهانة")

    def _attack(self, a, st, rng):
        tid = a.bonds.worst()
        b = self.agents.get(tid) if tid is not None else None
        motive = b is not None
        if b is None or not b.alive:
            b = self._pick(st, a, rng, hostile=True)
        if b is None:
            return None, 0.0
        if not motive:
            # لا ضغينة سابقة. يقع الفعل من ضيقٍ لا من حساب، ثم — وهذا هو
            # المهمّ — يصنع له صاحبه سببًا في ذاكرته بعد وقوعه، فيصدّقه.
            a.mem.store(K_BETRAYAL, self.year, who=b.id, val=-0.7,
                        strength=1.5, truth=0.0, src=S_CONFAB, tag="سببٌ صُنع بعد الفعل")
            a.bonds.bump(a.bonds.resentment, b.id, 0.8)
        leth = self.cfg.violence_lethality * (1.0 + T.effect(st.knowledge, "leth"))
        power = (0.4 + a.eg.t[G.VIGOR]) * (0.5 + a.skills[2]) * rng.gauss(1.0, 0.3)
        defence = (0.4 + b.eg.t[G.VIGOR]) * (0.5 + b.skills[2])
        a.skills[2] = min(1.0, a.skills[2] + 0.05)
        if power > defence:
            harm = leth * (0.6 + a.eg.t[G.CALLOUSNESS])
            b.health -= harm
            appraise(b.af, b.eg, threat=0.9, blame_other=1.0, status_delta=-0.8,
                     norm_violation=0.8)
            b.bonds.bump(b.bonds.resentment, a.id, 1.0)
            b.mem.store(K_VIOLENCE, self.year, who=a.id, val=-0.85,
                        strength=1.8, truth=1.0, src=S_LIVED, tag="ضرب")
            PW.dominance_gain(a, 0.35)
            if b.health <= 0.0:
                self._kill(b, "قتل", killer=a)
                a.kills += 1
                self.stats["murders"] += 1
                self.chron.add(self.year, "murder",
                               f"قتل {a.label()} {b.label()}.", 1.6)
                for k in b.bonds.kin:
                    kin = self.agents.get(k)
                    if kin is not None and kin.alive:
                        kin.bonds.bump(kin.bonds.resentment, a.id, 1.3)
                        appraise(kin.af, kin.eg, loss=1.0, blame_other=1.0)
                        kin.mem.store(K_DEATH, self.year, who=a.id, val=-0.95,
                                      strength=2.0, truth=1.0, src=S_LIVED, tag="ثأر")
            return K_VIOLENCE, 0.30 * (0.3 + a.eg.t[G.CALLOUSNESS])
        a.health -= leth * 0.5
        appraise(a.af, a.eg, status_delta=-0.6, blame_other=0.4)
        return K_VIOLENCE, -0.45

    def _preach(self, a, st, rng):
        if st.doctrine is None:
            return None, 0.0
        heard = 0
        n = len(st.members)
        pull = (0.3 + a.eg.t[G.EXTRAVERSION]) * (0.4 + a.prestige / 5.0)
        spoken = None
        if SP.will_lie(a, rng, stakes=0.5 + a.wrath_expectation):
            spoken = SP.lie(a, "wrath_is_sin", self.agents, self.world,
                            rng, self.year, st.doctrine.god)
            a.said.append(spoken)
            if len(a.said) > 6:
                del a.said[0]
            self.stats["lies"] += 1
            PW.dominance_gain(a, 0.20)
        for _ in range(min(6, n)):
            b = self.agents.get(st.members[rng.randrange(n)])
            if b is None or not b.alive or b.id == a.id:
                continue
            heard += 1
            gain = 0.06 * pull * (0.2 + b.eg.t[G.CREDULITY]) * (1.0 - b.doubt)
            b.faith = min(1.0, b.faith + gain)
            FA.transmit(a, b, rng, pull=0.09 * pull)
            awe_strike(b.af, b.eg, 0.15 * pull)
            if spoken is not None:
                # يخزّنها السامع منسوبةً إلى قائلها. من هنا وحده ينكشف الكذب.
                b.mem.store(K_VISION, self.year, who=a.id, val=0.6,
                            strength=1.1 + 0.6 * b.eg.t[G.CREDULITY], truth=0.0,
                            src=S_TOLD, tag="خطبة")
                for k in st.doctrine.tenets:
                    b.conv[k] = min(1.6, b.conv.get(k, 0.0) + 0.05 * pull)
            if a.heretic:
                b.doubt = min(1.0, b.doubt + 0.05 * pull * (0.3 + b.eg.t[G.REASONING]))
                b.faith = max(0.0, b.faith - 0.05 * pull)
        if not a.clergy and a.faith > 0.5 and rng.random() < 0.05 + 0.1 * a.eg.t[G.NARCISSISM]:
            a.clergy = True
            a.title = "كاهن"
            self.chron.add(self.year, "cleric", f"صار {a.name} كاهنًا.", 1.2)
        PW.prestige_gain(a, 0.10 * heard * 0.2)
        PW.dominance_gain(a, 0.05 * a.eg.t[G.MACHIAVELLIAN])
        return K_RITUAL, 0.30

    def _scheme(self, a, st, rng):
        ruler = self.agents.get(st.ruler)
        allies = 0
        n = len(st.members)
        for _ in range(min(5, n)):
            b = self.agents.get(st.members[rng.randrange(n)])
            if b is None or not b.alive or b.id == a.id:
                continue
            if ruler is not None and b.bonds.resentment.get(ruler.id, 0.0) > 0.2:
                b.bonds.bump(b.bonds.affection, a.id, 0.25)
                a.bonds.bump(a.bonds.trust, b.id, 0.3)
                allies += 1
        PW.dominance_gain(a, 0.10 + 0.05 * allies)
        st.unrest = min(2.0, st.unrest + 0.02 * allies)
        return K_BETRAYAL, 0.20

    def _seize(self, a, st, rng):
        ruler = self.agents.get(st.ruler)
        if ruler is None:
            PW.install(st, a, self.agents, self.year)
            self.chron.add(self.year, "rule", f"تولّى {a.name} أمر {st.name}.", 2.0)
            return K_VISION, 0.5
        if a.id == ruler.id:
            return None, 0.0
        if self.year - self.last_revolt.get(st.id, -99) < 8:
            appraise(a.af, a.eg, status_delta=-0.2)
            return K_BETRAYAL, -0.15
        res = PW.attempt_revolt(st, self.agents, self.cfg, rng, self.year)
        if res is None:
            appraise(a.af, a.eg, status_delta=-0.3)
            return K_BETRAYAL, -0.2
        self.last_revolt[st.id] = self.year
        ok, leader, dead = res
        for d in dead:
            self._kill(d, "ثورة")
        self.stats["revolts"] += 1
        if ok:
            self.chron.add(self.year, "revolt",
                           f"سقط الحاكم في {st.name}، وتولّى {leader.name}. "
                           f"قُتل {len(dead)}.", 3.0)
            return K_VIOLENCE, 0.6
        self.chron.add(self.year, "revolt",
                       f"قُمعت ثورة في {st.name}؛ قُتل {len(dead)} وبقي الحاكم.", 2.6)
        self.stats["persecutions"] += 1
        return K_VIOLENCE, -0.6

    def _observe(self, a, st, rng):
        """
        الرصد. هو نفسه اختبارٌ لمحرّم «من أحصى النجوم مرض» — والعالم يكذّبه:
        لا يمرض أحد من العدّ.
        """
        a.observations += 0.4 + a.eg.t[G.REASONING]
        a.skills[3] = min(1.0, a.skills[3] + 0.05)

        # يسجّل ما رأى: طلوع النجم، وخصب العام. لا نخبره أن بينهما صلة.
        a.star_log.append((self.world.star_early(self.year), self.world.bountiful()))
        if len(a.star_log) > 48:
            del a.star_log[0]
        # الإشارة الحقيقية نحو 67٪. من طلب يقينًا أعلى منها اكتشف ضجيجًا،
        # فنطلب رصدًا أطول وعتبةً تناسب ما في العالم فعلًا.
        if st.star_known is None and len(a.star_log) >= 26:
            hit = sum(1 for e, g in a.star_log if e == g)
            acc = hit / len(a.star_log)
            if acc > 0.68 and a.eg.t[G.REASONING] > 0.55 and rng.random() < 0.30:
                st.star_known = True
                NM.name_star(self, a, st, "العام الخصب", rng)
                a.mem.store(K_WONDER, self.year, val=0.9, strength=2.0,
                            truth=1.0, src=S_LIVED, tag="رصد")
                PW.prestige_gain(a, 1.2)
        d = st.doctrine
        if d is not None:
            t = d.tenets.get("counting_stars")
            if t is not None and a.conv.get("counting_stars", 0.0) > 0.05:
                before = a.conv.get("counting_stars", 0.0)
                route = self._dissonance(a, "counting_stars", 0.9, rng, t)
                if route == FA.REVISE and before > 0.4 and \
                        a.conv["counting_stars"] < 0.4 and rng.random() < 0.5:
                    self.chron.add(self.year, "taboo",
                                   f"{a.name} أحصى ولم يمرض، فسقط المحرّم عنده هو.", 1.9)
        if rng.random() < 0.06:
            tb = LB.write_tables(a, st, self, rng)
            if tb is not None:
                self.chron.add(self.year, "book",
                               f"دوّن {a.name} زِيجًا لما رصد.", 3.0)
        gap = self._detect(a, st)
        if gap:
            return K_VISION, 0.9
        return K_WONDER, 0.25

    def _detect(self, a, st):
        """اللحظة المفصلية: أن يرى أحدٌ أن الغضب رقمٌ لا ذنب."""
        if a.heretic or len(st.records) < 6:
            return None
        gap = FA.detect_period(st.records, a.eg.t[G.REASONING], "calendar" in st.knowledge)
        if gap is None or a.observations < 6:
            return None
        a.heretic = True
        a.doubt = 1.0
        a.faith = 0.0
        a.title = "المُنكِر"
        a.conv["wrath_is_sin"] = 0.0
        a.conv["counting_stars"] = 0.0
        a.mem.store(K_VISION, self.year, val=0.95, strength=2.2, truth=1.0,
                    src=S_LIVED, tag="كشف")
        if "writing" in st.knowledge and st.known_period is None:
            # دوّنها. من هنا فصاعدًا تعيش الحقيقة بعد صاحبها، وتُقرأ وتُنقل.
            st.known_period = gap
            self.chron.add(self.year, "discovery",
                           f"{a.name} حسب الفواصل بين وقائع الغضب فوجدها تدور كل "
                           f"{gap:.0f} سنة تقريبًا، ودوّنها. الغضب ليس عقابًا — "
                           f"إنه موعد. وصارت الحقيقة مكتوبة تُقرأ بعد موته.", 5.0)
        elif st.known_period is not None:
            self.chron.add(self.year, "rediscovery",
                           f"بلغ {a.name} الرقم نفسه — {gap:.0f} سنة — وقد كان "
                           f"مدوّنًا عندهم قبله.", 2.6)
        else:
            self.chron.add(self.year, "discovery",
                           f"{a.name} حسب الفواصل فوجد الغضب يدور كل {gap:.0f} سنة — "
                           f"ولا كتابة عندهم تحفظه، فمات معه.", 3.4)
        return gap

    def _wander(self, a, st, rng):
        w = self.world
        bx, by = w.white_mountain
        d = st.doctrine
        t = d.tenets.get("white_mountain") if d else None
        dist = abs(st.x - bx) + abs(st.y - by)
        if dist <= 5 and t is not None:
            mine = a.conv.get("white_mountain", 0.0)
            dare = (1.4 - mine) * (0.3 + a.eg.t[G.OPENNESS]) \
                * (1.2 - a.eg.t[G.FEAR]) * (0.4 + a.doubt)
            if dare * rng.gauss(1.0, 0.4) > 0.55:
                # صعد ولم يهلك
                route = self._dissonance(a, "white_mountain", 1.0, rng, t)
                if route == FA.REVISE and mine > 0.4 and rng.random() < 0.35:
                    self.chron.add(self.year, "taboo",
                                   f"صعد {a.name} الجبل الأبيض ونزل حيًّا.", 2.4)
                if t.strength < 0.35 and w.region(bx, by).taboo:
                    w.region(bx, by).taboo = False
                    self.chron.add(self.year, "taboo",
                                   "سقطت حرمة الجبل الأبيض؛ أخصب أرضٍ عرفوها "
                                   "صارت مباحة بعد ألفي سنة من التحريم.", 4.5)
                return K_JOURNEY, 0.55
        if rng.random() < 0.05:
            return K_WONDER, 0.35
        return K_JOURNEY, 0.12

    def _new_myth(self, a, st, rng):
        d = st.doctrine
        if d is None:
            return
        u = SP.myth(a, d.god, self.agents, self.world, rng, self.year)
        if u is None:
            return
        key = f"myth{self.year}_{a.id}"
        d.tenets[key] = FA.Tenet(key, u.text, 0.0, False, self.year)
        a.conv[key] = 1.2            # لا يعتقدها إلا هو — بعدُ
        a.said.append(u)
        if len(a.said) > 6:
            del a.said[0]
        d.complexity += self.cfg.doctrine_growth
        self.chron.add(self.year, "myth", u.text + ".", 1.6)

    # ================================================================ التوزيع
    def _distribute(self, st):
        """
        الطعام يُوزَّع بحسب المقام لا بحسب الحاجة. هنا يولد الغبن.
        """
        cfg = self.cfg
        ruler = self.agents.get(st.ruler)
        if ruler is not None:
            cut = st.granary * cfg.tribute_rate
            st.granary -= cut
            st.tribute_pool += cut
            for m in st.members:
                a = self.agents.get(m)
                if a is not None and a.id != ruler.id:
                    a.tribute += cut / max(1, st.pop())
        # ما يعرفه الحاكم عن حال رعيّته ليس حالهم: يعرف من يخالطه فقط.
        if ruler is not None:
            known = 0.0
            seen = 0
            for m in st.members[:40]:
                b = self.agents.get(m)
                if b is None:
                    continue
                if ruler.bonds.affection.get(b.id, 0.0) > 0.2 or b.status() > 2.0:
                    known += min(1.0, b.hunger)
                    seen += 1
            felt = known / seen if seen else 0.0
            real = sum(min(1.0, self.agents[m].hunger)
                       for m in st.members if m in self.agents) / max(1, st.pop())
            ruler.knows = felt
            if real - felt > 0.35:
                self.stats["blind"] = self.stats.get("blind", 0) + 1
            elif felt > 0.5 and cfg.tribute_rate > 0.1:
                self.stats["knowing"] = self.stats.get("knowing", 0) + 1

        members = [self.agents[m] for m in st.members if m in self.agents]
        members.sort(key=lambda a: a.status() + (9.0 if a.is_ruler else 0.0), reverse=True)
        pool = st.granary
        for a in members:
            need = cfg.yearly_food_need if a.age >= cfg.adult_age \
                else cfg.yearly_food_need * cfg.child_food_ratio
            got = min(need, pool)
            pool -= got
            short = 1.0 - (got / need if need > 0 else 1.0)
            a.hunger = max(0.0, min(1.5, a.hunger * 0.35 + short))
            if short > 0.3:
                appraise(a.af, a.eg, congruence=-0.2, threat=short * 0.4)
                if ruler is not None and a.id != ruler.id:
                    a.bonds.bump(a.bonds.resentment, ruler.id, 0.18 * short)
            elif short < 0.05:
                appraise(a.af, a.eg, congruence=0.2)
        # الجماهير غير المسمّاة
        m = self.mass.get(st.id, 0)
        if m > 0:
            mneed = m * cfg.yearly_food_need * 0.9
            if pool < mneed:
                die = int(min(m, (mneed - pool) / max(0.4, cfg.yearly_food_need) * 0.5))
                self.mass[st.id] = max(0, m - die)
                if die > 0:
                    self.stats["deaths"] += die
            pool = max(0.0, pool - mneed)
        # ما يُخزَّن للعام القادم — والفائض يتلف إن لم يكن مخزن
        keep = 1.6 + 2.2 * T.effect(st.knowledge, "buffer")
        st.granary = min(pool * 0.70, self._need(st) * keep)

    # ================================================================ اجتماع
    def _social(self, st):
        cfg = self.cfg
        rng = self.rs.get("social")
        n = len(st.members)
        if n < 2:
            return
        k = min(cfg.contacts_per_year, n)
        for m in st.members:
            a = self.agents.get(m)
            if a is None or not a.alive:
                continue
            a.bonds.decay(cfg.bond_decay, cfg.grudge_decay, a.eg.t[G.AGREEABLE])
            a.af.settle(a.eg)

    def _mating(self, st, ctx=None):
        cfg = self.cfg
        rng = self.rs.get("mate")
        ctx = ctx or dict(provision=1.0)
        for m in list(st.members):
            a = self.agents.get(m)
            if a is None or not a.alive or a.sex != FEMALE:
                continue
            if a.nursing > 0:
                a.nursing = max(0.0, a.nursing - 1.0)
            if a.pregnant > 0:
                a.pregnant -= 1
                if a.pregnant == 0:
                    self._birth(a, st, rng)
                continue
            if not a.fertile(cfg) or a.hunger > 0.85:
                continue
            # الشريك، أو من اشتدّ الانجذاب إليه
            pid = a.bonds.partner
            if pid not in self.agents or not self.agents[pid].alive:
                pid = -1
                best = 0.45
                for k, v in a.bonds.attraction.items():
                    if v > best and k in self.agents and self.agents[k].alive:
                        pid, best = k, v
                if pid < 0:
                    for k in st.members:               # من تقرّب إليها ورضيت
                        b = self.agents.get(k)
                        if b is None or b.sex == a.sex or not b.alive:
                            continue
                        v = b.bonds.attraction.get(a.id, 0.0) *                             (0.3 + a.bonds.affection.get(k, 0.0))
                        if v > best:
                            pid, best = k, v
            if pid < 0:
                continue
            # الأبوّة ليست يقينًا: من اشتدّ الانجذاب إليه قد يكون الأب،
            # ولا وسيلة عندهم للتحقّق. والنسب الذي يُبنى عليه الميراث
            # والثأر قد يكون غير النسب الواقع.
            if a.bonds.partner in self.agents:      # لا خيانة بلا عهد
                rival, best_att = -1, 1.10
                for k, v in a.bonds.attraction.items():
                    if k != pid and v > best_att and k in self.agents                             and self.agents[k].sex != a.sex:
                        rival, best_att = k, v
                if rival >= 0 and rng.random() < 0.055 * min(1.0, best_att)                         * (1.4 - a.eg.t[G.HONESTY]):
                    pid = rival
                    self.stats["cuckoo"] = self.stats.get("cuckoo", 0) + 1
            p = self.agents[pid]
            chance = 0.92 * (0.4 + a.eg.t[G.FERTILITY]) * (0.5 + p.eg.t[G.FERTILITY]) \
                * (1.0 - 0.45 * min(1.0, a.hunger)) * (1.0 - 0.4 * a.illness)
            if a.age > 35:
                chance *= 0.62
            if rng.random() < chance:
                a.pregnant = 1
                a.pregnancy_by = pid

    def _multitude(self, st, ctx):
        """
        ديموغرافيا الجماهير غير المسمّاة.

        كانت تتلقّى المواليد ولا تلدها، فصارت بالوعةً سكانية: يُحسب النسل
        على ثلاثمئة ويقع الموت على الألفين. هنا تُعطى ولادةً وموتًا،
        ويصعد منها من يملأ مقاعد المحاكاة الكاملة كلما خلا مقعد.
        """
        cfg = self.cfg
        rng = self.rs.get("mass")
        m = self.mass.get(st.id, 0)
        if m > 0:
            br = 0.046 * min(1.15, ctx["provision"]) * ctx["land"]
            dr = 0.030 + 0.070 * ctx["scarcity"]
            d = m * (br - dr)
            k = int(d)
            if rng.random() < abs(d - k):
                k += 1 if d > 0 else -1
            m = max(0, m + k)
            self.mass[st.id] = m
            if k > 0:
                self.stats["births"] += k
            elif k < 0:
                self.stats["deaths"] += -k

        # الصعود إلى المحاكاة الكاملة
        room = cfg.max_named - len(self.agents)
        if room > 0 and m > 0:
            for _ in range(min(room, 3, m)):
                if self._promote(st, rng):
                    m -= 1
                    self.mass[st.id] = m
                else:
                    break

    def _promote(self, st, rng):
        """يخرج من الجماهير فردٌ بعينه، وُلد لأبوين من أهل القرية."""
        cfg = self.cfg
        pool = [self.agents[i] for i in st.members if i in self.agents]
        adults = [a for a in pool if a.age >= cfg.adult_age]
        if len(adults) < 2:
            # لا أحد هنا يُحاكى معرفيًا. نأخذ من أقرب قريةٍ فيها أحياء —
            # فالجماهير نسلُ من عاش، لا خلقٌ جديد. وبغير هذا لا تعود العقول
            # من الصفر أبدًا، وتصير المحاكاة أرقامًا بلا رؤوس.
            everyone = [a for a in self.agents.values() if a.age >= cfg.adult_age]
            if len(everyone) >= 2:
                everyone.sort(key=lambda b: abs(b.settlement - st.id))
                adults = everyone[:24]
            elif everyone:
                adults = everyone * 2
            else:
                return False
        ma = rng.choice(adults)
        pa = rng.choice(adults)
        g = G.Genome.conceive(ma.g, pa.g, rng, cfg.mutation_sigma,
                              self._settlement_mean(st) or self._settlement_mean(
                                  self.world.settlements[ma.settlement]))
        prog = inherit(ma.prog, pa.prog, g, rng, cfg)
        sex = MALE if rng.random() < 0.5 else FEMALE
        age = cfg.adult_age + rng.randrange(0, 8)
        a = Agent(self.next_id, self._child_name(rng, ma, pa, sex), ma.house,
                  g, prog, sex, age, self.year - age, cfg, rng)
        self.next_id += 1
        a.settlement = st.id
        a.faith = 0.5 * (ma.faith + pa.faith)
        a.lineage = ma.lineage
        HI.implant(a, self.history, self.rs.get("implant"), cfg, self.year)
        FA.inherit_conv(a, ma, pa, rng, doc=st.doctrine)
        self.agents[a.id] = a
        st.members.append(a.id)
        return True

    def _birth(self, mother, st, rng):
        cfg = self.cfg
        father = self.agents.get(mother.pregnancy_by)
        if father is None:
            father = mother
        env = self._settlement_mean(st)
        g = G.Genome.conceive(mother.g, father.g, rng, cfg.mutation_sigma, env)
        prog = inherit(mother.prog, father.prog, g, rng, cfg)

        # خطر الولادة — يخفّ كثيرًا مع الطبّ
        risk = cfg.gestation_penalty * (1.0 + T.effect(st.knowledge, "birth"))
        risk *= (1.0 - 0.4 * mother.eg.t[G.VIGOR]) * (0.4 + mother.hunger)
        if rng.random() < risk * 0.35:
            self._kill(mother, "ولادة")
            return

        if len(self.agents) >= cfg.max_named:
            self.mass[st.id] = self.mass.get(st.id, 0) + 1
            self.stats["births"] += 1
            return

        sex = MALE if rng.random() < 0.5 else FEMALE
        name = self._child_name(rng, mother, father, sex)
        a = Agent(self.next_id, name, mother.house, g, prog, sex, 0, self.year, cfg, rng)
        self.next_id += 1
        a.settlement = st.id
        a.mother = mother.id
        a.father = father.id
        a.lineage = mother.lineage
        a.faith = 0.5 * (mother.faith + father.faith)
        # ويرث المذهب كما يرث الملّة.
        #
        # كان لا يُنتسَب إلا بقراءة رسالةٍ أو تلقينِ مسألةٍ بعينها، وكلاهما
        # نادر: ثلاثمئة انتساب في عشرة آلاف عُمر، فبقيت المدارس أفرادًا
        # وسيطُ أتباعها واحد. وليس هكذا تنتقل المذاهب في الناس — أكثرُ من
        # يحمل قولًا ورثه عن أبيه قبل أن يفهمه، ثم يراجعه أو يبقى عليه.
        # والانتماء يسبق الفهم، وهذا واقعٌ لا تجميل.
        par = mother if mother.school >= 0 else father
        if par.school >= 0 and rng.random() < 0.55:
            a.school = par.school
        mother.children.append(a.id)
        father.children.append(a.id)
        for par in (mother, father):
            a.bonds.kin.add(par.id); par.bonds.kin.add(a.id)
            a.bonds.reared_with.add(par.id); par.bonds.reared_with.add(a.id)
            a.bonds.bump(a.bonds.affection, par.id, 1.4)
            par.bonds.bump(par.bonds.affection, a.id, 1.7)
            appraise(par.af, par.eg, congruence=0.9, tenderness=1.0, status_delta=0.3)
            par.mem.store(K_BIRTH, self.year, who=a.id, val=0.8, strength=1.7,
                          truth=1.0, src=S_LIVED, tag="ولادة")
        for sib in mother.children:
            s = self.agents.get(sib)
            if s is not None and s.id != a.id:
                a.bonds.reared_with.add(s.id); s.bonds.reared_with.add(a.id)
                a.bonds.kin.add(s.id); s.bonds.kin.add(a.id)

        # الماضي الذي لم يقع يُزرع في كل مولود جديد
        HI.implant(a, self.history, self.rs.get("implant"), cfg, self.year)
        FA.inherit_conv(a, mother, father, rng, doc=st.doctrine)
        mother.nursing = CA.nursing_years(mother, 1.0 - min(1.0, mother.hunger),
                                          st.knowledge)
        self.agents[a.id] = a
        st.members.append(a.id)
        self.stats["births"] += 1

    _SYL = ("نَه", "سَل", "خَن", "دَر", "قَط", "وَر", "عَث", "زُه", "مَر", "هَج",
            "بَل", "صَف", "غَي", "تَل", "رَم", "لُب", "شَب", "كَر", "مِس", "ظَم",
            "جَذ", "نُع", "رَي", "غُص", "حَل", "آس", "فَي", "سُل", "أُم", "مِر",
            "سَم", "نَج", "ثَر", "حَز", "عَم", "يَس", "قَي", "زَي", "بَش", "طَر")
    _END_M = ("ران", "ماس", "لان", "سام", "هون", "دار", "يم", "وان", "اس",
              "ير", "ون", "اد", "يل", "ال", "ين", "ود", "اح", "ام", "يب", "رام")
    _END_F = ("ة", "اء", "ى", "ية", "انة", "ونة", "يرة", "الة", "امة",
              "مى", "نى", "وى", "يمة", "راء")

    def _child_name(self, rng, mother, father, sex):
        # يُسمّى على حيٍّ من أهله أحيانًا — عادةٌ تُبقي الأسماء في البيت
        if rng.random() < 0.20:
            pool = []
            for p in (mother, father):
                for gid in (p.mother, p.father):
                    g = self.agents.get(gid)
                    if g is not None and g.sex == sex:
                        pool.append(g.name)
                for cid in p.bonds.kin:
                    k = self.agents.get(cid)
                    if k is not None and k.sex == sex and k.age > 30:
                        pool.append(k.name)
            if pool:
                return rng.choice(pool)
        tail = self._END_F if sex == FEMALE else self._END_M
        return (rng.choice(self._SYL) + rng.choice(tail)).replace("ْ", "")

    def _settlement_mean(self, st):
        n = 0
        acc = [0.0] * G.NT
        for m in st.members:
            a = self.agents.get(m)
            if a is None:
                continue
            n += 1
            for i in range(G.NT):
                acc[i] += a.g.t[i]
        if n == 0:
            return None
        return [v / n for v in acc]

    # ================================================================ السلطة
    def _politics(self, st):
        cfg = self.cfg
        rng = self.rs.get("power")
        ruler = self.agents.get(st.ruler)
        if ruler is None or not ruler.alive:
            st.ruler = -1
            cand = PW.choose_ruler(st, self.agents, cfg, rng, self.year)
            if cand is not None:
                PW.install(st, cand, self.agents, self.year)
                kind = "طاغية" if cand.dominance > cand.prestige else "زعيم"
                self.chron.add(self.year, "rule",
                               f"تولّى {cand.name} أمر {st.name} ({kind}).", 2.2)
            return
        ruler.rule_years += 1
        PW.corrupt(ruler, cfg)                       # مفارقة السلطة
        if ruler.rule_years == 15:
            self.chron.add(self.year, "power",
                           f"مضت خمس عشرة سنة على حكم {ruler.name}؛ "
                           f"طغيانه {PW.tyranny_index(st, self.agents):.0%}.", 1.8)
        if st.unrest > 0.8 and rng.random() < 0.25 and                 self.year - self.last_revolt.get(st.id, -99) >= 8:
            res = PW.attempt_revolt(st, self.agents, cfg, rng, self.year)
            if res:
                self.last_revolt[st.id] = self.year
                ok, leader, dead = res
                for d in dead:
                    self._kill(d, "ثورة")
                self.stats["revolts"] += 1
                self.chron.add(self.year, "revolt",
                               (f"ثار أهل {st.name} فسقط الحاكم وتولّى {leader.name}."
                                if ok else
                                f"ثار أهل {st.name} فقُمعوا؛ قُتل {len(dead)}."), 3.0)
        st.unrest = max(0.0, st.unrest * 0.92 + PW.grievance(st, self.agents, cfg) * 0.10)

    # ================================================================ العقيدة
    def _faith_phase(self, st):
        cfg = self.cfg
        rng = self.rs.get("faith")
        d = st.doctrine
        if d is None:
            return
        d.ritual_debt *= 0.9
        for m in st.members:
            a = self.agents.get(m)
            if a is None or not a.alive or a.heretic:
                continue
            # دائرته: من بينه وبينهم رابطة قائمة، لا القرية كلها
            circle = []
            for who, v in a.bonds.affection.items():
                b = self.agents.get(who)
                if b is not None and b.alive and v > 0.15:
                    circle.append((b, v * (1.0 + 0.35 * b.prestige)))
            for who in list(a.bonds.kin)[:6]:
                b = self.agents.get(who)
                if b is not None and b.alive:
                    circle.append((b, 0.9))
            FA.conform(a, d, 0.055, circle if len(circle) >= 2 else None)
        gone = FA.recompute_orthodoxy(st, self.agents, self.year, self.cfg)
        if gone:
            self.stats["forgotten_tenets"] =                 self.stats.get("forgotten_tenets", 0) + gone
        # العقائد التي ماتت في الصدور تُشطب من النصّ بعد حين
        for k in [k for k, t in d.tenets.items()
                  if t.strength < 0.02 and self.year - t.born > 60]:
            del d.tenets[k]

        # اضطهاد المنكرين
        ruler = self.agents.get(st.ruler)
        clergy_power = sum(1 for m in st.members
                           if m in self.agents and self.agents[m].clergy)
        for m in list(st.members):
            a = self.agents.get(m)
            if a is None or not a.alive or not a.heretic:
                continue
            zeal = clergy_power * 0.05 + (ruler.eg.t[G.CALLOUSNESS] * 0.25 if ruler else 0.0)
            if rng.random() < min(0.5, zeal) * (1.0 - T.effect(st.knowledge, "free")):
                self._kill(a, "اضطهاد")
                d.martyrs += 1
                d.persecutions += 1
                self.stats["persecutions"] += 1
                self.chron.add(self.year, "persecution",
                               f"قُتل {a.name} لأنه أنكر.", 2.6)
                gone = st.library.burn(rng, 1 + rng.randrange(3))
                for bk in gone:
                    self.chron.add(self.year, "burning",
                                   f"أُحرق {bk.label()} فلم تبقَ منه نسخة.", 3.8)
                if st.known_period and rng.random() < 0.30:
                    st.known_period = None
                    st.burned += 1
                    self.chron.add(self.year, "burning",
                                   f"أُتلف ما دُوّن عن مواعيد الغضب في {st.name}. "
                                   f"عادت الحقيقة مجهولة.", 4.0)
                # الشهادة تصنع شكًّا في غيره أحيانًا
                for m2 in st.members:
                    b = self.agents.get(m2)
                    if b is not None and b.alive and b.bonds.feel(a.id) > 0.3:
                        b.doubt = min(1.0, b.doubt + 0.25)
                        b.faith = max(0.0, b.faith - 0.15)

        # انشقاق
        if len(st.members) > 25:
            doubters = [self.agents[m] for m in st.members
                        if m in self.agents and self.agents[m].doubt > 0.55]
            if len(doubters) > len(st.members) * cfg.schism_threshold * 0.5 and rng.random() < 0.05:
                new = d.fork(f"عهد المنشقّين {self.next_sect}", self.year, self.next_sect)
                self.doctrines[self.next_sect] = new
                self.next_sect += 1
                self.stats["schisms"] += 1
                self.chron.add(self.year, "schism",
                               f"انشقّ في {st.name} مذهب جديد ({len(doubters)} تابعًا).", 3.2)

        # النبوءة: الوعد بعد سبعة أجيال
        if not any(p[2] is not None for p in d.prophecies) and self.year >= 175:
            believers = [self.agents[m] for m in st.members
                         if m in self.agents and self.agents[m].faith > 0.4]
            z, l = FA.prophecy_failed(d, believers, rng, cfg, self.year)
            d.prophecies.append((175, "عودة الماء", False))
            self.chron.add(self.year, "prophecy",
                           f"مرّت سبعة أجيال ولم يعد الماء. ازداد {len(z)} يقينًا، "
                           f"وانصرف {len(l)}.", 4.0)

    # ================================================================ المعرفة
    def _invent(self):
        """
        الابتكار حدثٌ واحد في السنة على مستوى الحضارة كلها، لا رميةٌ لكل
        قرية بعقل الشبكة كاملًا — كان ذلك حسابًا مزدوجًا جعل خمسين قرية
        تخترع خمسين مرة في السنة بالدماغ نفسه.
        """
        # كان هنا مرورٌ على كل قريةٍ بدعوى «تحديث الحُجُب»، وهو يحسب
        # `n_eff` بجولةٍ على **كل القرى** ثم يرمي ما حسبه ولا يستعمله:
        # عملٌ من رتبة مربّع عدد القرى في كل سنة، بلا أثرٍ واحد. وهو
        # لا يسحب من مولّد العشوائيات شيئًا، فحذفُه لا يغيّر تاريخًا.
        hosts = [s for s in self.world.settlements if s.pop() >= 4]
        if not hosts:
            return
        rng = self.rs.get("tech")
        st = max(hosts, key=lambda s: len(s.knowledge) * 3 + s.pop())
        self._tech(st, roll=True)

    def _tech(self, st, roll=True):
        cfg = self.cfg
        rng = self.rs.get("tech")
        pop = st.pop() + self.mass.get(st.id, 0)
        n_eff = pop + sum(
            (s.pop() + self.mass.get(s.id, 0)) * max(0.0, st.relations.get(s.id, 0.35))
            for s in self.world.settlements if s.id != st.id)
        connect = min(1.0, 0.25 + T.effect(st.knowledge, "connect") +
                      0.05 * len(self.world.settlements))
        lei, opn, n = 0.0, 0.0, 0
        for m in st.members:
            a = self.agents.get(m)
            if a is None:
                continue
            n += 1
            lei += max(0.0, 1.0 - a.hunger) * (1.0 - min(1.0, a.illness))
            opn += a.eg.t[G.OPENNESS]
        if n == 0:
            return
        lei /= n
        opn /= n

        blocked = set()
        d = st.doctrine
        if d is not None:
            t = d.tenets.get("counting_stars")
            if t and t.strength > 0.45:
                blocked |= set(T.TABOO_BLOCKS["counting_stars"])
            # المنهج التجريبي يحتاج سابقةً وهامشَ حرية: تفسيرٌ طبيعي واحد
            # ثبت وحلّ محلّ تفسيرٍ إلهي، ومجتمعٌ لم يقتل من قاله.
            if st.known_period is None:
                blocked.add("method")
            elif d.persecutions > 6 and not any(
                    self.agents[m].heretic for m in st.members if m in self.agents):
                blocked.add("method")

        if not roll:
            return
        got = T.try_invent(st, n_eff, connect, lei, opn, blocked, cfg, rng)
        if got:
            key, name = got
            wt = 4.5 if key in T.LANDMARKS else 1.5
            self.chron.add(self.year, "tech", f"{name}", wt)
            if key == "calendar":
                # لا بدّ لتقويمٍ من مبدأ، ولا بدّ لأقسامه من أسماء.
                NM.name_epoch(self, st, rng)
                NM.name_months(self, st, rng)
            elif key == "law":
                r = self.agents.get(st.ruler)
                if r is not None:
                    NM.name_law(self, r, st, rng)
            if key == "writing":
                for m in st.members:
                    a = self.agents.get(m)
                    if a:
                        a.mem.fidelity = min(0.98, a.mem.fidelity + 0.25)

    def _trade(self):
        """
        نقلُ الطعام بين القرى.

        بغيره لا تتجاوز قريةٌ ما تنبته أرضها، فتتساوى الأحجام ولا تنشأ
        مدينة — وهذا ما كشفه فحص زيبف. والمدينة في التاريخ لم تقم إلا
        حين أمكن نقلُ فائض الحقول إليها: عجلةً ثم شراعًا ثم نقدًا.

        فالمدى هنا دالّة في المنقول لا في الرغبة.
        """
        sts = [s for s in self.world.settlements if s.pop() > 0]
        if len(sts) < 2:
            return
        rng = self.rs.get("trade")
        for st in sts:
            reach = 0
            k = st.knowledge
            if "wheel" in k:
                reach = 3
            if "sail" in k:
                reach = max(reach, 5)
            if "coin" in k:
                reach = max(reach, 6)
            if "printing" in k:
                reach = max(reach, 8)
            if not reach:
                continue
            need = self._need(st)
            gap = need * 1.05 - st.granary
            if gap <= 0:
                continue
            for other in sts:
                if other.id == st.id or gap <= 0:
                    continue
                if abs(other.x - st.x) + abs(other.y - st.y) > reach:
                    continue
                rel = st.relations.get(other.id, 0.4)
                if rel <= 0.05:
                    continue
                spare = other.granary - self._need(other) * 1.15
                if spare <= 0:
                    continue
                # ما ينقص في الطريق: بعدٌ وعطبٌ ومن يأخذ نصيبه
                loss = 0.10 + 0.05 * (abs(other.x - st.x) + abs(other.y - st.y))
                moved = min(gap, spare * rel * 0.55)
                st.granary += moved * (1.0 - loss)
                other.granary -= moved
                gap -= moved * (1.0 - loss)
                st.relations[other.id] = min(1.0, rel + 0.03)
                other.relations[st.id] = min(1.0, other.relations.get(st.id, 0.4) + 0.03)

    def _diffuse(self):
        rng = self.rs.get("diffuse")
        sts = self.world.settlements
        for a in sts:
            for b in sts:
                if a.id >= b.id:
                    continue
                rel = a.relations.get(b.id, 0.4)
                if rel <= 0.05:
                    continue
                dist = abs(a.x - b.x) + abs(a.y - b.y)
                p = rel * 0.12 / (1.0 + dist * 0.25)
                if rng.random() < p:
                    miss = b.knowledge - a.knowledge
                    if miss:
                        a.knowledge.add(min(miss, key=lambda k: T.ORDER[k]))
                    miss = a.knowledge - b.knowledge
                    if miss:
                        b.knowledge.add(min(miss, key=lambda k: T.ORDER[k]))
                    if a.records and not b.records:
                        b.records = list(a.records)
                    if a.known_period and not b.known_period:
                        b.known_period = a.known_period
                    elif b.known_period and not a.known_period:
                        a.known_period = b.known_period

    # ================================================================ الحرب
    def _laws_known(self, st):
        """كم قانونًا طبيعيًا بأيديهم — لا كم يظنّون أنهم يعرفون."""
        n = 0
        if st.known_period:
            n += 1
        if st.star_known:
            n += 1
        if st.rotation:
            n += 1
        if "medicine" in st.knowledge:
            n += 1
        return n

    def _naturalism(self, st, rng):
        """
        لا نصّ ولا وحيَ هنا. حين يجتمع في أيديهم ثلاثة تفسيراتٍ طبيعية
        كان كلٌّ منها يُنسب إلى غضبٍ أو رضًا، يتكوّن عند العقول القادرة
        موقفٌ عامّ: أن لكل شيء سببًا، وأن لا واحد من الأسباب شخصٌ.
        """
        k = self._laws_known(st)
        if k < 3:
            return
        if st.id not in self._natural:
            self.chron.add(self.year, "naturalism",
                           f"اجتمع لأهل {st.name} {k} تفسيراتٍ لما كانوا "
                           f"ينسبونه إلى الغضب. صار فيهم من يقول: لكل شيء "
                           f"سبب، ولا واحد من الأسباب أحد.", 5.0)
            self._natural.add(st.id)
        for m in st.members:
            a = self.agents.get(m)
            if a is None or a.heretic:
                continue
            grip = 0.02 * (k - 2) * (0.2 + a.eg.t[G.REASONING]) * (1.2 - a.eg.t[G.CREDULITY])
            if grip <= 0:
                continue
            for key in list(a.conv):
                a.conv[key] = max(0.0, a.conv[key] - grip)
            a.doubt = min(1.0, a.doubt + grip * 0.6)
            a.faith = max(0.0, a.faith - grip * 0.8)

    def _war(self):
        """
        الغزو صار تدبيرًا لا اندفاعًا (انظر war.py): يُختار الهدف بالأضعف
        الأغنى لا بالأقرب، ويُنتظر به وهنُ الجار، ويُطلب فيه هامشُ قوّة،
        ويُدوَّن خبرُه فيقرأه قائدٌ بعد قرن.
        """
        cfg = self.cfg
        rng = self.rs.get("war")
        for st in list(self.world.settlements):
            if st.pop() < 8:
                continue
            ruler = self.agents.get(st.ruler)
            if ruler is None:
                continue

            # التحصين قبل الحاجة — علامةُ من يدبّر
            if WR.should_fortify(self, st, ruler, cfg) and st.granary > self._need(st):
                st.walls += 0.9
                st.granary -= self._need(st) * 0.04

            if self.year - self.last_war.get(st.id, -99) < 12:
                continue
            appetite = (0.45 * ruler.eg.t[G.DOMINANCE] + 0.35 * ruler.eg.t[G.CALLOUSNESS]
                        + 0.30 * max(0.0, 1.0 - st.granary / max(1.0, self._need(st))))
            if rng.random() > appetite * 0.09:
                continue
            p = WR.plan(self, st, ruler, cfg)
            if p is None:
                continue
            tgt, helpers, why, lvl, margin = p

            leth = cfg.violence_lethality * (1.0 + T.effect(st.knowledge, "leth"))
            att = WR.strength(st, self.agents, cfg, T.effect(st.knowledge, "leth"))[0]
            att += sum(WR.strength(h, self.agents, cfg, 0.0)[0] * 0.45 for h in helpers)
            dfn, wall = WR.strength(tgt, self.agents, cfg, T.effect(tgt.knowledge, "leth"))
            dfn += wall
            win = att > dfn * rng.gauss(1.0, 0.20)

            loser, winner = (tgt, st) if win else (st, tgt)
            # القتلى تُحسب على كل السكان لا على المُحاكَين وحدهم. كان
            # الخطأ يجعل حربًا بين مدينتين فيهما ألوف تقتل اثنين.
            lose_all = loser.pop() + self.mass.get(loser.id, 0)
            win_all = winner.pop() + self.mass.get(winner.id, 0)
            rate_l = min(0.30, leth * rng.uniform(0.35, 1.25))
            rate_w = rate_l * 0.42
            toll_l = max(1, int(lose_all * rate_l))
            toll_w = max(0, int(win_all * rate_w))

            def _fall(sett, total_toll, tag):
                named = [self.agents[m] for m in list(sett.members)
                         if m in self.agents and self.agents[m].age >= cfg.adult_age]
                share = 0.0
                if total_toll and (sett.pop() + self.mass.get(sett.id, 0)):
                    share = sett.pop() / float(sett.pop() + self.mass.get(sett.id, 0))
                n_named = min(len(named), int(round(total_toll * share)))
                for a in named[:n_named]:
                    self._kill(a, "حرب")
                rest = total_toll - n_named
                if rest > 0:
                    m0 = self.mass.get(sett.id, 0)
                    gone = min(m0, rest)
                    self.mass[sett.id] = m0 - gone
                    self.stats["deaths"] += gone
                return n_named + max(0, min(rest, total_toll))

            dead_l = _fall(loser, toll_l, "حرب")
            dead_w = _fall(winner, toll_w, "حرب")
            fallen = [None] * dead_l
            back = dead_w

            spoil = loser.granary * 0.45
            loser.granary -= spoil
            winner.granary += spoil
            miss = loser.knowledge - winner.knowledge
            if miss:
                winner.knowledge.add(min(miss, key=lambda k: T.ORDER[k]))
            st.relations[tgt.id] = -1.0
            tgt.relations[st.id] = -1.0
            self.stats["wars"] += 1
            self.last_war[st.id] = self.year
            self.last_war[tgt.id] = self.year
            self.war_log.append((self.year, len(fallen) + back))
            for m in loser.members:
                a = self.agents.get(m)
                if a is not None:
                    appraise(a.af, a.eg, threat=1.0, loss=0.9, blame_other=0.9)
                    a.mem.store(K_VIOLENCE, self.year, val=-0.9, strength=2.0,
                                truth=1.0, src=S_LIVED, tag="حرب")
            bk = WR.record(self, st, ruler, win, tgt.name, len(fallen) + back)
            self.chron.add(self.year, "war",
                           f"غزا {ruler.name} أهلَ {tgt.name} ({why}؛ "
                           f"تدبيره {lvl:.1f}، وفضلُ قوّته {margin:.2f})"
                           + (f" ومعه {len(helpers)} حليفًا" if helpers else "")
                           + f". {'ظفروا' if win else 'رُدّوا'}؛ قُتل "
                           f"{len(fallen) + back}." + (" ودُوّن الخبر." if bk else ""), 3.4)

    # ================================================================ الوباء
    def _disease(self):
        cfg = self.cfg
        rng = self.rs.get("plague")
        # لا احتمالَ ثابتًا: يُشتقّ من الماشية والكثافة والاتصال والنظافة
        if rng.random() < CA.outbreak_pressure(self):
            np_ = PL.spawn(rng, self.year, G.N_ANTIGEN)
            self.pathogens.append(np_)
            st0 = self.world.settlements[0]
            first = None
            for m in st0.members:
                v = self.agents.get(m)
                if v is not None:
                    first = v
                    break
            NM.name_plague(self, np_, first, st0, rng)
        # التحوّر يخلف السلالةَ لا يضاعفها: بلا هذا القيد تنمو أسّيًا
        # (٧٪ لكل سلالة كل سنة ⇒ ملايين الكائنات بعد ثلاثة قرون).
        for i in range(len(self.pathogens)):
            if rng.random() < cfg.pathogen_mutate:
                q = PL.mutate(self.pathogens[i], rng, G.N_ANTIGEN, self.year)
                if len(self.pathogens) < cfg.max_strains:
                    self.pathogens.append(q)
                else:
                    self.pathogens[i] = q       # حلّت محلّ سلفها
        if len(self.pathogens) > cfg.max_strains:
            del self.pathogens[:-cfg.max_strains]   # القديمة تنقرض
        if not self.pathogens:
            for a in self.agents.values():
                a.illness = max(0.0, a.illness - 0.25)
            return
        p = self.pathogens[-1]
        med = -T.effect(self.world.settlements[0].knowledge, "mort")
        for a in self.agents.values():
            if not a.alive:
                continue
            if a.illness > 0.02:
                a.illness = max(0.0, a.illness - 0.22 - med * 0.3)
                a.immunity.add(p.antigen)
                continue
            if rng.random() < p.transmit * 0.06 * (1.0 - PL.resistance(a, p)):
                a.illness = min(1.0, p.virulence)
                a.health -= p.virulence * 0.25 * (1.0 - med)
                appraise(a.af, a.eg, threat=0.6, congruence=-0.5)
                a.mem.store(K_PLAGUE, self.year, val=-0.6, strength=1.4,
                            truth=1.0, src=S_LIVED, tag="سقم")

    # ============================================================== العلل
    def _maladies(self, y):
        """
        ما يقع من الأدواء هذه السنة. الضغطُ يُحسب **للقرية مرّةً**،
        ثم يُرمى لكل نفسٍ رميةٌ رخيصة — فلا يثقل الرنّ بمئة علّة.
        """
        rng = self.rs.get("plague")
        cfg = self.cfg
        mals, idx = self.maladies, self.mal_fam
        W = self.world
        for st in W.settlements:
            n = st.pop()
            if n < 2:
                continue
            reg = W.region(st.x, st.y)
            pop_all = n + self.mass.get(st.id, 0)
            foul_v = CA.foul(reg, pop_all, st.knowledge)
            marsh = 1.0 if reg.biome == 3 else 0.0
            if not marsh:
                for s in W.neighbours(st.x, st.y):
                    if s.biome == 3:
                        marsh = 0.45
                        break
            pres = MD.pressures(st, reg, st.knowledge, pop_all, foul_v,
                                W.climate, marsh)
            members = [self.agents[m] for m in st.members if m in self.agents]
            ill = sum(1 for a in members if a.sick)
            share = ill / max(1, len(members))
            for a in members:
                if not a.alive:
                    continue
                if len(a.sick) < 3:
                    m = MD.roll(a, pres, idx, rng, share)
                    if m is not None and not any(s[0] == m.id for s in a.sick):
                        a.sick.append((m.id, 1.0, 0.0))
                        a.mem.store(K_PLAGUE, y, val=-0.5 - 0.4 * m.severity,
                                    strength=1.1 + m.severity, truth=1.0,
                                    src=S_LIVED, tag="سقم")
                        self.stats["fell_ill"] = self.stats.get("fell_ill", 0) + 1
                        kf = "ill_" + m.family
                        self.stats[kf] = self.stats.get(kf, 0) + 1
                rep = CA.repair_capacity(a, cfg, 1.0, 0.0)
                MD.progress(a, mals, rng, rep)
                b = MD.burden(a, mals)
                if b > a.illness:
                    a.illness = b
                # **الالتهاب المزمن وحده يُسرطن، لا الحُمّى العابرة.**
                # لمّا صار كلُّ سقمٍ يرفع خطر الورم أصاب الورمُ الشباب،
                # وذلك خطأ: نموذج الإصابات المتعدّدة يقوده دورانُ
                # الخلايا الطويل لا نوبةُ حمّى. (Balkwill & Mantovani
                # 2001 في الالتهاب والسرطان.)
                a.inflam = sum(MD.intensity(mals[s[0]]) for s in a.sick
                               if mals[s[0]].chronic)

    # ================================================================ الغضب
    def _wrath(self):
        cfg = self.cfg
        rng = self.rs.get("wrath")
        kind = self.world.wrath.due(self.year, rng)
        if kind is None:
            return
        pop = self.population()
        cap = sum(self.world.capacity(s, T.yields(s.knowledge))
                  for s in self.world.settlements)
        sev = self.world.wrath.severity(cfg, pop, cap, rng)
        self.world.wrath.history.append((self.year, kind, sev))
        self.stats["wraths"] += 1

        victims = []
        for a in list(self.agents.values()):
            if not a.alive:
                continue
            # الهشاشة جسدية بحتة — لا علاقة للتقوى بالنجاة
            frail = (0.35 + 0.5 * min(1.0, a.hunger) + 0.4 * a.illness +
                     0.5 * max(0.0, (a.age - 40) / 30.0) +
                     0.4 * max(0.0, (10 - a.age) / 10.0) -
                     0.35 * a.eg.t[G.VIGOR])
            if rng.random() < sev * max(0.1, frail) * 1.7:
                victims.append(a)
        for v in victims:
            PG.fire('on_wrath', self, v, None, rng)
            self._kill(v, kind)
        for sid in list(self.mass):
            m = self.mass[sid]
            if m:
                left = max(0, int(m * (1.0 - sev)))
                # كان موتى الجماهير في الغضب لا يُعدّون أصلًا، فاختلّ الميزان:
                # مواليدُ تُحصى ووفياتٌ تضيع.
                self.stats["deaths"] += (m - left)
                self.mass[sid] = left

        for st in self.world.settlements:
            if "writing" in st.knowledge:
                st.records.append(self.year)
            st.wrath_seen.append(self.year)
            if len(st.wrath_seen) > 3:
                del st.wrath_seen[0]          # الشفهي ينسى الفواصل
            d = st.doctrine
            if d is None:
                continue
            t = d.tenets.get("wrath_is_sin")
            for m in st.members:
                a = self.agents.get(m)
                if a is None or not a.alive:
                    continue
                awe_strike(a.af, a.eg, 1.0)
                FA.wrath_conviction(a, d, rng)
                appraise(a.af, a.eg, threat=1.0, loss=1.0, congruence=-1.0)
                a.mem.store(K_DEATH, self.year, val=-0.95, strength=2.2,
                            truth=1.0, src=S_LIVED, tag=kind)
                # الاختبار: صلّينا كثيرًا وجاء الغضب. ماذا نفعل بالتناقض؟
                if t is not None and a.tribute > 0.4:
                    self._dissonance(a, "wrath_is_sin", min(1.0, a.tribute), rng, t)
            d.ritual_debt = 0.0

        self.chron.add(self.year, "wrath",
                       f"غضب — {kind}. مات {len(victims)} ({sev:.0%}).", 3.5)

    # ================================================================ الحياة
    def _lifecycle(self):
        cfg = self.cfg
        rng = self.rs.get("life")
        for a in list(self.agents.values()):
            if not a.alive:
                continue
            know_of = (self.world.settlements[a.settlement].knowledge
                       if a.settlement < len(self.world.settlements) else set())
            a.age += 1
            a.mem.age(cfg.decay_base, cfg.numinous_bonus)
            a.health = min(1.0, a.health + 0.06 - 0.02 * a.illness)
            if a.hunger > 0.5:
                a.health -= 0.115 * a.hunger
            # الشيخوخة لم تعد تُخصم من الصحّة: صارت انحدارًا في قدرة
            # الإصلاح (causes.repair_capacity). وحسابها هنا أيضًا كان
            # يقتل الناس قبل أن يعمل نموذج التراكم أصلًا.
            a.fatigue = max(0.0, a.fatigue - 0.35)
            a.tribute = max(0.0, a.tribute * 0.85)

            # لا عمرَ مفروضًا: الموت نتيجةُ أذًى تراكم فوق ما أُصلح.
            reg = (self.world.region(
                self.world.settlements[a.settlement].x,
                self.world.settlements[a.settlement].y)
                if a.settlement < len(self.world.settlements) else None)
            med = -T.effect(know_of, "mort")
            ctxw = dict(pop=(self.world.settlements[a.settlement].pop()
                             + self.mass.get(a.settlement, 0))
                        if a.settlement < len(self.world.settlements) else 0,
                        provision=max(0.0, 1.0 - min(1.0, a.hunger)))
            if reg is not None:
                CA.wear(a, ctxw, know_of, reg, cfg, rng, med)
            gone, why, detail = CA.hazard(a, cfg, rng)
            if gone:
                a.why_died = f"{why} — {detail} · {CA.explain(a)}"
                self._kill(a, why)
                continue
            haz = 0.0
            if a.age < 5:
                # موت الأطفال قبل الطبّ: ربعُ المواليد إلى نصفهم لم يبلغوا
                # الخامسة. وهذا ليس تفصيلًا ديموغرافيًا — هو أغزر مصادر
                # الحزن في هذه الدنيا، والحزن يغذّي كل ما بُني على الرهبة.
                haz += cfg.infant_mortality * (1.0 - 0.16 * a.age)                     * (1.0 - 0.55 * a.eg.t[G.VIGOR])                     * (1.0 + 0.8 * min(1.0, a.hunger))                     * (1.0 + 2.2 * T.effect(know_of, "mort"))
            haz += 0.30 * max(0.0, -a.health)
            if a.health <= 0.0:
                a.why_died = f"انهيار البدن · {CA.explain(a)}"
                self._kill(a, "جوع" if a.hunger > 0.7 else "سقم")
                continue
            if rng.random() < haz:
                a.why_died = CA.explain(a)
                self._kill(a, "سقم")
                continue

            # ما يُدفن، وما يعود، وما قد يُنهي
            st = (self.world.settlements[a.settlement]
                  if a.settlement < len(self.world.settlements) else None)
            if st is not None:
                if PS.repress(a, rng) is not None:
                    self.stats["repressed"] += 1
                back = PS.return_of_repressed(a, rng, self.year)
                if back is not None:
                    appraise(a.af, a.eg, loss=0.6, blame_self=0.4)

                out = CN.tick(a, None)
                if out == "broke":
                    self.stats["broken_vows"] = self.stats.get("broken_vows", 0) + 1
                elif out == "kept":
                    self.stats["kept_vows"] = self.stats.get("kept_vows", 0) + 1
                d, kind = PS.despair(a, st, st.doctrine, self.agents, cfg)
                a.despair = d
                if d > 1.05 and rng.random() < 0.055 * (d - 1.0):
                    # من عرف أن الغضب موعدٌ لا عقاب، ثم بقي الموت: ثلاثة أبواب
                    if a.heretic and a.stance is None:
                        a.stance = PS.absurd_response(a, rng)
                        if a.stance == "leap":
                            a.heretic = False
                            a.faith = 0.88
                            a.doubt = 0.12
                            if st.doctrine:
                                for k in st.doctrine.tenets:
                                    a.conv[k] = 1.15
                            a.despair *= 0.35
                            self.chron.add(self.year, "leap",
                                           f"عاد {a.name} إلى الإيمان بعد أن رأى "
                                           f"الدليل، ولم ينكره — تجاوزه.", 3.0)
                            continue
                        if a.stance == "revolt":
                            a.despair *= 0.4
                            PW.prestige_gain(a, 0.3)
                            self.chron.add(self.year, "revolt_absurd",
                                           f"عرف {a.name} أن لا عقاب ولا موعد، "
                                           f"ومضى في يومه وهو عارف.", 3.0)
                            continue
                    self._kill(a, "يأس · " + PS.AR_SUICIDE[kind])
                    self.stats["suicides"] += 1
                    self.chron.add(self.year, "suicide",
                                   f"أنهى {a.name} حياته — {PS.AR_SUICIDE[kind]}.", 2.4)
                    continue

            # التأمّل التلقائي في الشيخوخة والفراغ
            if a.age % 3 == 0 and a.hunger < 0.4:
                res, high = (self._ressentiment(a, st) if st is not None else (0.0, ()))
                reflect(a, cfg, rng, self.year, res, high)

    def _kill(self, a, cause, killer=None):
        if not a.alive:
            return
        a.alive = False
        a.cause = cause
        a.death_year = self.year
        self.stats["deaths"] += 1
        st = self.world.settlements[a.settlement] if a.settlement < len(self.world.settlements) else None
        if st is not None and a.id in st.members:
            st.members.remove(a.id)
            if st.ruler == a.id:
                st.ruler = -1
        for k in list(a.bonds.kin) + [a.bonds.partner]:
            b = self.agents.get(k)
            if b is not None and b.alive:
                if b.bonds.partner == a.id:
                    b.bonds.partner = -1          # فُكّ الرابط، فيمكن أن يرتبط ثانية
                appraise(b.af, b.eg, loss=1.0)
                b.mem.store(K_DEATH, self.year, who=a.id, val=-0.8, strength=1.8,
                            truth=1.0, src=S_LIVED, tag="فقد")
        PG.fire('on_death', self, a, None, self.rs.get('plugin'))
        self.dead.append(GD.Departed(a))
        del self.agents[a.id]

    def _migrate(self, st, dest, rng):
        """ينتقلون إلى قريةٍ قائمة بدل تأسيس واحدة — فينشأ التراتب."""
        cfg = self.cfg
        movers = [self.agents[m] for m in st.members if m in self.agents
                  and self.agents[m].age >= cfg.adult_age]
        movers.sort(key=lambda a: -(a.eg.t[G.OPENNESS] + a.longing))
        movers = movers[:max(4, st.pop() // 5)]
        if len(movers) < 4:
            return
        for a in movers:
            st.members.remove(a.id)
            dest.members.append(a.id)
            a.settlement = dest.id
            a.mem.store(K_JOURNEY, self.year, val=0.3, strength=1.3,
                        truth=1.0, src=S_LIVED, tag="انتقال")
        st.relations[dest.id] = min(1.0, st.relations.get(dest.id, 0.4) + 0.2)
        dest.relations[st.id] = min(1.0, dest.relations.get(st.id, 0.4) + 0.2)
        self.chron.add(self.year, "migration",
                       f"انتقل {len(movers)} من {st.name} إلى {dest.name}.", 2.0)

    def _split(self, st):
        cfg = self.cfg
        rng = self.rs.get("split")
        if st.pop() < cfg.settlement_split_at:
            return
        # هل ينضمّون إلى قائمةٍ أم يؤسّسون جديدة؟
        #
        # كانت كل مجموعةٍ تخرج فتؤسّس قرية، فخرجت قرًى متساوية الأحجام بلا
        # تراتب — ولا مدينة في العالم. والتراتب الحضري لا يأتي من انقسامٍ
        # متساوٍ بل من **الارتباط التفضيلي**: الكبير يجذب أكثر لأنه كبير
        # (Simon 1955 · Gabaix 1999)، وهو ما يعطي زيبف.
        near = [s for s in self.world.settlements
                if s.id != st.id and abs(s.x - st.x) + abs(s.y - st.y) <= 5
                and s.pop() + self.mass.get(s.id, 0) > 0]
        if near and rng.random() < 0.62:
            wts = [(s, (s.pop() + self.mass.get(s.id, 0)) ** 1.25 *
                    (0.4 + max(0.0, st.relations.get(s.id, 0.4)))) for s in near]
            tot = sum(w for _, w in wts)
            if tot > 0:
                pick = rng.random() * tot
                acc = 0.0
                for s, w in wts:
                    acc += w
                    if pick <= acc:
                        return self._migrate(st, s, rng)

        r = self.world.best_free(st.x, st.y, rng)
        if r is None:
            return
        movers = sorted((self.agents[m] for m in st.members if m in self.agents),
                        key=lambda a: -(a.eg.t[G.OPENNESS] + a.eg.t[G.DOMINANCE] * 0.5
                                        + a.bonds.resentment.get(st.ruler, 0.0)))
        movers = [a for a in movers if a.age >= cfg.adult_age][:max(6, st.pop() // 4)]
        if len(movers) < 6:
            return
        sid = len(self.world.settlements)
        new = Settlement(sid, r.name, r.x, r.y, self.year)
        r.settled = sid
        new.knowledge = set(st.knowledge)
        new.records = list(st.records)
        new.doctrine = st.doctrine.fork(st.doctrine.name, self.year, st.doctrine.sect) \
            if st.doctrine else None
        self.world.settlements.append(new)
        self.mass[sid] = 0
        for a in movers:
            st.members.remove(a.id)
            new.members.append(a.id)
            a.settlement = sid
            a.mem.store(K_JOURNEY, self.year, val=0.35, strength=1.4,
                        truth=1.0, src=S_LIVED, tag="هجرة")
        st.relations[sid] = 0.6
        new.relations[st.id] = 0.6
        self.chron.add(self.year, "settlement",
                       f"خرج {len(movers)} من {st.name} وأسّسوا {new.name}.", 2.4)

    # ================================================================ قياسات
    def population(self):
        return len(self.agents) + sum(self.mass.values())

    def _snapshot(self):
        ags = list(self.agents.values())
        n = max(1, len(ags))
        truth = sum(a.mem.truthfulness() for a in ags) / n
        faith = sum(a.faith for a in ags) / n
        doubt = sum(a.doubt for a in ags) / n
        tyr = 0.0
        for st in self.world.settlements:
            tyr += PW.tyranny_index(st, self.agents)
        tyr /= max(1, len(self.world.settlements))
        know = set()
        for st in self.world.settlements:
            know |= st.knowledge
        self.chron.snapshot(dict(
            year=self.year, pop=self.population(), named=len(ags),
            truth=truth, faith=faith, doubt=doubt, tyranny=tyr,
            tech=len(know), settlements=len(self.world.settlements),
            heretics=sum(1 for a in ags if a.heretic),
            clergy=sum(1 for a in ags if a.clergy),
            complexity=sum(a.prog.complexity() for a in ags) / n,
            foul=sum(s.foul for s in self.world.settlements) / max(1, len(self.world.settlements)),
            literacy=sum(s.literacy for s in self.world.settlements) / max(1, len(self.world.settlements)),
            concepts=sum(len(a.concepts) for a in ags),
            books=sum(len(s.library.books) for s in self.world.settlements),
            damage=sum(a.damage for a in ags) / n,
            maxims=sum(len(a.prog.maxims) for a in ags),
            doctrine=max((d.complexity for d in self.doctrines.values()), default=0.0),
            climate=self.world.climate,
        ))
