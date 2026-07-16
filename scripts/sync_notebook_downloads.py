"""Create student downloads and optional instructor-release copies."""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "downloads"
DOWNLOADS.mkdir(exist_ok=True)

for week in range(1, 9):
    source = ROOT / f"weeks/week-{week:02d}"
    pairs = {
        source / "lab.ipynb": DOWNLOADS / f"week-{week:02d}-participant.ipynb",
        source / "solutions.ipynb": DOWNLOADS / f"week-{week:02d}-lecture-walkthrough.ipynb",
    }
    for original, downloadable in pairs.items():
        shutil.copyfile(original, downloadable)

shutil.copyfile(ROOT / "data/datasaurus_dozen.csv",
                DOWNLOADS / "datasaurus_dozen.csv")

print(
    "Synchronised eight participant notebooks, eight optional instructor-release "
    f"walkthroughs and the Datasaurus CSV in {DOWNLOADS.relative_to(ROOT)}/"
)
