"""Generate a sampled mug-to-torus surface deformation and persistence diagrams.

One parameter domain (u,v) is used throughout. At the mug end, a thick
cross-section along one side of a D-shaped centreline forms the cup body while
the remaining narrow tube forms the handle. During the deformation the body
pinches down, the handle thickens and the centreline rounds into a circle.
Fixed low-discrepancy parameter samples are carried by this map.

No TDA package is used. For every frame, the script constructs the Rips
simplices needed through H2 and performs filtered boundary reduction over F2.
"""

from __future__ import annotations

from itertools import combinations
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SAMPLE_DENSITIES = (18, 28, 38)
DEFAULT_DENSITY = 28
N_FRAMES = 21
MESH_U = 34
MESH_V = 11


def centreline(q: np.ndarray, t: float) -> np.ndarray:
    """Planar centreline: D-shaped mug at t=0, circular torus at t=1."""
    q = np.asarray(q)
    theta = 2 * np.pi * q
    circle = np.column_stack((0.25 + 1.85 * np.cos(theta), 1.85 * np.sin(theta)))
    mug = np.empty_like(circle)
    straight = q < 0.40
    a = q[straight] / 0.40
    mug[straight] = np.column_stack(
        (np.zeros_like(a), 1.85 - 3.70 * a)
    )
    b = (q[~straight] - 0.40) / 0.60
    angle = -np.pi / 2 + np.pi * b
    mug[~straight] = np.column_stack(
        (2.25 * np.cos(angle), 1.85 * np.sin(angle))
    )
    return (1 - t) * mug + t * circle


def surface(q: np.ndarray, v: np.ndarray, t: float) -> np.ndarray:
    """Map persistent parameter labels (q,v) to the deforming genus-one surface."""
    q = np.asarray(q)
    v = np.asarray(v)
    core = centreline(q, t)
    h = 1e-4
    tangent = centreline((q + h) % 1, t) - centreline((q - h) % 1, t)
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    normal = np.column_stack((-tangent[:, 1], tangent[:, 0]))

    # On the mug, the left side of the parameter loop carries most material:
    # this is the cup body. Its cross-section shrinks while the handle grows.
    body_profile = np.zeros_like(q)
    mask = q < 0.40
    body_profile[mask] = np.sin(np.pi * q[mask] / 0.40) ** 0.06
    radial_mug = 0.26 + 0.92 * body_profile
    vertical_mug = 0.28 + 1.02 * body_profile
    radial = (1 - t) * radial_mug + t * 0.56
    vertical = (1 - t) * vertical_mug + t * 0.56

    planar_offset = radial * np.cos(v)
    return np.column_stack(
        (
            core[:, 0] + planar_offset * normal[:, 0],
            vertical * np.sin(v),
            core[:, 1] + planar_offset * normal[:, 1],
        )
    )


def observation_parameters(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Choose fixed labels that remain reasonably spread through the morph."""
    nq, nv = 80, 24
    q = np.repeat((np.arange(nq) + 0.5) / nq, nv)
    v = np.tile(2 * np.pi * (np.arange(nv) + 0.5) / nv, nq)
    reference = []
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        points = surface(q, v, t)
        points = points - points.mean(axis=0)
        points /= np.sqrt(np.mean(np.sum(points**2, axis=1)))
        reference.append(points)

    selected = [0]
    nearest = np.full(len(q), np.inf)
    while len(selected) < n:
        latest = selected[-1]
        distance = np.mean(
            [np.linalg.norm(points - points[latest], axis=1) for points in reference],
            axis=0,
        )
        nearest = np.minimum(nearest, distance)
        nearest[selected] = -1
        selected.append(int(np.argmax(nearest)))
    return q[selected], v[selected]


def mesh_at(t: float) -> np.ndarray:
    u = np.linspace(0, 1, MESH_U, endpoint=False)
    v = np.linspace(0, 2 * np.pi, MESH_V, endpoint=False)
    uu, vv = np.meshgrid(u, v, indexing="ij")
    return surface(uu.ravel(), vv.ravel(), t).reshape(MESH_U, MESH_V, 3)


def rips_intervals(
    points: np.ndarray,
) -> tuple[dict[int, list[tuple[float, float]]], list[dict]]:
    """Return intervals and birth-cycle representatives over F2."""
    n = len(points)
    distances = np.linalg.norm(points[:, None] - points[None, :, :], axis=2)
    simplices: list[tuple[float, int, tuple[int, ...]]] = []
    simplices.extend((0.0, 0, (i,)) for i in range(n))
    for dimension in range(1, 4):
        for vertices in combinations(range(n), dimension + 1):
            value = max(
                distances[i, j] for i, j in combinations(vertices, 2)
            )
            simplices.append((float(value), dimension, vertices))
    simplices.sort(key=lambda x: (round(x[0], 12), x[1], x[2]))
    index = {vertices: i for i, (_, _, vertices) in enumerate(simplices)}
    reduced: list[set[int]] = []
    changes: list[set[int] | None] = []
    pivot_to_column: dict[int, int] = {}
    pairs: list[tuple[int, int]] = []
    birth_cycles: dict[int, list[tuple[int, int]]] = {}
    for column_index, (_, dimension, vertices) in enumerate(simplices):
        if dimension == 0:
            column: set[int] = set()
        else:
            column = {
                index[vertices[:i] + vertices[i + 1 :]]
                for i in range(len(vertices))
            }
        change = {column_index} if dimension <= 1 else None
        while column and max(column) in pivot_to_column:
            reducer = pivot_to_column[max(column)]
            column ^= reduced[reducer]
            if change is not None and changes[reducer] is not None:
                change ^= changes[reducer]
        reduced.append(column)
        changes.append(change)
        if column:
            pivot_to_column[max(column)] = column_index
            pairs.append((max(column), column_index))
        elif dimension == 1 and change is not None:
            birth_cycles[column_index] = [
                simplices[i][2]
                for i in sorted(change)
                if simplices[i][1] == 1
            ]
    intervals: dict[int, list[tuple[float, float]]] = {0: [], 1: [], 2: []}
    cycle_records: list[dict] = []
    for birth_index, death_index in pairs:
        birth, dimension, _ = simplices[birth_index]
        death, _, _ = simplices[death_index]
        if dimension <= 2 and death > birth + 1e-9:
            intervals[dimension].append((birth, death))
            if dimension == 1 and birth_index in birth_cycles:
                cycle_records.append(
                    {
                        "birth": round(float(birth), 5),
                        "death": round(float(death), 5),
                        "edges": [list(edge) for edge in birth_cycles[birth_index]],
                    }
                )
    for dimension in intervals:
        intervals[dimension].sort(key=lambda x: x[1] - x[0], reverse=True)
    cycle_records.sort(key=lambda z: z["death"] - z["birth"], reverse=True)
    return intervals, cycle_records


def reference_cycles(t: float) -> dict[str, list[list[float]]]:
    """Two geometric generator loops on the continuous genus-one surface."""
    q = np.linspace(0, 1, 97, endpoint=True)
    longitude = surface(q % 1, np.zeros_like(q), t)
    v = np.linspace(0, 2 * np.pi, 65, endpoint=True)
    meridian = surface(np.full_like(v, 0.67), v, t)
    return {
        "longitude": np.round(longitude, 4).tolist(),
        "meridian": np.round(meridian, 4).tolist(),
    }


def compute_frames() -> list[dict]:
    parameters = {n: observation_parameters(n) for n in SAMPLE_DENSITIES}
    frames = []
    for t in np.linspace(0, 1, N_FRAMES):
        samples = {}
        for n, (q, v) in parameters.items():
            points = surface(q, v, float(t))
            intervals, cycles = rips_intervals(points)
            samples[str(n)] = {
                "points": np.round(points, 5).tolist(),
                "intervals": {
                    str(p): np.round(values, 5).tolist()
                    for p, values in intervals.items()
                },
                "birth_cycles": cycles,
            }
        frames.append(
            {
                "t": round(float(t), 5),
                "mesh": np.round(mesh_at(float(t)), 4).tolist(),
                "cycles": reference_cycles(float(t)),
                "samples": samples,
            }
        )
    return frames


def write_gif(frames: list[dict]) -> None:
    fig = plt.figure(figsize=(11.2, 5.0), dpi=105)
    ax_surface = fig.add_subplot(121, projection="3d")
    ax_pd = fig.add_subplot(122)
    max_d = max(
        d for f in frames
        for sample in f["samples"].values()
        for _, d in sample["intervals"]["1"]
    ) * 1.10

    def draw(k: int) -> None:
        f = frames[k]
        sample = f["samples"][str(DEFAULT_DENSITY)]
        points = np.asarray(sample["points"])
        mesh = np.asarray(f["mesh"])
        intervals = np.asarray(sample["intervals"]["1"])
        ax_surface.clear()
        wrapped = np.concatenate((mesh, mesh[:, :1, :]), axis=1)
        wrapped = np.concatenate((wrapped, wrapped[:1, :, :]), axis=0)
        ax_surface.plot_surface(
            wrapped[:, :, 0], wrapped[:, :, 1], wrapped[:, :, 2],
            color="#9fb8cc", edgecolor="#688ba4", linewidth=0.25,
            alpha=0.34, rstride=1, cstride=1,
        )
        ax_surface.scatter(
            points[:, 0], points[:, 1], points[:, 2],
            s=24, c="#fff", edgecolors="#245a7a", linewidths=1.3,
            depthshade=False,
        )
        rim = np.concatenate((mesh[2], mesh[2, :1]), axis=0)
        ax_surface.plot(
            rim[:, 0], rim[:, 1], rim[:, 2],
            color="#315f7d", linewidth=1.8, alpha=0.9,
        )
        label = "mug" if k == 0 else "torus" if k == len(frames) - 1 else "continuous deformation"
        ax_surface.set_title(f"One labelled surface mesh: {label}")
        ax_surface.text2D(
            0.02, 0.02,
            "The cup body pinches down while the handle grows and thickens.",
            transform=ax_surface.transAxes, fontsize=8.5, color="#52697b",
        )
        ax_surface.set(xlim=(-2.8, 2.8), ylim=(-1.8, 1.8), zlim=(-2.6, 2.6))
        ax_surface.set_box_aspect((1.2, 0.75, 1.1))
        ax_surface.view_init(elev=23, azim=-58)
        ax_surface.set_axis_off()

        ax_pd.clear()
        ax_pd.plot([0, max_d], [0, max_d], "--", color="#94a3b8", lw=1.1)
        persistence = intervals[:, 1] - intervals[:, 0]
        main = int(np.argmax(persistence))
        ax_pd.scatter(
            intervals[:, 0], intervals[:, 1], s=34, c="#b8c4cf",
            edgecolors="#617386", linewidths=0.6,
        )
        ax_pd.scatter(
            [intervals[main, 0]], [intervals[main, 1]],
            s=88, c="#93436f", zorder=3,
        )
        b, d = intervals[main]
        ax_pd.text(
            0.04, 0.94,
            f"{len(intervals)} finite H₁ intervals\n"
            f"longest this frame: [{b:.3f}, {d:.3f})",
            transform=ax_pd.transAxes, va="top", fontsize=9.5, color="#334155",
        )
        ax_pd.set(
            xlim=(0, max_d), ylim=(0, max_d), xlabel="birth ε",
            ylabel="death ε", title="Computed Vietoris–Rips H₁ diagram",
        )

    animation = FuncAnimation(fig, draw, frames=len(frames), interval=150)
    fig.suptitle(
        "The object is deformed; the same non-uniform sample labels move with it",
        fontsize=13.5, fontweight="bold",
    )
    fig.tight_layout()
    animation.save(
        ASSETS / "mug-torus-persistence.gif",
        writer=PillowWriter(fps=7), savefig_kwargs={"transparent": True},
    )
    plt.close(fig)


def write_html(frames: list[dict]) -> None:
    data = json.dumps(frames, separators=(",", ":"))
    template = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mug–torus persistence explorer</title><style>
:root{color-scheme:light dark;--bg:#fff;--fg:#263746;--muted:#607284;--line:#245a7a;--surface:#9fb8cc;--accent:#9b4774;--border:#b8c4cf}
@media(prefers-color-scheme:dark){:root{--bg:#1f2429;--fg:#edf2f7;--muted:#b8c4cf;--line:#82b7d7;--surface:#315f7d;--accent:#e18ab7;--border:#657381}}
*{box-sizing:border-box}body{margin:0;background:transparent;color:var(--fg);font:16px system-ui,sans-serif}
.wrap{border:1px solid var(--border);border-radius:14px;padding:14px;background:var(--bg)}
.controls{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px}.controls input[type=range]{flex:1;min-width:110px}.controls label{display:flex;align-items:center;gap:5px;font-size:.9rem}
button{padding:.45rem .8rem;border:1px solid var(--border);border-radius:7px;background:var(--bg);color:var(--fg)}
canvas{display:block;width:100%;height:auto}.caption{margin:.5rem .25rem 0;color:var(--muted);font-size:.92rem}
</style></head><body><div class="wrap"><div class="controls"><button id="play">Play</button>
<input id="slider" type="range" min="0" max="__MAX__" value="0" step="1" aria-label="deformation frame"><strong id="readout"></strong>
<label>Samples <select id="density"><option>18</option><option selected>28</option><option>38</option></select></label>
<label>Rotate <input id="azimuth" type="range" min="-180" max="180" value="-54" step="1" aria-label="horizontal rotation"></label>
<label>Tilt <input id="elevation" type="range" min="-75" max="75" value="23" step="1" aria-label="vertical rotation"></label></div>
<canvas id="plot" width="1180" height="520"></canvas>
  <p class="caption">One parameterised genus-one mesh is used throughout. The dots keep their parameter labels, but their spacing is deliberately non-uniform and changes with the deformation. The diagram is recomputed from their three-dimensional coordinates at every frame.</p></div>
<script>
const F=__DATA__,cv=document.getElementById("plot"),x=cv.getContext("2d"),s=document.getElementById("slider"),p=document.getElementById("play"),r=document.getElementById("readout"),density=document.getElementById("density"),azimuth=document.getElementById("azimuth"),elevation=document.getElementById("elevation");let timer=null;
function css(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim()}
function proj(a){let X=a[0],Y=a[1],Z=a[2],az=+azimuth.value*Math.PI/180,el=+elevation.value*Math.PI/180;let u=Math.cos(az)*X-Math.sin(az)*Y,v=Math.sin(az)*X+Math.cos(az)*Y;let w=Math.cos(el)*v-Math.sin(el)*Z;return[300+u*78,270-w*78,Math.sin(el)*v+Math.cos(el)*Z]}
const maxD=Math.max(...F.flatMap(f=>Object.values(f.samples).flatMap(g=>g.intervals.map(z=>z[1]))))*1.1;function pd(a,b){return[700+a/maxD*390,455-b/maxD*365]}
function draw(){let f=F[+s.value],M=f.mesh,S=f.samples[density.value],P=S.points;x.clearRect(0,0,1180,520);x.fillStyle=css("--bg");x.fillRect(0,0,1180,520);
x.fillStyle=css("--fg");x.font="700 21px system-ui";x.fillText(+s.value===0?"Mug surface":+s.value===F.length-1?"Torus surface":"Continuous surface deformation",75,34);x.fillText("Computed Vietoris–Rips H₁ diagram",700,34);
x.strokeStyle=css("--surface");x.lineWidth=1;x.globalAlpha=.65;
for(let i=0;i<M.length;i++){x.beginPath();for(let j=0;j<=M[i].length;j++){let q=proj(M[i][j%M[i].length]);j?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1])}x.stroke()}
for(let j=0;j<M[0].length;j++){x.beginPath();for(let i=0;i<=M.length;i++){let q=proj(M[i%M.length][j]);i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1])}x.stroke()}x.globalAlpha=1;
x.strokeStyle=css("--line");x.lineWidth=2;x.beginPath();for(let j=0;j<=M[2].length;j++){let q=proj(M[2][j%M[2].length]);j?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1])}x.stroke();
P.map(proj).sort((a,b)=>a[2]-b[2]).forEach(q=>{x.beginPath();x.arc(q[0],q[1],4.2,0,2*Math.PI);x.fillStyle=css("--bg");x.fill();x.strokeStyle=css("--line");x.lineWidth=2;x.stroke()});
x.strokeStyle=css("--muted");x.setLineDash([6,5]);let a=pd(0,0),b=pd(maxD,maxD);x.beginPath();x.moveTo(a[0],a[1]);x.lineTo(b[0],b[1]);x.stroke();x.setLineDash([]);
let ints=S.intervals,main=ints.length?ints.reduce((m,z,i)=>z[1]-z[0]>ints[m][1]-ints[m][0]?i:m,0):-1;ints.forEach((z,i)=>{let q=pd(z[0],z[1]);x.beginPath();x.arc(q[0],q[1],i===main?8:5.2,0,2*Math.PI);x.fillStyle=i===main?css("--accent"):css("--muted");x.globalAlpha=i===main?1:.72;x.fill();x.globalAlpha=1;x.strokeStyle=css("--bg");x.lineWidth=1;x.stroke()});
x.strokeStyle=css("--fg");x.lineWidth=1.5;x.beginPath();x.moveTo(700,455);x.lineTo(1090,455);x.moveTo(700,455);x.lineTo(700,90);x.stroke();x.fillStyle=css("--fg");x.font="15px system-ui";x.fillText("birth ε",1035,487);x.save();x.translate(665,145);x.rotate(-Math.PI/2);x.fillText("death ε",0,0);x.restore();
if(main>=0){let z=ints[main];x.fillText(`${ints.length} finite sample-induced H₁ intervals`,730,73);x.fillText(`longest this frame [${z[0].toFixed(3)}, ${z[1].toFixed(3)})`,730,98);x.fillText(`lifespan d − b = ${(z[1]-z[0]).toFixed(3)}`,730,123)}else{x.fillText("no finite H₁ intervals at this density",730,73)}
x.fillStyle=css("--muted");x.fillText("maroon: longest H₁ interval   grey: other H₁ intervals",730,151);x.fillText("this panel does not compute or display H₂ persistence",730,174);x.fillText("continuous surface truth: β₀=1, β₁=2, β₂=1",730,197);x.fillText("no filtration-independent true (birth, death) point",730,220);x.fillText("body pinches ↓   handle thickens ↑",75,490);r.textContent=`t = ${f.t.toFixed(2)}`}
[s,density,azimuth,elevation].forEach(e=>e.addEventListener("input",draw));p.addEventListener("click",()=>{if(timer){clearInterval(timer);timer=null;p.textContent="Play";return}p.textContent="Pause";timer=setInterval(()=>{s.value=(+s.value+1)%F.length;draw()},150)});matchMedia("(prefers-color-scheme: dark)").addEventListener("change",draw);draw();
</script></body></html>"""
    html = template.replace("__MAX__", str(len(frames) - 1)).replace("__DATA__", data)
    (ASSETS / "mug-torus-persistence.html").write_text(html)


def write_vineyard_proxy_html(frames: list[dict]) -> None:
    """Write a stacked-diagram view without claiming algebraic feature matching."""
    data = json.dumps(frames, separators=(",", ":"))
    template = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Mug–torus stacked persistence diagrams</title><style>
:root{color-scheme:light dark;--bg:#fff;--fg:#263746;--muted:#607284;--line:#245a7a;--surface:#9fb8cc;--accent:#9b4774;--border:#b8c4cf}
@media(prefers-color-scheme:dark){:root{--bg:#1f2429;--fg:#edf2f7;--muted:#b8c4cf;--line:#82b7d7;--surface:#315f7d;--accent:#e18ab7;--border:#657381}}
*{box-sizing:border-box}body{margin:0;background:transparent;color:var(--fg);font:16px system-ui,sans-serif}.wrap{border:1px solid var(--border);border-radius:14px;padding:14px;background:transparent}
.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.controls input{flex:1;min-width:150px}button{padding:.45rem .8rem;border:1px solid var(--border);border-radius:7px;background:var(--bg);color:var(--fg)}
canvas{display:block;width:100%;height:auto}.caption{margin:.45rem .25rem 0;color:var(--muted);font-size:.92rem}
</style></head><body><div class="wrap"><div class="controls"><button id="play">Play</button><input id="time" type="range" min="0" max="__MAX__" value="0"><strong id="readout"></strong><label>Samples <select id="density"><option>18</option><option selected>28</option><option>38</option></select></label></div>
<canvas id="plot" width="1180" height="520"></canvas><p class="caption">Each slanted plane is one independently computed persistence diagram. The dashed path joins the longest interval in each frame only as a visual proxy; it is not a vineyard feature match.</p></div><script>
const F=__DATA__,cv=document.getElementById("plot"),x=cv.getContext("2d"),time=document.getElementById("time"),play=document.getElementById("play"),readout=document.getElementById("readout"),density=document.getElementById("density");let timer=null;
function css(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim()}function proj(a){let X=a[0],Y=a[1],Z=a[2],az=-.94,el=.4,u=Math.cos(az)*X-Math.sin(az)*Y,v=Math.sin(az)*X+Math.cos(az)*Y,w=Math.cos(el)*v-Math.sin(el)*Z;return[285+u*72,275-w*72]}
const maxD=Math.max(...F.flatMap(f=>Object.values(f.samples).flatMap(g=>g.intervals["1"].map(z=>z[1]))))*1.1;
function longest(ints){if(!ints.length)return null;return ints.reduce((a,z)=>z[1]-z[0]>a[1]-a[0]?z:a,ints[0])}
function stackPoint(z,k){return[665+z[0]/maxD*300+k*3.2,450-z[1]/maxD*300-k*2.2]}
function draw(){let k=+time.value,f=F[k],M=f.mesh,P=f.samples[density.value].points;x.clearRect(0,0,1180,520);x.fillStyle=css("--fg");x.font="700 21px system-ui";x.fillText("Current deformed surface and observations",45,34);x.fillText("Persistence diagrams stacked through deformation time",625,34);
x.strokeStyle=css("--surface");x.lineWidth=1;x.globalAlpha=.65;for(let i=0;i<M.length;i++){x.beginPath();for(let j=0;j<=M[i].length;j++){let q=proj(M[i][j%M[i].length]);j?x.lineTo(...q):x.moveTo(...q)}x.stroke()}for(let j=0;j<M[0].length;j++){x.beginPath();for(let i=0;i<=M.length;i++){let q=proj(M[i%M.length][j]);i?x.lineTo(...q):x.moveTo(...q)}x.stroke()}x.globalAlpha=1;P.map(proj).forEach(q=>{x.beginPath();x.arc(...q,4,0,2*Math.PI);x.fillStyle=css("--bg");x.fill();x.strokeStyle=css("--line");x.lineWidth=2;x.stroke()});
for(let j=0;j<=k;j+=2){let o=[665+j*3.2,450-j*2.2],w=300;x.strokeStyle=css("--border");x.lineWidth=1;x.globalAlpha=j===k?1:.35;x.beginPath();x.moveTo(...o);x.lineTo(o[0]+w,o[1]);x.lineTo(o[0]+w,o[1]-w);x.stroke();for(const z of F[j].samples[density.value].intervals["1"]){let q=stackPoint(z,j);x.beginPath();x.arc(...q,j===k?5:3,0,2*Math.PI);x.fillStyle=css("--muted");x.fill()}}x.globalAlpha=1;
x.strokeStyle=css("--accent");x.lineWidth=2;x.setLineDash([5,4]);x.beginPath();let begun=false;for(let j=0;j<=k;j++){let z=longest(F[j].samples[density.value].intervals["1"]);if(z){let q=stackPoint(z,j);begun?x.lineTo(...q):x.moveTo(...q);begun=true}}x.stroke();x.setLineDash([]);let z=longest(f.samples[density.value].intervals["1"]);if(z){let q=stackPoint(z,k);x.beginPath();x.arc(...q,7,0,2*Math.PI);x.fillStyle=css("--accent");x.fill()}
x.fillStyle=css("--muted");x.font="14px system-ui";x.fillText("birth ε →",925,480);x.fillText("external deformation time ↗",655,500);x.fillText("dashed: longest-point proxy, not a matched vine",690,62);readout.textContent=`t = ${f.t.toFixed(2)}`}
[time,density].forEach(e=>e.addEventListener("input",draw));play.addEventListener("click",()=>{if(timer){clearInterval(timer);timer=null;play.textContent="Play";return}play.textContent="Pause";timer=setInterval(()=>{time.value=(+time.value+1)%F.length;draw()},160)});matchMedia("(prefers-color-scheme: dark)").addEventListener("change",draw);draw();
</script></body></html>"""
    html = template.replace("__MAX__", str(len(frames) - 1)).replace("__DATA__", data)
    (ASSETS / "mug-torus-vineyard-proxy.html").write_text(html)


def write_filtration_html(frames: list[dict]) -> None:
    """Write the transparent, pauseable deformation and filtration explorer."""
    template = (ROOT / "scripts" / "mug_torus_explorer_template.html").read_text()
    data = json.dumps(frames, separators=(",", ":"))
    deaths = [
        death
        for frame in frames
        for sample in frame["samples"].values()
        for dimension in ("1", "2")
        for _, death in sample["intervals"][dimension]
    ]
    html = (
        template.replace("__MAX__", str(len(frames) - 1))
        .replace("__EPSMAX__", f"{max(deaths) * 1.05:.3f}")
        .replace("__DATA__", data)
    )
    (ASSETS / "mug-torus-persistence.html").write_text(html)


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    frames = compute_frames()
    write_filtration_html(frames)
    write_vineyard_proxy_html(frames)
    print(
        "Generated mug-torus persistence assets; "
        "density options " + ", ".join(map(str, SAMPLE_DENSITIES))
    )


if __name__ == "__main__":
    main()
