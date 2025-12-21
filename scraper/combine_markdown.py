import os

INPUT_DIR = "scraped_site"
OUTPUT_FILE = "combined_documentation.md"

def combine_markdown_files():
    """
    Concatenates all markdown files from the input directory into a single
    output file, with each file's content preceded by its filename as a title.
    """
    md_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.md')]
    
    if not md_files:
        print(f"No markdown files found in '{INPUT_DIR}'.")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        for filename in sorted(md_files): # Sorting for consistent order
            filepath = os.path.join(INPUT_DIR, filename)
            
            # Add the original filename as a title
            outfile.write(f"# {filename}\n\n")
            
            with open(filepath, "r", encoding="utf-8") as infile:
                outfile.write(infile.read())
            
            # Add a separator for clarity between files
            outfile.write("\n\n---\n\n")
    
    print(f"Successfully combined {len(md_files)} files into '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    combine_markdown_files()