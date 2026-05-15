import os
import glob
import re

for filepath in glob.glob("frontend/src/components/*.vue"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remove HTML comments that are immediately after <template>
    # We look for <template> followed by optional whitespace/newlines, then a comment
    # We replace it by just <template>
    new_content = re.sub(r'(<template>)\s*<!--.*?-->\s*', r'\1\n  ', content, flags=re.DOTALL)
    
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed {filepath}")

