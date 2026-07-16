from pathlib import Path
import json
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors = []

required_root = ['_quarto.yml', 'index.qmd', 'README.md', 'AGENTS.md', 'TASKS.md',
                 'environment.yml', 'run-practicals.qmd']
for rel in required_root:
    if not (ROOT / rel).exists():
        errors.append(f'Missing {rel}')

try:
    yaml.safe_load((ROOT / '_quarto.yml').read_text())
except Exception as exc:
    errors.append(f'Invalid _quarto.yml: {exc}')

for n in range(1, 9):
    d = ROOT / f'weeks/week-{n:02d}'
    for name in ['index.qmd', 'slides.qmd', 'lab.ipynb', 'solutions.ipynb', 'case-study.qmd']:
        p = d / name
        if not p.exists():
            errors.append(f'Missing {p.relative_to(ROOT)}')
    for name in ['lab.ipynb', 'solutions.ipynb']:
        p = d / name
        if p.exists():
            try:
                json.loads(p.read_text())
            except Exception as exc:
                errors.append(f'Invalid notebook JSON {p.relative_to(ROOT)}: {exc}')
    index_text = (d / 'index.qmd').read_text()
    expected_href = f'href="../../downloads/week-{n:02d}-participant.ipynb"'
    if expected_href not in index_text:
        errors.append(
            f'Missing participant notebook download link in weeks/week-{n:02d}/index.qmd: '
            f'{expected_href}'
        )
    for role in ['participant', 'lecture-walkthrough']:
        download = ROOT / f'downloads/week-{n:02d}-{role}.ipynb'
        if not download.exists():
            errors.append(f'Missing {download.relative_to(ROOT)}; run scripts/sync_notebook_downloads.py')
        else:
            try:
                json.loads(download.read_text())
            except Exception as exc:
                errors.append(f'Invalid notebook JSON {download.relative_to(ROOT)}: {exc}')
            source_name = 'lab.ipynb' if role == 'participant' else 'solutions.ipynb'
            source = d / source_name
            if source.exists() and download.read_bytes() != source.read_bytes():
                errors.append(
                    f'Stale {download.relative_to(ROOT)}; run scripts/sync_notebook_downloads.py'
                )

algebra_guide = ROOT / 'weeks/week-02/algebra-survival-guide.qmd'
if not algebra_guide.exists():
    errors.append('Missing weeks/week-02/algebra-survival-guide.qmd')

topology_guide = ROOT / 'weeks/week-01/topology-survival-guide.qmd'
if not topology_guide.exists():
    errors.append('Missing weeks/week-01/topology-survival-guide.qmd')

datasaurus_source = ROOT / 'data/datasaurus_dozen.csv'
datasaurus_download = ROOT / 'downloads/datasaurus_dozen.csv'
if not datasaurus_source.exists():
    errors.append('Missing data/datasaurus_dozen.csv')
elif not datasaurus_download.exists():
    errors.append('Missing downloads/datasaurus_dozen.csv; run scripts/sync_notebook_downloads.py')
elif datasaurus_source.read_bytes() != datasaurus_download.read_bytes():
    errors.append('Stale downloads/datasaurus_dozen.csv; run scripts/sync_notebook_downloads.py')

if errors:
    print('\n'.join(f'ERROR: {e}' for e in errors))
    sys.exit(1)
print('Project structure and notebook JSON validated.')
