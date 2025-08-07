#!/bin/bash

# Initialize exclude patterns
EXCLUDE_FILES=()
EXCLUDE_PATHS=()

# Argument parsing
TARGET_DIR="."
while [[ $# -gt 0 ]]; do
    case "$1" in
        --exclude-file)
            EXCLUDE_FILES+=("$2")
            shift 2
            ;;
        --exclude-path)
            EXCLUDE_PATHS+=("$2")
            shift 2
            ;;
        *)
            TARGET_DIR="$1"
            shift
            ;;
    esac
done

# Ensure target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Directory '$TARGET_DIR' does not exist."
    exit 1
fi

# Output file setup
OUTPUT="combined_output.md"
SCRIPT="$(basename "$0")"
OUTPUT_PATH="$TARGET_DIR/$OUTPUT"
> "$OUTPUT_PATH"

# Add tree visualization at the top
echo "# Directory tree for '$TARGET_DIR'" >> "$OUTPUT_PATH"
echo '```' >> "$OUTPUT_PATH"
tree_ignore=".git|__pycache__|*.png|*.jpg|*.jpeg|*.gif|*.bmp|*.webp|*.ico|.env|*.md|combined_output.md|node_modules|dist|combine.sh"
for name in "${EXCLUDE_FILES[@]}"; do
    tree_ignore="$tree_ignore|$name"
done
tree -a -I "$tree_ignore" "$TARGET_DIR" >> "$OUTPUT_PATH"
echo '```' >> "$OUTPUT_PATH"
echo "" >> "$OUTPUT_PATH"

# Build find exclusion expression
FIND_CMD=(find "$TARGET_DIR" -type f)

# Always exclude output and script itself
FIND_CMD+=(
    ! -name "$SCRIPT"
    ! -name "$OUTPUT"
    ! -path "*/.git/*"
    ! -path "*/__pycache__/*"
    ! -path "*/dist/*"
    ! -name "*.png"
    ! -name "*.jpg"
    ! -name "style.css"
    ! -name "*package-lock.json"
    ! -name "*.jpeg"
    ! -name "*.gif"
    ! -name "*.md"
    ! -name "*.bmp"
    ! -name "*.webp"
    ! -name "*.ico"
    ! -name ".env"
    ! -path "*/node_modules/*"
)

# Add custom --exclude-file
for name in "${EXCLUDE_FILES[@]}"; do
    FIND_CMD+=( ! -name "$name" )
done

# Add custom --exclude-path
for path in "${EXCLUDE_PATHS[@]}"; do
    FIND_CMD+=( ! -path "*$path*" )
done

# Run the find command and process files
"${FIND_CMD[@]}" | sort | while read -r FILE; do
    if file "$FILE" | grep -qE 'text|ASCII|JavaScript|CSS|HTML'; then
        REL_PATH="${FILE#$TARGET_DIR/}"
        echo "// < $REL_PATH >" >> "$OUTPUT_PATH"
        cat "$FILE" >> "$OUTPUT_PATH"
        echo -e "\n" >> "$OUTPUT_PATH"
    fi
done

echo "✅ All text files concatenated into $OUTPUT_PATH"
