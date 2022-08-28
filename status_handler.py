import telegram
import sqlite3
import function
import cardfunction
import thread_lock
import ast
import air
import drawmap
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

org_dir = os.getcwd()

class handler():
    def __init__(self, type_, active_country_id, lock_id, passive_country_id = None, card_id = None, space_id = None, piece_id = None):
        self.type_ = type_
        self.active_country_id = active_country_id
        self.passive_country_id = passive_country_id
        self.card_id = card_id
        self.space_id = space_id
        self.piece_id = piece_id
        self.lock_id = lock_id
        self.message_id = {'ge':None, 'jp':None, 'it':None, 'uk':None, 'su':None, 'us':None, 'fr':None, 'ch':None}
        self.no_respone = {'ge':True, 'jp':True, 'it':True, 'uk':True, 'su':True, 'us':True, 'fr':True, 'ch':True}
        self.one_side_pass = False
        self.air_defense = False
        self.air_attack = False
        self.first = True
        text = "status_handler add: "
        info_list = {"type_":type_, "active_country_id":active_country_id, "passive_country_id":passive_country_id, "card_id":card_id, "space_id":space_id, "piece_id":piece_id, "lock_id":lock_id}
        for info in info_list:
            if info_list[info] != None:
                text += " [" + info + ": " + str(info_list[info]) + "]"
        print(text)


enemy_country_list = {'ge':['uk', 'su', 'us', 'fr', 'ch'],
                      'jp':['uk', 'su', 'us', 'fr', 'ch'],
                      'it':['uk', 'su', 'us', 'fr', 'ch'],
                      'uk':['ge', 'jp', 'it'],
                      'su':['ge', 'jp', 'it'],
                      'us':['ge', 'jp', 'it'],
                      'fr':['ge', 'jp', 'it'],
                      'ch':['ge', 'jp', 'it'] }

friendly_country_list = {'ge':['ge', 'jp', 'it'],
                      'jp':['ge', 'jp', 'it'],
                      'it':['ge', 'jp', 'it'],
                      'uk':['uk', 'su', 'us', 'fr', 'ch'],
                      'su':['uk', 'su', 'us', 'fr', 'ch'],
                      'us':['uk', 'su', 'us', 'fr', 'ch'],
                      'fr':['uk', 'su', 'us', 'fr', 'ch'],
                      'ch':['uk', 'su', 'us', 'fr', 'ch']}
    
def send_status_card(bot, active_country_id, type_, lock_id, session, passive_country_id = None, card_id = None, space_id = None, piece_id = None):
    db = sqlite3.connect(session.get_db_dir())
    session.draw_map()
    session.handler_list.append(handler(type_, active_country_id, lock_id, passive_country_id, card_id, space_id, piece_id))
    print("status_handler_id: " + str(len(session.handler_list)-1))
    handler_id = len(session.handler_list)-1
    #enemy_country_list = db.execute("select id from country where side = (select enemy from country where id = :country);", {'country':active_country_id}).fetchall()
    pass_ = True 
    for country in enemy_country_list[active_country_id]:
        info = info_list[type_](country, handler_id, session)
        if info[2] == None:
            session.handler_list[handler_id].no_respone[country] = True
        else:
            print('have - response ' + country)
            session.handler_list[handler_id].no_respone[country] = False
            pass_ = False
            status_message_id = bot.send_photo(chat_id = info[0], caption = info[1], reply_markup = info[2], parse_mode=telegram.ParseMode.HTML, photo=open(session.get_dir() + '/tmp.jpg', 'rb'))
            session.handler_list[handler_id].message_id[country] = status_message_id.message_id
    if pass_:
        air.check_reposition(bot, session)
        session.handler_list[handler_id].first = False
        session.handler_list[handler_id].one_side_pass = True
        #friendly_country_list = db.execute("select id from country where side = (select side from country where id = :country);", {'country':active_country_id}).fetchall()
        pass_ = True
        for country in friendly_country_list[active_country_id]:
            info = info_list[type_](country, handler_id, session)
            if info[2] == None:
                session.handler_list[handler_id].no_respone[country] = True
            else:
                print('have - response ' + country)
                session.handler_list[handler_id].no_respone[country] = False
                pass_ = False
                status_message_id = bot.send_photo(chat_id = info[0], caption = info[1], reply_markup = info[2], parse_mode=telegram.ParseMode.HTML, photo=open(session.get_dir() + '/tmp.jpg', 'rb'))
                print(country + ' add status_message_id:' + str(status_message_id.message_id))
                session.handler_list[handler_id].message_id[country] = status_message_id.message_id
        if pass_:
            air.check_reposition(bot, session)
            session.handler_list.pop(handler_id)
            session.release_lock(lock_id)
        else:
            session.thread_lock(lock_id)
    else:
        session.thread_lock(lock_id)

def send_status_card_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    handler_id = query_list[2]
    info_type = session.handler_list[handler_id].type_
    lock_id = session.handler_list[handler_id].lock_id
    if session.handler_list[handler_id].card_id != None:
        card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':session.handler_list[handler_id].card_id}).fetchall()
    if query_list[3] == 'pass':
        session.handler_list[handler_id].first = False
        session.handler_list[handler_id].no_respone[query_list[1]] = True
        #friendly_country_list = db.execute("select id, playerid from country where side = (select side from country where id = :country);", {'country':query_list[1]}).fetchall()
        if not all([session.handler_list[handler_id].no_respone[country] for country in friendly_country_list[query_list[1]]]):
            if session.handler_list[handler_id].card_id != None:
                text = "<b>[" + card_name[0][0] + " - " + info_type + "]</b> - You pass, waiting other players..."
            else:
                text = "<b>[" + info_type + "]</b> - You pass, waiting other players..."
            bot.edit_message_caption(chat_id=query.message.chat_id, message_id=query.message.message_id, caption=text , parse_mode=telegram.ParseMode.HTML)
            return
        for country in friendly_country_list[query_list[1]]:
            message_id = session.handler_list[handler_id].message_id[country]
            print(country + ' status_message_id: ' + str(message_id))
            if message_id != None:
                chat_id = db.execute("select playerid from country where id =:country;", {'country':country}).fetchall()
                bot.delete_message(chat_id=chat_id[0][0], message_id = message_id)
                session.handler_list[handler_id].message_id[country] = None
        if session.handler_list[handler_id].one_side_pass:
            session.handler_list.pop(handler_id)
            session.release_lock(lock_id)
            return
        session.handler_list[handler_id].one_side_pass = True
        session.handler_list[handler_id].first = False
    elif query_list[3] == 'confirm':
        if query_list[-1] == 'air_a':
            text = "<b>[" + info_type + "]</b> - You used Air Attack, processsing..."
        elif query_list[-1] == 'air_d':
            text = "<b>[" + info_type + "]</b> - You used Air Defense, processsing..."
        elif session.handler_list[handler_id].card_id != None:
            used_card_name = db.execute("select name from card where cardid = :card;",{'card':query_list[-1]}).fetchall()
            text = "<b>[" + card_name[0][0] + " - " + info_type + "]</b> - You used " + used_card_name[0][0] + ", processsing..."
        else:
            used_card_name = db.execute("select name from card where cardid = :card;",{'card':query_list[-1]}).fetchall()
            text = "<b>[" + info_type + "]</b> - You used " + used_card_name[0][0] + ", processsing..."
        bot.edit_message_caption(chat_id=query.message.chat_id, message_id=query.message.message_id, caption=text, parse_mode=telegram.ParseMode.HTML)
        for country in friendly_country_list[query_list[1]]:
            if country != query_list[1]:
                message_id = session.handler_list[handler_id].message_id[country]
                if message_id != None:
                    chat_id = db.execute("select playerid from country where id =:country;", {'country':country}).fetchall()
                    bot.delete_message(chat_id=chat_id[0][0], message_id = message_id)
                    session.handler_list[handler_id].message_id[country] = None
        session.handler_list[handler_id].one_side_pass = False
        #card execute
        if query_list[-1] == 'air_a':
            air_a_lock_id = session.add_lock()
            air.air_attack_list.append(air.air_attack(query_list[2], air_a_lock_id, session))
            print("air_attack_id: " + str(len(air.air_attack_list)-1))
            air_attack_id = len(air.air_attack_list)-1
            info = air.air_attack_list[air_attack_id].air_attack_info(session)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            session.thread_lock(air_a_lock_id)
        elif query_list[-1] == 'air_d':
            air.air_defense(bot, query_list[2], session)
        else:
            cardfunction.play_status(bot, query_list[-1], query_list[1], query_list[2], session)
        #card execute
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        session.handler_list[handler_id].message_id[query_list[1]] = None
        session.handler_list[handler_id].first = False
    else:
        if query_list[3] == 'back':
            info = info_list[info_type](query_list[1], handler_id, session)
            chat_id = info[0]
            text = info[1]
            reply_markup = info[2]
        else:
            selected = db.execute("select name, type, text from card where cardid = :cardid;", {'cardid':query_list[-1]}).fetchall()
            text = "<b>" + selected[0][0] + "</b> - " + selected[0][1] + " - " + selected[0][2]
            keyboard = []
            if query_list[3] != 'no_play':
                keyboard += [[InlineKeyboardButton('Confirm', callback_data="['{}', '{}', {}, 'confirm', {}]".format(query_list[0], query_list[1], query_list[2], query_list[-1]))]]
            keyboard += [[InlineKeyboardButton('Back', callback_data="['{}', '{}', {}, 'back']".format(query_list[0], query_list[1], query_list[2]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_caption(chat_id=query.message.chat_id, message_id=query.message.message_id, caption=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    if query_list[3] in ['pass', 'confirm']:
        #enemy_country_list = db.execute("select id, playerid from country where side = (select enemy from country where id = :country);", {'country':query_list[1]}).fetchall()
        pass_ = True
        for country in enemy_country_list[query_list[1]]:
            info = info_list[info_type](country, handler_id, session)
            message_id = session.handler_list[handler_id].message_id[country] 
            if info[2] == None:                         #No response
                if message_id != None:
                    bot.delete_message(chat_id= info[0], message_id = message_id)
                    session.handler_list[handler_id].message_id[country] = None
                session.handler_list[handler_id].no_respone[country] = True
            else:                                       #Have response
                print('have - response ' + country)
                session.handler_list[handler_id].no_respone[country] = False
                pass_ = False
                if message_id == None:
                    status_message_id = bot.send_photo(chat_id = info[0], caption = info[1], reply_markup = info[2], parse_mode=telegram.ParseMode.HTML, photo=open(session.get_dir() + '/tmp.jpg', 'rb'))
                    session.handler_list[handler_id].message_id[country] = status_message_id.message_id
                else:
                    bot.edit_message_caption(chat_id = info[0], message_id = message_id, caption = info[1], reply_markup = info[2], parse_mode=telegram.ParseMode.HTML)
        if pass_:
            air.check_reposition(bot, session)
            if session.handler_list[handler_id].one_side_pass:
                session.handler_list.pop(handler_id)
                session.release_lock(lock_id)
                return
            session.handler_list[handler_id].one_side_pass = True
            pass_ = True
            #friendly_country_list = db.execute("select id, playerid from country where side = (select side from country where id = :country);", {'country':query_list[1]}).fetchall()
            for country in friendly_country_list[query_list[1]]:
                info = info_list[info_type](country, handler_id, session)
                message_id = session.handler_list[handler_id].message_id[country]
                if info[2] == None:   #No respone
                    if message_id != None:
                        bot.delete_message(chat_id= info[0], message_id = message_id)
                        session.handler_list[handler_id].message_id[country] = None
                    session.handler_list[handler_id].no_respone[country] = True
                else:       #Have respone
                    print('have - response ' + country)
                    session.handler_list[handler_id].no_respone[country] = False
                    pass_ = False
                    if message_id == None:
                        status_message_id = bot.send_photo(chat_id = info[0], caption = info[1], reply_markup = info[2], parse_mode=telegram.ParseMode.HTML, photo=open(session.get_dir() + '/tmp.jpg', 'rb'))
                        session.handler_list[handler_id].message_id[country] = status_message_id.message_id
                    else:
                        bot.edit_message_caption(chat_id = info[0], message_id = message_id, caption = info[1], reply_markup = info[2], parse_mode=telegram.ParseMode.HTML)
            if pass_:
                air.check_reposition(bot, session)
                session.handler_list.pop(handler_id)
                session.release_lock(lock_id)

    #------------------------------------------Status Handler Info------------------------------------------
        #--------------------------------------------Battle---------------------------------------------
def status_battle_handler(bot, active_country, passive_country, space, session):
    print('in status_battle_handler - ' + active_country)
    db = sqlite3.connect(session.get_db_dir())
    s = [41, 47, 52, 347]
    space_info = db.execute("select distinct spaceid, type, name from space where spaceid = :space", {'space':space}).fetchall()
    questionmarks = '?' * len(s)
    avaliable_card = db.execute("select cardid, name from card where location = 'played' and cardid in ({});".format(','.join(questionmarks)), (s)).fetchall()
    if len(avaliable_card) > 0:
        for card in avaliable_card:
            if card[0] == 41 and passive_country in ('ge','jp','it') and space == 12:
                cardfunction.c41(bot, active_country, session)
            if card[0] == 47 and passive_country == 'ge' and space_info[0][1] == 'land':
                cardfunction.c47(bot, active_country, session)
                db.execute("update card set location = 'turn' where cardid = 47")
            if card[0] == 52 and passive_country in ('ge','jp','it') and space == 16:
                cardfunction.c52(bot, active_country, session)
                db.execute("update card set location = 'turn' where cardid = 52")
            if card[0] == 347 and passive_country =='ch':
                cardfunction.c347(bot, session)
        db.commit()
                
def status_battle_handler_info(country, handler_id, session):
    print('in status_battle_handler_info - ' + country)
    db = sqlite3.connect(session.get_db_dir())
    s = {'ge':[43, 45], 'jp':[97, 98, 99, 101, 102, 104, 107, 109, 112, 119, 120], 'it':[167, 168, 170], 'uk':[229, 230, 231, 232, 234, 242], 'su':[276, 284, 286, 287, 288, 289, 291, 292, 296, 303], 'us':[344, 346, 350, 363], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    space_info = db.execute("select distinct spaceid, type, name from space where spaceid = :space", {'space':session.handler_list[handler_id].space_id}).fetchall()
    piece_info = db.execute("select control, location, supply, type from piece where pieceid = :piece;", {'piece':session.handler_list[handler_id].piece_id}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    keyboard = []
    if country == 'jp':
        response_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Response';").fetchall()[0][0]
    if country == 'su':
        ba_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Build Army';").fetchall()[0][0]
        piece_count = db.execute("select count(*) from piece where control = 'su' and type = 'army' and location != 'none';").fetchall()[0][0]
    if country == 'us':
        ew_count = db.execute("select count(*) from card where location = 'hand' and control ='us' and type = 'Economic Warfare';").fetchall()[0][0]
    if not cardfunction.c59_used:
        if country == session.handler_list[handler_id].active_country_id:
            list1 = function.within(function.getside[session.handler_list[handler_id].active_country_id], [session.handler_list[handler_id].space_id], 1, db)
            list2 = function.control_air_space_list(session.handler_list[handler_id].active_country_id, db)
            if len([list1 and list2]) > 0  and session.handler_list[handler_id].air_defense and not session.handler_list[handler_id].air_attack:
                keyboard.append([InlineKeyboardButton('Air Attack', callback_data="['status_battle', '{}', {}, 'confirm', 'air_a']".format(country, handler_id))])
        if country == session.handler_list[handler_id].passive_country_id and session.handler_list[handler_id].first:
            if session.handler_list[handler_id].space_id in function.control_air_space_list(session.handler_list[handler_id].passive_country_id, db):
                keyboard.append([InlineKeyboardButton('Air Defense', callback_data="['status_battle', '{}', {}, 'confirm', 'air_d']".format(country, handler_id))])
    if len(avaliable_card) > 0:
        for card in avaliable_card:
            if country == 'ge':
                if card[0] == 43 and active_country == 'ge' and space_info[0][1] == 'land':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 45 and active_country == 'ge' and space_info[0][1] == 'land':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'jp':
                if card[0] == 97 and active_country == 'jp' and space_info[0][1] == 'land':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data = "['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 98 and piece_info[0][0] == 'jp' and space_info[0][0] in function.supplied_space_list('jp', db, space_type = 'sea'):   
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 99 and active_country == 'jp' and space_info[0][0] in [35,36,37]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 101 and active_country == 'jp' and space_info[0][1] == 'sea':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 102 and active_country == 'jp' and space_info[0][0] == 36:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 104 and active_country == 'jp' and space_info[0][0] == 32:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 107 and piece_info[0][0] == 'jp' and space_info[0][0] in list(set([35,37,42]) & set(function.supplied_space_list('jp', db, space_type = 'land'))):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 109 and piece_info[0][0] == 'jp' and space_info[0][0] in [38,43]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 112 and active_country == 'jp' and space_info[0][1] == 'sea':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 119 and active_country == 'jp' and space_info[0][1] == 'sea':
                    if response_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Response card in hand', callback_data="['status_battle', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
                if card[0] == 120 and piece_info[0][0] == 'jp' and space_info[0][1] == 'land':
                    if response_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Response card in hand', callback_data="['status_battle', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'it':
                if card[0] == 167 and piece_info[0][0] == 'it' and space_info[0][0] in function.within('Axis', [17], 1, db):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 168 and piece_info[0][0] == 'ge' and space_info[0][0] == 17:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 170 and piece_info[0][0] == 'ge' and piece_info[0][3] == 'army' and space_info[0][0] in function.supplied_space_list('ge', db, space_type = 'land'):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'uk':
                if card[0] == 229 and active_country == 'uk' and space_info[0][1] == 'sea':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 230 and piece_info[0][0] == 'uk' and space_info[0][0] in function.supplied_space_list('uk', db, space_type = 'land') and piece_info[0][3] == 'army':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 231 and piece_info[0][0] in ['uk','us'] and space_info[0][0] in list(set(function.within('Allies', function.supplied_space_list('uk', db, space_type = 'land'), 1, db)) & set(function.supplied_space_list(piece_info[0][0], db, space_type = 'sea'))):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 232 and active_country in ['uk','us','fr'] and space_info[0][0] in [12,13,19,25]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 234 and piece_info[0][0] in ['uk','su','us','fr','ch'] and space_info[0][0] in list(set([8,9]) & set(function.supplied_space_list(piece_info[0][0], db, space_type = 'sea'))):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 242 and piece_info[0][0] == 'fr' and space_info[0][0] == 12:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'su':
                if card[0] == 276 and active_country == 'su' and space_info[0][1] == 'land':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 284 and active_country == 'su' and space_info[0][1] == 'land':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 286 and piece_info[0][0] == 'su' and space_info[0][0] in [30,31]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 287 and piece_info[0][0] == 'su':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 288 and piece_info[0][0] == 'su' and space_info[0][0] == 20:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 289 and piece_info[0][0] == 'su' and space_info[0][0] == 28:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 291 and piece_info[0][0] == 'su' and space_info[0][0] in[24,28]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 292 and piece_info[0][0] == 'su' and space_info[0][0] == 24:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 296 and piece_info[0][0] == 'su' and piece_count == 0:
                    if ba_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Build Army in hand', callback_data="['status_battle', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
                if card[0] == 303 and active_country == 'su' and space_info[0][0] in[20,21,22,24]:
                    if ba_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Build Army in hand', callback_data="['status_battle', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'us':
                if card[0] == 344 and active_country == 'us' and space_info[0][1] == 'sea' and function.can_build(active_country, space_info[0][0], db):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 346 and active_country == 'us' and space_info[0][1] == 'land' and space_info[0][0] in function.within('Allies', function.control_supplied_space_list('us', db, space_type = 'sea'), 1, db) and space_info[0][0] in function.build_list('us', db):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 350 and piece_info[0][0] == 'us' and piece_info[0][3] == 'navy' and space_info[0][0] in function.supplied_space_list('us', db, space_type = 'sea'):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 363 and active_country == 'us':
                    if ew_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_battle', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Economic Warfare in hand', callback_data="['status_battle', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
    if len(keyboard) > 0:
        card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':session.handler_list[handler_id].card_id}).fetchall()
        keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_battle', '{}', {}, 'pass']".format(country, handler_id))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "<b>[" + card_name[0][0] + "]</b> - " + function.countryid2name[country] + " - " + space_info[0][2] + " is battled by " + function.countryid2name[active_country]
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

        #--------------------------------------------Build---------------------------------------------
def status_build_handler(bot, active_country, session):
    print('in status_build_handler - ' + active_country)
    db = sqlite3.connect(session.get_db_dir())
    s = [347]
    questionmarks = '?' * len(s)
    avaliable_card = db.execute("select cardid, name from card where location = 'played' and cardid in ({});".format(','.join(questionmarks)), (s)).fetchall()
    if len(avaliable_card) > 0:
        for card in avaliable_card:
            if card[0] == 347 and active_country =='ch':
                cardfunction.c347(bot, session)
        db.commit()

def status_build_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_build_handler_info - ' + country)
    s = {'ge': [42,50,58], 'jp':[106, 110, 111, 121], 'it':[169], 'uk':[233], 'su':[275, 280, 282, 290], 'us':[348, 353, 354, 357, 362], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    space_info = db.execute("select distinct spaceid, type, name from space where spaceid = :space", {'space':session.handler_list[handler_id].space_id}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        if country == 'jp':
            response_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Response';").fetchall()[0][0]
        if country == 'su':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Build Army';").fetchall()[0][0]
            lb_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Land Battle';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'ge':
                if card[0] == 42 and active_country == 'ge' and space_info[0][1] == 'land':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 50 and active_country == 'ge' and space_info[0][1] == 'land':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 58 and active_country == 'ge' and space_info[0][1] == 'sea':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'jp':
                if card[0] == 106 and active_country in ['uk', 'su', 'us', 'fr', 'ch'] and space_info[0][0] in function.filter_space_list(function.within('Axis', function.control_space_list('jp', db), 1, db), db, control = 'all', space_type = 'sea'):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 110 and active_country == 'jp' and space_info[0][1] == 'sea':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 111 and active_country == 'jp' and space_info[0][1] == 'sea':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 121 and active_country == 'jp' and space_info[0][1] == 'sea':
                    if response_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Response card in hand', callback_data="['status_build', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'it':
                if card[0] == 169 and active_country == 'su' and (space_info[0][0] in function.filter_space_list(function.within('Allies', function.control_space_list('uk', db), 1, db), db, control = 'all', space_type = 'land') or space_info[0][0] in function.filter_space_list(function.within('Allies', function.control_space_list('us', db), 1, db), db, control = 'all', space_type = 'land')):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'uk':
                if card[0] == 233 and active_country in ['ge', 'jp', 'it'] and space_info[0][0] in [1,32,41]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'su':
                if card[0] == 275 and active_country == 'su' and space_info[0][1] == 'land':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 280 and active_country == 'su' and space_info[0][1] == 'land':
                    if ba_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Build Army in hand', callback_data="['status_build', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
                if card[0] == 282 and active_country == 'su' and space_info[0][1] == 'land':
                    if ba_count > 0 and lb_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Build Army/Land Battle in hand', callback_data="['status_build', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
                if card[0] == 290 and active_country in ['ge', 'jp', 'it'] and space_info[0][0] in [20,24,28,30,31]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'us':
                if card[0] == 348 and active_country == 'us' and space_info[0][1] == 'sea':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 353 and active_country == 'us' and space_info[0][1] == 'sea':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 354 and active_country == 'us' and space_info[0][0] in [3,5,7,27,40,43,44,47,50,53]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 357 and active_country == 'us' and space_info[0][1] == 'land':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 362 and active_country == 'us' and space_info[0][0] in [3,44,47,50,53]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_build', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':session.handler_list[handler_id].card_id}).fetchall()
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_build', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "<b>[" + card_name[0][0] + "]</b> - " + function.countryid2name[country] + " - " + function.countryid2name[active_country] + " built in " + space_info[0][2]
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

        #--------------------------------------------Remove---------------------------------------------
def status_remove_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_remove_handler_info - ' + country)
    s = {'ge': [], 'jp':[98, 107, 109], 'it':[168, 170], 'uk':[230, 231, 234, 242], 'su':[286, 288, 289, 291, 292, 296], 'us':[350], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    piece_info = db.execute("select control, location, supply, type from piece where pieceid = :piece", {'piece':session.handler_list[handler_id].piece_id}).fetchall()
    space_info = db.execute("select distinct spaceid, type, name from space where spaceid = :space", {'space':session.handler_list[handler_id].space_id}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        if country == 'jp':
            response_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Response';").fetchall()[0][0]
        if country == 'su':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Build Army';").fetchall()[0][0]
            piece_count = db.execute("select count(*) from piece where control = 'su' and type = 'army' and location != 'none';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'jp':
                if card[0] == 98 and piece_info[0][0] == 'jp' and piece_info[0][3] == 'navy' and space_info[0][0] in function.supplied_space_list('jp', db, space_type = 'sea'):   
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 107 and piece_info[0][0] == 'jp' and space_info[0][0] in list(set([35,37,42]) & set(function.supplied_space_list('jp', db, space_type = 'land'))):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 109 and piece_info[0][0] == 'jp' and space_info[0][0] in [38,43]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'it':
                if card[0] == 168 and piece_info[0][0] == 'ge' and space_info[0][0] == 17:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 170 and piece_info[0][0] == 'ge' and piece_info[0][3] == 'army' and space_info[0][0] in function.supplied_space_list('ge', db, space_type = 'land'):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'uk':
                if card[0] == 230 and piece_info[0][0] == 'uk' and space_info[0][0] in function.supplied_space_list('uk', db, space_type = 'land') and piece_info[0][3] == 'army':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 231 and piece_info[0][0] in ['uk','us'] and space_info[0][0] in list(set(function.within('Allies', function.control_supplied_space_list('uk', db, space_type = 'land'), 1, db)) & set(function.supplied_space_list(piece_info[0][0], db, space_type = 'sea'))) and piece_info[0][3] == 'navy':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 234 and piece_info[0][0] in ['uk','su','us','fr','ch'] and space_info[0][0] in list(set([8,9]) & set(function.supplied_space_list(piece_info[0][0], db, space_type = 'sea'))) and piece_info[0][3] == 'navy':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 242 and piece_info[0][0] == 'fr' and space_info[0][0] == 12 and piece_info[0][3] == 'army':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="[status_remove'', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'su':
                if card[0] == 286 and piece_info[0][0] == 'su' and space_info[0][0] in [30,31]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 288 and piece_info[0][0] == 'su' and space_info[0][0] == 20:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 289 and piece_info[0][0] == 'su' and space_info[0][0] == 28:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 291 and piece_info[0][0] == 'su' and space_info[0][0] in[24,28]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 292 and piece_info[0][0] == 'su' and space_info[0][0] == 24:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 296 and piece_info[0][0] == 'su' and piece_count == 0:
                    if ba_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Build Army in hand', callback_data="['status_remove', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'us':
                if card[0] == 350 and piece_info[0][0] == 'us' and piece_info[0][3] == 'navy' and space_info[0][0] in function.supplied_space_list('us', db, space_type = 'sea'):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_remove', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':session.handler_list[handler_id].card_id}).fetchall()
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_remove', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            if len(card_name) > 0:
                text = "<b>[" + card_name[0][0] + "]</b> - " + function.countryid2name[country] + " - " + function.countryid2name[piece_info[0][0]] + " piece in " + space_info[0][2] + " removed"
            else:
                text = function.countryid2name[country] + " - " + function.countryid2name[piece_info[0][0]] + " piece in " + space_info[0][2] + " removed"
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

    #----------------------Recuit-----------------------
def status_recuit_handler(bot, active_country, session):
    print('in status_recuit_handler - ' + active_country)
    db = sqlite3.connect(session.get_db_dir())
    s = [347]
    questionmarks = '?' * len(s)
    avaliable_card = db.execute("select cardid, name from card where location = 'played' and cardid in ({});".format(','.join(questionmarks)), (s)).fetchall()
    if len(avaliable_card) > 0:
        for card in avaliable_card:
            if card[0] == 347 and active_country =='ch':
                cardfunction.c347(bot, session)
        db.commit()
        
def status_recuit_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_recuit_handler_info - ' + country)
    s = {'ge': [], 'jp':[], 'it':[], 'uk':[233], 'su':[290], 'us':[], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    space_info = db.execute("select distinct spaceid, type, name from space where spaceid = :space", {'space':session.handler_list[handler_id].space_id}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        if country == 'jp':
            response_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Response';").fetchall()[0][0]
        if country == 'su':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Build Army';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'uk':
                if card[0] == 233 and active_country in ['ge', 'jp', 'it'] and space_info[0][0] in [1,32,41]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_recuit', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'su':
                if card[0] == 290 and active_country in ['ge', 'jp', 'it'] and space_info[0][0] in [20,24,28,30,31]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_recuit', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':session.handler_list[handler_id].card_id}).fetchall()
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_recuit', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "<b>[" + card_name[0][0] + "]</b> - " + function.countryid2name[country] + " - " + function.countryid2name[active_country] + " recuit in " + space_info[0][2]
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

    #--------------------------------------------Deploy/Marshal---------------------------------------------
def status_deploy_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_deploy_handler_info - ' + country)
    s = {'ge': [63,64], 'jp':[124, 126], 'it':[177], 'uk':[], 'su':[300], 'us':[370], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    space_info = db.execute("select distinct spaceid, type, name from space where spaceid = :space", {'space':session.handler_list[handler_id].space_id}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        if country == 'jp':
            response_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Response';").fetchall()[0][0]
        if country == 'su':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Build Army';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'ge':
                if card[0] == 63 and active_country == 'ge':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_deploy', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 64 and active_country == 'ge':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_deploy', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'jp':
                if card[0] == 124 and active_country == 'jp' and space_info[0][1] == 'sea':
                    if response_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_deploy', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Response card in hand', callback_data="['status_deploy', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
                if card[0] == 126 and active_country == 'jp':
                    if response_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_deploy', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Response card in hand', callback_data="['status_deploy', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'it':
                if card[0] == 177 and active_country == 'it':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_deploy', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'su':
                if card[0] == 300 and active_country == 'su':
                    if ba_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_deploy', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Build Army in hand', callback_data="['status_deploy', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'us':
                if card[0] == 370 and active_country == 'us':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_deploy', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':session.handler_list[handler_id].card_id}).fetchall()
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_deploy', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            if len(card_name) > 0:
                text = "<b>[" + card_name[0][0] + "]</b> - " + function.countryid2name[country] + " - " + function.countryid2name[active_country] + " deploy/marshal in " + space_info[0][2]
            else:
                text = function.countryid2name[country] + " - " + function.countryid2name[active_country] + " deploy/marshal in " + space_info[0][2]
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

    #----------------------Play Step-----------------------
def status_before_play_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_before_play_handler_info - ' + country)
    s = {'ge': [59, 60, 62, 66], 'jp':[100, 103, 105, 108, 113, 127], 'it':[175], 'uk':[243, 244], 'su':[297], 'us':[365], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        if country == 'ge':
            air_count = db.execute("select count(*) from piece where control ='ge' and type = 'air' and location != 'none';").fetchall()[0][0]
        if country == 'jp':
            response_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Response';").fetchall()[0][0]
        if country == 'it':
            navy_count = db.execute("select count(*) from piece where control ='it' and type = 'navy' and location != 'none';").fetchall()[0][0]
        if country == 'su':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Build Army';").fetchall()[0][0]
        if country == 'us':
            bs_count = db.execute("select count(*) from card where location = 'hand' and control ='us' and type = 'Bolster';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'ge':
                if card[0] == 59 and active_country == 'ge':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 60 and active_country == 'ge':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 62 and active_country == 'ge':
                    if air_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Air Force on the board', callback_data="['status_before_play', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
                if card[0] == 66 and active_country == 'ge':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'jp':
                if card[0] == 100 and active_country == 'jp':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 103 and active_country == 'jp':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 105 and active_country == 'jp':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 108 and active_country == 'jp':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 113 and active_country == 'jp':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 127 and active_country == 'jp':
                    if response_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Response card in hand', callback_data="['status_before_play', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'it':
                if card[0] == 175 and active_country == 'it' and navy_count != 0:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'uk':
                if card[0] == 243:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 244 and active_country == 'uk':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'su':
                if card[0] == 297 and active_country == 'su':
                    if ba_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Build Army in hand', callback_data="['status_before_play', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'us':
                if card[0] == 365 and active_country == 'us':
                    if bs_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_before_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Bolster in hand', callback_data="['status_before_play', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_before_play', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = function.countryid2name[country] + " - Beginning of " + function.countryid2name[active_country] + " Play step"
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup    

def status_play_keyboard(country, db):
    print('in status_play_keyboard - ' + country)
    s = {'ge': [44], 'jp':[], 'it':[161], 'uk':[], 'su':[278, 279], 'us':[345], 'fr':[], 'ch':[]}
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        extra_keyboard = []
        if country == 'it':
            dis_land_battle_count = db.execute("select count(*) from card where name = 'Land Battle' and location in ('played','discardd') and control = 'it';").fetchall()[0][0]
        if country == 'su':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Build Army';").fetchall()[0][0]
        if country == 'us':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='us' and type = 'Build Army';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'ge':
                if card[0] == 44 and country == 'ge':
                    extra_keyboard.append([InlineKeyboardButton("Status - " + card[1], callback_data="['status_play', '{}', {}]".format(country, card[0]))])
            if country == 'it':
                if card[0] == 161 and country == 'it':
                    if dis_land_battle_count > 0:
                        extra_keyboard.append([InlineKeyboardButton("Status - " + card[1], callback_data="['status_play', '{}', {}]".format(country, card[0]))])
                    else:
                        extra_keyboard.append([InlineKeyboardButton("Status - " + card[1] + ' - No Land Battle in discard', callback_data="['status_play', '{}', 'no_play', {}]".format(country, card[0]))])
            if country == 'su':
                if card[0] == 278 and country == 'su':
                    extra_keyboard.append([InlineKeyboardButton("Status - " + card[1], callback_data="['status_play', '{}', {}]".format(country, card[0]))])
                if card[0] == 279 and country == 'su':
                    if ba_count > 0:
                        extra_keyboard.append([InlineKeyboardButton("Status - " + card[1], callback_data="['status_play', '{}', {}]".format(country, card[0]))])
                    else:
                        extra_keyboard.append([InlineKeyboardButton("Status - " + card[1] + ' - No Build Army in hand', callback_data="['status_play', '{}', 'no_play', {}]".format(country, card[0]))])
            if country == 'us':
                if card[0] == 345 and country == 'us':
                    if ba_count > 0:
                        extra_keyboard.append([InlineKeyboardButton("Status - " + card[1], callback_data="['status_play', '{}', {}]".format(country, card[0]))])
                    else:
                        extra_keyboard.append([InlineKeyboardButton("Status - " + card[1] + ' - No Build Army in hand', callback_data="['status_play', '{}', 'no_play', {}]".format(country, card[0]))])
        return extra_keyboard
    else:
        return None

def status_after_play_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_after_play_handler_info - ' + country)
    s = {'ge': [], 'jp':[], 'it':[], 'uk':[227], 'su':[285], 'us':[], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    played_card = session.handler_list[handler_id].card_id
    card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':played_card}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        for card in avaliable_card:
            if country == 'uk':
                if card[0] == 227 and active_country == 'uk':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_after_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'su':
                if card[0] == 285 and active_country == 'su' and played_card in [246,247,248,249,250,251,252,253,254]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_after_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_after_play', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = function.countryid2name[country] + " - " + function.countryid2name[active_country] + " played " + card_name[0][0]
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup                

def status_play_status_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_play_status_handler_info - ' + country)
    s = {'ge': [], 'jp':[], 'it':[], 'uk':[241], 'su':[], 'us':[], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    played_card = session.handler_list[handler_id].card_id
    card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':played_card}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        for card in avaliable_card:
            if country == 'uk':
                if card[0] == 241 and active_country in ['ge', 'jp', 'it']:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_after_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_after_play', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = function.countryid2name[country] + " - " + function.countryid2name[active_country] + " use " + card_name[0][0]
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

def status_play_bolster_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_play_bolster_handler_info - ' + country)
    s = {'ge': [], 'jp':[], 'it':[], 'uk':[239], 'su':[], 'us':[], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    played_card = session.handler_list[handler_id].card_id
    card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':played_card}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        for card in avaliable_card:
            if country == 'uk':
                if card[0] == 239 and active_country in ['ge', 'it']:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_after_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_after_play', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = function.countryid2name[country] + " - " + function.countryid2name[active_country] + " use " + card_name[0][0]
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup
#----------------------Air Step-----------------------
def status_air_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_air_handler_info - ' + country)
    s = {'ge': [], 'jp':[], 'it':[], 'uk':[238], 'su':[299], 'us':[364], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    played_card = session.handler_list[handler_id].card_id
    card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':played_card}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        if country == 'jp':
            response_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Response';").fetchall()[0][0]
        if country == 'su':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Build Army';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'uk':
                if card[0] == 238 and active_country == 'uk':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_after_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'su':
                if card[0] == 299 and active_country == 'su':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_after_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'us':
                if card[0] == 364 and active_country == 'us':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_after_play', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_after_play', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = function.countryid2name[country] + " - Beginning of " + function.countryid2name[active_country] + " Air step"
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

    #----------------------Victory Step-----------------------
def status_victory_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_victory_handler_info - ' + country)
    s = {'ge': [65], 'jp':[122, 125], 'it':[176, 180, 181], 'uk':[240, 245], 'su':[302], 'us':[368, 369], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        if country == 'jp':
            response_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Response';").fetchall()[0][0]
        if country == 'su':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Build Army';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'ge':
                if card[0] == 65 and active_country == 'ge':
                    keyboard.append([InlineKeyboardButton("Bolster - " + card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'jp':
                if card[0] == 122 and active_country == 'jp':
                    if response_count > 0:
                        keyboard.append([InlineKeyboardButton("Bolster - " + card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton("Bolster - " + card[1] + ' - No Response card in hand', callback_data="['status_victory', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
                if card[0] == 125 and active_country == 'jp':
                    keyboard.append([InlineKeyboardButton("Bolster - " + card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'it':
                if card[0] == 176 and active_country == 'it':
                    keyboard.append([InlineKeyboardButton("Bolster - " + card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 180 and active_country == 'it':
                    keyboard.append([InlineKeyboardButton("Bolster - " + card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 181 and active_country == 'it':
                    keyboard.append([InlineKeyboardButton("Bolster - " + card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'uk':
                if card[0] == 240 and active_country == 'uk':
                    keyboard.append([InlineKeyboardButton("Bolster - " + card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 245 and active_country == 'uk':
                    keyboard.append([InlineKeyboardButton("Bolster - " + card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'su':
                if card[0] == 302 and active_country == 'su':
                    if ba_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Build Army in hand', callback_data="['status_victory', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'us':
                if card[0] == 368 and active_country == 'us':
                    keyboard.append([InlineKeyboardButton("Bolster - " + card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 369 and active_country == 'us':
                    keyboard.append([InlineKeyboardButton("Bolster - " + card[1], callback_data="['status_victory', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_victory', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = function.countryid2name[country] + " - Beginning of " + function.countryid2name[active_country] + " Victory step"
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

def status_extra_victory_point(country, db):
    print('in status_extra_victory_point - ' + country)
    s = {'ge': [40, 49], 'jp':[91, 92, 93, 94, 95, 96], 'it':[159, 160, 162, 163, 164], 'uk':[], 'su':[], 'us':[], 'fr':[], 'ch':[]}
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where location = 'played' and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        text = ""
        extra_point = 0
        for card in avaliable_card:
            if country == 'ge':
                if card[0] == 40 and 24 in function.control_space_list('ge', db):
                    text += function.countryid2name[country] + " gain 1 point from <b>" + card[1] + "</b>\n"
                    extra_point += 1
                if card[0] == 49 and 15 in function.control_space_list('ge', db):
                    if 11 in function.control_space_list('ge', db):
                        text += function.countryid2name[country] + " gain 2 point from <b>" + card[1] + "</b>\n"
                        extra_point += 2
                    else:
                        text += function.countryid2name[country] + " gain 1 point from <b>" + card[1] + "</b>\n"
                        extra_point += 1
            if country == 'jp':
                if card[0] == 91:
                    navy_count = db.execute("select count(*) from piece where control = 'jp' and type = 'navy' and location != 'none';").fetchall()
                    if navy_count[0][0] >= 3:
                        text += function.countryid2name[country] + " gain 1 point from <b>" + card[1] + "</b>\n"
                        extra_point += 1
                if card[0] == 92:
                    c92_point = 0
                    if 48 in function.control_space_list('jp', db):
                        c92_point += 1
                    if 49 in function.control_space_list('jp', db):
                        c92_point += 1
                    if 51 in function.control_space_list('jp', db):
                        c92_point += 1
                    if c92_point > 0:
                        text += function.countryid2name[country] + " gain " + str(c92_point) + " point from <b>" + card[1] + "</b>\n"
                        extra_point += c92_point
                if card[0] == 93:
                    c93_point = 0
                    if 33 in function.control_space_list('jp', db):
                        c93_point += 1
                    if 36 in function.control_space_list('jp', db):
                        c93_point += 1
                    if 45 in function.control_space_list('jp', db):
                        c93_point += 1
                    if c93_point > 0:
                        text += function.countryid2name[country] + " gain " + str(c93_point) + " point from <b>" + card[1] + "</b>\n"
                        extra_point += c93_point
                if card[0] == 94:
                    c94_point = 0
                    if 30 in function.control_space_list('jp', db):
                        c94_point += 1
                    if 42 in function.control_space_list('jp', db):
                        c94_point += 1
                    if c94_point > 0:
                        text += function.countryid2name[country] + " gain " + str(c94_point) + " point from <b>" + card[1] + "</b>\n"
                        extra_point += c94_point
                if card[0] == 95 and not {39, 46}.isdisjoint(set(function.control_space_list('jp', db))):
                    text += function.countryid2name[country] + " gain 1 point from <b>" + card[1] + "</b>\n"
                    extra_point += 1
                if card[0] == 96 and 44 in function.control_space_list('jp', db):
                    text += function.countryid2name[country] + " gain 1 point from <b>" + card[1] + "</b>\n"
                    extra_point += 1
            if country == 'it':
                if card[0] == 159 and not {20, 24}.isdisjoint(set(function.control_space_list('it', db))):
                    text += function.countryid2name[country] + " gain 1 point from <b>" + card[1] + "</b>\n"
                    extra_point += 1
                if card[0] == 160 and 22 in function.control_space_list('it', db):
                    text += function.countryid2name[country] + " gain 1 point from <b>" + card[1] + "</b>\n"
                    extra_point += 1
                if card[0] == 162:
                    c162_point = 0
                    if 13 in function.control_space_list('it', db) or 13 in function.control_space_list('ge', db):
                        c162_point += 1
                    if 19 in function.control_space_list('it', db) or 19 in function.control_space_list('ge', db):
                        c162_point += 1
                    if 25 in function.control_space_list('it', db) or 25 in function.control_space_list('ge', db):
                        c162_point += 1
                    if c162_point > 0:
                        text += function.countryid2name[country] + " gain " + str(c162_point) + " point from <b>" + card[1] + "</b>\n"
                        extra_point += c162_point
                if card[0] == 163 and 12 in function.control_space_list('it', db):
                    text += function.countryid2name[country] + " gain 1 point from <b>" + card[1] + "</b>\n"
                    extra_point += 1     
                if card[0] == 164:
                    navy_count = db.execute("select count(*) from piece where control = 'it' and type = 'navy' and location != 'none';").fetchall()
                    text += function.countryid2name[country] + " gain " + str(navy_count[0][0]) + " point from <b>" + card[1] + "</b>\n"
                    extra_point += navy_count[0][0]
        if extra_point > 0:
            return extra_point, text
        else:
            return None

                    
    #----------------------Draw Step-----------------------
def status_draw_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_draw_handler_info - ' + country)
    s = {'ge': [48], 'jp':[], 'it':[], 'uk':[], 'su':[295, 298], 'us':[366], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        if country == 'jp':
            response_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Response';").fetchall()[0][0]
        if country == 'su':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Build Army';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'ge':
                if card[0] == 48 and active_country == 'ge':
                    card_count = db.execute("select count(*) from card where location = 'deck' and control = 'ge';").fetchall()
                    if card_count[0][0] != 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_draw', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'su':
                if card[0] == 295 and active_country == 'su':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_draw', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 298 and active_country == 'su':
                    if ba_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_draw', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Build Army in hand', callback_data="['status_draw', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'us':
                if card[0] == 366 and active_country == 'us':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_draw', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_draw', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = function.countryid2name[country] + " - " + "Beginning of " + function.countryid2name[active_country] + " Draw step:"   
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

    #----------------------Discard Step-----------------------                                            

def status_discard_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_discard_handler_info - ' + country)
    s = {'ge': [], 'jp':[], 'it':[], 'uk':[], 'su':[301], 'us':[351], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    active_country = session.handler_list[handler_id].active_country_id
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        if country == 'jp':
            response_count = db.execute("select count(*) from card where location = 'hand' and control ='jp' and type = 'Response';").fetchall()[0][0]
        if country == 'su':
            ba_count = db.execute("select count(*) from card where location = 'hand' and control ='su' and type = 'Build Army';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'su':
                if card[0] == 301 and active_country == 'su':
                    if ba_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_discard', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Build Army in hand', callback_data="['status_discard', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'us':
                if card[0] == 351 and active_country == 'us':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_discard', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_discard', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = function.countryid2name[country] + " - " + "Beginning of " + function.countryid2name[active_country] + " Discard step:"
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

    #----------------------Build Location-----------------------
def status_build_location(country, db):
    print('in status_build_location - ' + country)
    s = {'ge': [], 'jp':[], 'it':[], 'uk':[220, 224, 226], 'su':[], 'us':[], 'fr':[228], 'ch':[345]}
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where location = 'played' and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        extra_space_list = []
        for card in avaliable_card:
            if country == 'uk':
                if card[0] == 220:
                    extra_space_list.append(41)
                if card[0] == 224:
                    extra_space_list.append(32)
                if card[0] == 226:
                    extra_space_list.append(21)
            if country == 'fr':
                if card[0] == 228:
                    extra_space_list.append(13)
        return extra_space_list

    #----------------------Battle Location-----------------------
def status_battle_location(country, db):
    print('in status_battle_location - ' + country)
    s = {'ge': [51], 'jp':[], 'it':[], 'uk':[], 'su':[], 'us':[], 'fr':[], 'ch':[]}
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where location = 'played' and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        extra_space_list = []
        for card in avaliable_card:
            if country == 'ge':
                if card[0] == 39:
                    extra_space_list.append(16)
        return extra_space_list
                    
    #----------------------VP Location-----------------------
def status_vp_location(country, space_list, db):
    print('in status_vp_location - ' + country)
    temp_space_list = space_list.copy()
    s = {'ge': [281], 'jp':[], 'it':[281], 'uk':[225, 226], 'su':[277],'us':[], 'fr':[228], 'ch':[345]}
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where location = 'played' and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        for card in avaliable_card:
            if country in ['ge', 'it']:
                if card[0] == 281 and 24 in space_list:
                    temp_space_list.remove(24)
            if country == 'uk':
                if card[0] == 225:
                    temp_space_list.append(1)
                if card[0] == 226:
                    temp_space_list.append(21)
            if country == 'su':
                if card[0] == 277:
                    temp_space_list.append(30)
            if country == 'fr':
                if card[0] == 228:
                    temp_space_list.append(13)        
            if country == 'ch':
                if card[0] == 345:
                    temp_space_list.append(35)
    return temp_space_list

    #----------------------Supply-----------------------
def status_supply(db):
    print('in status_supply')
    s = [221, 279, 281, 283]
    questionmarks = '?' * len(s)
    avaliable_card = db.execute("select cardid, name from card where location in ('played', 'turn') and cardid in ({});".format(','.join(questionmarks)), (s)).fetchall()
    if len(avaliable_card) > 0:
        for card in avaliable_card:
            if card[0] == 221:
                db.execute("update piece set supply = 1 where control = 'fr';")
            if card[0] == 279:
                db.execute("update piece set supply = 1 where control = 'ch' and type = 'army';")
            if card[0] == 281:
                db.execute("update piece set supply = 0 where control in ('ge','it') and location = '24';")
            if card[0] == 283:
                db.execute("update piece set supply = 1 where control = 'su' and type = 'army';")
    if cardfunction.c62_used:
        db.execute("update piece set supply = 1 where control = 'ge';")
    db.commit()

def status_supply_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_supply_handler_info - ' + country)
    s = {'ge': [], 'jp':[114], 'it':[], 'uk':[], 'su':[], 'us':[], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        for card in avaliable_card:
            if country == 'jp':
                if card[0] == 114:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_supply', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_supply', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = function.countryid2name[country] + " - " + "Supply step:"
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup

    #----------------------Economic Warfare-----------------------
def status_ew_handler(bot, cardid, active_country, passive_country, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_ew_handler - ' + active_country)
    s = [39, 46, 53, 349]
    card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':cardid}).fetchall()
    questionmarks = '?' * len(s)
    avaliable_card = db.execute("select cardid, name from card where location = 'played' and cardid in ({});".format(','.join(questionmarks)), (s)).fetchall()
    extra_number = 0
    if len(avaliable_card) > 0:
        for card in avaliable_card:
            if card[0] == 39 and passive_country == 'ge':
                extra_number -= 2
            if card[0] == 46 and passive_country == 'ge':
                cardfunction.c46(bot, active_country, session)
            if card[0] == 53 and active_country == 'ge' and 'Submarine' in card_name[0][0]:
                if 11 in function.control_space_list('ge', db):
                    extra_number += 2
                else:
                    extra_number += 1
            if card[0] == 349 and active_country == 'us':
                extra_number += 1
    if cardfunction.c62_used:
        extra_number -= 4
        cardfunction.c62_used = False
    return extra_number
    

def status_ew_handler_info(country, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    print('in status_ew_handler_info - ' + country)
    s = {'ge': [61, 67], 'jp':[123], 'it':[171, 174, 179], 'uk':[], 'su':[], 'us':[367], 'fr':[], 'ch':[]}
    chat_id = db.execute("select playerid from country where id = :id;",{'id':country}).fetchall()
    passive_country = session.handler_list[handler_id].passive_country_id
    active_country = session.handler_list[handler_id].active_country_id
    played_card = session.handler_list[handler_id].card_id
    card_name = db.execute("select name from card where cardid = :cardid;",{'cardid':played_card}).fetchall()
    questionmarks = '?' * len(s[country])
    avaliable_card = db.execute("select cardid, name from card where (location = 'played' or (location = 'hand' and type = 'Bolster')) and cardid in ({});".format(','.join(questionmarks)), (s[country])).fetchall()
    if len(avaliable_card) > 0:
        keyboard = []
        if country == 'it':
            air_count = db.execute("select count(*) from piece where control ='it' and type = 'air' and location != 'none';").fetchall()[0][0]
        for card in avaliable_card:
            if country == 'ge':
                if card[0] == 61 and active_country == 'ge' and 'Submarine' in card_name[0][0]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_ew', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 67 and active_country == 'ge':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_ew', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'jp':
                if card[0] == 123 and passive_country == 'jp' and 38 in function.control_air_space_list('jp', db):
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_ew', '{}', {}, {}]".format(country, handler_id, card[0]))])
            if country == 'it':
                if card[0] == 171 and passive_country == 'it' and 'Bomb' in card_name[0][0]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_ew', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 174 and active_country == 'ge' and 'Submarine' in card_name[0][0]:
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_ew', '{}', {}, {}]".format(country, handler_id, card[0]))])
                if card[0] == 179 and passive_country == 'it':
                    if air_count > 0:
                        keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_ew', '{}', {}, {}]".format(country, handler_id, card[0]))])
                    else:
                        keyboard.append([InlineKeyboardButton(card[1] + ' - No Air Force on the board', callback_data="['status_ew', '{}', {}, 'no_play', {}]".format(country, handler_id, card[0]))])
            if country == 'us':
                if card[0] == 367 and active_country == 'us':
                    keyboard.append([InlineKeyboardButton(card[1], callback_data="['status_ew', '{}', {}, {}]".format(country, handler_id, card[0]))])
        if len(keyboard) > 0:
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['status_ew', '{}', {}, 'pass']".format(country, handler_id))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = function.countryid2name[passive_country]  + " is attacked by " + card_name[0][0]
        else:
            reply_markup = None
            text = None
    else:
        reply_markup = None
        text = None
    return chat_id[0][0], text, reply_markup






info_list = {'Battle':status_battle_handler_info,
             'Build':status_build_handler_info,
             'Remove':status_remove_handler_info,
             'Recruit':status_recuit_handler_info,
             'Beginning of Play step':status_before_play_handler_info,
             'After Playing a card':status_after_play_handler_info,
             'Using Status':status_play_status_handler_info,
             'Using Bolster':status_play_bolster_handler_info,
             'Beginning of Air step':status_air_handler_info,
             'Beginning of Victory step':status_victory_handler_info,
             'Beginning of Draw step':status_draw_handler_info,
             'Beginning of Discard step':status_discard_handler_info,
             'Checking Supply':status_supply_handler_info,
             'Economic Warfare':status_ew_handler_info,
             'Deploy/Marshal':status_deploy_handler_info
             }
