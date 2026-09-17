import argparse
import shutil
import sqlite3
from pathlib import Path


INVALID_FILENAME_CHARS = '<>:"/\\|?*'


def sanitize_filename(name: str) -> str:
    cleaned = "".join("_" if ch in INVALID_FILENAME_CHARS else ch for ch in name.strip())
    cleaned = cleaned.rstrip(". ")
    return cleaned or "unnamed_card"


def iter_cards(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, image_path FROM Cards ORDER BY id")
        yield from cur.fetchall()
    finally:
        conn.close()


def copy_placeholder(source_image: Path, target_path: Path):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_image, target_path)


def build_targets(card, mode: str, source_suffix: str, names_dir: Path):
    targets = []

    if mode in {"image-path", "both"}:
        image_path = (card["image_path"] or "").strip()
        if image_path:
            targets.append(Path(image_path))

    if mode in {"card-name", "both"}:
        card_name = sanitize_filename(card["name"] or f"card_{card['id']}")
        targets.append(names_dir / f"{card_name}{source_suffix}")

    return targets


def main():
    parser = argparse.ArgumentParser(
        description="Create placeholder copies for every card from data/cards.db."
    )
    parser.add_argument("placeholder", help="Path to the source placeholder image.")
    parser.add_argument("--db", default="data/cards.db", help="Path to data/cards.db.")
    parser.add_argument(
        "--mode",
        choices=["image-path", "card-name", "both"],
        default="image-path",
        help="`image-path` matches the app paths, `card-name` uses card names, `both` does both.",
    )
    parser.add_argument(
        "--names-dir",
        default="placeholder_by_name",
        help="Output directory for `card-name` mode.",
    )
    args = parser.parse_args()

    root = Path.cwd()
    db_path = (root / args.db).resolve()
    source_image = Path(args.placeholder).resolve()
    names_dir = (root / args.names_dir).resolve()

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    if not source_image.exists():
        raise FileNotFoundError(f"Placeholder image not found: {source_image}")

    created = 0
    skipped = 0
    seen = set()

    for card in iter_cards(db_path):
        for target in build_targets(card, args.mode, source_image.suffix or ".jpg", names_dir):
            target_path = (root / target).resolve()
            if target_path in seen:
                skipped += 1
                continue

            seen.add(target_path)
            copy_placeholder(source_image, target_path)
            created += 1

    print(f"Created: {created}")
    print(f"Skipped duplicates: {skipped}")


if __name__ == "__main__":
    main()
