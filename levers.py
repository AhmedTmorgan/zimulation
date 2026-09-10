#!/usr/bin/env python
"""تجارب مضبوطة على أسباب الموت: أطفئ سببًا واحدًا وقِس الفارق."""
import statistics, sys
from collections import Counter
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from village.config import Config
from village.engine import Sim
from village.guard import be_polite, yield_cpu

YEARS = int(sys.argv[1]) if len(sys.argv) > 1 else 240

def run(**kw):
    """
    يقيس أثرًا **مباشرًا** وأثرًا **صافيًا**، ولا يخلط بينهما.

    الأثر الصافي (عمر الوفاة في الرنّ كله) مُلوَّثٌ بمالتوس: إزالة سببِ
    موتٍ تزيد العدد، فيعود الشحُّ بما ذهب. ولذلك يُقاس الأثر المباشر في
    **القرن الأول وحده** — قبل أن يستجيب التعداد — وعلى **قسمٍ عمريّ
    واحد** حتى لا يختلف تركيب السكان.
    """
    cfg = Config()
    cfg.mem_limit_mb = 700
    for k, v in kw.items():
        setattr(cfg, k, v)
    s = Sim(cfg)
    early_alive = early_dead = 0
    for _ in range(YEARS):
        s.step()
        yield_cpu(s.year, 25)
        if s.year % 25 == 0:
            s.housekeep()
        if s.year <= 90:            # القرن الأول: قبل أن يتحرّك التعداد
            n40 = sum(1 for a in s.agents.values() if 35 <= a.age < 50)
            early_alive += n40
            early_dead += sum(1 for d in s.dead
                              if d.death_year == s.year and 35 <= d.age < 50)
    sur = [d.age for d in s.dead if d.age >= 5]
    c = Counter(d.cause for d in s.dead)
    n = max(1, len(s.dead))
    return dict(age=statistics.mean(sur) if sur else 0,
                kid=100 * sum(1 for d in s.dead if d.age < 5) / n,
                pop=s.population(), tum=100 * c.get("ورم", 0) / n,
                wan=100 * c.get("وهنٌ", 0) / n, born=s.stats["births"],
                q40=1000.0 * early_dead / max(1, early_alive))

be_polite()
base = run()
rows = [("— الأصل —", base, None)]
for k, lab in (("cause_water", "بلا أذى الماء"), ("cause_toil", "بلا إنهاك الكدح"),
               ("cause_soma", "بلا مقايضة النسل"), ("cause_tumour", "بلا أورام"),
               ("sky_orbit", "بلا ترنّح المحور"), ("sky_ocean", "بلا مرجّح المحيط"),
               ("sky_volcano", "بلا براكين"), ("sky_albedo", "بلا أثرٍ لعريِ أرضهم")):
    r = run(**{k: False})
    rows.append((lab, r, r["age"] - base["age"]))

print(f"{YEARS} سنة لكل تجربة · نفس البذرة · الفارق سببٌ واحد\n")
print("الأثر المباشر: وفيات من هم بين 35 و50 في القرن الأول (لكل ألف).")
print("الأثر الصافي: عمر الوفاة في الرنّ كله — وهو مُلوَّثٌ باستجابة التعداد.")
print()
print(f"{'المِعوَل':<20}{'مباشر q40':>11}{'فارقه':>9}{'صافٍ (عمر)':>12}{'العدد':>9}")
print("-" * 64)
for lab, r, d in rows:
    dq = f"{r['q40'] - base['q40']:+.1f}" if d is not None else ""
    print(f"{lab:<20}{r['q40']:>11.1f}{dq:>9}{r['age']:>12.1f}{r['pop']:>9,}")
print()
print("إشارةُ الأثر المباشر هي الحقيقة السببية. وانقلابُها في العمود الصافي")
print("ليس خطأً بل مالتوس: ما رُفع من موتٍ يعود شحًّا.")
