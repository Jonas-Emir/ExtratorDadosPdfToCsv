import re

linhas = [
    "1 29/04 ITALIA PANIFICADORA 3,06",
    "1 29/04 MILIUM 3,90",
    "1 23/05 CASADOCHINEQUE 14,50",
]

regex = r'(\d{2}/\d{2})\s+(.*)\s+(-?[\d.,]+)$'

for linha in linhas:
    m = re.search(regex, linha)
    if m:
        print("✅ Match:", m.groups())
    else:
        print("❌ Falhou:", linha)
