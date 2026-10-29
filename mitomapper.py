"""Split FASTA records into individual files and create a mapping CSV."""

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from pathlib import Path
import re
import sys


@dataclass
class Record:
    identifier: str
    taxon: str
    lines: list[str]


def validate_identifier(identifier: str) -> None:
    """Require an identifier usable as a filename on Windows."""
    reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    reserved.update(f"{prefix}{number}" for prefix in ("COM", "LPT")
                    for number in "123456789¹²³")
    if (identifier in {".", ".."}
            or identifier.endswith((".", " "))
            or re.search(r'[<>:"/\\|?*\x00-\x1f]', identifier)
            or identifier.split(".", 1)[0].upper() in reserved
            or len((identifier + ".fasta").encode("utf-16-le")) // 2 > 255):
        raise ValueError(f"Sequence ID cannot safely form a Windows filename: {identifier!r}")


def read_records(input_path: Path) -> list[Record]:
    records = []
    has_sequence = False
    with input_path.open(encoding="utf-8-sig", newline="") as source:
        for line_number, line in enumerate(source, 1):
            if line.startswith(">"):
                if records and not has_sequence:
                    raise ValueError(f"Empty sequence for ID {records[-1].identifier!r}")
                header = line[1:].rstrip("\r\n")
                tokens = header.split()
                if not tokens:
                    raise ValueError(f"Missing sequence ID at line {line_number}")
                identifier = tokens[0]
                validate_identifier(identifier)
                organism = re.search(r"\[orgn=([^\]]*)\]", header)
                records.append(Record(identifier, organism.group(1) if organism else "", [line]))
                has_sequence = False
            elif records:
                records[-1].lines.append(line)
                has_sequence = has_sequence or bool(line.strip())
            elif line.strip():
                raise ValueError(f"Sequence content before the first FASTA header at line {line_number}")
    if not records:
        raise ValueError("Input contains no FASTA records")
    if not has_sequence:
        raise ValueError(f"Empty sequence for ID {records[-1].identifier!r}")

    counts = Counter(record.identifier for record in records)
    duplicates = [identifier for identifier, count in counts.items() if count > 1]
    if duplicates:
        raise ValueError("Duplicate sequence IDs found: " + ", ".join(duplicates))
    names: dict[str, list[str]] = {}
    for record in records:
        names.setdefault(record.identifier.casefold(), []).append(record.identifier)
    collisions = [", ".join(ids) for ids in names.values() if len(ids) > 1]
    if collisions:
        raise ValueError("Sequence IDs have conflicting Windows filenames: " + "; ".join(collisions))
    return records


def split_fasta(input_path: Path, output_dir: Path) -> int:
    """Validate the entire input before creating any output files."""
    records = read_records(input_path)
    filenames = ["map", *(record.identifier + ".fasta" for record in records)]
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"Output directory is not a directory: {output_dir}")
        existing = {path.name.casefold() for path in output_dir.iterdir()}
        conflicts = [name for name in filenames if name.casefold() in existing]
        if conflicts:
            raise ValueError("Output files already exist: " + ", ".join(conflicts))
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for record in records:
            destination = output_dir / (record.identifier + ".fasta")
            with destination.open("x", encoding="utf-8", newline="") as target:
                created.append(destination)
                target.writelines(record.lines)
        map_path = output_dir / "map"
        with map_path.open("x", encoding="utf-8", newline="") as target:
            created.append(map_path)
            writer = csv.writer(target)
            writer.writerow(["ID", "Taxon", "R1", "R2", "Assembly"])
            writer.writerows([record.identifier, record.taxon, "", "", record.identifier + ".fasta"]
                             for record in records)
    except OSError:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return len(records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input FASTA file")
    parser.add_argument("output_dir", type=Path, help="Output directory")
    args = parser.parse_args(argv)
    try:
        count = split_fasta(args.input, args.output_dir)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {count} sequences and map to {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
