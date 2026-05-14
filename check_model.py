import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\RAVI KIRAN\mini_project\namasthe-boss.ipynb', 'r', encoding='utf-8', errors='ignore') as f:
    nb = json.load(f)

print("=== Training Results from Notebook ===\n")
keywords = ['acc', 'accuracy', 'loss', 'epoch', 'val', 'test', 'f1', 'best', 'precision', 'recall']

for i, cell in enumerate(nb.get('cells', [])):
    outputs = cell.get('outputs', [])
    for out in outputs:
        text = ''
        if 'text' in out:
            text = ''.join(out['text'])
        elif 'data' in out:
            text = ''.join(out['data'].get('text/plain', []))
        
        if text and any(k.lower() in text.lower() for k in keywords):
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            relevant = [l for l in lines if any(k.lower() in l.lower() for k in keywords)]
            if relevant:
                print(f"Cell {i}:")
                for l in relevant[:15]:
                    try:
                        print(f"  {l.encode('ascii','replace').decode('ascii')}")
                    except:
                        pass
                print()
