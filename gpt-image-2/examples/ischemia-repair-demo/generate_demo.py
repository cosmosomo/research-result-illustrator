from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle


OUTPUT_DIR = Path(__file__).resolve().parent
DATA_DIR = OUTPUT_DIR / "data"
RNG = np.random.default_rng(20260718)

COLORS = {
    "Healthy control": "#59636B",
    "Ischemia": "#C85C4A",
    "Hydrogel treatment": "#18877C",
}


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def create_synthetic_data() -> dict[str, object]:
    days = np.array([0, 3, 7, 14, 21, 28])
    perfusion_means = {
        "Healthy control": np.array([100, 99, 101, 100, 100, 101]),
        "Ischemia": np.array([100, 35, 42, 48, 54, 58]),
        "Hydrogel treatment": np.array([100, 38, 55, 70, 82, 90]),
    }
    perfusion = {
        group: np.clip(RNG.normal(means, 4.0, size=(8, len(days))), 20, 110)
        for group, means in perfusion_means.items()
    }

    hypoxia_means = {
        "Healthy control": 5.5,
        "Ischemia": 41.0,
        "Hydrogel treatment": 14.5,
    }
    hypoxia = {
        group: np.clip(RNG.normal(mean, 3.2, size=8), 1, 50)
        for group, mean in hypoxia_means.items()
    }

    genes = ["HIF1A", "IL6", "TNF", "VEGFA", "ANGPT1"]
    heatmap = np.array(
        [
            [-1.1, 1.5, -0.3],
            [-0.9, 1.3, -0.5],
            [-0.8, 1.4, -0.4],
            [0.1, -0.7, 1.2],
            [0.2, -0.8, 1.3],
        ]
    )

    correlation_perfusion = np.concatenate(
        [perfusion[group][:, -1] for group in COLORS]
    )
    correlation_hypoxia = np.concatenate([hypoxia[group] for group in COLORS])

    perfusion_rows = []
    for group, values in perfusion.items():
        for replicate, row in enumerate(values, 1):
            for day, value in zip(days, row, strict=True):
                perfusion_rows.append(
                    {
                        "group": group,
                        "replicate": replicate,
                        "day": int(day),
                        "perfusion_percent_baseline": round(float(value), 3),
                    }
                )
    write_rows(
        DATA_DIR / "perfusion_timecourse.csv",
        ["group", "replicate", "day", "perfusion_percent_baseline"],
        perfusion_rows,
    )

    hypoxia_rows = [
        {
            "group": group,
            "replicate": replicate,
            "hypoxic_area_percent": round(float(value), 3),
        }
        for group, values in hypoxia.items()
        for replicate, value in enumerate(values, 1)
    ]
    write_rows(
        DATA_DIR / "hypoxia_endpoint.csv",
        ["group", "replicate", "hypoxic_area_percent"],
        hypoxia_rows,
    )

    heatmap_rows = [
        {
            "marker": gene,
            "healthy_control_z": heatmap[index, 0],
            "ischemia_z": heatmap[index, 1],
            "hydrogel_treatment_z": heatmap[index, 2],
        }
        for index, gene in enumerate(genes)
    ]
    write_rows(
        DATA_DIR / "response_heatmap.csv",
        ["marker", "healthy_control_z", "ischemia_z", "hydrogel_treatment_z"],
        heatmap_rows,
    )

    correlation_rows = [
        {
            "sample": index,
            "perfusion_day_28_percent": round(float(perfusion_value), 3),
            "hypoxic_area_percent": round(float(hypoxia_value), 3),
        }
        for index, (perfusion_value, hypoxia_value) in enumerate(
            zip(correlation_perfusion, correlation_hypoxia, strict=True), 1
        )
    ]
    write_rows(
        DATA_DIR / "perfusion_hypoxia_correlation.csv",
        ["sample", "perfusion_day_28_percent", "hypoxic_area_percent"],
        correlation_rows,
    )

    return {
        "days": days,
        "perfusion": perfusion,
        "hypoxia": hypoxia,
        "genes": genes,
        "heatmap": heatmap,
        "correlation_perfusion": correlation_perfusion,
        "correlation_hypoxia": correlation_hypoxia,
    }


def style_axis(axis: plt.Axes) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(labelsize=8, width=0.8, color="#59636B")
    axis.grid(axis="y", color="#D9DEE2", linewidth=0.7, alpha=0.7)
    axis.set_axisbelow(True)


def add_panel_label(axis: plt.Axes, label: str) -> None:
    axis.text(-0.13, 1.08, label, transform=axis.transAxes, fontsize=12, fontweight="bold")


def plot_results(data: dict[str, object]) -> Path:
    days = data["days"]
    perfusion = data["perfusion"]
    hypoxia = data["hypoxia"]
    heatmap = data["heatmap"]
    genes = data["genes"]
    correlation_perfusion = data["correlation_perfusion"]
    correlation_hypoxia = data["correlation_hypoxia"]

    figure, axes = plt.subplots(2, 2, figsize=(9.2, 7.2), constrained_layout=True)
    figure.patch.set_facecolor("white")
    figure.suptitle(
        "Synthetic test: hydrogel-associated recovery after ischemic injury",
        fontsize=13,
        fontweight="bold",
    )

    axis = axes[0, 0]
    for group, values in perfusion.items():
        mean = values.mean(axis=0)
        sem = values.std(axis=0, ddof=1) / np.sqrt(values.shape[0])
        axis.plot(days, mean, marker="o", linewidth=2.0, markersize=4.5, color=COLORS[group], label=group)
        axis.fill_between(days, mean - sem, mean + sem, color=COLORS[group], alpha=0.15)
    style_axis(axis)
    axis.set_xlabel("Days after injury", fontsize=9)
    axis.set_ylabel("Perfusion (% baseline)", fontsize=9)
    axis.set_title("Perfusion recovery", fontsize=10)
    axis.legend(frameon=False, fontsize=7, loc="lower right")
    add_panel_label(axis, "a")

    axis = axes[0, 1]
    for position, (group, values) in enumerate(hypoxia.items()):
        jitter = RNG.uniform(-0.08, 0.08, size=len(values))
        axis.scatter(
            np.full(len(values), position) + jitter,
            values,
            s=24,
            color=COLORS[group],
            edgecolor="white",
            linewidth=0.5,
            alpha=0.85,
        )
        mean = values.mean()
        sem = values.std(ddof=1) / np.sqrt(len(values))
        axis.errorbar(position, mean, yerr=sem, color="#20272C", capsize=5, linewidth=1.5, marker="_", markersize=16)
    style_axis(axis)
    axis.set_xticks(range(3), ["Control", "Ischemia", "Hydrogel"], rotation=15, ha="right")
    axis.set_ylabel("Hypoxic area (%)", fontsize=9)
    axis.set_title("Endpoint tissue hypoxia", fontsize=10)
    add_panel_label(axis, "b")

    axis = axes[1, 0]
    image = axis.imshow(heatmap, cmap="RdBu_r", vmin=-1.6, vmax=1.6, aspect="auto")
    axis.set_xticks(range(3), ["Control", "Ischemia", "Hydrogel"], rotation=20, ha="right", fontsize=8)
    axis.set_yticks(range(len(genes)), genes, fontsize=8)
    axis.set_title("Tissue-response markers", fontsize=10)
    for row in range(heatmap.shape[0]):
        for column in range(heatmap.shape[1]):
            axis.text(column, row, f"{heatmap[row, column]:.1f}", ha="center", va="center", fontsize=7)
    colorbar = figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    colorbar.set_label("z-score", fontsize=8)
    colorbar.ax.tick_params(labelsize=7)
    add_panel_label(axis, "c")

    axis = axes[1, 1]
    group_names = list(COLORS)
    for group_index, group in enumerate(group_names):
        start = group_index * 8
        stop = start + 8
        axis.scatter(
            correlation_perfusion[start:stop],
            correlation_hypoxia[start:stop],
            s=30,
            color=COLORS[group],
            label=group,
            alpha=0.85,
        )
    slope, intercept = np.polyfit(correlation_perfusion, correlation_hypoxia, 1)
    x_line = np.linspace(correlation_perfusion.min(), correlation_perfusion.max(), 100)
    axis.plot(x_line, slope * x_line + intercept, color="#20272C", linewidth=1.5, linestyle="--")
    correlation = np.corrcoef(correlation_perfusion, correlation_hypoxia)[0, 1]
    axis.text(0.05, 0.93, f"r = {correlation:.2f}", transform=axis.transAxes, fontsize=9, va="top")
    style_axis(axis)
    axis.set_xlabel("Perfusion at day 28 (%)", fontsize=9)
    axis.set_ylabel("Hypoxic area (%)", fontsize=9)
    axis.set_title("Perfusion-hypoxia relationship", fontsize=10)
    add_panel_label(axis, "d")

    figure.text(0.5, 0.002, "SYNTHETIC TEST DATA - not experimental evidence", ha="center", fontsize=7, color="#8C3A2D")
    output_path = OUTPUT_DIR / "results-panels.png"
    figure.savefig(output_path, dpi=180, facecolor="white")
    plt.close(figure)
    return output_path


def draw_tissue_stage(axis: plt.Axes, center_x: float, title: str, state: str) -> None:
    axis.add_patch(Rectangle((center_x - 0.115, 0.33), 0.23, 0.28, facecolor="#F3E6DF", edgecolor="#8B6D62", linewidth=1.2))
    vessel_color = "#C85C4A" if state == "injured" else "#18877C"
    vessel_width = 1.5 if state == "injured" else 3.0
    axis.plot([center_x - 0.09, center_x + 0.09], [0.47, 0.47], color=vessel_color, linewidth=vessel_width)
    axis.plot([center_x - 0.03, center_x - 0.03], [0.39, 0.55], color=vessel_color, linewidth=vessel_width * 0.7)
    axis.plot([center_x + 0.04, center_x + 0.04], [0.39, 0.55], color=vessel_color, linewidth=vessel_width * 0.7)
    if state == "injured":
        for offset in (-0.07, 0.0, 0.07):
            axis.add_patch(Circle((center_x + offset, 0.38), 0.015, facecolor="#D98A75", edgecolor="none", alpha=0.8))
    else:
        for offset in (-0.07, -0.02, 0.04, 0.08):
            axis.add_patch(Circle((center_x + offset, 0.56), 0.012, facecolor="#7CB8A8", edgecolor="none", alpha=0.9))
    axis.text(center_x, 0.66, title, ha="center", va="bottom", fontsize=9, fontweight="bold")


def plot_composite_concept(results_path: Path) -> Path:
    figure = plt.figure(figsize=(12, 8), facecolor="white")
    figure.text(0.04, 0.95, "Hydrogel treatment restores perfusion after ischemic injury", fontsize=17, fontweight="bold")
    figure.text(0.04, 0.915, "Mechanism-led composite with subordinate quantitative evidence", fontsize=10, color="#59636B")

    mechanism_axis = figure.add_axes([0.04, 0.09, 0.40, 0.78])
    mechanism_axis.set_xlim(0, 1)
    mechanism_axis.set_ylim(0, 1)
    mechanism_axis.axis("off")
    mechanism_axis.add_patch(Rectangle((0, 0), 1, 1, facecolor="#F7F8F7", edgecolor="#C8CED2", linewidth=1.0))
    mechanism_axis.text(0.04, 0.95, "Conceptual mechanism", fontsize=11, fontweight="bold", va="top")
    draw_tissue_stage(mechanism_axis, 0.23, "Ischemic tissue", "injured")
    draw_tissue_stage(mechanism_axis, 0.77, "Restored perfusion", "restored")
    mechanism_axis.add_patch(
        FancyArrowPatch((0.36, 0.47), (0.64, 0.47), arrowstyle="-|>", mutation_scale=18, linewidth=2, color="#18877C")
    )
    mechanism_axis.add_patch(Circle((0.50, 0.47), 0.075, facecolor="#D7ECE7", edgecolor="#18877C", linewidth=1.5))
    mechanism_axis.text(0.50, 0.47, "Hydrogel", ha="center", va="center", fontsize=8, fontweight="bold", color="#12665E")
    mechanism_axis.text(0.50, 0.27, "reduced hypoxia and inflammation", ha="center", fontsize=9, color="#59636B")
    mechanism_axis.text(0.50, 0.21, "enhanced pro-angiogenic response", ha="center", fontsize=9, color="#59636B")
    mechanism_axis.text(0.04, 0.05, "GPT Image 2 illustration region", fontsize=8, color="#8A9399")

    results_axis = figure.add_axes([0.48, 0.075, 0.50, 0.82])
    results_axis.imshow(plt.imread(results_path))
    results_axis.axis("off")
    results_axis.set_title("Quantitative results", fontsize=11, fontweight="bold", pad=6)

    output_path = OUTPUT_DIR / "composite-concept.png"
    figure.savefig(output_path, dpi=160, facecolor="white")
    plt.close(figure)
    return output_path


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = create_synthetic_data()
    results_path = plot_results(data)
    concept_path = plot_composite_concept(results_path)
    print(results_path)
    print(concept_path)


if __name__ == "__main__":
    main()
