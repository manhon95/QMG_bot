import telegram
import sqlite3
import random
import ast
import game
import os
import function
import cardfunction
import traceback
import battlebuild
import thread_lock
import drawmap
import logging
import status_handler
import air
import game_session
import os

from telegram import ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

org_dir = os.getcwd()

updater = Updater(token='731906195:AAEjKS1Qv_vYn6whd1Niq6z6UPkwkemfvy4', workers=128, use_context=True)
dispatcher = updater.dispatcher
Admin = [678036043]
logger = logging.getLogger('QMG_main')
# create logger
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - Thread ID:%(thread)d - %(filename)s - %(funcName)s - Line %(lineno)d - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)


@run_async
def trial(update, context):
    print('1')
    bot = context.bot
    session = game_session.find_session(update.message.chat_id)
    print('found')
    try:
        game.setup(bot, session)
    except Exception as e:
        traceback.print_exc()
        text = "<b>Exception:</b> " + str(e)
        bot.send_message(chat_id = session.get_session_id(), text = text, parse_mode=telegram.ParseMode.HTML)
    

@run_async
def cb(update, context):
    bot = context.bot
    #query_list format = [current action, current country, data, next action]
    query = update.callback_query
    print('query.message.chat_id ' + str(query.message.chat_id))
    try:
        logger.debug(query.from_user.name + '(' + str(query.from_user.id) + '): ' + query.data)
        query_list = ast.literal_eval(query.data)
        session = game_session.find_session(query.message.chat_id)
        if session.started:
            db = sqlite3.connect(session.get_db_dir())
    except Exception as e:
        traceback.print_exc()    
    try:
        if query_list[0] == 'clear':
            bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        if query_list[0] == 'start':
            start_cb(bot, query, query_list, session)
        if query_list[0] == 'recover_turn':
            recover_turn_cb(bot, query, query_list, db)
        if query_list[0] == 'country_info':
            country_info_cb(bot, query, query_list, db)
        if query_list[0] == 'deck_summary':
            deck_summary_cb(bot, query, query_list, db)
        if query_list[0] == 'discard_summary':
            discard_summary_cb(bot, query, query_list, db)
        if query_list[0] == 'hand_summary':
            hand_summary_cb(bot, query, query_list, db)
        if query_list[0] == 'calculator':
            draw_calculator_cb(bot, query, query_list, db)
        if query_list[0] == 'vp':
            vp_cb(bot, query, query_list, db)
        if query_list[0] == 'setup':
            game.setup_cb(bot, query, query_list, db)
        if query_list[0] == 'play':
            game.play_cb(bot, query, query_list, session)
        if query_list[0] == 'r_r':
            cardfunction.r_r_cb(bot, query, query_list, db)    
        if query_list[0] == 'air':
            game.air_force_cb(bot, query, query_list, session)    
        if query_list[0] == 'discard':
            game.discard_cb(bot, query, query_list, db)
        if query_list[0] == 'dh':
            function.discardhand_cb(bot, query, query_list, db)
        if query_list[0] == 'dh_nd':
            function.discardhand_no_deck_cb(bot, query, query_list, db)
        if query_list[0] == 'dr':
            function.discardresponse_cb(bot, query, query_list, db)
        if query_list[0] == 'dec':
            function.discardew_cb(bot, query, query_list, db)
        if query_list[0] == 'build':
            battlebuild.build_cb(bot, query, query_list, session)
        if query_list[0] == 'battle':
            battlebuild.battle_cb(bot, query, query_list, session)
        if query_list[0] == 'recuit':
            battlebuild.recuit_cb(bot, query, query_list, session)
        if query_list[0] == 'remove':
            battlebuild.remove_list[query_list[-1]].remove_cb(bot, query, query_list, session)
        if query_list[0] == 'self_remove':
            battlebuild.self_remove_list[query_list[-1]].self_remove_cb(bot, query, query_list, session)
        if query_list[0] == 'deploy':
            air.deploy_cb(bot, query, query_list, session)
        if query_list[0] == 'marshal':
            air.marshal_cb(bot, query, query_list, session)
        if query_list[0] == 'reposition':
            air.reposition_cb(bot, query, query_list, db)
        if query_list[0] == 'air_attack':
            air.air_attack_list[query_list[-1]].air_attack_cb(bot, query, query_list, session)
        if query_list[0] == 'status_play':
            game.status_play_cb(bot, query, query_list, session)
        if query_list[0] in ('status_battle','status_build','status_remove','status_recuit','status_deploy','status_before_play','status_after_play','status_draw','status_discard','status_supply','status_victory','status_ew'):
            status_handler.send_status_card_cb(bot, query, query_list, session)
        if query_list[0] in ('c20','c28','c30','c31','c33','c35','c36','c37','c48','c66','c100','c102','c144','c147','c149','c152','c175','c178','c202','c203','c205','c206','c209','c211','c219','c227','c271','c272','c273','c287','c298','c322','c325','c326','c328','c331','c332','c334','c335','c336','c337','c341','c342','c351','c365','c366','c369'):
            eval('cardfunction.' + query_list[0] + '_cb(bot, query, query_list, session)')
    except Exception as e:
        traceback.print_exc()
        logger.error(str(e))
        text = "<b>Exception:</b> " + str(e)
        bot.send_message(chat_id = session.get_session_id(), text = text, parse_mode=telegram.ParseMode.HTML)
        

player_list = {None:" "}
player_message_list = {}
chat_message = None

@run_async
def message(update, context):
    bot = context.bot
    try:
        logger.debug(update.message.from_user.full_name + ": " + update.message.text)
    except Exception as e:
        traceback.print_exc()


#-------------------------------------Start-----------------------------------------------
player_name = {}
id_list = {'Allied':[], 'Axis':[]}
country_player_id = {'ge':None, 'jp':None, 'it':None, 'uk':None, 'su':None, 'us':None}


@run_async
def start(update, context):
    bot = context.bot
    try:
        if update.message.from_user.id in Admin:
            session = game_session.find_session(update.message.chat_id)
            if session:
                text = "New game created, choose your country\n"
                for country in session.get_player_id_list():
                    text += "<b>" + function.countryid2name[country] + "</b>: "
                    if session.get_player_id_list()[country]:
                        player_name = bot.get_chat_member(update.message.chat_id,session.get_player_id_list()[country]).user.full_name
                        text += player_name
                    text += "\n"
                empty_country_list = [country for country in session.get_player_id_list() if not session.get_player_id_list()[country]]
                keyboard = [[InlineKeyboardButton(function.countryid2name[empty_country], callback_data="['start', '{}']".format(empty_country))] for empty_country in empty_country_list]
            else:
                new_session = game_session.session_list.append(game_session.session(update.message.chat_id))
                text = "New game created, choose your country"
                keyboard = [[InlineKeyboardButton(function.countryid2name[country], callback_data="['start', '{}']".format(country))] for country in function.player_country_list]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        else:
            logger.info('non-admin user: start')
    except Exception:
        traceback.print_exc()           


@run_async
def restart(update, context):
    bot = context.bot
    try:
        if update.message.from_user.id in Admin:
            session = game_session.find_session(update.message.chat_id)
            if session:
                game.game_end(bot, session)
            new_session = game_session.session_list.append(game_session.session(update.message.chat_id))
            text = "New game created, choose your country"
            keyboard = [[InlineKeyboardButton(function.countryid2name[country], callback_data="['start', '{}']".format(country))] for country in function.player_country_list]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        else:
            logger.info('non-admin user: restart')
    except Exception:
        traceback.print_exc()

        
@run_async
def start_cb(bot, query, query_list, session):
    print('1')
    if query.from_user.id not in game_session.get_all_active_player():
        print('2')
        country = query_list[1]
        new_player_id = query.from_user.id
        group_chat_id = query.message.chat_id
        if new_player_id not in session.get_allied_player_id_list().values() and country in session.get_axis_player_id_list().keys():
            print('3')
            if not session.get_axis_player_id_list()[country]:
                session.set_axis_player_id_list(country, new_player_id)
                session.set_player_id_list(country, new_player_id)
        elif new_player_id not in session.get_axis_player_id_list().values() and country in session.get_allied_player_id_list().keys():
            print('4')
            if not session.get_allied_player_id_list()[country]:
                session.set_allied_player_id_list(country, new_player_id)
                session.set_player_id_list(country, new_player_id)
        if all(session.get_player_id_list().values()):
            print('5')
            text = "New game created\n"
            for country in ['ge', 'jp', 'it', 'uk', 'su', 'us']:
                player_name = bot.get_chat_member(group_chat_id,session.get_player_id_list()[country]).user.full_name
                text += "<b>" + function.countryid2name[country] + "</b>: " + player_name + "\n" 
            bot.edit_message_text(chat_id=group_chat_id, message_id=query.message.message_id, text=text, parse_mode=telegram.ParseMode.HTML)
            try:
                session.set_game_id(game_session.get_new_game_id())
                session.create_dir()
                session.create_db()
                session.started = True
                session.turn = 1
                game.setup(bot, session)
            except Exception as e:
                traceback.print_exc()
                text = "<b>Exception:</b> " + str(e)
                bot.send_message(chat_id = group_chat_id, text = text, parse_mode=telegram.ParseMode.HTML)
        else:
            print('6')
            empty_country_list = [country for country in session.get_player_id_list() if not session.get_player_id_list()[country]]
            keyboard = [[InlineKeyboardButton(function.countryid2name[empty_country], callback_data="['start', '{}']".format(empty_country))] for empty_country in empty_country_list]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "New game created, please choose your country\n"
            for country in ['ge', 'jp', 'it', 'uk', 'su', 'us']:
                text += "<b>" + function.countryid2name[country] + "</b>: "
                if session.get_player_id_list()[country]:
                    player_name = bot.get_chat_member(group_chat_id,session.get_player_id_list()[country]).user.full_name
                    text += player_name
                text += "\n"
            print('7')
            bot.edit_message_text(chat_id=group_chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
            print('8')
            logger.info(query.from_user.full_name + " join " + function.countryid2name[query_list[2]])
    else:
        bot.send_message(chat_id = query.message.chat_id, text = query.from_user.full_name + " already join another game!", parse_mode=telegram.ParseMode.HTML)       
#-------------------------------------Recovery-----------------------------------------------

@run_async
def save(update, context):
    bot = context.bot
    if update.message.from_user.id in Admin:
        session = game_session.find_session(update.message.chat_id)
        if session.save_session():
            update.message.reply_text("Save success")
            logger.info("Save success")
        else:
            update.message.reply_text("Save fail")
            logger.info("Save fail")
    else:
        logger.info('non-admin user: save')


@run_async
def recover(update, context):
    try:
        bot = context.bot
        if update.message.from_user.id in Admin:
            session = game_session.find_session(update.message.chat_id)
            if session.load_session():
                db = sqlite3.connect(session.get_db_dir())
                phase = db.execute("select id, status from country where status != 'inactive';").fetchall()
                breakpt ="game." + phase[0][1] + "(bot, '{}', session)".format(phase[0][0])
                logger.debug(breakpt)
                eval(breakpt)
            else:
                update.message.reply_text("Load fail")
        else:
            logger.info('non-admin user: recover')
    except Exception as e:
        traceback.print_exc()
        text = "<b>Exception:</b> " + str(e)
        bot.send_message(chat_id = update.message.chat_id, text = text, parse_mode=telegram.ParseMode.HTML)
        
@run_async
def recover_turn(update, context):
    if update.message.from_user.id in Admin:
        country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us']
        keyboard = [[InlineKeyboardButton(function.countryid2name[country] , callback_data="['recover_turn', '{}']".format(country))] for country in country_list]
        keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
        text = 'Recover country turn:'
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text = text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        logger.debug('recover_turn called')
    else:
        logger.info('non-admin user: recover_turn')

def recover_turn_cb(bot, query, query_list, db):
    if query.from_user.id in Admin:
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text="Loading...")
        session = game_session.find_session(query.message.chat_id)
        if session.load_session_turn(query_list[1]):
            db = sqlite3.connect(session.get_db_dir())
            phase = db.execute("select id, status from country where status != 'inactive';").fetchall()
            breakpt ="game." + phase[0][1] + "(bot, '{}', session)".format(phase[0][0])
            logger.debug(breakpt)
            try:
                bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
                eval(breakpt)
            except Exception as e:
                traceback.print_exc()
                text = "<b>Exception:</b> " + str(e)
                bot.send_message(chat_id = query.message.chat_id, text = text, parse_mode=telegram.ParseMode.HTML)
        else:
            bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text="Load fail")
    
#-------------------------------------Draw Map-----------------------------------------------

@run_async
def draw_map(update, context):
    bot = context.bot
    try:
        session = game_session.find_session(update.message.chat_id)
        message_id = update.message.reply_text(text = "Drawing map...", parse_mode=telegram.ParseMode.HTML).message_id
        bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING)
        session.drawmap(sqlite3.connect(session.get_db_dir()))
        keyboard = [[InlineKeyboardButton("❎", callback_data="['clear']")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_photo(chat_id=update.message.chat_id, photo=open(org_dir + '/pic/tmp.jpg', 'rb', ), timeout=1000, reply_markup=reply_markup)
        bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
    except:
        traceback.print_exc()


#-------------------------------------Country Info-----------------------------------------------

@run_async
def country_info(update, context):
    country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us']
    keyboard = [[InlineKeyboardButton(function.countryid2name[country] , callback_data="['country_info', '{}']".format(country))] for country in country_list if country not in ['ch','fr']]
    keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
    text = 'Check a country current status:'
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text = text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    logger.debug('country_info called')
    
    
    
def country_info_cb(bot, query, query_list, db):
    country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us']
    country = query_list[1]
    deck_count = db.execute("select count(*) from card where location = 'deck' and control =:country;", {'country':country}).fetchall()
    discard_count = db.execute("select count(*) from card where ((location in ('discardd', 'discardu')) or (location = 'played' and type not in ('Status', 'Response', 'Bolster')) or (location = 'used' and type in ('Response', 'Bolster'))) and control =:country;", {'country':country}).fetchall()
    hand_count = db.execute("select count(*) from card where location = 'hand' and control =:country;", {'country':country}).fetchall()
    response_list = db.execute("select name from card where location == 'played' and type == 'Response' and control =:country;", {'country':country}).fetchall()
    status_list = db.execute("select name, text from card where location in ('played','turn') and type == 'Status' and control =:country;", {'country':country}).fetchall()
    text = function.countryid2name[country] + '\n'
    text += 'Deck: ' + str(deck_count[0][0]) + '    Discard: ' + str(discard_count[0][0]) + '\n'
    text += 'Hand: ' + str(hand_count[0][0]) + '\n'
    text += 'Response in play:'
    for card in response_list:
        text += "&#9646"
    text += '\nStatus in play:\n'
    for card in status_list:
        text += "<b>" + card[0] +  "</b> - " + card[1] + "\n"
    keyboard = [[InlineKeyboardButton(function.countryid2name[country], callback_data="['country_info', '{}']".format(country))] for country in country_list if country not in ['ch','fr',query_list[1]]]
    keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)

#-------------------------------------Deck Summary-----------------------------------------------
def deck_summary(update, context):
    bot = context.bot
    session = game_session.find_session(update.message.chat_id)
    try:
        db = sqlite3.connect(session.get_db_dir())
        player_country = db.execute("select id from country where playerid = :playerid;", {'playerid':update.message.from_user.id}).fetchall()
        if len(player_country) != 0:
            text = 'Check your country deck:'
            keyboard = [[InlineKeyboardButton(function.countryid2name[country[0]] , callback_data="['deck_summary', '{}']".format(country[0]))] for country in player_country if country[0] not in ['ch','fr']]
            keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text = text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
            logger.debug('deck_summary called')
    except Exception as e:
        traceback.print_exc()
        
def deck_summary_cb(bot, query, query_list, db):
    try:
        player_country = db.execute("select id from country where playerid = (select playerid from country where id = :country);", {'country':query_list[1]}).fetchall()
        card_type_list = db.execute("select distinct type from card;").fetchall()
        text = function.countryid2name[query_list[1]] + ' Deck\n\n'
        for card_type in card_type_list:
            text += "<b>" + card_type[0] + "</b>: "
            deck_count = db.execute("select count(*) from card where type =:type and control =:country and location = 'deck';", {'type':card_type[0], 'country':query_list[1]}).fetchall()
            text += str(deck_count[0][0]) + "\n"
        keyboard = [[InlineKeyboardButton(function.countryid2name[country[0]], callback_data="['deck_summary', '{}']".format(country[0]))] for country in player_country if country[0] not in ['ch','fr',query_list[1]]]
        keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    except Exception as e:
        traceback.print_exc()

#-------------------------------------Discard Summary-----------------------------------------------
def discard_summary(update, context):
    bot = context.bot
    session = game_session.find_session(update.message.chat_id)
    try:
        db = sqlite3.connect(session.get_db_dir())
        player_country = db.execute("select id from country where playerid = :playerid;", {'playerid':update.message.from_user.id}).fetchall()
        if len(player_country) != 0:
            text = 'Check your country discard:'
            keyboard = [[InlineKeyboardButton(function.countryid2name[country[0]] , callback_data="['discard_summary', '{}']".format(country[0]))] for country in player_country if country[0] not in ['ch','fr']]
            keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text = text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
            logger.debug('discard_summary called')
    except Exception as e:
        traceback.print_exc()

def discard_summary_cb(bot, query, query_list, db):
    try:
        player_country = db.execute("select id from country where playerid = (select playerid from country where id = :country);", {'country':query_list[1]}).fetchall()
        card_type_list = db.execute("select distinct type from card;").fetchall()
        text = function.countryid2name[query_list[1]] + ' Discard\n\n'
        for card_type in card_type_list:
            text += "<b>" + card_type[0] + "</b>: "
            if card_type[0] == 'Status':
                discard_count = db.execute("select count(*) from card where type =:type and control =:country and location in ('discardd', 'discardu');", {'type':card_type[0], 'country':query_list[1]}).fetchall()
            elif card_type[0] in ['Response', 'Bolster']:
                discard_count = db.execute("select count(*) from card where type =:type and control =:country and location in ('used', 'discardd', 'discardu');", {'type':card_type[0], 'country':query_list[1]}).fetchall()
            else:
                discard_count = db.execute("select count(*) from card where type =:type and control =:country and location in ('played', 'discardd', 'discardu');", {'type':card_type[0], 'country':query_list[1]}).fetchall()
            text += str(discard_count[0][0]) + "\n"
        keyboard = [[InlineKeyboardButton(function.countryid2name[country[0]], callback_data="['discard_summary', '{}']".format(country[0]))] for country in player_country if country[0] not in ['ch','fr',query_list[1]]]
        keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    except Exception as e:
        traceback.print_exc()

#-------------------------------------Hand Summary-----------------------------------------------
def hand_summary(update, context):
    bot = context.bot
    session = game_session.find_session(update.message.chat_id)
    try:
        db = sqlite3.connect(session.get_db_dir())
        player_country = db.execute("select id from country where playerid = :playerid;", {'playerid':update.message.from_user.id}).fetchall()
        if len(player_country) != 0:
            text = 'Check your country hand:'
            keyboard = [[InlineKeyboardButton(function.countryid2name[country[0]] , callback_data="['hand_summary', '{}']".format(country[0]))] for country in player_country if country[0] not in ['ch','fr']]
            keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text = text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
            logger.debug('hand_summary called')
    except Exception as e:
        traceback.print_exc()
        
def hand_summary_cb(bot, query, query_list, db):
    try:
        player_country = db.execute("select id from country where playerid = (select playerid from country where id = :country);", {'country':query_list[1]}).fetchall()
        hand = db.execute("select name, cardid, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
        text = function.countryid2name[query_list[1]] + " - hand\n"
        for card in hand:
            text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
        keyboard = [[InlineKeyboardButton(function.countryid2name[country[0]], callback_data="['hand_summary', '{}']".format(country[0]))] for country in player_country if country[0] not in ['ch','fr',query_list[1]]]
        keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    except Exception as e:
        traceback.print_exc()

#-------------------------------------Draw Calculator-----------------------------------------------
def draw_calculator(update, context):
    bot = context.bot
    session = game_session.find_session(update.message.chat_id)
    try:
        db = sqlite3.connect(session.get_db_dir())
        player_country = db.execute("select id from country where playerid = :playerid;", {'playerid':update.message.from_user.id}).fetchall()
        if len(player_country) != 0:
            text = 'Calculate your country draw card probability:'
            keyboard = [[InlineKeyboardButton(function.countryid2name[country[0]] , callback_data="['calculator', '{}']".format(country[0]))] for country in player_country if country[0] not in ['ch','fr']]
            keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text = text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
            logger.debug('calculator called')
    except Exception as e:
        traceback.print_exc()

def draw_calculator_cb(bot, query, query_list, db):
    try:
        player_country = db.execute("select id from country where playerid = (select playerid from country where id = :country);", {'country':query_list[1]}).fetchall()
        card_type_list = ['Build Army', 'Build Navy', 'Land Battle', 'Sea Battle']
        deck_count = db.execute("select count(*) from card where location = 'deck' and control = :country;", {'country':query_list[1]}).fetchall()
        text = function.countryid2name[query_list[1]] + ' - Deck count: ' + str(deck_count[0][0]) + '\n'
        text += 'Probability to draw:\n'
        text += ' - <b>A specific card</b>:'
        for i in range(1, 8):
            text += str(round((i/deck_count[0][0])*100, 1))
            if i != 7:
                text += '/'
        text += '\n'
        for card_type in card_type_list:
            card_count = db.execute("select count(*) from card where type = :type and location = 'deck' and control = :country;", {'type':card_type, 'country':query_list[1]}).fetchall()
            text += ' - <b>' + card_type + '</b>:'
            for i in range(1, 8):
                factor = 1
                for j in range(i):
                    factor *= ((deck_count[0][0] - card_count[0][0] - j)/(deck_count[0][0] - j))
                text += str(round((1 - factor)*100, 1))
                if i != 7:
                    text += '/'
            text += '\n'    
        keyboard = [[InlineKeyboardButton(function.countryid2name[country[0]], callback_data="['calculator', '{}']".format(country[0]))] for country in player_country if country[0] not in ['ch','fr',query_list[1]]]
        keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup, parse_mode = telegram.ParseMode.HTML)
    except Exception as e:
        traceback.print_exc()

#-------------------------------------Victory Point-----------------------------------------------
def vp(update, context):
    bot = context.bot
    session = game_session.find_session(update.message.chat_id)
    try:
        db = sqlite3.connect(session.get_db_dir())
        country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us', 'fr', 'ch']
        text = ''
        for country in country_list:
            if db.execute("select enemy from country where id = :country", {'country':country}).fetchall() == db.execute("select distinct control from space where spaceid = (select home from country where id = :country);", {'country':country}).fetchall():
                round_point = 0
            else:
                vp_space_list = function.control_vp_space_list(country, db)
                extra_point = status_handler.status_extra_victory_point(country, db)
                round_point = len(vp_space_list[0]) * 2 + len(vp_space_list[1])
                if extra_point != None:
                    round_point += extra_point[0]
            text += '<b>' + function.countryid2name[country] + '</b> - ' + str(round_point) + ' points/turn\n'
        keyboard = [[InlineKeyboardButton(function.countryid2name[country] , callback_data="['vp', '{}']".format(country))] for country in country_list]
        keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text = text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        logger.debug('vp called')
    except Exception as e:
        traceback.print_exc()
            
def vp_cb(bot, query, query_list, db):
    try:
        country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us', 'fr', 'ch']
        if db.execute("select enemy from country where id = :country", {'country':query_list[1]}).fetchall() == db.execute("select distinct control from space where spaceid = (select home from country where id = :country);", {'country':query_list[1]}).fetchall():
            text = "<b>" + function.countryid2name[query_list[1]] + "</b> home space occupied by enemy"
        else:
            vp_space_list = function.control_vp_space_list(query_list[1], db)
            control_point = len(vp_space_list[0]) * 2
            round_point = control_point
            text = function.countryid2name[query_list[1]] + " gain " + str(control_point) + " point from controlling:\n"
            for space in function.get_name_list(vp_space_list[0], db):
                text += "<b>" + space[1] + "</b>\n"
            if len(vp_space_list[1]) > 0:
                shared_point = len(vp_space_list[1])
                round_point += shared_point
                text += function.countryid2name[query_list[1]] + " gain " + str(shared_point) + " point from sharing control:\n"
                for space in function.get_name_list(vp_space_list[1], db):
                    text += "<b>" + space[1] + "</b>\n"
            extra_point = status_handler.status_extra_victory_point(query_list[1], db)
            if extra_point != None:
                round_point += extra_point[0]
                text += extra_point[1]
        keyboard = [[InlineKeyboardButton(function.countryid2name[country] , callback_data="['vp', '{}']".format(country))] for country in country_list if country != query_list[1]]
        keyboard.append([InlineKeyboardButton("❎", callback_data="['clear']")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup, parse_mode = telegram.ParseMode.HTML)
    except Exception as e:
        traceback.print_exc()

        
#--------------------------------------handler-----------------------------------------------
message_handler = MessageHandler(Filters.text & (~Filters.command), message)
dispatcher.add_handler(message_handler)
dispatcher.add_handler(CallbackQueryHandler(cb))
draw_handler = CommandHandler('draw', draw_map)
dispatcher.add_handler(draw_handler)
try_handler = CommandHandler('try', trial)
dispatcher.add_handler(try_handler)   
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
start_handler = CommandHandler('restart', restart)
dispatcher.add_handler(start_handler)
recover_handler = CommandHandler('recover', recover)
dispatcher.add_handler(recover_handler)
recover_turn_handler = CommandHandler('recover_turn', recover_turn)
dispatcher.add_handler(recover_turn_handler)
save_handler = CommandHandler('save', save)
dispatcher.add_handler(save_handler)
info_handler = CommandHandler('info', country_info)
dispatcher.add_handler(info_handler)
deck_handler = CommandHandler('deck', deck_summary)
dispatcher.add_handler(deck_handler)
discard_handler = CommandHandler('discard', discard_summary)
dispatcher.add_handler(discard_handler)
hand_handler = CommandHandler('hand', hand_summary)
dispatcher.add_handler(hand_handler)
calculator_handler = CommandHandler('calculator', draw_calculator)
dispatcher.add_handler(calculator_handler)
vp_handler = CommandHandler('vp', vp)
dispatcher.add_handler(vp_handler)

updater.start_polling()
