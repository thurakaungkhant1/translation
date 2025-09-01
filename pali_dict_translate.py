#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pali_dict_translate.py  — OFFLINE dictionary-based Pali→English draft translator
Usage:
  python pali_dict_translate.py --pali pali.txt --dict pali_dictionary.json --title "My Title"
Options:
  --outdir outputs_draft
  --keep-unknown        # keep unknown tokens in draft as <word>
  --lower               # lowercase the glosses
  --csv-delim ";"       # change CSV delimiter
Outputs:
  english_draft.txt
  pali_english_gloss.csv
  my_input.json         # can be fed to build_translation_bundles.py
  unknown_words.txt
  glossary_auto.json
"""
import argparse, csv, json, re, unicodedata
from pathlib import Path
from collections import Counter, defaultdict

EDGE_PUNCT = ".,;:!?—–-()[]{}\"'“”‘’…·|/\\«»‹›"
NAIVE_SUFFIXES = ["ssa","nnaṃ","naṃ","hi","su","ṃ","o","aṃ","ā","a","i","e","u","yo","ya","ena","āya","ato","amhākaṃ","ttha","nti"]

def normalize(s: str) -> str:
    return s.lower()

def strip_edge_punct(token: str):
    return token.strip(EDGE_PUNCT)

def naive_lemmatize(token: str):
    cands = [token]
    for suf in sorted(NAIVE_SUFFIXES, key=len, reverse=True):
        if token.endswith(suf) and len(token) > len(suf) + 1:
            cands.append(token[:-len(suf)])
    return cands

def build_index(dict_map):
    def strip_diacritics(t):
        nfkd = unicodedata.normalize('NFKD', t)
        return ''.join(ch for ch in nfkd if not unicodedata.combining(ch))
    idx = defaultdict(list)
    for k, v in dict_map.items():
        k_norm = k.lower()
        idx[k_norm].append((k, v))
        idx[strip_diacritics(k_norm)].append((k, v))
    return idx

def lookup_gloss(token, idx):
    tnorm = normalize(token)
    if tnorm in idx:
        return idx[tnorm][0]
    for cand in naive_lemmatize(tnorm)[1:]:
        if cand in idx:
            return idx[cand][0]
    nfkd = unicodedata.normalize('NFKD', tnorm)
    nodiac = ''.join(ch for ch in nfkd if not unicodedata.combining(ch))
    if nodiac in idx:
        return idx[nodiac][0]
    for cand in naive_lemmatize(nodiac)[1:]:
        if cand in idx:
            return idx[cand][0]
    return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pali", required=True)
    ap.add_argument("--dict", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--outdir", default="outputs_draft")
    ap.add_argument("--keep-unknown", action="store_true")
    ap.add_argument("--lower", action="store_true")
    ap.add_argument("--csv-delim", default=",")
    args = ap.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    pali_lines = [ln.rstrip("\n") for ln in Path(args.pali).read_text(encoding="utf-8").splitlines()]
    dict_map = json.loads(Path(args.dict).read_text(encoding="utf-8"))
    idx = build_index(dict_map)

    english_lines = []
    unknown = set()
    freq = Counter()
    capture = {}

    for line in pali_lines:
        tokens = re.findall(r"\S+|\s+", line)
        out = []
        for tok in tokens:
            if tok.isspace():
                out.append(tok); continue
            core = strip_edge_punct(tok)
            prefix = tok[: len(tok) - len(tok.lstrip(EDGE_PUNCT))]
            suffix = tok[len(tok.rstrip(EDGE_PUNCT)) :]
            k, g = lookup_gloss(core, idx)
            if g is None:
                out.append(prefix + (f"<{core}>" if args.keep_unknown else core) + suffix)
                unknown.add(core)
            else:
                out.append(prefix + (g.lower() if args.lower else g) + suffix)
                freq[k] += 1; capture[k] = g
        draft = "".join(out).strip()
        if draft:
            draft = draft[0].upper() + draft[1:]
        english_lines.append(draft)

    (outdir / "english_draft.txt").write_text("\n".join(english_lines) + "\n", encoding="utf-8")
    with (outdir / "pali_english_gloss.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=args.csv_delim)
        w.writerow(["line_number","pali","english_draft"])
        for i, (p, e) in enumerate(zip(pali_lines, english_lines), start=1):
            w.writerow([i, p, e])
    bundle = {"title": args.title, "pali": pali_lines, "english": english_lines, "footnotes": {}, "glossary": {}}
    (outdir / "my_input.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir / "unknown_words.txt").write_text("\n".join(sorted(unknown)) + ("\n" if unknown else ""), encoding="utf-8")
    ordered = {k: capture[k] for k, _ in freq.most_common()}
    (outdir / "glossary_auto.json").write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")

    print("✓ Done. Files written to", outdir)

if __name__ == "__main__":
    main()
