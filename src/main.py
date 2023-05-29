import screenshot
import logging as log
import requests, json, locale, math, sys
import xml.etree.ElementTree as ET
from geopy.distance import geodesic as geo_distance
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

locale.setlocale(locale.LC_ALL, 'es_ES')
log.basicConfig(stream=sys.stdout, level=log.INFO)

# Telegram bot token
TOKEN = open('/etc/telegram-bot-token', 'r').read().strip()
log.info(f'{TOKEN}')

KEYBOARD_OPTIONS = dict(
    info='info',
    navigate='navigate',
    photo='photo',
    new_search='new_search',
)

options_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton('Información detallada', callback_data=KEYBOARD_OPTIONS['info'])],
                [InlineKeyboardButton('Cómo ir a la parcela', callback_data=KEYBOARD_OPTIONS['navigate'])],
                [InlineKeyboardButton('Una foto de la parcela', callback_data=KEYBOARD_OPTIONS['photo'])],
                [InlineKeyboardButton('Nueva búsqueda', callback_data=KEYBOARD_OPTIONS['new_search'])],
            ])
remove_keyboard = InlineKeyboardMarkup([])

async def start(update, context):
    await update.message.reply_text('¿Cuál es el polígono?')

async def InlineKeyboardHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poligono = context.user_data.get('poligono')
    parcela = context.user_data.get('parcela')

    option = update.callback_query.data
    if option == KEYBOARD_OPTIONS['info']:
        sigpac_info = get_catastro_sigpac(poligono, parcela)
        if not sigpac_info:
            await update.callback_query.edit_message_text(text='El polígono y la parcela no existen, introduce los datos de nuevo')
            context.user_data['poligono'] = None
            context.user_data['parcela'] = None
            await update.callback_query.message.reply_text(text='¿Cuál es el polígono?', reply_markup=remove_keyboard)
            return
        await update.callback_query.edit_message_text(text=get_info(poligono, parcela))
        await update.callback_query.message.reply_text(text='¿Qué más quieres saber?', reply_markup=options_keyboard)
    elif option == KEYBOARD_OPTIONS['navigate']:
        sigpac_info = get_catastro_sigpac(poligono, parcela)
        if not sigpac_info:
            await update.callback_query.edit_message_text(text='El polígono y la parcela no existen, introduce los datos de nuevo')
            context.user_data['poligono'] = None
            context.user_data['parcela'] = None
            await update.callback_query.message.reply_text(text='¿Cuál es el polígono?', reply_markup=remove_keyboard)
            return
        await update.callback_query.edit_message_text(text='Envíame la ubicación desde la que ir a la parcela')
        await update.callback_query.message.reply_text(text='¿Qué más quieres saber?', reply_markup=options_keyboard)
    elif option == KEYBOARD_OPTIONS['photo']:
        sigpac_info = get_catastro_sigpac(poligono, parcela)
        if not sigpac_info:
            await update.callback_query.edit_message_text(text='El polígono y la parcela no existen, introduce los datos de nuevo')
            context.user_data['poligono'] = None
            context.user_data['parcela'] = None
            await update.callback_query.message.reply_text(text='¿Cuál es el polígono?', reply_markup=remove_keyboard)
            return
        await update.callback_query.edit_message_text(text='En unos segundos recibirás fotos de tu parcela')
        ref_catastral = get_ref_catastral(sigpac_info)
        path_small_image, path_large_image = take_screenshot(ref_catastral)
        await update.callback_query.message.reply_photo(photo=open(path_small_image, 'rb'))
        await update.callback_query.message.reply_photo(photo=open(path_large_image, 'rb'))
        screenshot.delete_images(path_small_image, path_large_image)
        await update.callback_query.message.reply_text(text='¿Qué más quieres saber?', reply_markup=options_keyboard)
    elif option == KEYBOARD_OPTIONS['new_search']:
        context.user_data['poligono'] = None
        context.user_data['parcela'] = None
        await update.callback_query.message.reply_text(text='¿Cuál es el polígono?', reply_markup=remove_keyboard)

async def calculate_distance(update, context):
    pol_empty = True if not context.user_data.get('poligono') else False
    par_empty = True if not context.user_data.get('parcela') else False

    if pol_empty or par_empty:
        await update.message.reply_text('No has introducido el polígono y parcela, haz click en \'Introducir información\'')
        
    # get user coordinates
    user_location = update.message.location
    origen_coordinates = (user_location.latitude, user_location.longitude)
    log.debug(f'Origin coordinates: {origen_coordinates[0]}, {origen_coordinates[1]}')

    # get parcel coordinates
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
    await update.message.reply_text(f'La parcela está a {distance_text} al {direction_text}')

async def any_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pol_empty = True if not context.user_data.get('poligono') else False
    par_empty = True if not context.user_data.get('parcela') else False

    if pol_empty:
        context.user_data['poligono'] = update.message.text
        await update.message.reply_text('¿Cuál es la parcela?')
    elif par_empty:
        context.user_data['parcela'] = update.message.text
        poligono = context.user_data.get('poligono')
        parcela = context.user_data.get('parcela')
        await update.message.reply_text(f'Has selecionado el polígono {poligono} y la parcela {parcela}')
        await update.message.reply_text('¿Qué quieres saber?', reply_markup=options_keyboard)
    else:
        poligono = context.user_data.get('poligono')
        parcela = context.user_data.get('parcela')
        await update.message.reply_text(f'Ya has selecionado el polígono {poligono} y la parcela {parcela}')

def get_catastro_jcyl(poligono, parcela):
    url = f'https://idecyl.jcyl.es/vcig/proxy.php?url=https%3A%2F%2Fovc.catastro.meh.es%2Fovcservweb%2FOVCSWLocalizacionRC%2FOVCCoordenadas.asmx%2FConsulta_CPMRC%3FSRS%3DEPSG%3A4326%26Provincia%3D%26Municipio%3D%26RC%3D49135A0{poligono}{parcela.zfill(5)}'
    log.debug(f'jcyl requested url: {url}')
    response = requests.get(url)
    return ET.fromstring(response.content)

def get_catastro_sigpac(poligono, parcela):
    url = f'https://sigpac.mapama.gob.es/fega/serviciosvisorsigpac/layerinfo?layer=parcela&id=49,135,0,0,{poligono},{parcela}'
    log.debug(f'sigpac requested url: {url}')
    response = requests.get(url)
    res_json = json.loads(response.content)
    log.info(f'sigpac info:\n {res_json}')

    if res_json['query'] == []:
        log.info(f'Parcel does not exist')
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

    return f'La parcela en el {paraje} tiene un área de {area:.0f}m² y un {slope:.0f}% de pendiente'

def take_screenshot(ref_catastral):
    path_small_image, path_large_image = screenshot.take_screenshoot(ref_catastral)
    return path_small_image, path_large_image

def main():
    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.LOCATION, calculate_distance))
    bot.add_handler(CallbackQueryHandler(InlineKeyboardHandler))
    bot.add_handler(MessageHandler(filters.TEXT, any_input))

    bot.run_polling()

if __name__ == '__main__':
    main()
