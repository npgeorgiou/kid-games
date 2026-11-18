#!/usr/bin/env python3
"""Cue table -> readable doc (docs/patterns/cues.md).

usage: python3 tools/cues_doc.py games/<game>/cues.json
Writes games/<game>/cues.md (version B) from cues.json (version A), and rewrites cues.json in its tidy form.
It stops with a list when the table uses a word its "words" section does not explain."""
import json, re, sys, pathlib

def tidy(obj, ind=0):
    """JSON with one key per line, short lists kept on one line."""
    pad = " " * ind
    if isinstance(obj, dict):
        if not obj: return "{}"
        return "{\n" + ",\n".join(pad + " " + json.dumps(k, ensure_ascii=False) + ": " + tidy(v, ind + 1) for k, v in obj.items()) + "\n" + pad + "}"
    if isinstance(obj, list):
        flat = json.dumps(obj, ensure_ascii=False)
        if not any(isinstance(v, dict) for v in obj) and len(flat) < 160: return flat
        return "[\n" + ",\n".join(pad + " " + tidy(v, ind + 1) for v in obj) + "\n" + pad + "]"
    return json.dumps(obj, ensure_ascii=False)

def main(path):
    p = pathlib.Path(path)
    T = json.loads(p.read_text(encoding="utf-8"))
    p.write_text(tidy(T) + "\n", encoding="utf-8")
    W, L, sites = T["words"], T["lines"], [s["name"] for s in T.get("sites", [])]
    missing = []
    def word(kind, name):
        base = name[4:] if kind == "conditions" and name.startswith("not ") else name
        table = W[kind]
        if base in table: d = table[base]
        elif base.startswith("done:") and "done:<cue>" in table: d = "cue " + base[5:] + " has already played"
        elif kind == "points" and base.split(":")[0] + ":<name>" in table: d = table[base.split(":")[0] + ":<name>"] + " — " + base.split(":")[1]
        else: missing.append(kind + " " + name); d = name
        if isinstance(d, dict): d = d["desc"]
        return ("not: " + d) if name.startswith("not ") else d
    said = []  # owner 16 Nov: when it plays first, in bold; the Greek text after it
    def q(n):
        if str(n) in L: said.append("«%s»" % L[str(n)])
        return "line %s" % n if str(n) in L else "line %s (no text: recording only)" % n
    def greek_after(desc):
        out = "**%s**" % desc + ("<br>" + "<br>".join(said) if said else ""); said.clear(); return out
    def says(s):
        if s is None: return None
        if isinstance(s, int): return q(s)
        if s.get("group"):
            g = T["groups"][s["group"]]
            nums = [n for part in g["bySite"] for n in part] if g.get("bySite") else g["lines"]
            return "one line from the group *%s* (%s–%s%s)" % (s["group"], min(nums), max(nums), ", the site's own three" if g.get("bySite") else "")
        return "the site's own line (%s–%s)" % (min(s["bySite"]), max(s["bySite"]))
    ONCE = {"ever": "once ever", "site": "once at each site", "visit": "once per visit", "session": "once for each site per session (since the game was opened; a refresh or the restart starts a new one)"}
    def show(s):
        verb, rest = s.split(" ", 1)
        if verb == "drag": a, b = rest.split(" > "); return "drags %s to %s" % (word("points", a), word("points", b))
        return ("taps %s three times" if verb == "tap3" else "taps %s") % word("points", rest)
    def render(c, step=False):
        said.clear(); parts = []
        if not step:
            when = "When " + word("events", c["on"]) + ("" if c["on"] in ("step",) else " (`%s`)" % c["on"])
            if c.get("if"): when += " (only if " + "; ".join(word("conditions", k) for k in c["if"]) + ")"
            if c.get("once"): when += ", " + ONCE[c["once"]]
            parts.append(when + ":")
        if c.get("start"): parts.append("Begins once " + word("conditions", c["start"]) + ".")
        if c.get("do") == "demo": parts.append("Plays the site's demo (below).")
        if c.get("do") == "teaching": parts.append("Runs the site's teaching steps, from where the child left them.")
        if c.get("teaching"): parts.append("Teaching: silent when ΔΙΔΑΣΚΑΛΙΑ is unticked.")
        s = says(c.get("say"))
        if s:
            kind = {"teach": "teaching", "bg": "background, only if nothing else is playing or waiting"}.get(c.get("kind"), "queued")
            parts.append("says %s (%s%s%s)." % (s, kind, ", may play during a test" if c.get("during") == "test" else "", (", %s s after it fires" % c["delay"] if isinstance(c.get("delay"), (int, float)) else ", after the %s sound" % c["delay"][6:]) if c.get("delay") else ""))
        if c.get("points"): parts.append(("Glows for %s s: " % c["glow"] if c.get("glow") else "Points at ") + ", ".join(word("points", x) for x in c["points"]) + ".")
        if c.get("attention") == "point": parts.append("The rest of the screen darkens while it waits; only %s can be touched." % ", ".join(word("points", x) for x in c.get("touch", c.get("points", []))))
        if c.get("attention") == "freeze": parts.append("The screen darkens and the game freezes while it plays.")
        if c.get("wait"):
            w = c["wait"]; parts.append("Waits until " + (word("conditions", w[6:]) if w.startswith("until:") else word("events", w)) + "; its line comes again 5 s after it ends.")
        if c.get("show"): parts.append("The ghost hand " + show(c["show"]) + ".")
        if c.get("needs"): parts.append("Needs %s; without it, back to step `%s`." % (word("conditions", c["needs"]), c["back"]))
        if c.get("after") is not None: parts.append("When done, says " + q(c["after"]) + ".")
        if c.get("then"): word("events", c["then"]); parts.append("Then → `%s`." % c["then"])
        if c.get("note"): parts.append("*" + c["note"] + "*")
        parts = [x[0].upper() + x[1:] if i == 0 or parts[i - 1].endswith(".") else x for i, x in enumerate(parts)]
        return greek_after(" ".join(parts))
    used = {}
    def use(n, who): used.setdefault(str(n), []).append(who)
    out = ["# " + T["title"], "",
           "> Written from `%s` by `tools/cues_doc.py`. Do not edit this file: the owner comments, the table (`cues.json`) changes, this file is written again." % p.name, "",
           T["about"], "", "## How cues work", ""]
    out += ["- " + r for r in T["rules"]]
    seq_ids = {i for s in T["sequences"].values() for i in s["steps"]}
    topics = []
    for c in T["cues"]:
        if c["id"] not in seq_ids and c.get("topic") not in topics: topics.append(c.get("topic"))
    out += ["", "## Cues", "", "Each cue: when it fires, what it says, what it shows, what it waits for. Its name (in `code` style) is how to refer to it."]
    for t in topics:
        out += ["", "### " + (t or "Other"), ""]
        for c in T["cues"]:
            if c.get("topic") == t and c["id"] not in seq_ids: out.append("- `%s` — %s" % (c["id"], render(c)))
    for name, sq in T["sequences"].items():
        out += ["", "## Teaching steps: %s" % name, "", sq.get("note", ""), ""]
        for k, i in enumerate(sq["steps"], 1):
            c = next(x for x in T["cues"] if x["id"] == i)
            out.append("%d. `%s` — %s" % (k, i, render(c, True)))
        word("events", sq["then"]); out += ["", "When all steps are done → `%s`." % sq["then"]]
    out += ["", "## Demos", "", "On every visit to a site until it is finished, after its welcome line. " + " ".join("**%s**: %s." % (k, v) for k, v in W["demo-steps"].items()), "",
            "| Site | New | Demo |", "|---|---|---|"]
    keys = [s["key"] for s in T.get("sites", [])]
    for k, d in T["demos"].items():
        said.clear(); steps = []
        for op in d["steps"]:
            if op[0] in ("tell", "say"): steps.append(("tells " if op[0] == "tell" else "says, after: ") + q(op[1])); use(op[1], "demo " + k)
            elif op[0] == "put": steps.append("builds " + ", ".join(str(x) if isinstance(x, int) else "%s %s at (%s, %s)" % (x[1], x[0], x[2], x[3]) for x in op[1:]))
            elif op[0] == "wait": steps.append("waits %s s" % op[1])
            elif op[0] == "pull": steps.append("pulls the forms out")
            elif op[0] == "taps": steps.append("taps the %s three times" % op[1])
            elif op[0] == "fade": steps.append("fades")
        name = sites[keys.index(k)] if k in keys else k
        out.append("| %s | %s | %s |" % (name, d.get("new", ""), greek_after(("; ".join(steps) or "no demo") + (". *" + d["note"] + "*" if d.get("note") else ""))))
    for c in T["cues"]:
        s = c.get("say")
        if isinstance(s, int): use(s, c["id"])
        elif isinstance(s, dict) and s.get("bySite") and not s.get("group"):
            for i, n in enumerate(s["bySite"]): use(n, c["id"] + (" (" + sites[i] + ")" if i < len(sites) else ""))
        elif isinstance(s, dict) and s.get("group"):
            g = T["groups"][s["group"]]
            if g.get("bySite"):
                for i, part in enumerate(g["bySite"]):
                    for n in part: use(n, c["id"] + " (" + sites[i] + ")")
            else:
                for n in g["lines"]: use(n, c["id"] + ((" — only if " + word("conditions", g["lineIf"][str(n)])) if str(n) in g.get("lineIf", {}) else ""))
        if c.get("after") is not None: use(c["after"], c["id"] + " (when done)")
    out += ["", "## All lines", "", "Recordings: `sounds/voice/NN.mp3`, NN = the line number. Until one exists, its text shows in a box for 2 s.", ""]
    for n in sorted(set(L) | set(used), key=int):
        note = T.get("lineNotes", {}).get(n)
        out.append("%s. **%s%s**<br>%s" % (n, ", ".join(used.get(n, ["not used"])), (" " + note) if note else "", "«" + L[n] + "»" if n in L else "(recording only)"))
    out += ["", "## Words", ""]
    for kind in ("events", "conditions", "points", "fields"):
        out += ["### " + kind.capitalize(), ""] + ["- `%s`: %s" % (k, v["desc"] + " *(" + v["where"] + ")*" if isinstance(v, dict) else v) for k, v in W[kind].items()] + [""]
    out += ["## Notes", ""] + ["- " + n for n in T.get("notes", [])]
    if missing: sys.exit("the table uses words its 'words' section does not explain:\n  " + "\n  ".join(sorted(set(missing))))
    (p.parent / "cues.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("wrote", p.parent / "cues.md")

if __name__ == "__main__":
    main(sys.argv[1])
