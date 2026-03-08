import os
import glob

directory = 'c:/Users/Kartikey/Desktop/Bytebit-Ai/src/screens'
files = glob.glob(f"{directory}/**/*.jsx", recursive=True)

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the missing interpolation brace
    new_content = content.replace("`process.env.REACT_APP_API_URL/", "`${process.env.REACT_APP_API_URL}/")
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {file}")
