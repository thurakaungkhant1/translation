#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pairs_to_json.py
Make a JSON input for build_translation_bundles.py from two plaintext files:
 - One Pali file (one line per segment)
 - One English file (one line per segment); may include {{fn:ID}} markers
Optional footnotes and glossary JSON can be merged.
Usage:
  python pairs_to_json.py --pali pali.txt --english english.txt --title "My Title" --out out.json \
      --footnotes footnotes.json --glossary glossary.json
"""
import argparse, json, sys, pathlib

def read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pali", required=True)
    p.add_argument("--english", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--footnotes")
    p.add_argument("--glossary")
    args = p.parse_args()

    pali_lines = read_lines(args.pali)
    english_lines = read_lines(args.english)

    if len(english_lines) < len(pali_lines):
        sys.stderr.write(f"WARNING: english lines ({len(english_lines)}) < pali lines ({len(pali_lines)}). Missing lines will be empty.\n")

    footnotes = {}
    glossary = {}
    if args.footnotes:
        with open(args.footnotes, "r", encoding="utf-8") as f:
            footnotes = json.load(f)
    if args.glossary:
        with open(args.glossary, "r", encoding="utf-8") as f:
            glossary = json.load(f)

    doc = {
        "title": args.title,
        "pali": pali_lines,
        "english": english_lines,
        "footnotes": footnotes,
        "glossary": glossary
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"✓ Wrote {args.out}")

if __name__ == "__main__":
    main()
