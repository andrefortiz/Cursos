import duckduckgo

for r in duckduckgo.query('Sausages').results:
    if 'Text' in r:
        print(r['FirstURL'] + ' - ' + r['Text'])


