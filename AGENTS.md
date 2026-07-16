# Instructions for Codex

## Project purpose

Build an eight-week MasterClass on topological data analysis for dynamical-systems researchers, incoming Honours students and selected industry audiences. The course must develop mathematical judgement rather than present TDA as a black-box feature generator.

## Voice and presentation

- Use British spelling.
- Be direct, precise and conversational rather than promotional.
- Avoid em dashes.
- Avoid inflated claims that topology is automatically superior.
- Preserve the distinction between the observed scientific object and every constructed mathematical representation.
- Keep slides visually sparse. Put fuller explanations in notes and notebooks.

## Required structure for each week

Each `weeks/week-XX/` directory contains:

- `index.qmd`: durable reference notes
- `slides.qmd`: the live conceptual argument
- `lab.ipynb`: participant notebook
- `solutions.ipynb`: worked notebook
- `case-study.qmd`: an application route

Do not duplicate all prose across these files. Slides orient; notes explain; notebooks expose consequences through computation.

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
- `◇ Object check`: explicitly name the current spaces, vector spaces, maps, modules or summaries.

Use the CSS classes `.sticking-point`, `.qualification` and `.object-check` in web notes. Use `.sticking`, `.qualification` and `.object-check` in slides.

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
