"""Крок 7. Факти зі Spark event log (те саме, що показує History Server, але таблицею).

Для кожного stage: задачі, прочитано (input), shuffle read/write (записи, байти), тривалість задач (медіана / max).
Ці числа йдуть у стовпці «Факт» і «Stage» таблиці оцінок, у розділ про перекіс (розміри задач) і в експеримент.

Запуск:  python3 scripts/07_stage_metrics.py --app final-05-full --out out/07_stages_full.md
         python3 scripts/07_stage_metrics.py --app-prefix final-05-exp- --summary --out out/10_experiment_runs.md
"""
import argparse
import glob
import json
import os
import statistics

MB = 1024 * 1024


def read_events(path: str) -> list:
    files = sorted(glob.glob(os.path.join(path, "events_*")),
                   key=lambda p: int(os.path.basename(p).split("_")[1])) if os.path.isdir(path) else [path]
    events = []
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            for line in f:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:  # останній рядок застосунку, який ще пише лог
                    pass
    return events


def analyze(events: list) -> dict:
    app = {"stages": {}}
    for e in events:
        kind = e["Event"]
        if kind == "SparkListenerApplicationStart":
            app.update(name=e["App Name"], id=e.get("App ID"), start=e["Timestamp"])
        elif kind == "SparkListenerApplicationEnd":
            app["end"] = e["Timestamp"]
        elif kind == "SparkListenerStageCompleted":
            info = e["Stage Info"]
            st = app["stages"].setdefault(info["Stage ID"], {"tasks": []})
            st.update(name=info["Stage Name"], ntasks=info["Number of Tasks"])
        elif kind == "SparkListenerTaskEnd" and e.get("Task Metrics"):
            m, ti = e["Task Metrics"], e["Task Info"]
            sr, sw, inp = m["Shuffle Read Metrics"], m["Shuffle Write Metrics"], m["Input Metrics"]
            app["stages"].setdefault(e["Stage ID"], {"tasks": []})["tasks"].append({
                "dur": (ti["Finish Time"] - ti["Launch Time"]) / 1000,
                "in_b": inp["Bytes Read"], "in_r": inp["Records Read"],
                "sr_b": sr["Remote Bytes Read"] + sr["Local Bytes Read"], "sr_r": sr["Total Records Read"],
                "sw_b": sw["Shuffle Bytes Written"], "sw_r": sw["Shuffle Records Written"],
            })
    for st in app["stages"].values():
        t = st["tasks"]
        st.update({k: sum(x[k] for x in t) for k in ("in_b", "in_r", "sr_b", "sr_r", "sw_b", "sw_r")})
        durs = [x["dur"] for x in t] or [0]
        reads = [x["sr_b"] for x in t] or [0]
        st.update(dur_med=statistics.median(durs), dur_max=max(durs),
                  sr_med=statistics.median(reads), sr_max=max(reads))
    app["seconds"] = (app.get("end", app.get("start", 0)) - app.get("start", 0)) / 1000
    return app


def stage_table(app: dict) -> str:
    lines = [f"### {app['name']} ({app['id']}): {app['seconds']:.1f} с", "",
             "| Stage | Назва | Задач | Input (записи / МБ) | Shuffle read (записи / МБ) | Shuffle write (записи / МБ) "
             "| Задача: медіана / max, с | Shuffle read на задачу: медіана / max, МБ |",
             "|---|---|---|---|---|---|---|---|"]
    for sid in sorted(app["stages"]):
        s = app["stages"][sid]
        if not s["tasks"]:
            continue
        lines.append(
            f"| {sid} | {s.get('name', '')[:40]} | {len(s['tasks'])} | {s['in_r']:,} / {s['in_b'] / MB:,.1f} "
            f"| {s['sr_r']:,} / {s['sr_b'] / MB:,.2f} | {s['sw_r']:,} / {s['sw_b'] / MB:,.2f} "
            f"| {s['dur_med']:.2f} / {s['dur_max']:.2f} | {s['sr_med'] / MB:.2f} / {s['sr_max'] / MB:.2f} |")
    return "\n".join(lines) + "\n"


def summary_row(app: dict) -> str:
    st = [app["stages"][k] for k in sorted(app["stages"]) if app["stages"][k]["tasks"]]
    read_stage = max(st, key=lambda s: s["in_b"])
    shuffles = " / ".join(f"{s['sw_r']:,} ({s['sw_b'] / MB:.1f} МБ)" for s in st if s["sw_r"])
    return (f"| {app['name']} | {app['seconds']:.1f} | {sum(s['in_b'] for s in st) / MB:,.1f} "
            f"| {len(read_stage['tasks'])} | {shuffles} |")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--app", help="точна назва застосунку (береться останній запуск)")
    ap.add_argument("--app-prefix", help="усі застосунки з таким початком назви")
    ap.add_argument("--dir", default="spark-events")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()

    apps = [analyze(read_events(p)) for p in a.paths]
    if a.app or a.app_prefix:
        for p in sorted(glob.glob(os.path.join(a.dir, "*")), key=os.path.getmtime):
            if os.path.basename(p).startswith("."):
                continue
            app = analyze(read_events(p))
            name = app.get("name", "")
            if (a.app and name == a.app) or (a.app_prefix and name.startswith(a.app_prefix)):
                apps.append(app)
        if a.app:
            apps = apps[-1:]
    if a.summary:
        text = ("| Запуск | Час застосунку, с | Прочитано, МБ | Задач на читанні | Shuffle write по stage-ах |\n"
                "|---|---|---|---|---|\n" + "\n".join(summary_row(x) for x in apps) + "\n")
    else:
        text = "\n".join(stage_table(x) for x in apps)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    main()
