# TDA for Static and Dynamic Data

A Quarto-based MasterClass combining:

- RevealJS teaching slides
- Fuller web notes
- Jupyter practical notebooks and worked versions
- Stand-alone application case studies
- A retained LaTeX planning source

## Run locally

1. Install [Quarto](https://quarto.org/).
2. Create the Python environment:

   ```bash
   conda env create -f environment.yml
   conda activate tda-masterclass
   ```

3. Preview the site:

   ```bash
   quarto preview
   ```

4. Render everything:

   ```bash
   quarto render
   ```

## Development principle

Slides carry the live conceptual argument. Notebooks are where participants manipulate design choices. Notes preserve the qualifications and explanations that should remain available after class.

See `AGENTS.md` before using Codex and `TASKS.md` for bounded development tasks.
