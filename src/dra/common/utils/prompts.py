# Common prompt utilities
from pathlib import Path
import re

def split_frontmatter_and_content(frontmatter_and_content: str) -> (str, str):
    """
    Split the frontmatter from the content, returning both in a tuple. The 
    expected format is the following:
    ```
    ---
    frontmatter
    ---
    content
    ```
    Where the expected delimiter is three or more dashes on separate lines, before and
    after the frontmatter, e.g., matching regex `\n?---\\s*\n`. If there is no 
    frontmatter block, (including the case where only one string matching `---\\s*\n` 
    is found in the text), then the first string returned will be `None` and
    the second string will contain the entire input `frontmatter_and_content`. 
    If the first returned string is empty, it means there was frontmatter, 
    but it was empty!
    If there is text before the frontmatter, it will be ignored!
    """

    parts = re.split(r'\n?---+\s*\n', frontmatter_and_content, maxsplit=2)
    if len(parts) == 3:
        return parts[1], parts[2]
    else:
        return None, frontmatter_and_content

def load_prompt_markdown(path: Path) -> str:
    """
    Load a markdown prompt file and return the content after the frontmatter.
    """
    
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    
    with path.open('r', encoding='utf-8') as f:
        content = f.read()
        frontmatter, content = split_frontmatter_and_content(content)
        return content
