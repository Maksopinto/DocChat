"""Збірка контексту для AI: об'єднуємо знайдені шматки та їхніх сусідів у зв'язні блоки."""


def merge_blocks(records: list[dict]) -> list[dict]:
    """Приймає шматки {source, idx, page, text}, повертає блоки.

    - дублікати (той самий документ і номер шматка) прибираються;
    - шматки, що йдуть підряд, склеюються в один блок;
    - у блоці зберігається діапазон сторінок.
    """
    unique = {(r["source"], r["idx"]): r for r in records}
    ordered = sorted(unique.values(), key=lambda r: (r["source"], r["idx"]))

    blocks: list[dict] = []
    for r in ordered:
        last = blocks[-1] if blocks else None
        if last and last["source"] == r["source"] and last["last_idx"] == r["idx"] - 1:
            # якщо сторінка змінилась, ставимо позначку, щоб AI міг вказати точну сторінку
            if r["page"] != last["cur_page"]:
                last["text"] += f" [стор. {r['page']}] "
            else:
                last["text"] += " "
            last["text"] += r["text"]
            last["page_to"] = max(last["page_to"], r["page"])
            last["cur_page"] = r["page"]
            last["last_idx"] = r["idx"]
        else:
            blocks.append({
                "source": r["source"],
                "page_from": r["page"],
                "page_to": r["page"],
                "cur_page": r["page"],
                "last_idx": r["idx"],
                "text": r["text"],
            })
    return blocks


def pages_label(block: dict) -> str:
    if block["page_from"] == block["page_to"]:
        return f"стор. {block['page_from']}"
    return f"стор. {block['page_from']}-{block['page_to']}"


def format_context(blocks: list[dict]) -> str:
    parts = []
    for n, b in enumerate(blocks, start=1):
        parts.append(f"[Фрагмент {n}: {b['source']}, {pages_label(b)}]\n{b['text']}")
    return "\n\n".join(parts)
