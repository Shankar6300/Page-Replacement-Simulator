from __future__ import annotations

import os
import re
from datetime import datetime

from flask import Flask, jsonify, render_template, request

import page_replacement_simulator

app = Flask(__name__)

STATIC_VERSION = "20260319-3"

TEAM_MEMBERS = [
    {
        "name": "G Shankar Narayana Reddy",
        "registration": "12304121",
        "roll": "19",
    },
    {
        "name": "Uppari Venkatesh",
        "registration": "12313445",
        "roll": "62",
    },
    {
        "name": "J Mohammad Rabbani",
        "registration": "12300555",
        "roll": "33",
    },
]

PROJECT_INFO = {
    "course": "CSE316 - Operating Systems",
    "section": "K23CT",
    "mentor": "Gagandeep Kaur",
    "title": "Efficient Page Replacement Algorithm Simulator",
}


@app.context_processor
def inject_global_template_values() -> dict[str, str | int]:
    return {
        "current_year": datetime.now().year,
        "static_version": STATIC_VERSION,
    }


def _parse_frame_count(raw_value: str | int | None) -> int:
    if raw_value in (None, ""):
        raise ValueError("Number of frames is required.")

    try:
        frame_count = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Number of frames must be an integer.") from exc

    if frame_count < 1 or frame_count > 15:
        raise ValueError("Number of frames must be between 1 and 15.")

    return frame_count


def _parse_pages(raw_value: str | None) -> list[int]:
    if not raw_value or not raw_value.strip():
        raise ValueError("Page reference string is required.")

    tokens = [token for token in re.split(r"[\s,]+", raw_value.strip()) if token]

    try:
        pages = [int(token) for token in tokens]
    except ValueError as exc:
        raise ValueError(
            "Page reference must contain only integers separated by spaces or commas."
        ) from exc

    if not pages:
        raise ValueError("Please provide at least one page reference.")

    if len(pages) > 200:
        raise ValueError("Please keep the page reference length to 200 or fewer values.")

    if any(page < 0 for page in pages):
        raise ValueError("Page references must be zero or positive integers.")

    return pages


def _parse_algorithm(raw_value: str | None) -> str:
    algorithm = (raw_value or "all").strip().lower()
    allowed = {"fifo", "lru", "optimal", "all"}

    if algorithm not in allowed:
        raise ValueError("Algorithm must be one of FIFO, LRU, Optimal, or all.")

    return algorithm


@app.route("/")
def home() -> str:
    return render_template(
        "index.html",
        active_page="home",
        page_title="Home",
        project_info=PROJECT_INFO,
    )


@app.route("/simulator")
def simulator() -> str:
    return render_template(
        "simulator.html",
        active_page="simulator",
        page_title="Simulator",
        project_info=PROJECT_INFO,
    )


@app.route("/guide")
def guide() -> str:
    return render_template(
        "guide.html",
        active_page="guide",
        page_title="Guide",
        project_info=PROJECT_INFO,
    )


@app.route("/about")
def about() -> str:
    return render_template(
        "about.html",
        active_page="about",
        page_title="About",
        project_info=PROJECT_INFO,
        team_members=TEAM_MEMBERS,
    )


@app.route("/api/simulate", methods=["POST"])
def run_simulation():
    payload = request.get_json(silent=True)
    if payload is None:
        payload = request.form.to_dict()

    try:
        frame_count = _parse_frame_count(payload.get("frames"))
        pages = _parse_pages(payload.get("pages"))
        algorithm = _parse_algorithm(payload.get("algorithm"))

        results = page_replacement_simulator.run_algorithms(
            frame_count=frame_count,
            pages=pages,
            algorithm=algorithm,
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception:
        return jsonify(
            {
                "ok": False,
                "error": "Unexpected server error while running the simulation.",
            }
        ), 500

    return jsonify(
        {
            "ok": True,
            "input": {
                "frames": frame_count,
                "pages": pages,
                "algorithm": algorithm,
            },
            "results": results,
        }
    )


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug_mode)
