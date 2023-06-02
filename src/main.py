import screenshot

import logging as log
import requests, json, locale, math, sys, utm
import xml.etree.ElementTree as ET
from geopy.distance import geodesic as geo_distance
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

locale.setlocale(locale.LC_ALL, 'es_ES')
log.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=log.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Telegram bot token
TOKEN = open('/etc/telegram-bot-token/telegram-bot-token', 'r').read().strip()
log.info(f'{TOKEN}')

KEYBOARD_OPTIONS = dict(
    navigate='navigate',
    photo='photo',
    new_search='new_search',
)

options_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton('Cómo ir a la parcela', callback_data=KEYBOARD_OPTIONS['navigate'])],
                [InlineKeyboardButton('Una foto de la parcela', callback_data=KEYBOARD_OPTIONS['photo'])],
                [InlineKeyboardButton('Nueva búsqueda', callback_data=KEYBOARD_OPTIONS['new_search'])],
            ])
search_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton('Nueva búsqueda', callback_data=KEYBOARD_OPTIONS['new_search'])],
            ])
remove_keyboard = InlineKeyboardMarkup([])

async def start(update, context):
    await update.message.reply_text(text='Escribe el número de la parcela o envía tu ubicación para saber en qué parcela estás', reply_markup=search_keyboard)

async def InlineKeyboardHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poligono = context.user_data.get('poligono')
    parcela = context.user_data.get('parcela')

    option = update.callback_query.data
    if option == KEYBOARD_OPTIONS['navigate']:
        sigpac_info = get_catastro_sigpac(poligono, parcela)
        if not sigpac_info:
            await update.callback_query.edit_message_text(text='Ha habido un error, comprueba que la parcel y polígono son correctos. Inténtalo de nuevo más tarde.')
            context.user_data['poligono'] = None
            context.user_data['parcela'] = None
            await update.callback_query.message.reply_text(text='Escribe el número de la parcela o envía tu ubicación para saber en qué parcela estás', reply_markup=search_keyboard)
            return
        await update.callback_query.edit_message_text(text=f'{await calculate_distance(update, context, (41.9986276,-6.3471484))} de la iglesia de Fresno')
        await update.callback_query.message.reply_text(text='Envíame una ubicación para obtener indicaciones sobre cómo ir desde cualquier sitio')
        await update.callback_query.message.reply_text(text='¿Qué más quieres saber?', reply_markup=options_keyboard)
    elif option == KEYBOARD_OPTIONS['photo']:
        sigpac_info = get_catastro_sigpac(poligono, parcela)
        if not sigpac_info:
            await update.callback_query.edit_message_text(text='Ha habido un error, comprueba que la parcel y polígono son correctos. Inténtalo de nuevo más tarde.')
            context.user_data['poligono'] = None
            context.user_data['parcela'] = None
            await update.callback_query.edit_message_text(text='Escribe el número de la parcela o envía tu ubicación para saber en qué parcela estás', reply_markup=search_keyboard)
            return
        await update.callback_query.edit_message_text(text='Por favor, espera unos segundos para recibir imágenes de la parcela')
        ref_catastral = get_ref_catastral(sigpac_info)
        path_small_image, path_large_image = take_screenshot(ref_catastral)
        await update.callback_query.message.reply_photo(photo=open(path_small_image, 'rb'))
        await update.callback_query.message.reply_photo(photo=open(path_large_image, 'rb'))
        screenshot.delete_images(path_small_image, path_large_image)
        await update.callback_query.message.reply_text(text='¿Qué más quieres saber?', reply_markup=options_keyboard)
    elif option == KEYBOARD_OPTIONS['new_search']:
        context.user_data['poligono'] = None
        context.user_data['parcela'] = None
        await update.callback_query.message.reply_text(text='Escribe el número de la parcela o envía tu ubicación para saber en qué parcela estás', reply_markup=search_keyboard)

async def location_handle(update, context):
    pol_empty = True if not context.user_data.get('poligono') else False
    par_empty = True if not context.user_data.get('parcela') else False

    log.info(f'pol_empty={pol_empty}')
    log.info(f'par_empty={par_empty}')

    if pol_empty and pol_empty:
        await find_parcel_from_coordinates(update, context)
    elif not pol_empty and not par_empty:
        await update.message.reply_text(await calculate_distance(update, context))
    else:
        await update.callback_query.message.reply_text(text='¿Qué quieres saber?', reply_markup=options_keyboard)

async def find_parcel_from_coordinates(update, context):
    coordinates = await get_user_coordinates(update, context)
    log.info(f'user coordinated: {coordinates}')
    x_coor, y_coor, _, _ = utm.from_latlon(coordinates[0], coordinates[1])
    log.info(f'UTM coordinates: x={x_coor} y={y_coor}')
    url = f'http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx/Consulta_RCCOOR?Coordenada_X={x_coor}&Coordenada_Y={y_coor}&SRS=EPSG%3A32629'
    log.info(f'Catastro API requested url: {url}')
    response = ET.fromstring(requests.get(url).content)
    log.info(f'Catastro API response: {response}')

    namespace = {'ns': 'http://www.catastro.meh.es/'}
    paraje = response.find('.//ns:ldt', namespace).text.split(' ')
    print(paraje)

    poligono = paraje[1]
    parcela = paraje[3]
    context.user_data['poligono'] = poligono
    context.user_data['parcela'] = parcela
    await update.message.reply_text(f'Estás en la parcela {parcela} y el polígono {poligono}, {get_info(poligono, parcela)}')
    await update.message.reply_text('¿Qué quieres saber?', reply_markup=options_keyboard)

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
    jcyl_info = get_catastro_jcyl(poligono, parcela)
    destination_coordinates = get_parcela_coordinates(jcyl_info)
    log.debug(f'Destination coordinates: {destination_coordinates[0]}, {destination_coordinates[1]}')
    
    # get distance
    distance = geo_distance(origen_coordinates, destination_coordinates).meters
    distance_text = print_distance(distance)

    # get direction
    degrees = get_direction(origen_coordinates, destination_coordinates)
    direction_text = print_direction(degrees)

    # return information
    return f'La parcela está a {distance_text} al {direction_text}'

async def any_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pol_empty = True if not context.user_data.get('poligono') else False
    par_empty = True if not context.user_data.get('parcela') else False

    if par_empty:
        context.user_data['parcela'] = update.message.text
        await update.message.reply_text('Escribe el número del polígono')
    elif pol_empty:
        context.user_data['poligono'] = update.message.text
        poligono = context.user_data.get('poligono')
        parcela = context.user_data.get('parcela')
        await update.message.reply_text(f'Has selecionado la parcela {parcela} y el polígono {poligono}')
        await update.message.reply_text(f'Está en {get_info(poligono, parcela)}')
        await update.message.reply_text('¿Qué quieres saber?', reply_markup=options_keyboard)
    else:
        poligono = context.user_data.get('poligono')
        parcela = context.user_data.get('parcela')
        await update.message.reply_text(f'Ya has selecionado la parcela {parcela} y el polígono {poligono}')

def get_catastro_jcyl(poligono, parcela):
    url = f'https://idecyl.jcyl.es/vcig/proxy.php?url=https%3A%2F%2Fovc.catastro.meh.es%2Fovcservweb%2FOVCSWLocalizacionRC%2FOVCCoordenadas.asmx%2FConsulta_CPMRC%3FSRS%3DEPSG%3A4326%26Provincia%3D%26Municipio%3D%26RC%3D49135A0{poligono}{parcela.zfill(5)}'
    log.debug(f'jcyl requested url: {url}')
    response = requests.get(url)
    return ET.fromstring(response.content)

def get_catastro_sigpac(poligono, parcela):
    url = f'https://sigpac.mapama.gob.es/fega/serviciosvisorsigpac/layerinfo?layer=parcela&id=49,135,0,0,{poligono},{parcela}'
    log.debug(f'sigpac requested url: {url}')
    response = requests.get(url)
    log.info(f'sigpac info:\n {response.content}')
    if response.status_code > 399:
        log.info(f'Server returned {response.status_code} HTTP code')
        return None
    res_json = json.loads(response.content)

    if res_json['query'] == []:
        log.info('Parcel does not exist')
        return None
    return res_json

def get_parcela_coordinates(catastro_info):
    namespace = {'ns': 'http://www.catastro.meh.es/'}
    longitude = catastro_info.find('.//ns:xcen', namespace).text
    latitude = catastro_info.find('.//ns:ycen', namespace).text
    return (float(latitude), float(longitude))

def get_paraje(catastro_info):
    namespace = {'ns': 'http://www.catastro.meh.es/'}
    return catastro_info.find('.//ns:ldt', namespace).text

def get_detailed_info(sigpac_info):
    area =  float(sigpac_info['query'][0]['dn_surface'])
    slope = float(sigpac_info['query'][0]['pendiente_media'])
    return area, slope

def get_ref_catastral(sigpac_info):
    return sigpac_info['parcelaInfo']['referencia_cat']

def print_distance(distance):
    if distance > 1000:
        distance = distance / 1000
        return f"{locale.format_string('%.1f', distance)} km"
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
    log.debug(f'Direction degrees: {degrees}')
    compass = ['este', 'noreste', 'norte', 'noroeste', 'oeste', 'suroeste', 'este', 'sureste', 'este']
    return compass[round(degrees/45)]

def get_info(poligono, parcela): 
    if not poligono or not parcela:
        log.error('parcela or poligono vars are not set')
        return 'Introduce el número del polígono y la parcela'

    jcyl_info = get_catastro_jcyl(poligono, parcela)
    sigpac_info = get_catastro_sigpac(poligono, parcela)

    paraje = get_paraje(jcyl_info).split(f'{parcela} ')[1].split('.')[0].title()
    area, slope = get_detailed_info(sigpac_info)
    slope = slope/10

    return f'en el paraje \'{paraje}\', tiene {area:.0f}m² de superficie y un {slope:.0f}% de pendiente'

def take_screenshot(ref_catastral):
    path_small_image, path_large_image = screenshot.take_screenshoot(ref_catastral)
    return path_small_image, path_large_image

def main():
    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.LOCATION, location_handle))
    bot.add_handler(CallbackQueryHandler(InlineKeyboardHandler))
    bot.add_handler(MessageHandler(filters.TEXT, any_input))

    bot.run_polling()

if __name__ == '__main__':
    main()
