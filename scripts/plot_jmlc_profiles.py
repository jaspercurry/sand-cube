"""Plot Le Cleac'h/JMLC stop-angle options for the current horn params."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from params import p
from src.features.horn import jmlc_profile_points


def main() -> None:
    mouth_inner_r = p.horn_mouth_outer_d / 2 - p.horn_wall_t
    angles = (120.0, 140.0, 150.0)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=180)
    for angle in angles:
        points, cutoff_hz = jmlc_profile_points(
            throat_d=p.horn_throat_d,
            mouth_inner_r=mouth_inner_r,
            exit_angle_deg=angle,
            wavefront_t=p.horn_wavefront_t,
            throat_angle_deg=p.horn_throat_angle_deg,
            step=p.horn_profile_step,
        )
        z = [point[1] for point in points]
        r = [point[0] for point in points]
        label = f"{angle:.0f} deg stop: Fc {cutoff_hz:.0f} Hz, length {max(z):.1f} mm"
        (line,) = ax.plot(z, r, label=label)
        ax.plot(z, [-value for value in r], color=line.get_color())

    ax.axhline(mouth_inner_r, color="0.75", lw=0.8)
    ax.axhline(-mouth_inner_r, color="0.75", lw=0.8)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("axial distance from throat, mm")
    ax.set_ylabel("radius, mm")
    ax.set_title(f"JMLC recurrence, fixed {2 * mouth_inner_r:.1f} mm inner mouth")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="lower right")

    out = ROOT / "build" / "jmlc_profile_stop_angles.png"
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
