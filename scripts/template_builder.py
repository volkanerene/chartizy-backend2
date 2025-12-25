#!/usr/bin/env python3
"""
Utility script to generate richly styled Chartizy templates.

The script emits a JSON file with template definitions (example_data + preview DSL)
that can be imported into Supabase or used locally during development.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "supabase" / "generated_templates.json"


def build_theme(
    primary: str = "#165DFC",
    secondary: str = "#8EC6FF",
    accent: str = "#4A7DFD",
    background: str = "#0F172A",
    foreground: str = "#F8FAFC",
    effects: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "palette": {
            "primary": primary,
            "secondary": secondary,
            "accent": accent,
            "background": background,
            "foreground": foreground,
            "muted": "#94A3B8",
            "success": "#10B981",
            "warning": "#F59E0B",
            "error": "#EF4444",
        },
        "typography": {
            "fontFamily": "Geist, sans-serif",
            "fontSize": 16,
            "fontWeight": 500,
        },
        "effects": effects or {
            "gradient": {
                "type": "linear",
                "colors": [
                    {"color": primary, "offset": 0},
                    {"color": secondary, "offset": 1},
                ],
                "start": {"x": 0, "y": 0},
                "end": {"x": 1, "y": 1},
            },
            "shadow": {"blur": 24, "color": "#00000055", "offsetX": 0, "offsetY": 16},
            "opacity": 1,
            "blendMode": "normal",
        },
    }


def base_canvas(width: int = 1200, height: int = 720) -> Dict[str, Any]:
    return {
        "width": width,
        "height": height,
        "padding": {"top": 64, "right": 64, "bottom": 96, "left": 96},
        "background": "transparent",
    }


def base_interactions() -> Dict[str, Any]:
    return {
        "tooltip": {"enabled": True, "position": "auto"},
        "zoom": {"enabled": False, "mode": "xy"},
        "pan": {"enabled": False, "mode": "xy"},
        "selection": {"enabled": False, "mode": "single"},
    }


def base_scales(x_type: str = "band", x_padding: float = 0.2) -> Dict[str, Any]:
    return {
        "x": {"type": x_type, "nice": True, "padding": x_padding},
        "y": {"type": "linear", "nice": True},
    }


def data_source(labels: List[str], datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "source": {
            "labels": labels,
            "datasets": datasets,
        },
        "transforms": [],
    }


def grid_layer(direction: str = "both", opacity: float = 0.35) -> Dict[str, Any]:
    return {
        "type": "grid",
        "direction": direction,
        "color": "#1E293B",
        "width": 1,
        "opacity": opacity,
        "style": "solid",
    }


def axis_layer(axis_type: str, position: str, show_labels: bool = True) -> Dict[str, Any]:
    return {
        "type": axis_type,
        "position": position,
        "showLabels": show_labels,
        "showTicks": show_labels,
        "showLine": True,
        "color": "#94A3B8",
        "fontSize": 14,
        "tickLength": 8,
    }


def area_layer(
    dataset_index: int,
    colors: List[str],
    opacity: float = 0.75,
    smooth: bool = True,
) -> Dict[str, Any]:
    return {
        "type": "area",
        "xField": "labels",
        "yField": f"datasets.{dataset_index}.data",
        "color": colors[0],
        "opacity": opacity,
        "smooth": smooth,
        "stroke": {"color": colors[1] if len(colors) > 1 else colors[0], "width": 3},
        "effects": {
            "gradient": {
                "type": "linear",
                "colors": [{"color": c, "offset": idx / (len(colors) - 1 or 1)} for idx, c in enumerate(colors)],
                "start": {"x": 0, "y": 0},
                "end": {"x": 0, "y": 1},
            },
            "shadow": {"blur": 20, "color": colors[0] + "44", "offsetX": 0, "offsetY": 18},
            "opacity": 0.95,
            "blendMode": "normal",
        },
    }


def bar_layer(dataset_index: int, colors: List[str]) -> Dict[str, Any]:
    return {
        "type": "bars",
        "xField": "labels",
        "yField": f"datasets.{dataset_index}.data",
        "color": colors,
        "width": 0.72,
        "borderRadius": 14,
        "effects": {
            "shadow": {"blur": 14, "color": "#00000033", "offsetX": 0, "offsetY": 10},
            "opacity": 0.95,
        },
    }


def line_layer(dataset_index: int, color: str, smooth: bool = True) -> Dict[str, Any]:
    return {
        "type": "line",
        "xField": "labels",
        "yField": f"datasets.{dataset_index}.data",
        "color": color,
        "width": 4,
        "smooth": smooth,
        "showPoints": True,
        "effects": {
            "shadow": {"blur": 8, "color": color + "66", "offsetX": 0, "offsetY": 6},
            "opacity": 1,
        },
    }


def donut_layers(colors: List[str]) -> List[Dict[str, Any]]:
    return [
        {
            "type": "grid",
            "direction": "both",
            "color": "#1F2937",
            "width": 1,
            "opacity": 0.15,
        },
        {
            "type": "annotations",
            "items": [
                {
                    "type": "text",
                    "x": 0.5,
                    "y": 0.5,
                    "text": "Top Segments",
                    "color": "#E2E8F0",
                    "fontSize": 28,
                }
            ],
        },
        {
            "type": "customPath",
            "path": "",
            "color": colors[0],
            "effects": {"opacity": 0},
        },
    ]


@dataclass
class TemplateSpec:
    name: str
    description: str
    chart_type: str
    example_data: Dict[str, Any]
    preview_dsl: Dict[str, Any]
    is_premium: bool = False

    def to_record(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["example_data"] = dict(self.example_data)
        payload["example_data"]["preview_dsl"] = self.preview_dsl
        return payload


def build_templates() -> List[TemplateSpec]:
    templates: List[TemplateSpec] = []

    # 1. Aurora Gradient Revenues (stacked area)
    aurora_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    aurora_datasets = [
        {"label": "Subscriptions", "data": [42, 56, 68, 74, 80, 92, 110, 124, 138]},
        {"label": "Services", "data": [24, 32, 41, 47, 53, 60, 72, 81, 95]},
    ]
    area_layers = [
        grid_layer(opacity=0.2),
        axis_layer("axis-x", "bottom"),
        axis_layer("axis-y", "left"),
        area_layer(0, ["#34D399", "#10B981", "#064E3B"]),
        area_layer(1, ["#60A5FA", "#3B82F6", "#1E3A8A"]),
      ]
    aurora_dsl = {
        "version": "1.0.0",
        "canvas": base_canvas(),
        "theme": build_theme(background="#020617", foreground="#E2E8F0"),
        "data": data_source(aurora_labels, aurora_datasets),
        "layers": area_layers,
        "scales": base_scales("band", 0.1),
        "interactions": base_interactions(),
    }
    templates.append(
        TemplateSpec(
            name="Aurora Growth",
            description="Gradient-stacked area showing revenue pillars with neon glow.",
            chart_type="area",
            example_data={"labels": aurora_labels, "datasets": aurora_datasets},
            preview_dsl=aurora_dsl,
        )
    )

    # 2. Midnight Neon Bars
    neon_labels = ["Design", "Dev", "Ops", "Growth", "Success", "Finance"]
    neon_dataset = [
        {"label": "Velocity", "data": [82, 64, 58, 91, 74, 68]},
    ]
    neon_layers = [
        grid_layer(),
        axis_layer("axis-x", "bottom"),
        axis_layer("axis-y", "left"),
        bar_layer(0, ["#8B5CF6", "#6366F1", "#EC4899", "#F43F5E", "#F97316", "#22D3EE"]),
    ]
    neon_dsl = {
        "version": "1.0.0",
        "canvas": base_canvas(),
        "theme": build_theme(primary="#8B5CF6", secondary="#F43F5E", background="#020617"),
        "data": data_source(neon_labels, neon_dataset),
        "layers": neon_layers,
        "scales": base_scales(),
        "interactions": base_interactions(),
    }
    templates.append(
        TemplateSpec(
            name="Midnight Velocity",
            description="Rounded neon bars with ambient glow for KPIs.",
            chart_type="bar",
            example_data={"labels": neon_labels, "datasets": neon_dataset},
            preview_dsl=neon_dsl,
        )
    )

    # 3. Horizon Split (line + area hybrid)
    horizon_labels = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
    horizon_dataset = [
        {"label": "Net Retention", "data": [104, 108, 111, 115, 119, 124]},
    ]
    horizon_layers = [
        grid_layer(opacity=0.25),
        axis_layer("axis-x", "bottom"),
        axis_layer("axis-y", "left"),
        area_layer(0, ["#FDE68A88", "#F59E0B55", "#78350F33"], opacity=0.35, smooth=True),
        line_layer(0, "#FBBF24"),
    ]
    horizon_dsl = {
        "version": "1.0.0",
        "canvas": base_canvas(),
        "theme": build_theme(primary="#FBBF24", secondary="#F97316", background="#0F172A"),
        "data": data_source(horizon_labels, horizon_dataset),
        "layers": horizon_layers,
        "scales": base_scales("band", 0.05),
        "interactions": base_interactions(),
    }
    templates.append(
        TemplateSpec(
            name="Horizon Split",
            description="Minimal retention trajectory with glowing line overlay.",
            chart_type="line",
            example_data={"labels": horizon_labels, "datasets": horizon_dataset},
            preview_dsl=horizon_dsl,
        )
    )

    # 4. Stellar Contribution (doughnut style, represented via bars/points)
    stellar_labels = ["Product", "Marketing", "Sales", "Success", "Ops"]
    stellar_dataset = [
        {"label": "Contribution", "data": [34, 27, 21, 11, 7]},
    ]
    stellar_layers = [
        grid_layer(direction="horizontal", opacity=0.15),
        axis_layer("axis-x", "bottom"),
        bar_layer(0, ["#0EA5E9", "#38BDF8", "#7DD3FC", "#CFFAFE", "#F0F9FF"]),
        line_layer(0, "#F472B6", smooth=False),
    ]
    stellar_dsl = {
        "version": "1.0.0",
        "canvas": base_canvas(),
        "theme": build_theme(primary="#0EA5E9", secondary="#F472B6", background="#020617"),
        "data": data_source(stellar_labels, stellar_dataset),
        "layers": stellar_layers,
        "scales": base_scales(),
        "interactions": base_interactions(),
    }
    templates.append(
        TemplateSpec(
            name="Stellar Contribution",
            description="Contrasting cyan/pink bars for channel splits.",
            chart_type="bar",
            example_data={"labels": stellar_labels, "datasets": stellar_dataset},
            preview_dsl=stellar_dsl,
        )
    )

    return templates


def main() -> None:
    templates = build_templates()
    payload = [tpl.to_record() for tpl in templates]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Generated {len(payload)} templates → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
