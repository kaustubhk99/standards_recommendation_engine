"""Chunker module for splitting documents into manageable pieces."""

import re
import json
from typing import List, Dict
from pathlib import Path

# -----------------------------
# CONFIGURATION
# -----------------------------

CLAUSE_REGEX = re.compile(r"^(\d+(\.\d+){0,4})\s+", re.MULTILINE)

MANDATORY_KEYWORDS = ["shall", "shall not", "is required to"]
CONDITIONAL_KEYWORDS = ["if", "where", "in case"]
TEST_KEYWORDS = ["shall be tested", "test shall", "verification shall"]
SCOPE_KEYWORDS = ["this standard applies", "this document specifies", "scope"]
EXCLUSION_KEYWORDS = ["does not apply", "is not covered", "excluded"]

MIN_TOKENS = 80
MAX_TOKENS = 900


# -----------------------------
# HELPERS
# -----------------------------

def tokenize(text: str) -> int:
    return len(text.split())


def classify_section(text: str) -> str:
    text_lower = text.lower()

    if any(k in text_lower for k in SCOPE_KEYWORDS):
        return "scope"
    if any(k in text_lower for k in EXCLUSION_KEYWORDS):
        return "exclusion"
    if any(k in text_lower for k in TEST_KEYWORDS):
        return "test_requirement"
    if any(k in text_lower for k in MANDATORY_KEYWORDS):
        if any(k in text_lower for k in CONDITIONAL_KEYWORDS):
            return "conditional_requirement"
        return "mandatory_requirement"
    return "informative_note"


def split_by_clause(text: str) -> List[Dict]:
    matches = list(CLAUSE_REGEX.finditer(text))
    clauses = []

    for i, match in enumerate(matches):
        clause_id = match.group(1)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        clause_text = text[start:end].strip()

        clauses.append({
            "clause_id": clause_id,
            "text": clause_text
        })

    return clauses


def merge_small_clauses(clauses: List[Dict]) -> List[Dict]:
    merged = []
    buffer = None

    for clause in clauses:
        token_count = tokenize(clause["text"])

        if token_count < MIN_TOKENS:
            if buffer:
                buffer["text"] += "\n" + clause["text"]
            else:
                buffer = clause
        else:
            if buffer:
                merged.append(buffer)
                buffer = None
            merged.append(clause)

    if buffer:
        merged.append(buffer)

    return merged


# -----------------------------
# MAIN CHUNKING FUNCTION
# -----------------------------

def chunk_document(
    text: str,
    standard_name: str,
    edition: str
) -> List[Dict]:
    raw_clauses = split_by_clause(text)
    clauses = merge_small_clauses(raw_clauses)

    chunks = []

    for clause in clauses:
        token_count = tokenize(clause["text"])

        if token_count > MAX_TOKENS:
            continue  # Skip overly large blocks for safety

        section_type = classify_section(clause["text"])

        chunk = {
            "chunk_id": f"{standard_name}_{clause['clause_id']}",
            "standard": standard_name,
            "edition": edition,
            "clause_id": clause["clause_id"],
            "parent_clause": clause["clause_id"].rsplit(".", 1)[0],
            "section_type": section_type,
            "text": clause["text"],
            "token_count": token_count
        }

        chunks.append(chunk)

    return chunks


# -----------------------------
# CLI ENTRY POINT
# -----------------------------

def run_chunking(
    input_file: Path,
    output_file: Path,
    standard_name: str,
    edition: str
):
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_document(text, standard_name, edition)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    print(f"Chunking completed: {len(chunks)} chunks created")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Standards PDF Chunker")
    parser.add_argument("--input", required=True, help="Extracted text file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--standard", required=True, help="Standard name")
    parser.add_argument("--edition", required=True, help="Edition / Year")

    args = parser.parse_args()

    run_chunking(
        Path(args.input),
        Path(args.output),
        args.standard,
        args.edition
    )

