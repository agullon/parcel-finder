import screenshot, handlers

import logging as log
import requests, json, math, utm
import xml.etree.ElementTree as ET
from geopy.distance import geodesic as geo_distance

async def find_parcel_from_coordinates(update, context):
    coordinates = await get_user_coordinates(update, context)
    log.info(f'user coordinated: {coordinates}')
    x_coor, y_coor, _, _ = utm.from_latlon(coordinates[0], coordinates[1])
    log.info(f'UTM coordinates: x={x_coor} y={y_coor}')
    url = f'http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx/Consulta_RCCOOR?Coordenada_X={x_coor}&Coordenada_Y={y_coor}&SRS=EPSG%3A32629'
    log.info(f'Catastro API requested url: {url}')
    response = requests.get(url).content
    log.info(f'Catastro API response: {response}')
    response_parsed = ET.fromstring(response).find('.//ns:ldt', {'ns': 'http://www.catastro.meh.es/'}).text.split(' ')
    
    poligono = context.user_data['poligono'] = response_parsed[1]
    parcela = context.user_data['parcela'] = response_parsed[3]

    paraje, area, slope, error = get_info(poligono, parcela) 
    if error:
        text = f'Ha habido un error: {error}'
        context.user_data['poligono'] = None
        context.user_data['parcela'] = None
    else:
        text = f'Estás en la parcela {parcela} y el polígono {poligono}, el paraje es \'{paraje}\', tiene {area:.0f}m² de superficie y un {slope:.0f}% de pendiente'
    await update.message.reply_text(f'{text}')
    await update.message.reply_text('¿Qué quieres saber?', reply_markup=handlers.options_keyboard)

async def get_user_coordinates(update, context):
    user_location = update.message.location
    coordinates = (user_location.latitude, user_location.longitude)
    log.info(f'Coordinates: {coordinates[0]}, {coordinates[1]}')
    return coordinates

async def calculate_distance(update, context, coordinates=None):
    # get origin coordinates
    origen_coordinates = coordinates if coordinates else await get_user_coordinates(update, context)

    # get destination coordinates
    poligono = context.user_data.get('poligono')
    parcela = context.user_data.get('parcela')

    jcyl_info, jcyl_error = get_catastro_jcyl(poligono, parcela)
    if jcyl_error:
        log.error(jcyl_error)
        context.user_data['poligono'] = None
        context.user_data['parcela'] = None
        return f'Ha habido un error: {jcyl_error}'
    destination_coordinates = get_parcela_coordinates(jcyl_info)
    log.info(f'Destination coordinates: {destination_coordinates[0]}, {destination_coordinates[1]}')
    
    # get distance
    distance = geo_distance(origen_coordinates, destination_coordinates).meters
    distance_text = print_distance(distance)

    # get direction
    degrees = get_direction(origen_coordinates, destination_coordinates)
    direction_text = print_direction(degrees)

    # return information
    return f'La parcela está a {distance_text} al {direction_text}'

def get_catastro_jcyl(poligono, parcela):
    url = f'https://idecyl.jcyl.es/vcig/proxy.php?url=https%3A%2F%2Fovc.catastro.meh.es%2Fovcservweb%2FOVCSWLocalizacionRC%2FOVCCoordenadas.asmx%2FConsulta_CPMRC%3FSRS%3DEPSG%3A4326%26Provincia%3D%26Municipio%3D%26RC%3D49135A0{poligono.zfill(2)}{parcela.zfill(5)}'
    log.info(f'idecyl.jcyl.es requested url:\n{url}')
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e: 
        log.error(f'Server returned error:\n {e}')
        return None, 'No se ha podido consultar la parcela y polígono en el Catastro'
    
    log.info(f'idecyl.jcyl.es info:\n {response.content}')
    if response.status_code > 399:
        log.error(f'Server returned {response.status_code} HTTP code')
        return None, 'No se ha podido consultar la parcela y polígono en el Catastro'
    return ET.fromstring(response.content), None

def get_catastro_sigpac(poligono, parcela):
    url = f'https://sigpac.mapama.gob.es/fega/serviciosvisorsigpac/layerinfo?layer=parcela&id=49,135,0,0,{poligono},{parcela}'
    log.info(f'sigpac.mapama.gob.es requested url:\n{url}')
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e: 
        log.error(f'Server returned error:\n {e}')
        return None, 'No se ha podido consultar la parcela y polígono en el Catastro'
    
    log.info(f'sigpac.mapama.gob.es info:\n{response.content}')
    if response.status_code > 399:
        log.error(f'Server returned {response.status_code} HTTP code')
        return None, 'No se ha podido consultar la parcela y polígono en el Catastro'
    res_json = json.loads(response.content)

    if res_json['query'] == []:
        log.error(f'Parcel does not exist: poligono={poligono} parcela={parcela}')
        return None, f'No se han encontrado la parcela y el polígono en el Catastro'
    return res_json, None

def get_parcela_coordinates(catastro_info):
    namespace = {'ns': 'http://www.catastro.meh.es/'}
    longitude = catastro_info.find('.//ns:xcen', namespace).text
    latitude = catastro_info.find('.//ns:ycen', namespace).text
    return (float(latitude), float(longitude))

def get_paraje(catastro_info):
    namespace = {'ns': 'http://www.catastro.meh.es/'}
    return catastro_info.find('.//ns:ldt', namespace).text

def get_detailed_info(sigpac_info):
    area =  float(sigpac_info['parcelaInfo']['dn_surface'])

    avg_slope = 0
    for recinto in sigpac_info['query']:
        avg_slope += recinto['pendiente_media']
    slope = float(avg_slope / len(sigpac_info['query']))
    
    return area, slope

def get_ref_catastral(sigpac_info):
    return sigpac_info['parcelaInfo']['referencia_cat']

def print_distance(distance):
    if distance > 1000:
        distance = distance / 1000
        if distance >= 10:
            return f"{distance:.0f} km"
        elif distance < 10:
            return f"{distance:.1f} km".replace('.', ',')
    else:
        return f"{distance:.0f} metros"

def get_direction(org, dest):
    deltaX = dest[0] - org[0]
    deltaY = dest[1] - org[1]
    degrees = math.atan2(deltaX, deltaY)/math.pi*180
    if degrees < 0:
        return degrees+360
    elif degrees > 360:
        return degrees-360
    else:
        return degrees

def print_direction(degrees):
    log.info(f'Direction degrees: {degrees}')
    compass = ['este', 'noreste', 'norte', 'noroeste', 'oeste', 'suroeste', 'sur', 'sureste', 'este']
    return compass[round(degrees/45)]

def get_info(poligono, parcela):
    jcyl_info, jcyl_error = get_catastro_jcyl(poligono, parcela)
    if jcyl_error:
        return None, None, None, jcyl_error
    
    sigpac_info, sigpac_error = get_catastro_sigpac(poligono, parcela)
    if sigpac_error:
        return None, None, None, sigpac_error

    paraje = get_paraje(jcyl_info).split(f'{parcela} ')[1].split('.')[0].title()
    area, slope = get_detailed_info(sigpac_info)
    slope = slope/10

    return paraje, area, slope, None

def take_screenshot(ref_catastral):
    path_small_image, path_large_image = screenshot.take_screenshoot(ref_catastral)
    return path_small_image, path_large_image

async def monitor_user_actions(message_text):
    import os
    import telegram
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_DEV")
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id='5374343', text=message_text)
