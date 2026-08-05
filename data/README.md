# Course data

## Datasaurus Dozen

`datasaurus_dozen.csv` contains the canonical long-form Datasaurus Dozen:

- 1,846 observations;
- 13 named datasets;
- 142 `(x, y)` points per dataset; and
- columns `dataset`, `x` and `y`.

The data were created by Justin Matejka and George Fitzmaurice, inspired by Alberto Cairo's original Datasaurus. They are distributed here from the MIT-licensed `datasauRus` package data, using the CSV published by OpenIntro.

Sources:

- <https://jumpingrivers.github.io/datasauRus/>
- <https://www.openintro.org/data/index.php?data=datasaurus>
- Matejka, J. and Fitzmaurice, G. (2017), *Same Stats, Different Graphs*, DOI: 10.1145/3025453.3025912.

Suggested citations are stored in the course `references.bib` as `matejka2017samestats` and `gillespie2025datasaurus`.

The package licence is reproduced in `DATASAURUS-LICENSE.md`.

## Grid-cell torus teaching subset

The static real-data spine uses the public data associated with:

- Gardner, R. J. and collaborators (2022), *Toroidal topology of population
  activity in grid cells*, DOI: 10.1038/s41586-021-04268-7; and
- Gardner, R. and Hermansen, E. (2022), Figshare dataset version 6,
  DOI: 10.6084/m9.figshare.16764508.v6.

The source archive is approximately 320 MB and is released under CC0. It is
not copied wholesale into this repository. The authors' analysis code is
available at <https://github.com/erikher/GridCellTorus>.

`grid_cell_torus_r_day1_module2_teaching.npz` is a 384 KB teaching subset
from rat R, day 1, open-field module 2. It contains 1,200 selected population
states from 168 recorded cells, their six-dimensional PCA coordinates,
recording times, animal positions and speeds, source cell identifiers and
machine-readable provenance.

It also contains one separate 20-second passage of 400 consecutive 50 ms
population states. Unlike the 1,200 states selected to cover the static cloud,
these observations retain temporal order. They support the bridge from the
static question “what space is occupied?” to the dynamic question “how does
the population state move through that space?”

The deterministic regeneration script is
`scripts/make_grid_cell_teaching_subset.py`. It bins spikes at 50 ms, smooths
with a 50 ms Gaussian width, retains movement faster than 2.5 cm/s, selects
15,000 high-activity candidate bins, standardises the cell coordinates,
reduces them to six principal components and chooses 1,200 spread-out states
using cosine distance. The contiguous passage is chosen for sustained movement
and activity, then projected using the same standardisation and PCA transform.

This transparent reduction resembles the broad stages of the published
workflow but is not an exact reproduction. In particular, it retains all 168
recorded module-2 cells and uses a simple farthest-point teaching sampler
rather than the authors' cell classification and density-aware denoising.
The published torus result therefore belongs to the full analysis, not to
this reduced file alone.

Suggested citations are stored in `references.bib` as
`gardner2022torus` and `gardner2022torusdata`.

## Golden-shiner transition teaching subset

The empirical dynamic-data spine uses the public [*Fish Schooling Data
Subset*](https://doi.org/10.7267/zk51vq07c). The source contains 5,000 frames of detected
positions, velocities and temporary track identifiers from a school of 300
golden shiners swimming in a shallow tank. The original observations and
tracking procedure are described by [Katz and
collaborators](https://doi.org/10.1073/pnas.1107583108). The same experiment supports the established
polarisation-and-rotation description of swarm, polarised and milling states
reported by [Tunstrøm and
collaborators](https://doi.org/10.1371/journal.pcbi.1002915).

The 83 MB source JSON is released under CC BY 4.0 and is not copied wholesale
into this repository. The course retains two smaller files:

- `golden_shiner_transition_observations.csv` contains positions, velocities
  and source track identifiers for every fifth frame from source frames
  2701–3500; and
- `golden_shiner_transition_frames.csv` records the number detected,
  polarisation, collective rotation and the state label obtained from the
  published threshold rule.

Together these files cover 160 observations over 26.5 seconds, moving from a
disordered regime through a transition and into sustained milling. The
observation count varies because automated tracking does not recover all 300
fish in every frame. Track identifiers are also retired and replaced when an
individual is lost and later detected again. Those limitations are part of
the teaching example rather than details to hide.

The deterministic regeneration script is
`scripts/make_golden_shiner_teaching_subset.py`. It downloads the source from
Oregon State University, checks its SHA-256 digest and performs only temporal
subsampling. Coordinates remain in the source camera-pixel system. The course
therefore distinguishes raw camera geometry from any later centring,
normalisation, distance or filtration chosen for analysis.

The empirical question is whether framewise topological summaries register the
emergence of spatial organisation in a way that adds information to the
published polarisation and rotation baselines. This is a new course analysis,
not a result claimed by the source papers. A related study used the same
schooling data to classify collective behaviour through manifold learning
([Titus, Hagstrom and
Watson](https://doi.org/10.1371/journal.pcbi.1007811)), providing a useful
non-topological comparison.
