"""السجلّ: ما جرى فعلًا — لا ما يتذكّرونه."""


class Event:
    __slots__ = ("year", "kind", "text", "weight")

    def __init__(self, year, kind, text, weight):
        self.year = year
        self.kind = kind
        self.text = text
        self.weight = weight


class Chronicle:
    def __init__(self):
        self.events = []
        self.snapshots = []
        self.firsts = {}

    def add(self, year, kind, text, weight=1.0):
        self.events.append(Event(year, kind, text, weight))
        if kind not in self.firsts:
            self.firsts[kind] = (year, text)

    def snapshot(self, row):
        self.snapshots.append(row)

    def major(self, minimum=2.0, limit=None):
        out = [e for e in self.events if e.weight >= minimum]
        return out[-limit:] if limit else out

    def by_kind(self, kind):
        return [e for e in self.events if e.kind == kind]

    def eras(self, width=500):
        """يقسّم التاريخ إلى حقب ويلخّص كلًّا منها."""
        if not self.snapshots:
            return []
        out = []
        last = self.snapshots[-1]["year"]
        y = 0
        while y <= last:
            rows = [s for s in self.snapshots if y <= s["year"] < y + width]
            evs = [e for e in self.events if y <= e.year < y + width]
            if rows:
                out.append(dict(
                    start=y, end=y + width - 1,
                    pop_max=max(r["pop"] for r in rows),
                    pop_min=min(r["pop"] for r in rows),
                    pop_end=rows[-1]["pop"],
                    truth=sum(r["truth"] for r in rows) / len(rows),
                    faith=sum(r["faith"] for r in rows) / len(rows),
                    doubt=sum(r["doubt"] for r in rows) / len(rows),
                    tyranny=sum(r["tyranny"] for r in rows) / len(rows),
                    tech=rows[-1]["tech"],
                    settlements=rows[-1]["settlements"],
                    wraths=len([e for e in evs if e.kind == "wrath"]),
                    revolts=len([e for e in evs if e.kind == "revolt"]),
                    murders=len([e for e in evs if e.kind == "murder"]),
                    wars=len([e for e in evs if e.kind == "war"]),
                    schisms=len([e for e in evs if e.kind == "schism"]),
                    discoveries=[e.text for e in evs if e.kind == "tech"],
                    milestones=[e for e in evs if e.weight >= 3.0],
                ))
            y += width
        return out
