# Mechanism generation

The mechanism generator defaults to `paper-only-mech-v2`. It inventories mechanisms and assumptions, then generates conditional limitations. Candidate quotes are verified, evaluation critiques are separated, and candidates are merged by quote anchor or normalized mechanism overlap. Run evidence records dropped and merged counts and preserves reasoning fields.

Select `--mechanism-version paper-only-mech-v1` for the single-call version. Optional caller-supplied examples can be passed with `--mechanism-examples PATH`; no examples are included by default. Use a fresh output directory when changing versions or examples.

Prompt design used only public category definitions in README, the structure (not content) of the four validation labels, and the dimensions of evaluation/RUBRIC_zh.md.
