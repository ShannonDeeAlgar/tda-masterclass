"""Create student notebook and data downloads."""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "downloads"
DOWNLOADS.mkdir(exist_ok=True)

for topic in range(1, 7):
    source = ROOT / f"topics/topic-{topic:02d}"
    shutil.copyfile(
        source / "lab.ipynb",
        DOWNLOADS / f"topic-{topic:02d}-participant.ipynb",
    )

shutil.copyfile(
    ROOT / "pause-and-take-stock/lab.ipynb",
    DOWNLOADS / "pause-and-take-stock-practical.ipynb",
)

shutil.copyfile(ROOT / "data/datasaurus_dozen.csv",
                DOWNLOADS / "datasaurus_dozen.csv")

print(
    "Synchronised six participant notebooks, the take-stock practical and "
    "the Datasaurus CSV in "
    f"{DOWNLOADS.relative_to(ROOT)}/"
)
