import re
import os

INPUT_FILE = "combined_documentation.md"
OUTPUT_FILE = "cleaned_documentation.md"

def clean_markdown_file():
    """
    Cleans the combined markdown file by removing redundant headers, footers,
    and other non-content elements scraped from the website.
    """
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as infile:
        content = infile.read()

    # 1. Remove the entire repetitive GitBook header/navigation block.
    # This pattern looks for the block starting with [![Logo] and ending with the first
    # major content heading (which is kept).
    gitbook_header_pattern = re.compile(
        r'\[!\[Logo\]\(https?.*?\)\]\(https?.*?\).*?Powered by GitBook.*?\nCopy\n',
        re.DOTALL
    )
    cleaned_content = gitbook_header_pattern.sub('', content)

    # 2. Remove navigation elements like [Previous...][Next...] and "Last updated..."
    nav_pattern = re.compile(r'\[Previous.*?\]\(.*?\)|\[Next.*?\]\(.*?\)|Last updated .*? ago\n', re.DOTALL)
    cleaned_content = nav_pattern.sub('', cleaned_content)

    # 3. Remove standalone "Copy" text, often found after code blocks or headers.
    copy_pattern = re.compile(r'\nCopy\n')
    cleaned_content = copy_pattern.sub('\n', cleaned_content)

    # 4. Remove keyboard shortcuts like `Ctrl``k`
    shortcut_pattern = re.compile(r'`Ctrl``k`|`⌘``k`')
    cleaned_content = shortcut_pattern.sub('', cleaned_content)

    # 5. Remove any remaining image-only links that might be left.
    image_link_pattern = re.compile(r'\[!\[.*?\]\(.*?\)\]\(.*?\)\n')
    cleaned_content = image_link_pattern.sub('', cleaned_content)

    # 6. Normalize excessive newlines to a maximum of two.
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content).strip()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        outfile.write(cleaned_content)

    print(f"Successfully cleaned '{INPUT_FILE}' and saved it as '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    clean_markdown_file()