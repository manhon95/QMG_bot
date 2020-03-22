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
import backup
import logging
import log
import status_handler
import air

from telegram import ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async

updater = Updater(token='731906195:AAEjKS1Qv_vYn6whd1Niq6z6UPkwkemfvy4', workers=32)
dispatcher = updater.dispatcher
logger = logging.getLogger('QMG_main')
Admin = [678036043]
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
def trial(bot, update):
    chat = bot.get_chat_member(update.message.chat_id,update.message.from_user.id).user
    print(chat)
    message = bot.send_message(chat_id=update.message.chat_id, text="userid:{} username:{} chatid:{}".format(update.message.from_user.id, update.message.from_user.name, update.message.chat.id), reply_markup = None)
    print(message.message_id)
    print(message.text)
    
    '''db = sqlite3.connect('database.db')
    try:
        lock_id = thread_lock.add_lock()
        space_list = function.control_space_list('su', db, space_type = 'land')
        battlebuild.self_remove_list.append(battlebuild.self_remove('su', space_list, 297, lock_id, 'army'))
        print("self_remove_id: " + str(len(battlebuild.self_remove_list)-1))
        self_remove_id = len(battlebuild.self_remove_list)-1
        info = battlebuild.self_remove_list[self_remove_id].self_remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        lock_id = thread_lock.add_lock()
    except Exception:
        traceback.print_exc()'''

def draw_map(bot, update):
    message_id = bot.send_message(chat_id=update.message.chat_id, text="Drawing map...").message_id
    db = sqlite3.connect('database.db')
    try:
        bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
        drawmap.drawmap(db)
        keyboard = [[InlineKeyboardButton("❎", callback_data="['clear']")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_photo(chat_id=update.message.chat_id, photo=open('pic/tmp.jpg', 'rb', ), timeout=1000, reply_markup=reply_markup)
        bot.delete_message(chat_id=update.message.chat_id, message_id=message_id)
    except Exception as e:
        traceback.print_exc()

@run_async
def cb(bot, update):
    #query_list format = [current action, current country, data, next action]
    query = update.callback_query
    try:
        logger.debug(query.from_user.name + '(' + str(query.from_user.id) + '): ' + query.data)
    except Exception as e:
        traceback.print_exc()    
    query_list = ast.literal_eval(query.data)
    db = sqlite3.connect('database.db')
    try:
        if query_list[0] == 'clear':
            bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        if query_list[0] == 'start':
            start_cb(bot, query, query_list, db)
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
            game.play_cb(bot, query, query_list, db)
        if query_list[0] == 'r_r':
            cardfunction.r_r_cb(bot, query, query_list, db)    
        if query_list[0] == 'air':
            game.air_force_cb(bot, query, query_list, db)    
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
            battlebuild.build_cb(bot, query, query_list, db)
        if query_list[0] == 'battle':
            battlebuild.battle_cb(bot, query, query_list, db)
        if query_list[0] == 'recuit':
            battlebuild.recuit_cb(bot, query, query_list, db)
        if query_list[0] == 'remove':
            #battlebuild.remove_cb(bot, query, query_list, db)
            battlebuild.remove_list[query_list[-1]].remove_cb(bot, query, query_list, db)
        if query_list[0] == 'self_remove':
            #battlebuild.self_remove_cb(bot, query, query_list, db)
            battlebuild.self_remove_list[query_list[-1]].self_remove_cb(bot, query, query_list, db)
        if query_list[0] == 'deploy':
            air.deploy_cb(bot, query, query_list, db)
        if query_list[0] == 'marshal':
            air.marshal_cb(bot, query, query_list, db)
        if query_list[0] == 'reposition':
            air.reposition_cb(bot, query, query_list, db)
        if query_list[0] == 'air_attack':
            air.air_attack_list[query_list[-1]].air_attack_cb(bot, query, query_list, db)
        if query_list[0] == 'status_play':
            game.status_play_cb(bot, query, query_list, db)
        if query_list[0] in ('status_battle','status_build','status_remove','status_recuit','status_deploy','status_before_play','status_after_play','status_draw','status_discard','status_supply','status_victory','status_ew'):
            status_handler.send_status_card_cb(bot, query, query_list, db)
        if query_list[0] in ('c20','c28','c30','c31','c33','c35','c36','c37','c48','c66','c100','c102','c144','c147','c149','c152','c175','c178','c202','c203','c205','c206','c209','c211','c219','c227','c271','c272','c273','c287','c298','c322','c325','c326','c328','c331','c332','c334','c335','c336','c337','c341','c342','c351','c365','c366','c369'):
            eval('cardfunction.' + query_list[0] + '_cb(bot, query, query_list, db)')
    except Exception as e:
        traceback.print_exc()
        logger.error(str(e))
        db = sqlite3.connect('database.db')
        group_chat_id = db.execute("select chatid from game;").fetchall()
        text = "<b>Exception:</b> " + str(e)
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        db.close()
        

player_list = {None:" "}
player_message_list = {}
chat_message = None
@run_async
def message(bot, update):
    try:
        logger.debug(update.message.from_user.full_name + ": " + update.message.text)
    except Exception as e:
        traceback.print_exc()
        
    db = sqlite3.connect('database.db')
    #start
    country_list = ['Germany', 'Japan', 'Italy', 'United Kingdom', 'Soviet Union', 'United States']
    for country in country_list:
        if update.message.text == country:
            if db.execute("select status from country where name = :country;", {'country': country}).fetchall()[0][0] == 'none':
                db.execute("update country set playerid =:id, status = 'filled' where name = :country ;", {'id': update.message.from_user.id, 'country': country})
                keyboard = []
                if db.execute("select count(*) from country where status = 'none';").fetchall()[0][0] == 0:
                    reply_markup = ReplyKeyboardRemove()
                    bot.send_message(chat_id=update.message.chat_id, text="{} is playing {}".format(update.message.from_user.name, country), reply_markup=reply_markup)
                    db.commit()
                    db.close()
                    try:
                        game.setup(bot)
                    except Exception as e:
                        traceback.print_exc()
                        db = sqlite3.connect('database.db')
                        group_chat_id = db.execute("select chatid from game;").fetchall()
                        text = "<b>Exception:</b> " + str(e)
                        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
                        db.close()
                else:      
                    if db.execute("select count(*) from country where status = 'none' and side = 'Axis';").fetchall()[0][0] != 0:
                        axis = db.execute("select name from country where status = 'none' and side = 'Axis';").fetchall()
                        keyboard.append([axis[x][0] for x in range(len(axis))])
                    if db.execute("select count(*) from country where status = 'none' and side = 'Allied';").fetchall()[0][0] != 0:
                        Allied = db.execute("select name from country where status = 'none' and side = 'Allied';").fetchall()
                        keyboard.append([Allied[x][0] for x in range(len(Allied))])
                    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
                    bot.send_message(chat_id=update.message.chat_id, text="{} is playing {}".format(update.message.from_user.name, country), reply_markup=reply_markup)
                    db.commit()
                    db.close()
        #start2
        #country_list = db.execute('select name, id from country').fetchall()
    if update.message.text == "Join!":
        global chat_message
        if chat_message == None:
            chat_message = bot.send_message(chat_id=update.message.chat_id, text="Game Begin, waiting player choose side...").message_id
        global player_list
        if len(player_list) < 6:
            player_list[update.message.from_user.id] = update.message.from_user.name
            if len(player_list) < 6:
                bot.send_message(chat_id=update.message.chat_id, text="{} join the game, current player:{}".format(update.message.from_user.name, str(player_count)), reply_markup=reply_markup)
            else:
                bot.send_message(chat_id=update.message.chat_id, text="{} join the game, current player:{}, game begin!".format(update.message.from_user.name, str(player_count)), reply_markup=reply_markup)
                for player in player_list:
                    keyboard = [[InlineKeyboardButton(country[0], callback_data="['start', {}]".format(country[1]))] for country in country_list]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    player_message_list[update.message.from_user.id] = bot.send_message(chat_id = player, text = "please choose a faction...", reply_markup = reply_markup).message_id
        else:
            bot.send_message(chat_id=update.message.chat_id, text="Current game is full!".format(update.message.from_user.name, str(player_count)), reply_markup=reply_markup) 
        db.commit()
        db.close()


#-------------------------------------Start-----------------------------------------------
player_name = {}
id_list = {'Allied':[], 'Axis':[]}
@run_async
def start2(bot, update):
    if update.message.from_user.id in Admin:
        db = sqlite3.connect('database.db')
        country = db.execute('select name from country').fetchall()
        db.execute("update country set status = 'none';")
        db.execute("update country set status = 'filled' where country in ('fr', 'ch');")
        db.execute("update game set chatid = :id;", {'id':update.message.chat_id})
        keyboard = [[country[0][0], country[1][0], country[2][0]], [country[3][0], country[4][0], country[5][0]]]
        db.commit()
        db.close()
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        update.message.reply_text("New game created, choose your country", reply_markup=reply_markup)
    else:
        logger.info('non-admin user: start')

@run_async
def start(bot, update):
    try:
        global player_name, id_list
        player_name = {}
        id_list = {'Allied':[], 'Axis':[]}
        if update.message.from_user.id in Admin:
            country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us']
            db = sqlite3.connect('database.db')
            db.execute("update country set status = 'none';")
            db.execute("update country set status = 'filled' where id in ('fr', 'ch');")
            db.execute("update game set chatid = :id;", {'id':update.message.chat_id})
            keyboard = [[InlineKeyboardButton(function.countryid2name[country], callback_data="['start', '{}']".format(country))] for country in country_list]
            db.commit()
            db.close()
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("New game created, choose your country", reply_markup=reply_markup)
        else:
            logger.info('non-admin user: start')
    except Exception as e:
        traceback.print_exc()           


@run_async
def start_cb(bot, query, query_list, db):
    global id_list
    if query.from_user.id not in id_list[db.execute("select enemy from country where id = :country;", {'country':query_list[1]}).fetchall()[0][0]]:
        if db.execute("select status from country where id = :country;", {'country':query_list[1]}).fetchall()[0][0] == 'none':
            db.execute("update country set playerid =:id, status = 'filled' where id = :country ;", {'id': query.from_user.id, 'country': query_list[1]})
            if query_list[1] == 'uk':
                db.execute("update country set playerid =:id, status = 'filled' where id = 'fr' ;", {'id': query.from_user.id})
            if query_list[1] == 'us':
                db.execute("update country set playerid =:id, status = 'filled' where id = 'ch' ;", {'id': query.from_user.id})
            global player_name
            player_name[query_list[1]] = query.from_user.full_name
            id_list[function.getside[query_list[1]]].append(query.from_user.id)
            keyboard = []
            if db.execute("select count(*) from country where status = 'none';").fetchall()[0][0] == 0:
                text = "New game created\n"
                for country in ['ge', 'jp', 'it', 'uk', 'su', 'us']:
                    text += "<b>" + function.countryid2name[country] + "</b>: "
                    if db.execute("select status from country where id = :country;", {'country':country}).fetchall()[0][0] != 'none':
                        text += player_name[country]
                    text += "\n"
                bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, parse_mode=telegram.ParseMode.HTML)
                db.commit()
                db.close()
                try:
                    game.setup(bot)
                except Exception as e:
                    traceback.print_exc()
                    db = sqlite3.connect('database.db')
                    group_chat_id = db.execute("select chatid from game;").fetchall()
                    text = "<b>Exception:</b> " + str(e)
                    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
                    db.close()
            else:
                country_list = db.execute("select id from country where status = 'none';").fetchall()
                keyboard = [[InlineKeyboardButton(function.countryid2name[country[0]], callback_data="['start', '{}']".format(country[0]))] for country in country_list]
                reply_markup = InlineKeyboardMarkup(keyboard)
                text = "New game created, please choose your country\n"
                for country in ['ge', 'jp', 'it', 'uk', 'su', 'us']:
                    text += "<b>" + function.countryid2name[country] + "</b>: "
                    if db.execute("select status from country where id = :country;", {'country':country}).fetchall()[0][0] != 'none':
                        text += player_name[country]
                    text += "\n"
                bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
                db.commit()
                db.close()
                logger.info(query.from_user.full_name + ' join ' + function.countryid2name[query_list[1]])
            
#-------------------------------------Recovery-----------------------------------------------

@run_async
def save(bot, update):
    if update.message.from_user.id in Admin:
        if backup.save():
            update.message.reply_text("Save success")
            logger.info("Save success")
        else:
            update.message.reply_text("Save fail")
            logger.info("Save fail")
    else:
        logger.info('non-admin user: save')


@run_async
def recover(bot, update):
    if update.message.from_user.id in Admin:
        if backup.load():
            db = sqlite3.connect('database.db')
            phase = db.execute("select id, status from country where status != 'inactive';").fetchall()
            breakpt ="game." + phase[0][1] + "(bot, '{}')".format(phase[0][0])
            logger.debug(breakpt)
            try:
                eval(breakpt)
            except Exception as e:
                traceback.print_exc()
                db = sqlite3.connect('database.db')
                group_chat_id = db.execute("select chatid from game;").fetchall()
                text = "<b>Exception:</b> " + str(e)
                bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
                db.close()
        else:
            update.message.reply_text("Load fail")
    else:
        logger.info('non-admin user: recover')

@run_async
def recover_turn(bot, update):
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
    bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text="Loading...")
    if backup.load_turn(query_list[1]):
        db = sqlite3.connect('database.db')
        phase = db.execute("select id, status from country where status != 'inactive';").fetchall()
        breakpt ="game." + phase[0][1] + "(bot, '{}')".format(phase[0][0])
        logger.debug(breakpt)
        try:
            bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
            eval(breakpt)
        except Exception as e:
            traceback.print_exc()
            db = sqlite3.connect('database.db')
            group_chat_id = db.execute("select chatid from game;").fetchall()
            text = "<b>Exception:</b> " + str(e)
            bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
            db.close()
    else:
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text="Load fail")
    
#-------------------------------------Country Info-----------------------------------------------

@run_async
def country_info(bot, update):
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
    discard_count = db.execute("select count(*) from card where ((location in ('discardd', 'discardu')) or (location = 'played' and type not in ('Status', 'Response')) or (location = 'used' and type = 'Response')) and control =:country;", {'country':country}).fetchall()
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
def deck_summary(bot, update):
    try:
        db = sqlite3.connect('database.db')
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
def discard_summary(bot, update):
    try:
        db = sqlite3.connect('database.db')
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
            elif card_type[0] == 'Response':
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
def hand_summary(bot, update):
    try:
        db = sqlite3.connect('database.db')
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
def draw_calculator(bot, update):
    try:
        db = sqlite3.connect('database.db')
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
def vp(bot, update):
    try:
        db = sqlite3.connect('database.db')
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
message_handler = MessageHandler(Filters.text, message, message_updates = True)
dispatcher.add_handler(message_handler)
dispatcher.add_handler(CallbackQueryHandler(cb))
draw_handler = CommandHandler('draw', draw_map)
dispatcher.add_handler(draw_handler)
try_handler = CommandHandler('try', trial)
dispatcher.add_handler(try_handler)   
start_handler = CommandHandler('start', start)
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
