#!/usr/bin/env python
"""
تشغيل القرية.

  python run.py --years 200                 بداية آمنة
  python run.py --years 10000 --report out.html
  python run.py --history                   اطبع الماضي الذي لم يقع
  python run.py --years 500 --speed 50      خمسون سنة في الثانية

الرنّ يقيس ذاكرته كل خمس وعشرين سنة ويقف بأدب عند السقف (--mem-limit)،
ويحفظ ما بلغه على القرص كل حين (--checkpoint) فلا يضيع شيء إن توقّف.
"""

import argparse
import json
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from village.config import Config
from village.engine import Sim
from village.guard import MemoryCeiling, rss_mb, be_polite, yield_cpu
from village import history as HI
from village import tech as T
from village.lang import render_maxim


def banner(sim):
    print("=" * 78)
    print(f"  القرية — بذرة {sim.cfg.seed}")
    print(f"  {len(sim.agents)} إنسانًا · ماضٍ مزروع طوله {sim.cfg.prior_years} سنة "
          f"({sim.history['generations']} جيلًا)")
    print(f"  سقف الذاكرة {sim.cfg.mem_limit_mb} ميجابايت · "
          f"الاستهلاك الآن {rss_mb():.0f}")
    print("=" * 78)


def line(sim):
    s = sim.chron.snapshots[-1] if sim.chron.snapshots else None
    if not s:
        return
    print(f"سنة {s['year']:>6} | عدد {s['pop']:>6} | قرى {s['settlements']:>3} "
          f"| معرفة {s['tech']:>2} | إيمان {s['faith']:.2f} | شكّ {s['doubt']:.2f} "
          f"| صدق الذاكرة {s['truth']:.2f} | طغيان {s['tyranny']:.2f} "
          f"| منكرون {s['heretics']:>3} | ذاكرة {rss_mb():>5.0f}م")


def save_checkpoint(sim, path):
    data = dict(
        year=sim.year, seed=sim.cfg.seed, population=sim.population(),
        stats=dict(sim.stats), snapshots=sim.chron.snapshots[-400:],
        wrath=[[y, k, round(s, 3)] for y, k, s in sim.world.wrath.history],
        discoveries=[[e.year, e.text] for e in sim.chron.by_kind("tech")],
        major=[[e.year, e.kind, e.text] for e in sim.chron.major(3.0)][-200:],
        # أوّل كل نوعٍ من الأحداث لا يسقط أبدًا مهما طال الرنّ
        firsts={k: [v[0], v[1]] for k, v in sim.chron.firsts.items()},
        milestones=[[e.year, e.kind, e.text]
                    for e in sim.chron.events
                    if e.kind in ("discovery", "epoch", "star", "naturalism",
                                  "months", "taboo", "prophecy", "burning")],
        rss_mb=round(rss_mb(), 1),
    )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def summary(sim, dt, stopped=None):
    print()
    print("=" * 78)
    if stopped:
        print(f"توقّف: {stopped}")
    print(f"انتهى عند سنة {sim.year:,} في {dt:.1f} ثانية "
          f"({sim.year / max(0.01, dt):.0f} سنة/ث) · ذاكرة {rss_mb():.0f} ميجابايت")
    print(f"الأحياء {sim.population():,} | مواليد {sim.stats['births']:,} | "
          f"وفيات {sim.stats['deaths']:,} | قتل {sim.stats['murders']:,} | "
          f"غضب {sim.stats['wraths']:,} | ثورات {sim.stats['revolts']:,} | "
          f"اضطهاد {sim.stats['persecutions']:,} | انشقاقات {sim.stats['schisms']:,}")

    know = set()
    for st in sim.world.settlements:
        know |= st.knowledge
    print("المعرفة:", "، ".join(T.BY_KEY[k][1] for k in
                                sorted(know, key=lambda k: T.ORDER[k])) or "—")

    wr = sim.world.wrath.history
    if len(wr) > 1:
        gaps = [wr[i + 1][0] - wr[i][0] for i in range(len(wr) - 1)]
        print(f"دورة الغضب الحقيقية: {sum(gaps)/len(gaps):.1f} سنة "
              f"(وقعت {len(wr)} مرة)")
    disc = sim.chron.by_kind("discovery")
    print("الكشف:", disc[0].text if disc else "لم يكتشف أحدٌ منهم الدورة.")

    print("\n--- أهم ما جرى ---")
    for e in sim.chron.major(3.0)[-25:]:
        print(f"  سنة {e.year:>6}: {e.text}")

    maxims, seen = [], set()
    for a in sim.agents.values():
        for m in a.prog.maxims:
            if m.lineage in seen:
                continue
            seen.add(m.lineage)
            maxims.append((m.taught, m, a))
    maxims.sort(key=lambda p: -p[0])
    if maxims:
        print("\n--- حِكَم ألّفوها بأنفسهم (الكود الذي كتبوه) ---")
        for taught, m, a in maxims[:12]:
            print(f"  «{render_maxim(m)}»  — {a.name}، نُقلت {taught} مرة")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=200)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--speed", default="max", help="سنة/ثانية، أو max")
    ap.add_argument("--every", type=int, default=None)
    ap.add_argument("--report", default=None)
    ap.add_argument("--checkpoint", default=None, help="ملف JSON يُحفَظ دوريًا")
    ap.add_argument("--checkpoint-every", type=int, default=200)
    ap.add_argument("--mem-limit", type=int, default=None,
                    help="سقف الذاكرة بالميجابايت (افتراضي 1200)")
    ap.add_argument("--max-named", type=int, default=None)
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--yield-every", type=int, default=40,
                    help="أفسِح للنظام كل كم سنة (0 = لا تفسح)")
    args = ap.parse_args()

    cfg = Config()
    if args.seed is not None:
        cfg.seed = args.seed
    if args.max_named:
        cfg.max_named = args.max_named
    if args.mem_limit:
        cfg.mem_limit_mb = args.mem_limit
    cfg.years = args.years

    if args.history:
        import random
        print(HI.render(HI.generate(cfg, random.Random(cfg.seed))))
        return

    pol = be_polite()
    sim = Sim(cfg)
    if not args.quiet and pol:
        print(f"  أولويّة العملية: {pol} — كي يبقى الجهاز مستجيبًا")
    if not args.quiet:
        banner(sim)

    every = args.every or max(cfg.snapshot_every, args.years // 40 or 1)
    delay = 0.0 if args.speed == "max" else 1.0 / max(0.01, float(args.speed))

    t0 = time.time()
    stopped = None
    try:
        for _ in range(args.years):
            sim.step()
            yield_cpu(sim.year, args.yield_every)
            if sim.year % cfg.housekeep_every == 0:
                sim.housekeep()
            if delay:
                time.sleep(delay)
            if not args.quiet and sim.year % every == 0:
                line(sim)
            if args.checkpoint and sim.year % args.checkpoint_every == 0:
                save_checkpoint(sim, args.checkpoint)
            if sim.population() <= 0:
                stopped = f"انقرضوا في سنة {sim.year:,}"
                break
    except MemoryCeiling as e:
        stopped = str(e)
    except KeyboardInterrupt:
        stopped = f"أُوقف يدويًا عند سنة {sim.year:,}"

    summary(sim, time.time() - t0, stopped)

    if args.checkpoint:
        save_checkpoint(sim, args.checkpoint)
        print(f"\nنقطة الحفظ: {args.checkpoint}")
    if args.report:
        from village.report import build
        build(sim, args.report)
        print(f"التقرير: {args.report}")


if __name__ == "__main__":
    main()
