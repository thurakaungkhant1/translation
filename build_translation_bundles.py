#!/usr/bin/env python3
# (Shortened copy) — See previous long version for full comments.
import argparse, csv, json, re, unicodedata
from pathlib import Path
FN_PATTERN = re.compile(r"\{\{fn:([a-zA-Z0-9_\-]+)\}\}")
def slugify(t): 
    nfkd = unicodedata.normalize('NFKD', str(t))
    t = ''.join(ch for ch in nfkd if not unicodedata.combining(ch))
    return re.sub(r'[^a-zA-Z0-9]+','-',t).strip('-').lower()
def strip_md(s):
    s = re.sub(r"\[(\d+)\]","",s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = s.lstrip(); s = s[2:] if s.startswith("~ ") else s
    return s.replace("*","").strip()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--link-all", action="store_true")
    ap.add_argument("--csv-delim", default=",")
    a = ap.parse_args()
    p = Path(a.input)
    if not Path(a.outdir).exists(): Path(a.outdir).mkdir(parents=True, exist_ok=True)
    docs = [json.loads(Path(p).read_text(encoding="utf-8"))] if p.is_file() else [json.loads(Path(j).read_text(encoding="utf-8")) for j in sorted(p.glob("*.json"))]
    for doc in docs:
        title = doc.get("title","Untitled")
        pali = doc.get("pali",[]); eng = doc.get("english",[])
        fnotes = doc.get("footnotes",{}); gloss = doc.get("glossary",{})
        base = slugify(title) or "output"
        md = Path(a.outdir)/f"{base}.md"
        csvp = Path(a.outdir)/f"{base}.csv"
        fnmd = Path(a.outdir)/f"{base}_footnotes.md"
        # Footnotes numbering
        fn_map = {}; n=0
        def apply_fn(s):
            nonlocal n
            def rep(m):
                nonlocal n
                fid = m.group(1)
                if fid not in fn_map: n+=1; fn_map[fid]=n
                return f"[{fn_map[fid]}]"
            return FN_PATTERN.sub(rep, s)
        # Glossary linking (first occurrence only)
        linked=set()
        def link_once(s):
            for term in sorted(gloss.keys(), key=len, reverse=True):
                if term in linked: continue
                pat = re.compile(rf"(?<!\[)\b({re.escape(term)})\b",re.I)
                m = pat.search(s)
                if m:
                    s = s[:m.start()] + f"[{m.group(0)}](#glossary-{slugify(term)})" + s[m.end():]
                    linked.add(term)
            return s
        out_lines = []
        for line in eng:
            raw = (line or "").lstrip()
            is_verse = raw.startswith("~ ")
            body = raw[2:] if is_verse else (line or "")
            if gloss: body = link_once(body)
            body = apply_fn(body)
            if is_verse: body = f"*{body.strip()}*"
            out_lines.append(body)
        parts = [f"# {title}\n"] + [ln for ln in out_lines if ln.strip()]+[""]
        if fn_map:
            parts.append("## Footnotes\n")
            inv = {v:k for k,v in fn_map.items()}
            for i in sorted(inv): parts.append(f"[{i}] {fnotes.get(inv[i], '(Missing note)')}")
            parts.append("")
        if gloss:
            parts.append("## Glossary\n")
            for term in sorted(gloss, key=slugify):
                parts.append(f'<a id="glossary-{slugify(term)}"></a>')
                parts.append(f"**{term}** — {gloss[term]}\n")
        md.write_text("\n".join(parts).strip()+"\n", encoding="utf-8")
        # CSV clean
        eng_clean = [strip_md(s) for s in out_lines]
        import csv as _csv
        with csvp.open("w", encoding="utf-8", newline="") as f:
            w=_csv.writer(f, delimiter=a.csv_delim); w.writerow(["line_number","pali","english"])
            for i in range(max(len(pali),len(eng_clean))):
                w.writerow([i+1, pali[i] if i < len(pali) else "", eng_clean[i] if i < len(eng_clean) else ""])
        if fn_map:
            inv = {v:k for k,v in fn_map.items()}
            fn_parts=[f"# Footnotes for “{title}”\n"]+[f"[{i}] {fnotes.get(inv[i],'(Missing note)')}" for i in sorted(inv)]+[""]
            fnmd.write_text("\n".join(fn_parts), encoding="utf-8")
        print("✓ Wrote", md, csvp, ("and " + str(fnmd) if fn_map else ""))
if __name__=="__main__":
    main()
