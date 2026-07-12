import csv
import io
from typing import Dict, Any, List

import chardet


COMMON_DELIMITERS = ["|", ",", "\t", ";"]


def detect_encoding(content_bytes: bytes) -> str:
    detected = chardet.detect(content_bytes)
    encoding = detected.get("encoding") or "utf-8"
    return encoding


def detect_delimiter(sample_text: str) -> str:
    lines = [line for line in sample_text.splitlines() if line.strip()]

    if not lines:
        return "|"

    scores = {}

    for delimiter in COMMON_DELIMITERS:
        counts = [line.count(delimiter) for line in lines[:20]]
        non_zero = [count for count in counts if count > 0]

        if non_zero:
            scores[delimiter] = sum(non_zero)

    if not scores:
        return "|"

    return max(scores, key=scores.get)


def inspect_flat_file(content_bytes: bytes) -> Dict[str, Any]:
    encoding = detect_encoding(content_bytes)
    text = content_bytes.decode(encoding, errors="replace")

    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    delimiter = detect_delimiter("\n".join(non_empty_lines[:20]))

    column_counts: List[int] = []

    for line in non_empty_lines[:50]:
        column_counts.append(len(line.split(delimiter)))

    return {
        "encoding": encoding,
        "detected_delimiter": delimiter,
        "total_lines": len(lines),
        "non_empty_lines": len(non_empty_lines),
        "sample_column_counts": column_counts[:10],
        "likely_column_count": max(set(column_counts), key=column_counts.count)
        if column_counts else 0,
    }


def convert_flat_file_bytes_to_windows_csv(
    content_bytes: bytes,
    delimiter: str | None = None,
    input_encoding: str | None = None
) -> Dict[str, Any]:
    """
    Converts Linux flat file bytes into Windows-friendly CSV bytes.

    Output:
    - comma-delimited CSV
    - UTF-8 BOM for Excel compatibility
    - CRLF Windows line endings
    - proper CSV quoting
    """

    encoding = input_encoding or detect_encoding(content_bytes)
    text = content_bytes.decode(encoding, errors="replace")

    selected_delimiter = delimiter or detect_delimiter(text)

    input_stream = io.StringIO(text)
    output_stream = io.StringIO(newline="")

    reader = csv.reader(input_stream, delimiter=selected_delimiter)
    writer = csv.writer(
        output_stream,
        delimiter=",",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\r\n",
    )

    row_count = 0
    max_columns = 0
    min_columns = None

    for row in reader:
        writer.writerow(row)
        row_count += 1

        column_count = len(row)
        max_columns = max(max_columns, column_count)
        min_columns = column_count if min_columns is None else min(min_columns, column_count)

    csv_text = output_stream.getvalue()

    # utf-8-sig adds BOM so Excel opens it cleanly
    csv_bytes = csv_text.encode("utf-8-sig")

    return {
        "csv_bytes": csv_bytes,
        "row_count": row_count,
        "delimiter_used": selected_delimiter,
        "input_encoding": encoding,
        "min_columns": min_columns or 0,
        "max_columns": max_columns,
    }