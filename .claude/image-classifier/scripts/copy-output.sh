#!/usr/bin/env bash
# Usage: copy-output.sh <input_folder> <principal_filename> [gallery_file1] [gallery_file2] ...
# Copies the principal image and selected gallery images to <input_folder>/output/

INPUT_FOLDER="$1"
PRINCIPAL_FILENAME="$2"
shift 2  # Remove first two arguments, remaining are gallery files

if [[ -z "$INPUT_FOLDER" || -z "$PRINCIPAL_FILENAME" ]]; then
  echo "Usage: $0 <input_folder> <principal_filename> [gallery_file1] [gallery_file2] ..." >&2
  exit 1
fi

OUTPUT="$INPUT_FOLDER/output"
PRINCIPAL_FILE="$INPUT_FOLDER/$PRINCIPAL_FILENAME"
EXT="${PRINCIPAL_FILENAME##*.}"

# Create/clean output folder
rm -rf "$OUTPUT" && mkdir -p "$OUTPUT"

# Copy principal
if [[ ! -f "$PRINCIPAL_FILE" ]]; then
  echo "Error: Principal file not found: $PRINCIPAL_FILE" >&2
  exit 1
fi
cp -p "$PRINCIPAL_FILE" "$OUTPUT/imagen principal.$EXT"

# Copy gallery images in the order provided
i=1
for gallery_file in "$@"; do
  # Skip if this is the principal (shouldn't happen, but be safe)
  if [[ "$gallery_file" == "$PRINCIPAL_FILENAME" ]]; then
    continue
  fi

  gallery_path="$INPUT_FOLDER/$gallery_file"
  if [[ ! -f "$gallery_path" ]]; then
    echo "Warning: Gallery file not found, skipping: $gallery_file" >&2
    continue
  fi

  file_ext="${gallery_file##*.}"
  cp -p "$gallery_path" "$OUTPUT/galeria$i.$file_ext"
  i=$((i+1))
done

echo "Copied principal and $((i-1)) gallery images to $OUTPUT"
