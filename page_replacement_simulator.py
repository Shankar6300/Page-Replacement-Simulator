def fifo(frames, pages):
    queue = []
    faults = 0

    for page in pages:
        if page not in queue:
            if len(queue) < frames:
                queue.append(page)
            else:
                queue.pop(0)
                queue.append(page)
            faults += 1

    return faults

def lru(frames, pages):
    queue = []
    faults = 0

    for page in pages:
        if page not in queue:
            if len(queue) < frames:
                queue.append(page)
            else:
                queue.pop(0)
                queue.append(page)
            faults += 1
        else:
            queue.remove(page)
            queue.append(page)

    return faults

def optimal(frames, pages):
    queue = []
    faults = 0

    for i, page in enumerate(pages):
        if page not in queue:
            if len(queue) < frames:
                queue.append(page)
            else:
                future_use = {p: float("inf") for p in queue}
                for j in range(i + 1, len(pages)):
                    if pages[j] in future_use and future_use[pages[j]] == float("inf"):
                        future_use[pages[j]] = j
                page_to_replace = max(future_use, key=future_use.get)
                queue.remove(page_to_replace)
                queue.append(page)
            faults += 1

    return faults
