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

for n in range(1, 7):
    d = ROOT / f'topics/topic-{n:02d}'
    for name in ['index.qmd', 'lab.ipynb']:
        p = d / name
        if not p.exists():
            errors.append(f'Missing {p.relative_to(ROOT)}')
    for name in ['lab.ipynb']:
        p = d / name
        if p.exists():
            try:
                json.loads(p.read_text())
            except Exception as exc:
                errors.append(f'Invalid notebook JSON {p.relative_to(ROOT)}: {exc}')
    index_text = (d / 'index.qmd').read_text()
    expected_href = f'href="../../downloads/topic-{n:02d}-participant.ipynb"'
    if expected_href not in index_text:
        errors.append(
            f'Missing participant notebook download link in topics/topic-{n:02d}/index.qmd: '
            f'{expected_href}'
        )
    for role in ['participant']:
        download = ROOT / f'downloads/topic-{n:02d}-{role}.ipynb'
        if not download.exists():
            errors.append(f'Missing {download.relative_to(ROOT)}; run scripts/sync_notebook_downloads.py')
        else:
            try:
                json.loads(download.read_text())
            except Exception as exc:
                errors.append(f'Invalid notebook JSON {download.relative_to(ROOT)}: {exc}')
            source = d / 'lab.ipynb'
            if source.exists() and download.read_bytes() != source.read_bytes():
                errors.append(
                    f'Stale {download.relative_to(ROOT)}; run scripts/sync_notebook_downloads.py'
                )

algebra_guide = ROOT / 'topics/topic-02/algebra-survival-guide.qmd'
if not algebra_guide.exists():
    errors.append('Missing topics/topic-02/algebra-survival-guide.qmd')

topology_guide = ROOT / 'topics/topic-01/topology-survival-guide.qmd'
if not topology_guide.exists():
    errors.append('Missing topics/topic-01/topology-survival-guide.qmd')

pause_lab = ROOT / 'pause-and-take-stock/lab.ipynb'
pause_download = ROOT / 'downloads/pause-and-take-stock-practical.ipynb'
if not pause_lab.exists():
    errors.append('Missing pause-and-take-stock/lab.ipynb')
elif not pause_download.exists():
    errors.append('Missing downloads/pause-and-take-stock-practical.ipynb')
elif pause_lab.read_bytes() != pause_download.read_bytes():
    errors.append(
        'Stale downloads/pause-and-take-stock-practical.ipynb; '
        'run scripts/sync_notebook_downloads.py'
    )

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
