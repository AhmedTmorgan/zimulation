#!/usr/bin/env python
"""
الدراسة: رنٌّ واحد حكاية، ومئة رنٍّ إجابة.

  python study.py --seeds 20 --years 1000 --workers 4
  python study.py --seeds 100 --years 4000 --workers 8 --out study.json

يشغّل العالم نفسه ببذور مختلفة ويجمع النتائج، فيصير السؤال قابلًا للقياس:
كم مرّة اتّحدوا فبلغوا الكتابة والتقويم وكشفوا دورة الغضب؟
وكم مرّة اقتتلوا فبقوا محبوسين في الحلقة؟

كل رنّ يقع في عملية مستقلة بسقف ذاكرته، فلا يجرّ رنٌّ متعثّر البقيةَ معه.
"""

import argparse
import concurrent.futures as cf
import json
import os
import pathlib
import sys
import time
import traceback

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def one(args):
    seed, years, max_named, mem_limit = args
    from village.config import Config
    from village.engine import Sim
    from village.guard import MemoryCeiling, rss_mb
    from village import tech as T

    cfg = Config()
    cfg.seed = seed
    cfg.years = years
    cfg.max_named = max_named
    cfg.mem_limit_mb = mem_limit

    t0 = time.time()
    stopped = None
    try:
        sim = Sim(cfg)
        for _ in range(years):
            sim.step()
            if sim.year % cfg.housekeep_every == 0:
                sim.housekeep()
            if sim.population() <= 0:
                stopped = "extinct"
                break
    except MemoryCeiling:
        stopped = "memory"
    except Exception:
        return dict(seed=seed, error=traceback.format_exc()[-600:])

    know = set()
    for st in sim.world.settlements:
        know |= st.knowledge
    wr = sim.world.wrath.history
    gaps = [wr[i + 1][0] - wr[i][0] for i in range(len(wr) - 1)]
    disc = sim.chron.by_kind("discovery")
    snaps = sim.chron.snapshots

    return dict(
        seed=seed, years=sim.year, stopped=stopped,
        population=sim.population(),
        peak=max((s["pop"] for s in snaps), default=0),
        settlements=len(sim.world.settlements),
        techs=len(know),
        landmarks=[k for k in T.LANDMARKS if k in know],
        writing="writing" in know,
        calendar="calendar" in know,
        method="method" in know,
        electricity="current" in know,
        waves="waves" in know,
        discovered=bool(disc),
        discovery_year=disc[0].year if disc else None,
        true_gap=round(sum(gaps) / len(gaps), 2) if gaps else None,
        wraths=sim.stats["wraths"],
        revolts=sim.stats["revolts"],
        murders=sim.stats["murders"],
        persecutions=sim.stats["persecutions"],
        schisms=sim.stats["schisms"],
        births=sim.stats["births"], deaths=sim.stats["deaths"],
        faith=round(snaps[-1]["faith"], 3) if snaps else None,
        doubt=round(snaps[-1]["doubt"], 3) if snaps else None,
        truth=round(snaps[-1]["truth"], 3) if snaps else None,
        tyranny=round(sum(s["tyranny"] for s in snaps) / len(snaps), 3) if snaps else None,
        heretics=snaps[-1]["heretics"] if snaps else 0,
        maxims=snaps[-1]["maxims"] if snaps else 0,
        doctrine=round(snaps[-1]["doctrine"], 1) if snaps else None,
        seconds=round(time.time() - t0, 1),
        rss=round(rss_mb(), 1),
    )


def digest(rows):
    ok = [r for r in rows if "error" not in r]
    n = len(ok) or 1
    survived = [r for r in ok if r["population"] > 0]
    disc = [r for r in ok if r["discovered"]]

    def pct(xs):
        return f"{100.0 * len(xs) / n:.0f}%"

    print()
    print("=" * 74)
    print(f"  {len(ok)} رنًّا · {ok[0]['years'] if ok else 0} سنة لكلٍّ منها")
    print("=" * 74)
    print(f"نجَوا حتى النهاية      : {len(survived):>3} ({pct(survived)})")
    for key, label in (("writing", "بلغوا الكتابة"),
                       ("calendar", "بلغوا التقويم"),
                       ("method", "بلغوا المنهج التجريبي"),
                       ("electricity", "بلغوا الكهرباء"),
                       ("waves", "بلغوا الموجات")):
        xs = [r for r in ok if r[key]]
        print(f"{label:<22}: {len(xs):>3} ({pct(xs)})")
    print(f"كشفوا دورة الغضب      : {len(disc):>3} ({pct(disc)})")
    if disc:
        ys = sorted(r["discovery_year"] for r in disc)
        print(f"  سنة الكشف: أبكر {ys[0]:,} · وسيط {ys[len(ys)//2]:,} · أمتع {ys[-1]:,}")

    if survived:
        def avg(k):
            vs = [r[k] for r in survived if r[k] is not None]
            return sum(vs) / len(vs) if vs else 0.0
        print()
        print(f"من نجا — متوسطات: عدد {avg('population'):,.0f} · "
              f"قرى {avg('settlements'):.1f} · معارف {avg('techs'):.1f}")
        print(f"  إيمان {avg('faith'):.2f} · شكّ {avg('doubt'):.2f} · "
              f"صدق الذاكرة {avg('truth'):.2f} · طغيان {avg('tyranny'):.2f}")
        print(f"  ثورات {avg('revolts'):.0f} · قتل {avg('murders'):.0f} · "
              f"اضطهاد {avg('persecutions'):.0f} · انشقاقات {avg('schisms'):.1f}")

    # السؤال الأصلي: هل الاتّحاد هو ما يفتح الباب؟
    if len(ok) >= 6:
        hi = [r for r in ok if r["discovered"]]
        lo = [r for r in ok if not r["discovered"]]
        if hi and lo:
            print()
            print("من كشف الدورة مقابل من لم يكشف:")
            for k, lab in (("peak", "ذروة العدد"), ("settlements", "القرى"),
                           ("murders", "القتل"), ("revolts", "الثورات"),
                           ("persecutions", "الاضطهاد"), ("tyranny", "الطغيان")):
                a = sum(r[k] or 0 for r in hi) / len(hi)
                b = sum(r[k] or 0 for r in lo) / len(lo)
                print(f"  {lab:<12}: كاشفون {a:>9,.1f}  |  غير كاشفين {b:>9,.1f}")

    bad = [r for r in rows if "error" in r]
    if bad:
        print(f"\n{len(bad)} رنًّا تعثّر. أول خطأ:\n{bad[0]['error']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--first-seed", type=int, default=1000)
    ap.add_argument("--years", type=int, default=1000)
    ap.add_argument("--max-named", type=int, default=300)
    ap.add_argument("--mem-limit", type=int, default=900)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--out", default="study.json")
    ap.add_argument("--merge", default=None,
                    help="بدل التشغيل: ادمج كل ملفات json في هذا المجلّد ولخّصها")
    args = ap.parse_args()

    if args.merge:
        rows = []
        for f in sorted(pathlib.Path(args.merge).rglob("*.json")):
            try:
                rows += json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:
                print("تعذّر:", f, e)
        print(f"دُمج {len(rows)} رنًّا من {args.merge}")
        digest(rows)
        pathlib.Path(args.out).write_text(
            json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        return

    jobs = [(args.first_seed + i, args.years, args.max_named, args.mem_limit)
            for i in range(args.seeds)]
    print(f"{len(jobs)} رنًّا × {args.years} سنة على {args.workers} عاملًا…")

    rows = []
    t0 = time.time()
    with cf.ProcessPoolExecutor(max_workers=args.workers) as ex:
        for r in ex.map(one, jobs):
            rows.append(r)
            done = len(rows)
            tag = "خطأ" if "error" in r else (
                "كشف!" if r["discovered"] else
                ("انقرض" if r["population"] == 0 else f"{r['population']:,}"))
            print(f"  [{done:>3}/{len(jobs)}] بذرة {r['seed']} — {tag} "
                  f"({r.get('seconds', 0)}ث)")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    digest(rows)
    print(f"\nالبيانات الكاملة: {args.out} · الزمن {time.time() - t0:.0f}ث")


if __name__ == "__main__":
    main()
