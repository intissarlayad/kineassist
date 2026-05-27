import re

def patch(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changed = False
    
    # Insert material icons fix
    if '.stIconMaterial' not in content:
        content = re.sub(
            r'(\*, html, body, \[class\*="css"\]\s*\{[^\}]*\})',
            r'\1\n        .stIconMaterial, .material-symbols-rounded { font-family: \'Material Symbols Rounded\' !important; }',
            content
        )
        changed = True
    
    # Hide radio dots
    if 'data-baseweb="radio"' not in content:
        content = re.sub(
            r'(\[role="radiogroup"\] label\s*\{[^\}]*\})',
            r'\1\n        [role="radiogroup"] div[data-baseweb="radio"] > div:first-child { display: none !important; }',
            content
        )
        changed = True
    
    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Patched {file_path}')

patch('app.py')
patch('auth.py')
patch('pages/1_Dashboard_Kine.py')
