from __future__ import annotations

from math import inf
from typing import Any


SUPPORTED_ALGORITHMS = ("fifo", "lru", "optimal")


def _validate_inputs(frame_count: int, pages: list[int]) -> None:
    if frame_count <= 0:
        raise ValueError("Frame count must be greater than zero.")
    if not pages:
        raise ValueError("Page reference string cannot be empty.")


def _frame_snapshot(memory: list[int], frame_count: int) -> list[int | None]:
    padded = memory[:]
    if len(padded) < frame_count:
        padded.extend([None] * (frame_count - len(padded)))
    return padded


def _build_result(
    algorithm_name: str,
    faults: int,
    hits: int,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    total = faults + hits
    return {
        "algorithm": algorithm_name,
        "page_faults": faults,
        "page_hits": hits,
        "fault_ratio": (faults / total) if total else 0,
        "hit_ratio": (hits / total) if total else 0,
        "steps": steps,
    }


def simulate_fifo(frame_count: int, pages: list[int]) -> dict[str, Any]:
    _validate_inputs(frame_count, pages)

    memory: list[int] = []
    steps: list[dict[str, Any]] = []
    faults = 0
    hits = 0
    pointer = 0

    for turn, page in enumerate(pages, start=1):
        is_hit = page in memory
        replaced = None

        if is_hit:
            hits += 1
        else:
            faults += 1
            if len(memory) < frame_count:
                memory.append(page)
            else:
                replaced = memory[pointer]
                memory[pointer] = page
                pointer = (pointer + 1) % frame_count

        steps.append(
            {
                "step": turn,
                "page": page,
                "status": "hit" if is_hit else "fault",
                "replaced": replaced,
                "frames": _frame_snapshot(memory, frame_count),
            }
        )

    return _build_result("FIFO", faults, hits, steps)


def simulate_lru(frame_count: int, pages: list[int]) -> dict[str, Any]:
    _validate_inputs(frame_count, pages)

    memory: list[int] = []
    last_used: dict[int, int] = {}
    steps: list[dict[str, Any]] = []
    faults = 0
    hits = 0

    for turn, page in enumerate(pages, start=1):
        is_hit = page in memory
        replaced = None

        if is_hit:
            hits += 1
        else:
            faults += 1
            if len(memory) < frame_count:
                memory.append(page)
            else:
                victim = min(memory, key=lambda value: last_used.get(value, -1))
                victim_index = memory.index(victim)
                replaced = victim
                memory[victim_index] = page

        last_used[page] = turn
        steps.append(
            {
                "step": turn,
                "page": page,
                "status": "hit" if is_hit else "fault",
                "replaced": replaced,
                "frames": _frame_snapshot(memory, frame_count),
            }
        )

    return _build_result("LRU", faults, hits, steps)


def simulate_optimal(frame_count: int, pages: list[int]) -> dict[str, Any]:
    _validate_inputs(frame_count, pages)

    memory: list[int] = []
    steps: list[dict[str, Any]] = []
    faults = 0
    hits = 0

    for index, page in enumerate(pages):
        turn = index + 1
        is_hit = page in memory
        replaced = None

        if is_hit:
            hits += 1
        else:
            faults += 1
            if len(memory) < frame_count:
                memory.append(page)
            else:
                farthest_next_use = -1
                victim = memory[0]

                for resident_page in memory:
                    try:
                        next_use = pages.index(resident_page, index + 1)
                    except ValueError:
                        next_use = inf

                    if next_use > farthest_next_use:
                        farthest_next_use = next_use
                        victim = resident_page

                victim_index = memory.index(victim)
                replaced = victim
                memory[victim_index] = page

        steps.append(
            {
                "step": turn,
                "page": page,
                "status": "hit" if is_hit else "fault",
                "replaced": replaced,
                "frames": _frame_snapshot(memory, frame_count),
            }
        )

    return _build_result("Optimal", faults, hits, steps)


def run_algorithms(
    frame_count: int,
    pages: list[int],
    algorithm: str = "all",
) -> dict[str, dict[str, Any]]:
    normalized_algorithm = algorithm.lower().strip()

    handlers = {
        "fifo": simulate_fifo,
        "lru": simulate_lru,
        "optimal": simulate_optimal,
    }

    if normalized_algorithm == "all":
        selected = SUPPORTED_ALGORITHMS
    elif normalized_algorithm in handlers:
        selected = (normalized_algorithm,)
    else:
        raise ValueError("Algorithm must be FIFO, LRU, Optimal, or all.")

    return {
        name.upper(): handlers[name](frame_count, pages)
        for name in selected
    }


def fifo(frame_count: int, pages: list[int]) -> int:
    return simulate_fifo(frame_count, pages)["page_faults"]


def lru(frame_count: int, pages: list[int]) -> int:
    return simulate_lru(frame_count, pages)["page_faults"]


def optimal(frame_count: int, pages: list[int]) -> int:
    return simulate_optimal(frame_count, pages)["page_faults"]
