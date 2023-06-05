import sys, requests, json

parcela = sys.argv[1]
print(f'Buscando polígonos para la parcela {parcela}')
print(f'PARCELA     POLÍGONO       SUPERFICIE')

for poligono in range(1,70):
    url = f'https://sigpac.mapama.gob.es/fega/serviciosvisorsigpac/layerinfo?layer=parcela&id=49,135,0,0,{poligono},{parcela}'
    
    response = requests.get(url)
    if response.status_code > 399:
        print(f'ERROR: {response.status_code} HTTP code')
        continue
    
    res_json = json.loads(response.content)
    if res_json['query'] == []:
        continue

    area = float(res_json['parcelaInfo']['dn_surface'])

    print(f'{parcela}        {poligono}             {area:.0f}m²')
