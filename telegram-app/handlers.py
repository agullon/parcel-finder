
import screenshot, utils

import logging as log
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Keyboards definitions
KEYBOARD_OPTIONS = dict(
    navigate='navigate',
    photo='photo',
    new_search='new_search',
)
options_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Cómo ir a la parcela', callback_data=KEYBOARD_OPTIONS['navigate'])],
        [InlineKeyboardButton('Una foto de la parcela', callback_data=KEYBOARD_OPTIONS['photo'])],
        [InlineKeyboardButton('Nueva búsqueda', callback_data=KEYBOARD_OPTIONS['new_search'])],
    ]
)
search_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Nueva búsqueda', callback_data=KEYBOARD_OPTIONS['new_search'])],
    ]
)
remove_keyboard = InlineKeyboardMarkup([])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id='5374343', text=f'{update.effective_user.username} joined for first time')
    await update.message.reply_text(text=f'Hola {update.effective_user.first_name}, escribe el número de la parcela o envía tu ubicación para saber en qué parcela estás')

async def InlineKeyboardHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poligono = context.user_data.get('poligono')
    parcela = context.user_data.get('parcela')

    option = update.callback_query.data
    if option == KEYBOARD_OPTIONS['navigate']:
        await context.bot.send_message(chat_id='5374343', text=f'{update.effective_user.username} requested instructions to go to a parcel')
        sigpac_info, sigpac_error = utils.get_catastro_sigpac(poligono, parcela)
        if sigpac_error:
            await update.callback_query.edit_message_text(text=f'Ha habido un error: {sigpac_error}')
            context.user_data['poligono'] = None
            context.user_data['parcela'] = None
            await update.callback_query.message.reply_text(text='Escribe el número de la parcela o envía tu ubicación para saber en qué parcela estás', reply_markup=search_keyboard)
            return
        await update.callback_query.edit_message_text(text=f'{await utils.calculate_distance(update, context, (41.9986276,-6.3471484))} de la iglesia de Fresno')
        await update.callback_query.message.reply_text(text='Envíame una ubicación para obtener indicaciones sobre cómo ir desde cualquier sitio')
        await update.callback_query.message.reply_text(text='¿Qué más quieres saber?', reply_markup=options_keyboard)
    elif option == KEYBOARD_OPTIONS['photo']:
        await context.bot.send_message(chat_id='5374343', text=f'{update.effective_user.username} requested a photo')
        sigpac_info, sigpac_error = utils.get_catastro_sigpac(poligono, parcela)
        if sigpac_error:
            await update.callback_query.edit_message_text(text=f'Ha habido un error: {sigpac_error}')
            context.user_data['poligono'] = None
            context.user_data['parcela'] = None
            await update.callback_query.edit_message_text(text='Escribe el número de la parcela o envía tu ubicación para saber en qué parcela estás', reply_markup=search_keyboard)
            return
        await update.callback_query.edit_message_text(text='Por favor, espera unos segundos para recibir imágenes de la parcela')
        ref_catastral = utils.get_ref_catastral(sigpac_info)
        path_small_image, path_large_image = utils.take_screenshot(ref_catastral)
        await update.callback_query.message.reply_photo(photo=open(path_small_image, 'rb'))
        await update.callback_query.message.reply_photo(photo=open(path_large_image, 'rb'))
        screenshot.delete_images(path_small_image, path_large_image)
        await update.callback_query.message.reply_text(text='¿Qué más quieres saber?', reply_markup=options_keyboard)
    elif option == KEYBOARD_OPTIONS['new_search']:
        await context.bot.send_message(chat_id='5374343', text=f'{update.effective_user.username} started a new search')
        context.user_data['poligono'] = None
        context.user_data['parcela'] = None
        await update.callback_query.message.reply_text(text='Escribe el número de la parcela o envía tu ubicación para saber en qué parcela estás', reply_markup=search_keyboard)

async def text_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    input = update.message.text

    # Only integers are valid input
    if not str.isdigit(input):
        await update.message.reply_text(f'\'{input}\' no es un valor válido, debe ser un número entre 1 y 9999')
        await update.message.reply_text('Escribe el número del polígono')
        return

    pol_empty = True if not context.user_data.get('poligono') else False
    par_empty = True if not context.user_data.get('parcela') else False

    if par_empty:
        await context.bot.send_message(chat_id='5374343', text=f'{update.effective_user.username} introduced parcela number')
        context.user_data['parcela'] = input
        await update.message.reply_text('Escribe el número del polígono')
        return
    elif pol_empty:
        await context.bot.send_message(chat_id='5374343', text=f'{update.effective_user.username} introduced polígono number')
        context.user_data['poligono'] = input
        poligono = context.user_data.get('poligono')
        parcela = context.user_data.get('parcela')
        await update.message.reply_text(f'Has selecionado la parcela {parcela} y el polígono {poligono}')
        paraje, area, slope, error = utils.get_info(poligono, parcela) 
        if error:
            text = f'Ha habido un error: {error}'
            context.user_data['poligono'] = None
            context.user_data['parcela'] = None
            await update.message.reply_text(f'{text}')
            await update.message.reply_text('Escribe el número de la parcela o envía tu ubicación para saber en qué parcela estás')
            return
        else:
            await context.bot.send_message(chat_id='5374343', text=f'{update.effective_user.username} received parcela info')
            text = f'El paraje es \'{paraje}\' y la parcela tiene {area:.0f}m² de superficie y un {slope:.0f}% de pendiente'
            await update.message.reply_text(f'{text}')
            await update.message.reply_text('¿Qué más quieres saber?', reply_markup=options_keyboard)
            return
    else:
        poligono = context.user_data.get('poligono')
        parcela = context.user_data.get('parcela')
        await update.message.reply_text(f'Ya has selecionado la parcela {parcela} y el polígono {poligono}')
        await update.message.reply_text('¿Qué quieres saber?', reply_markup=options_keyboard)
        return
    
async def location_input_handler(update, context):
    await context.bot.send_message(chat_id='5374343', text=f'{update.effective_user.username} sent location')
    pol_empty = True if not context.user_data.get('poligono') else False
    par_empty = True if not context.user_data.get('parcela') else False

    log.info(f'pol_empty={pol_empty}')
    log.info(f'par_empty={par_empty}')

    if pol_empty and pol_empty:
        await utils.find_parcel_from_coordinates(update, context)
    elif not pol_empty and not par_empty:
        await update.message.reply_text(await utils.calculate_distance(update, context))
    else:
        await update.callback_query.message.reply_text(text='¿Qué quieres saber?', reply_markup=options_keyboard)

