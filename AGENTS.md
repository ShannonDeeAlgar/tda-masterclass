# Instructions for Codex

## Project purpose

Build a six-topic MasterClass, with a modelling pause after the foundations,
on topological data analysis for dynamical systems researchers, incoming
Honours students and selected industry audiences. The course must develop
mathematical judgement rather than present TDA as a black-box feature
generator.

## Voice and presentation

- Use British spelling.
- Be direct, precise and conversational rather than promotional.
- Avoid em dashes.
- Avoid inflated claims that topology is automatically superior.
- Preserve the distinction between the observed scientific object and every constructed mathematical representation.
- Keep explanations brief in the reader and use margin notes only when they
  materially aid interpretation.

## Required structure for each topic

Each topic directory contains durable reader material and one participant
notebook. The reader develops the argument; the notebook applies it through
observe, predict, implement, compare and interpret. Do not create parallel
slides, lecture walkthroughs or application pages unless the project is later
given a distinct teaching-delivery brief.

## Teaching pattern for notebooks

Use:

1. Observe
2. Predict
3. Implement
4. Compare
5. Interpret

Whenever possible, keep the data fixed and change one modelling decision at a time. Ask participants to predict before revealing output.

## Recurring visual markers

- `▶ Likely sticking point`: a subtle conceptual transition.
- `† Qualification`: a condition or distinction that must remain visible.
Use the CSS classes `.sticking-point` and `.qualification` in web notes.

## Figure titles

- Use sentence case for titles inside multi-panel figures.
- Centre each title over its own panel.
- Use the reader typeface (`system-ui, sans-serif`), semibold weight and the
  dark teal text colour used elsewhere in the course.
- Keep titles to one short line. Put interpretation in the caption or margin,
  not in a second competing title.
- Use a smaller muted line only when a panel needs a factual subtitle.

## Mathematical standards

- State coefficient fields when treating homology as a vector space.
- Distinguish a simplicial complex from its 1-skeleton.
- Distinguish inclusion of complexes from the induced linear map on homology.
- Distinguish a persistence module from its interval decomposition and barcode.
- State the hypotheses behind interval decomposition or stability claims.
- For dynamic data, distinguish repeated static persistence, feature tracking, vineyards, vineyard modules, zigzag and multiparameter persistence.

## Application standards

Every real-data example must include:

- the operational or scientific question;
- the observed data and preprocessing;
- the complex and filtration;
- a simpler baseline;
- sensitivity to at least one modelling choice;
- the interpretation boundary and likely failure modes.

Do not invent empirical results or industry claims. Mark synthetic examples clearly.

## Repository workflow

- Keep notebooks deterministic by setting random seeds.
- Avoid very large datasets in the repository.
- Run `python scripts/check_project.py` before completing a task.
- Render the changed Quarto page or deck when Quarto is available.
- Update `TASKS.md` only when a task is genuinely complete.
