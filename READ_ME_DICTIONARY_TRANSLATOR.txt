
RUN (Windows CMD / PowerShell):
1) Put your Pali lines into pali.txt (one segment per line).
2) Edit/expand pali_dictionary.json with more entries.
3) Run:
   python pali_dict_translate.py --pali pali.txt --dict pali_dictionary.json --title "My Draft" --keep-unknown
4) Outputs in /outputs_draft:
   - english_draft.txt
   - pali_english_gloss.csv
   - my_input.json
   - unknown_words.txt (grow your dictionary from this)
   - glossary_auto.json
5) (Optional) To build final Markdown/CSV/Footnotes:
   python build_translation_bundles.py --input outputs_draft/my_input.json --outdir outputs
