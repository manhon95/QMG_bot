import telegram
import sqlite3
import function
import thread_lock
import battlebuild
import random
import buffer
import air
import drawmap
import traceback

from telegram import ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

#----------------------Pass-----------------------
pass_ = True
#----------------------Reallocate Resources-----------------------
def r_r(bot, country, db):
    print('in r_r')
    group_chat_id = db.execute("select chatid from game;").fetchall()
    text = "<b>" + function.countryid2name[country] + "</b> uses Reallocate Resources"
    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    if country == 'us' and db.execute("select location from card where cardid = 355;").fetchall()[0][0] == 'played':
        function.discardhand(bot, country, 1, db)
    else:
        function.discardhand(bot, country, 4, db)
    lock_id = thread_lock.add_lock()
    info = r_r_info(bot, country, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    if info[2] != None:
        thread_lock.thread_lock(lock_id)

def r_r_info(bot, country, lock_id, db):
    chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    keyboard = []
    card_list = ['Build Army', 'Build Navy', 'Land Battle', 'Sea Battle', 'Deploy Air Force']
    for card in card_list:
        if country == 'us' and db.execute("select location from card where cardid = 356;").fetchall()[0][0] == 'played' and db.execute("select count(*) from card where name = :card and location in ('discardu', 'discardd', 'played') and control=:country;", {'country':country, 'card':card}).fetchall()[0][0] > 0:
            keyboard.append([InlineKeyboardButton('Discard - ' + card, callback_data="['r_r', '{}', '{}', {}]".format(country, card, lock_id))])
        elif db.execute("select count(*) from card where name = :card and location = 'deck' and control = :country;", {'country':country, 'card':card}).fetchall()[0][0] > 0:
            keyboard.append([InlineKeyboardButton(card, callback_data="['r_r', '{}', '{}', {}]".format(country, card, lock_id))])
    if len(keyboard) > 0:
        if country == 'us' and db.execute("select location from card where cardid = 356;").fetchall()[0][0] == 'played':
            text = "Choose a card from your deck and discrd pile:"
        else:
            text = "Choose a card from your deck:"
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        if country == 'us' and db.execute("select location from card where cardid = 356;").fetchall()[0][0] == 'played':
            text = "You have no Build Army, Build Navy, Land Battle, Sea Battle or Deploy Air Force in your deck and discrd pile"
        else:
            text = "You have no Build Army, Build Navy, Land Battle, Sea Battle or Deploy Air Force in your deck"
        reply_markup = None
    return  chat_id[0][0], text, reply_markup

def r_r_cb(bot, query, query_list, db):
    if query_list[1] == 'confirm':
        bot.delete_message(chat_id= query.message.chat_id, message_id = query.message.message_id)
        if query_list[2] == 'us' and db.execute("select location from card where cardid = 356;").fetchall()[0][0] == 'played' and db.execute("select count(*) from card where name = :card and location in ('discardu', 'discardd', 'played') and control=:country;", {'country':query_list[2], 'card':query_list[3]}).fetchall()[0][0] > 0:
            card_id = db.execute("select min(cardid) from card where name = :card and location in ('discardu', 'discardd', 'played') and control=:country;", {'country':query_list[2], 'card':query_list[3]}).fetchall()[0][0]
        else:
            card_id = db.execute("select min(cardid) from card where name = :card and location = 'deck' and control=:country;", {'country':query_list[2], 'card':query_list[3]}).fetchall()[0][0]
        function.movecardhand(bot, card_id, db)
        function.shuffledeck(bot, query_list[2], db)
        thread_lock.release_lock(query_list[-1])
    elif query_list[1] == 'back':
        info = r_r_info(bot, query_list[2], query_list[3], db)
        bot.edit_message_text(chat_id = query.message.chat_id, message_id = query.message.message_id, text = info[1], reply_markup = info[2])
    else:
        text = "You chose " + query_list[2]
        keyboard = [[InlineKeyboardButton('Confirm', callback_data="['r_r', 'confirm', '{}', '{}', {}]".format(query_list[1], query_list[2], query_list[3]))],
                    [InlineKeyboardButton('Back', callback_data="['r_r', 'back', '{}', {}]".format(query_list[1], query_list[3]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)

#----------------------Card Handler-----------------------
def card_cb_handler(bot, query, query_list):
    db = sqlite3.connect('database.db')
    group_chat = db.execute("select chatid from game;").fetchall()
    country_name = db.execute("select name from country where id = :country;", {'country':query_list[1]}).fetchall()
    card_name = db.execute("select name from card where cardid = :card;", {'card':query_list[2]}).fetchall()
    text = country_name[0][0] + " play <b>" + card_name[0][0] + "</b>"
    bot.send_message(chat_id = group_chat[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    eval(query_list[-1])
                               
#---------------------Play Card------------------------
cardtofunction = {#ge
                  2:1,3:1,4:1,5:1,6:1,
                  8:7,
                  10:9,11:9,12:9,13:9,14:9,15:9,16:9,
                  18:17,
                  23:22,
                  #jp
                  69:68,70:68,71:68,
                  73:72,74:72,75:72,76:72,77:72,78:72,
                  80:79,81:79,
                  83:82,84:82,85:82,
                  #it
                  129:128,130:128,131:128,
                  133:132,134:132,135:132,
                  137:136,138:136,139:136,140:136,
                  142:141,
                  #uk
                  183:182,184:182,185:182,186:182,
                  188:187,189:187,190:187,191:187,192:187,
                  194:193,195:193,196:193,
                  198:197,199:197,200:197,201:197,
                  208:204,
                  215:214,
                  #su
                  247:246,248:246,249:246,250:246,251:246,252:246,253:246,254:246,
                  257:256,258:256,259:256,260:256,261:256,262:256,
                  264:263,
                  #us
                  305:304,306:304,307:304,308:304,
                  310:309,311:309,312:309,313:309,
                  315:314,316:314,317:314,
                  319:318,320:318,321:318,
                  323:322,
                  327:326
                  }
                  
def play_card(bot, cardid, country, db):
    db.execute("update card set location = 'played' where cardid = :card", {'card':cardid})
    db.commit()
    group_chat = db.execute("select chatid from game;").fetchall()
    country_name = db.execute("select name from country where id = :country;", {'country':country}).fetchall()
    card_info = db.execute("select name, type from card where cardid = :card;", {'card':cardid}).fetchall()
    if card_info[0][1] == "Response":
        text = country_name[0][0] + " play a <b>Response</b>"
    else:
        text = country_name[0][0] + " play <b>" + card_info[0][0] +"</b>"
    bot.send_message(chat_id = group_chat[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    #if card_info[0][1] == "Economic Warfare":
        #status_handler.status_ew_handler(bot, cardid, country, passive_country, db)
    if card_info[0][1] not in ("Status", "Response"):
        if cardid in cardtofunction:
            function = "c" + str(cardtofunction[cardid]) + "(bot, db)"
        else:
            function = "c" + str(cardid) + "(bot, db)"
        eval(function)

#---------------------Play Status------------------------
need_info_status = [42,43,45,50,53,61,63,64,97,98,99,101,106,107,109,110,111,119,120,124,126,167,168,169,170,177,227,229,230,231,232,233,234,242,243,244,276,282,284,285,286,287,288,289,290,292,295,300,303,344,346,348,349,350,354,362,363,367,370]
once_per_turn_status = [42,43,45,47,50,52,227,229,272,275,276,280,344,348,350,351,353,357]
def play_status(bot, cardid, country, handler_id, db):
    card_info = db.execute("select name, type from card where cardid = :card;", {'card':cardid}).fetchall()
    group_chat = db.execute("select chatid from game;").fetchall()
    country_name = db.execute("select name from country where id = :country;", {'country':country}).fetchall()
    text = country_name[0][0] + " use " + card_info[0][0]
    bot.send_message(chat_id = group_chat[0][0], text = text)
    if card_info[0][1] == 'Response':
        db.execute("update card set location = 'used' where cardid = :card", {'card':cardid})
    elif card_info[0][1] == 'Bolster':
        import status_handler
        lock_id = thread_lock.add_lock()
        status_handler.send_status_card(bot, country, 'Using a status', lock_id, db, card_id = cardid)
        db.execute("update card set location = 'used' where cardid = :card", {'card':cardid})
    else:
        import status_handler
        lock_id = thread_lock.add_lock()
        status_handler.send_status_card(bot, country, 'Using a status', lock_id, db, card_id = cardid)
    if cardid in once_per_turn_status:
        db.execute("update card set location = 'turn' where cardid = :card", {'card':cardid})
    db.commit()
    global c241_used, c239_used
    if c241_used or c239_used:
        c239_used = False
        c241_used = False
        text = card_info[0][0] + " cancelled"
        bot.send_message(chat_id = group_chat[0][0], text = text)
    else:
        if cardid in need_info_status:
            function = "c" + str(cardid) + "(bot, {}, db)".format(handler_id)
        else:
            function = "c" + str(cardid) + "(bot, db)"
        eval(function)
    
#---------------------card------------------------
    #------------------c1~6----------------------
def c1(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('ge', db), 'ge', db, space_type = 'land')
    space_list = function.build_list('ge', db, space_type = 'land')
    info = battlebuild.build_info(bot, 'ge', space_list, 1, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c7~8----------------------
def c7(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('ge', db), 'ge', db, space_type = 'sea')
    space_list = function.build_list('ge', db, space_type = 'sea')
    info = battlebuild.build_info(bot, 'ge', space_list, 7, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c9~16----------------------
def c9(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('ge', db), 'ge', db, space_type = 'land')
    space_list = function.battle_list('ge', db, space_type = 'land')
    info = battlebuild.battle_info(bot, 'ge', space_list, 9, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c17~18----------------------
def c17(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('ge', db), 'ge', db, space_type = 'sea')
    space_list = function.battle_list('ge', db, space_type = 'sea')
    info = battlebuild.battle_info(bot, 'ge', space_list, 17, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c19---------------------
def c19(bot, db):
    if {11,20}.isdisjoint(set(function.side_control_space_list('Axis', db, space_type = 'all'))):
        function.ewdiscard(bot, 19, 'ge', 'su', 5, db)
        function.add_vp(bot, 'ge', 1, db)
    #------------------c20---------------------
def c20(bot, db):
    lock_id = thread_lock.add_lock()
    chat_id = db.execute("select playerid from country where id = 'ge';").fetchall()
    keyboard = [[InlineKeyboardButton("United Kingdom", callback_data="['c20', 'uk', {}]".format(lock_id))],
                [InlineKeyboardButton("Soviet Union", callback_data="['c20', 'su', {}]".format(lock_id))],
                [InlineKeyboardButton("United States", callback_data="['c20', 'us', {}]".format(lock_id))]]
    text = "Choose a player to discard the top card of its draw deck:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)
    
def c20_cb(bot, query, query_list, db):
    bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
    if query_list[1] == 'uk':
        #function.discarddeck(bot, 'ge', 4, db)
        function.ewdiscard(bot, 20, 'ge', 'uk', 1, db)
    elif query_list[1] == 'su':
        #function.discarddeck(bot, 'it', 4, db)
        function.ewdiscard(bot, 20, 'ge', 'su', 1, db)
    elif query_list[1] == 'us':
        #function.discarddeck(bot, 'it', 4, db)
        function.ewdiscard(bot, 20, 'ge', 'us', 1, db)
    function.add_vp(bot, 'ge', 3, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c21~22----------------------
def c21(bot, db):
    space_list = function.within('Axis', function.control_space_list('ge', db), 1, db)
    if 9 in space_list:
        #function.discarddeck(bot, 'uk', 3, db)
        function.ewdiscard(bot, 21, 'ge', 'uk', 3, db)
        function.add_vp(bot, 'ge', 1, db)

    #------------------c23----------------------
def c23(bot, db):
    space_list = function.control_space_list('ge', db)
    space_list2 = function.within('Axis', space_list, 1, db)
    if 9 in space_list:
        #function.discarddeck(bot, 'us', 5, db)
        function.ewdiscard(bot, 23, 'ge', 'us', 5, db)
        function.add_vp(bot, 'ge', 1, db)
    elif 9 in space_list2:
        #function.discarddeck(bot, 'us', 3, db)
        function.ewdiscard(bot, 23, 'ge', 'us', 3, db)
        function.add_vp(bot, 'ge', 1, db)
        
    #------------------c24----------------------
def c24(bot, db):
    space_list = function.control_space_list('ge', db)
    if 11 in space_list:
        #function.discarddeck(bot, 'su', 5, db)
        function.ewdiscard(bot, 24, 'ge', 'su', 5, db)
    else:
        #function.discarddeck(bot, 'su', 2, db)
        function.ewdiscard(bot, 24, 'ge', 'su', 2, db)
    function.add_vp(bot, 'ge', 1, db)

    #------------------c25----------------------
def c25(bot, db):
    space_list = function.within('Axis', function.control_space_list('ge', db), 1, db)
    if 9 in space_list:
        #function.discarddeck(bot, 'uk', 2, db)
        function.ewdiscard(bot, 25, 'ge', 'uk', 2, db)
        function.add_vp(bot, 'ge', 2, db)

    #------------------c26----------------------
def c26(bot, db):
    if 12 in function.battle_list('ge', db):
        lock_id = thread_lock.add_lock()
        info = battlebuild.battle_info(bot, 'ge', [12], 26, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    if 12 in function.build_list('ge', db):
        battlebuild.build(bot, 'ge', 12, 26, db)


    #------------------c27----------------------
def c27(bot, db):
    ge_battle_space_list = function.battle_list('ge', db, space_type = 'land')
    su_space_list = function.control_space_list('su', db)
    #org_space_list = [space for space in ge_battle_space_list if space in su_space_list]
    org_space_list = list(set(ge_battle_space_list) & set(su_space_list))
    for i in range(3):
        #space_list = function.filter_battle_list(org_space_list, 'ge', db, space_type = 'land')
        space_list = list(set(org_space_list) & set(function.battle_list('ge', db, space_type = 'land')))
        if len(space_list) > 0:
            lock_id = thread_lock.add_lock()
            info = battlebuild.battle_info(bot, 'ge', space_list, 27, lock_id, db)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)
        
    #------------------c28----------------------
def c28(bot, db):
    function.discarddeck(bot, 'ge', 1, db)
    if 21 in function.recuit_list('ge', db):
        battlebuild.recuit(bot, 'ge', 21, 28, db)
    lock_id = thread_lock.add_lock()
    hand = db.execute("select name, cardid from card where location = 'hand' and control = 'ge' order by sequence;").fetchall()
    playerid = db.execute("select playerid from country where id = 'ge';").fetchall()
    keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['c28', {}, {}]".format(hand[x][1], lock_id))] for x in range(len(hand))]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = playerid[0][0], text = "Play a card", reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)
    
def c28_cb(bot, query, query_list, db):
    if query_list[1] == 'confirm':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        cardid = db.execute("select cardid from card where location = 'selected';").fetchall()
        play_card(bot, cardid[0][0], 'ge', db)
        db.commit()
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[1] == 'back':
            db.execute("update card set location = 'hand' where location = 'selected' and control = 'ge';")
            text = 'play a card'
            hand = db.execute("select name, cardid from card where location = 'hand' and control = 'ge' order by sequence;").fetchall()
            keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['c28', {}, {}]".format(hand[x][1], query_list[-1]))] for x in range(len(hand))]
        else:
            db.execute("update card set location = 'selected' where cardid =:id and control = 'ge';", {'id': query_list[1]})
            selected = db.execute("select name, type, text from card where location = 'selected' and control = 'ge' order by sequence;").fetchall()
            text = "<b>" + selected[0][0] + "</b> - " + selected[0][1] + " - " + selected[0][2]
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c28', 'confirm', {}]".format(query_list[-1]))], [InlineKeyboardButton('Back', callback_data="['c28', 'back', {}]".format(query_list[-1]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    db.commit()
    
    #------------------c29----------------------
def c29(bot, db):
    for i in range(2):
        space_list = list(set(function.within('Axis', [16], 1, db)) & set(function.recuit_list('ge', db, space_type = 'land')))
        if len(space_list) > 0:
            lock_id = thread_lock.add_lock()
            info = battlebuild.recuit_info(bot, 'ge', space_list, 29, lock_id, db)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)

    #------------------c30----------------------
def c30(bot, db):
    lock_id = thread_lock.add_lock()
    info = c30_info(bot, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    if info[2] != None:
        thread_lock.thread_lock(lock_id)

def c30_info(bot, lock_id, db):
    chat_id = db.execute("select playerid from country where id = 'ge';").fetchall()
    keyboard = []
    card_list = ['Build Army', 'Build Navy', 'Land Battle', 'Sea Battle']
    for card in card_list:
        if db.execute("select count(*) from card where name = :card and location = 'deck' and control = 'ge';", {'card':card}).fetchall()[0][0] > 0:
            keyboard.append([InlineKeyboardButton(card, callback_data="['c30', '{}', {}]".format(card, lock_id))])
    if len(keyboard) > 0:
        text = "Choose and play a card from your deck"
        keyboard.append([InlineKeyboardButton('Pass', callback_data="['c30', 'Pass', {}]".format(lock_id))])
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        text = "You have no Build Army, Build Navy, Land Battle or Sea Battle in your deck"
        reply_markup = None
    return  chat_id[0][0], text, reply_markup

def c30_cb(bot, query, query_list, db):
    if query_list[1] == 'confirm':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        card = {'Build Army':1, 'Build Navy':7, 'Land Battle':9, 'Sea Battle':16}
        play_card(bot, card[query_list[2]], 'ge', db)
        function.shuffledeck(bot, 'ge', db)
        thread_lock.release_lock(query_list[-1])
    elif query_list[1] == 'back':
        info = c25_info(bot, query_list[2], db)
        bot.edit_message_text(chat_id = query.message.chat_id, message_id = query.message.message_id, text = info[1], reply_markup = info[2])
    elif query_list[1] == 'pass':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
        text = "Germany play nothing"
        bot.send_message(chat_id = chat_id[0][0], text = text)
        thread_lock.release_lock(query_list[-1])
    else:
        text = "You chose " + query_list[1]
        keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c30', 'confirm', '{}', {}]".format(query_list[1], query_list[2]))],
                    [InlineKeyboardButton('Back', callback_data="['c30', 'back', {}]".format(query_list[2]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)

    #------------------c31----------------------
def c31(bot, db):
    lock_id = thread_lock.add_lock()
    chat_id = db.execute("select playerid from country where id = 'ge';").fetchall()
    keyboard = [[InlineKeyboardButton("Recruit an Italian Army in the Balkans", callback_data="['c31', 'recruit', {}]".format(lock_id))],
                [InlineKeyboardButton("Eliminate an Allied Army in Ukraine", callback_data="['c31', 'eliminate', {}]".format(lock_id))]]
    text = "Choose what to do first:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)
    
def c31_cb(bot, query, query_list, db):
    if query_list[1] == 'recruit':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        if function.can_recuit('it', 22, db):
            battlebuild.recuit(bot, 'it', 22, 31, db)
        if function.can_remove('ge', 24, db):
            piece_list = db.execute("select country.name, piece.pieceid from piece inner join country on piece.control = country.id where piece.location = '24';").fetchall()
            if len(piece_list) == 1:
                battlebuild.remove(bot, 'ge', piece_list[0][1], 24, 31, db)
            else:
                lock_id = thread_lock.add_lock()
                keyboard = [[InlineKeyboardButton(piece[0], callback_data="['c31', {}, {}]".format(piece[1], lock_id))] for piece in piece_list]
                text = "Choose a piece to remove:"
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.send_message(chat_id = query.message.chat_id, text = text, reply_markup = reply_markup)
                thread_lock.thread_lock(lock_id)
            thread_lock.release_lock(query_list[-1])    
    elif query_list[1] == 'eliminate':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        if function.can_remove('ge', 24, db):
            piece_list = db.execute("select country.name, piece.pieceid from piece inner join country on piece.control = country.id where piece.location = '24';").fetchall()
            if len(piece_list) == 1:
                battlebuild.remove(bot, 'ge', piece_list[0][1], 24, 31, db)
            else:
                lock_id = thread_lock.add_lock()
                keyboard = [[InlineKeyboardButton(piece[0], callback_data="['c31', {}, {}]".format(piece[1], lock_id))] for piece in piece_list]
                text = "Choose a piece to remove:"
                reply_markup = InlineKeyboardMarkup(keyboard)
                bot.send_message(chat_id = query.message.chat_id, text = text, reply_markup = reply_markup)
                thread_lock.thread_lock(lock_id)
            if function.can_recuit('it', 22, db):
                battlebuild.recuit(bot, 'it', 22, 31, db)
            thread_lock.release_lock(query_list[-1])
    else:
        battlebuild.remove(bot, 'ge', query_list[1], 24, 31, db)
        thread_lock.release_lock(query_list[-1])

    #------------------c32----------------------
def c32(bot, db):
    army = db.execute("select count(*) from piece where control = 'ge' and location != 'none' and type = 'army';").fetchall()
    function.add_vp(bot, 'ge', army[0][0], db)

    #------------------c33----------------------
def c33(bot, db):
    lock_id = thread_lock.add_lock()
    info = c33_info(bot, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    if info[2] != None:
        thread_lock.thread_lock(lock_id)

def c33_info(bot, lock_id, db):
    chat_id = db.execute("select playerid from country where id = 'ge';").fetchall()
    keyboard = []
    status_list = db.execute("select cardid, name from card where type = 'Status' and location = 'deck' and control = 'ge';").fetchall()
    for status in status_list:
        keyboard.append([InlineKeyboardButton(status[1], callback_data="['c33', '{}', {}]".format(status[0], lock_id))])
    if len(keyboard) > 0:
        text = "Choose and play a Status card from your deck"
        keyboard.append([InlineKeyboardButton('Pass', callback_data="['c33', 'Pass', {}]".format(lock_id))])
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        text = "You have no Status card in your deck"
        reply_markup = None
    return  chat_id[0][0], text, reply_markup

def c33_cb(bot, query, query_list, db):
    if query_list[1] == 'confirm':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        play_card(bot, query_list[2], 'ge', db)
        function.shuffledeck(bot, 'ge', db)
        thread_lock.release_lock(query_list[-1])
    elif query_list[1] == 'back':
        info = c33_info(bot, db)
        bot.edit_message_text(chat_id = query.message.chat_id, message_id = query.message.message_id, text = info[1], reply_markup = info[2])
    elif query_list[1] == 'pass':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
        text = "Germany play nothing"
        bot.send_message(chat_id = chat_id[0][0], text = text)
        thread_lock.release_lock(query_list[-1])
    else:
        card_name = db.execute("select name, type from card where cardid = :cardid;", {'cardid':query_list[1]}).fetchall() 
        text = "You chose " + card_name[0][0]
        keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c33', 'confirm', {}, {}]".format(query_list[1], query_list[2]))],
                    [InlineKeyboardButton('Back', callback_data="['c33', 'back', {}, {}]".format(query_list[1], query_list[2]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)

    #------------------c34----------------------
def c34(bot, db):
    if 9 in function.build_list('ge', db):
        battlebuild.build(bot, 'ge', 9, 34, db)
    if 8 in function.battle_list('ge', db):
        lock_id = thread_lock.add_lock()
        info = battlebuild.battle_info(bot, 'ge', [8], 34, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    
    #------------------c35----------------------
def c35(bot, db):
    for i in range(2):
        lock_id = thread_lock.add_lock()
        info = c35_info(lock_id, db)
        if info != None:
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)
    function.discardhand(bot, 'ge', 1, db)
    function.shuffledeck(bot, 'ge', db)

def c35_info(lock_id, db):
    deck_list = db.execute("select cardid, name, type from card where location = 'deck' and control = 'ge' and type not in ('Build Army', 'Build Navy', 'Land Battle', 'Sea Battle', 'Deploy Air Force');").fetchall()
    if len(deck_list) > 0:
        keyboard = [[InlineKeyboardButton(card[2] + ' - ' + card[1], callback_data="['c35', {}, {}]".format(card[0], lock_id))] for card in deck_list]
    else:
        keyboard = []
    for _type in ['Build Army', 'Build Navy', 'Land Battle', 'Sea Battle', 'Deploy Air Force']:
        count = db.execute("select count(*) from card where location = 'deck' and control = 'ge' and type = :type;", {'type': _type}).fetchall()
        if count[0][0] > 0:
            card_id = db.execute("select min(cardid) from card where location = 'deck' and control = 'ge' and type = :type;", {'type': _type}).fetchall()
            keyboard += [[InlineKeyboardButton(_type + ' - ' + _type, callback_data="['c35', {}, {}]".format(card_id[0][0], lock_id))]]
    if len(keyboard) > 0:
        chat_id = db.execute("select playerid from country where id = 'ge';").fetchall()
        text = 'Take your choice of 1 or 2 cards from your draw deck and add them to your hand:'
        reply_markup = InlineKeyboardMarkup(keyboard)
        return chat_id[0][0], text, reply_markup
    else:
        return None

def c35_cb(bot, query, query_list, db):
    if query_list[1] == 'confirm':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        function.movecardhand(bot, query_list[2], db)                 
        db.close()
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[1] == 'back':
            info =  c35_info(query_list[-1], db)
            text = info[1]
            reply_markup = info[2]
        else:
            selected = db.execute("select name, type, text from card where cardid = :cardid;", {'cardid':query_list[1]}).fetchall()
            text = "<b>" + selected[0][0] + "</b> - " + selected[0][1] + " - " + selected[0][2]
            keyboard = []
            keyboard += [[InlineKeyboardButton('Confirm', callback_data="['c35', 'confirm', {}, {}]".format(query_list[1], query_list[-1]))]]
            keyboard += [[InlineKeyboardButton('Back', callback_data="['c35', 'back', {} ]".format(query_list[-1]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        except:
            traceback.print_exc()
            pass
        db.commit()
        db.close()
                         
    #------------------c36----------------------
def c36(bot, db):
    if 20 in function.control_space_list('ge', db) or 20 in function.control_space_list('su', db):
        lock_id = thread_lock.add_lock()
        chat_id = db.execute("select playerid from country where id = 'ge';").fetchall()
        keyboard = [[InlineKeyboardButton("Build a Navy in the Baltic Sea", callback_data="['c35', 'b', {}]".format(lock_id))],
                    [InlineKeyboardButton("Recuit an Army in Scandinavia", callback_data="['c35', 'r', {}]".format(lock_id))]]
        text = "Choose what to do first:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
    
def c36_cb(bot, query, query_list, db):
    bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
    if query_list[1] == 'b':
        if 15 in function.build_list('ge', db):
            battlebuild.build(bot, 'ge', 15, 36, db)
        if 11 in function.recuit_list('ge', db):
            battlebuild.recuit(bot, 'ge', 11, 36, db)    
    elif query_list[1] == 'r':
        if 11 in function.recuit_list('ge', db):
            battlebuild.recuit(bot, 'ge', 11, 36, db)
        if 15 in function.build_list('ge', db):
            battlebuild.build(bot, 'ge', 15, 36, db)
    thread_lock.release_lock(query_list[-1])
   
    #------------------c37----------------------
c37_list = []
def c37(bot, db):
    global _pass
    _pass = True
    global c37_list
    c37_list = function.control_space_list('ge', db, space_type = 'land')
    while _pass:
        buffer.space_list = c37_list
        lock_id = thread_lock.add_lock()
        info = c37_info(bot, 'ge', c37_list, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

def c37_info(bot, country, space_list, lock_id, db):
    name_list = function.get_name_list(space_list, db)
    chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    text = "Choose a space to remove"
    keyboard = [[InlineKeyboardButton(space[1], callback_data="['c37', '{}', {}, {}]".format(country, space[0], lock_id))] for space in name_list]
    keyboard.append([InlineKeyboardButton('Pass', callback_data="['c37', '{}', 'pass', {}]".format(country, lock_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return chat_id[0][0], text, reply_markup

def c37_cb(bot, query, query_list, db):
    if query_list[2] == 'confirm':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        piece = db.execute("select pieceid from piece where control = 'ge' and location = :space;", {'space':query_list[3]}).fetchall()
        battlebuild.remove(bot, 'ge', piece[0][0], query_list[3], 37, db)
        c1(bot, db)
        global c37_list
        c37_list.remove(query_list[3])
        thread_lock.release_lock(query_list[-1])
    elif query_list[2] == 'pass':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        global _pass
        _pass = False
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            info = c37_info(bot, query_list[1] , buffer.space_list, query_list[-1], db)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[2]}).fetchall()
            text = 'Removed ' + location[0][0] + ':'
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c37', '{}', 'confirm', {}, {}]".format(query_list[1], query_list[2], query_list[3]))], [InlineKeyboardButton('Back', callback_data="['c37', '{}', 'back', {}]".format(query_list[1], query_list[3]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)
        db.commit()

    #------------------c38----------------------
def c38(bot, db):
    if 23 in function.build_list('ge', db):
        battlebuild.build(bot, 'ge', 23, 38, db)
    if 25 in function.recuit_list('ge', db):
        battlebuild.recuit(bot, 'ge', 25, 38, db)

    #------------------c39----------------------

    #------------------c40----------------------

    #------------------c41----------------------   
def c41(bot, active_country, db):
    #active_country = db.execute("select info_1 from status_handler where handler_id = :handler_id;", {'handler_id':handler_id}).fetchall()[0][0]
    function.discarddeck(bot, active_country, 3, db)
    
    #------------------c42----------------------
def c42(bot, handler_id, db):
    built_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'ge', 1, db)
    space_list1 = function.within('Axis', [built_space], 1, db)
    space_list2 = function.battle_list('ge', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.battle_info(bot, 'ge', space_list, 42, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c43----------------------
def c43(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'ge', 1, db)
    if function.can_build('ge', battled_space, db):
        battlebuild.build(bot, 'ge', battled_space, 43, db)
        
    #------------------c44----------------------
def c44(bot, db):
    function.discarddeck(bot, 'ge', 2, db)
    if db.execute("select count(*) from card where name = 'Build Army' and location in ('discardd', 'discardu', 'played') and control = 'ge';").fetchall()[0][0] > 0:
        c1(bot, db)
    
    #------------------c45----------------------
def c45(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'ge', 1, db)
    space_list1 = function.within('Axis', [battled_space], 1, db)
    space_list2 = function.battle_list('ge', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.battle_info(bot, 'ge', space_list, 45, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c46----------------------
def c46(bot, active_country, db):
    function.discarddeck(bot, active_country, 3, db)

    #------------------c47----------------------
def c47(bot, active_country, db):
    function.discarddeck(bot, active_country, 3, db)

    #------------------c48----------------------
c48_list = []
def c48(bot, db):
    global c48_list
    c48_list = []
    lock_id = thread_lock.add_lock()
    card_count = db.execute("select count(*) from card where location = 'deck' and control = 'ge';").fetchall()
    if card_count[0][0] < 3:
        group_chat_id = db.execute("select chatid from game;").fetchall()
        if card_count[0][0] != 0:
            top_card = db.execute("select name, cardid from card where location = 'deck' and control = 'ge';").fetchall()
        text = "<b>" + countryid2name[country] + "</b> finished his deck"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    else:
        top_card = db.execute("select name, cardid from card where location = 'deck' and sequence <= 3 and control = 'ge';").fetchall()
    chat_id = db.execute("select playerid from country where id = 'ge';").fetchall()
    text = "You may examine the top three cards of your draw deck and put them back on top of your draw deck in the order of your choice\n1:"
    keyboard = [[InlineKeyboardButton(card[0], callback_data="['c48', {}, {}]".format(card[1], lock_id))] for card in top_card]
    keyboard.append([InlineKeyboardButton('Pass', callback_data="['c48', 'pass', {}]".format(lock_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)

def c48_cb(bot, query, query_list, db):
    global c48_list
    if query_list[1] == 'confirm':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        for card in c48_list:
            db.execute("update card set sequence = :seq, location = 'deck' where cardid = :cardid;", {'seq':c48_list.index(card) + 1, 'cardid':card})
            db.commit()
        thread_lock.release_lock(query_list[-1])
    elif query_list[1] == 'pass':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        db.execute("update card set location = 'deck' where location = 'selected';")
        db.commit()
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[1] == 'back':
            c48_list = []
            db.execute("update card set location = 'deck' where location = 'selected';")
        else:
            c48_list.append(query_list[1])
            db.execute("update card set location = 'selected' where cardid =:cardid;", {'cardid':query_list[1]})
        db.commit()
        top_card = db.execute("select name, cardid from card where location = 'deck' and sequence <= 3 and control = 'ge';").fetchall()
        text = "You may examine the top three cards of your draw deck and put them back on top of your draw deck in the order of your choice\n"
        if len(c48_list) > 0:
            for i in range(len(c48_list)):
                card_name = db.execute("select name from card where cardid =:cardid;", {'cardid':c48_list[i]}).fetchall()
                text += str(i + 1) + " - " + card_name[0][0] + "\n"
        card_count = db.execute("select count(*) from card where location = 'deck' and control = 'ge';").fetchall()
        if card_count[0][0] < 3:
            if len(c48_list) == card_count:
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c48', 'confirm', {}]".format(query_list[-1]))],
                            [InlineKeyboardButton('Back', callback_data="['c48', 'back', {}]".format(query_list[-1]))]]
        else:
            if len(c48_list) > 2:
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c48', 'confirm', {}]".format(query_list[-1]))],
                            [InlineKeyboardButton('Back', callback_data="['c48', 'back', {}]".format(query_list[-1]))]]
            else:
                keyboard = [[InlineKeyboardButton(card[0], callback_data="['c48', {}, {}]".format(card[1], query_list[-1]))] for card in top_card]
                keyboard.append([InlineKeyboardButton('Pass', callback_data="['c48', 'pass', {}]".format(query_list[-1]))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)
        
    #------------------c49----------------------

    #------------------c50----------------------
def c50(bot, handler_id, db):
    built_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'ge', 2, db)
    space_list1 = function.within('Axis', [built_space], 1, db)
    space_list2 = function.build_list('ge', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.build_info(bot, 'ge', space_list, 50, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c51----------------------

    #------------------c52----------------------
def c52(bot, active_country, db):
    function.discarddeck(bot, active_country, 4, db)

    #------------------c53----------------------
def c53(bot, handler_id, db):
    passive_country = buffer.handler_list[handler_id].passive_country_id
    if 11 in function.control_space_list('ge', db):
        function.discarddeck(bot, passive_country, 2, db)
    else:
        function.discarddeck(bot, passive_country, 1, db)

    #------------------c54-57----------------------

    #------------------c58----------------------
def c58(bot, db):
    function.discarddeck(bot, 'ge', 1, db)
    space_list1 = [5, 9, 10]
    space_list2 = function.battle_list('ge', db, space_type = 'sea')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.battle_info(bot, 'ge', space_list, 58, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c59----------------------

    #------------------c60----------------------
def c60(bot, db):
    function.discarddeck(bot, 'ge', 1, db)
    space_list1 = function.within('Axis', function.control_air_space_list('ge', db), 1, db)
    space_list2 = function.battle_list('ge', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.battle_info(bot, 'ge', space_list, 60, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c61----------------------
def c61(bot, handler_id, db):
    passive_country = buffer.handler_list[handler_id].passive_country_id
    function.discarddeck(bot, 'ge', 1, db)
    space_list1 = function.control_space_list(passive_country, db)
    space_list2 = function.battle_list('ge', db, space_type = 'sea')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.battle_info(bot, 'ge', space_list, 61, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)



    #------------------c62----------------------

    #------------------c63----------------------
def c63(bot, handler_id, db):
    marshalled_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'ge', 1, db)
    space_list1 = function.within('Axis', [marshalled_space], 1, db)
    space_list2 = function.battle_list('ge', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.battle_info(bot, 'ge', space_list, 63, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c64----------------------
def c64(bot, handler_id, db):
    marshalled_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'ge', 1, db)
    lock_id = thread_lock.add_lock()
    space_list1 = function.within('Axis', [marshalled_space], 1, db)
    space_list2 = function.control_side_air_space_list('Allied', db, space_type = 'all')
    space_list = list(set(space_list1) & set(space_list2))
    battlebuild.self_remove_list.append(battlebuild.self_remove('ge', space_list, 64, lock_id, 'air'))
    print("self_remove_id: " + str(len(battlebuild.self_remove_list)-1))
    self_remove_id = len(battlebuild.self_remove_list)-1
    info = battlebuild.self_remove_list[self_remove_id].self_remove_info(db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    lock_id = thread_lock.add_lock()

    #------------------c65----------------------
def c65(bot, db):
    function.discarddeck(bot, 'ge', 1, db)
    if 11 in function.recuit_list('ge', db):
        battlebuild.recuit(bot, 'ge', 11, 65, db)

    #------------------c66----------------------
def c66(bot, db):
    ge_played_status = db.execute("select name, cardid from card where control = 'ge' and location = 'played' and type = 'Status';").fetchall()
    ge_hand_status = db.execute("select name, cardid from card where control = 'ge' and location = 'hand' and type = 'Status';").fetchall()
    if len(ge_status) > 0:
        lock_id = thread_lock.add_lock()
        chat_id = db.execute("select playerid from country where id = 'ge';").fetchall()
        keyboard = [[InlineKeyboardButton(card[0], callback_data="['c66', 1, {}, {}]".format(card[1], lock_id))] for card in ge_played_status]
        text = "Discard your Status card on the table:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
        lock_id = thread_lock.add_lock()
        chat_id = db.execute("select playerid from country where id = 'ge';").fetchall()
        keyboard = [[InlineKeyboardButton(card[0], callback_data="['c66', 2, {}, {}]".format(card[1], lock_id))] for card in ge_hand_status]
        text = "Place a Status card from your hand on the table:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
    
    
def c66_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] == 1:
        function.discardcard(bot, query_list[2], db)
    if query_list[1] == 2:
        play_card(bot, query_list[2], 'ge', db)
    thread_lock.release_lock(query_list[-1])
    
    #------------------c67----------------------
def c67(bot, db):
    space_list1 = function.within('Axis', [8], 2, db)
    space_list2 = function.control_air_space_list('ge', db)
    space_list = list(set(space_list1) & set(space_list2))
    if len(space_list) > 0:
        function.discarddeck(bot, 'uk', 2 * len(space_list), db)

    #------------------c68~71----------------------
def c68(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('jp', db), 'jp', db, space_type = 'land')
    space_list = function.build_list('jp', db, space_type = 'land')
    info = battlebuild.build_info(bot, 'jp', space_list, 67, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c72~78----------------------
def c72(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('jp', db), 'jp', db, space_type = 'sea')
    space_list = function.build_list('jp', db, space_type = 'sea')
    info = battlebuild.build_info(bot, 'jp', space_list, 72, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c79~81----------------------
def c79(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('jp', db), 'jp', db, space_type = 'land')
    space_list = function.battle_list('jp', db, space_type = 'land')
    info = battlebuild.battle_info(bot, 'jp', space_list, 79, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c82~85----------------------
def c82(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('jp', db), 'jp', db, space_type = 'sea')
    space_list = function.battle_list('jp', db, space_type = 'sea')
    info = battlebuild.battle_info(bot, 'jp', space_list, 82, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c86----------------------
def c86(bot, db):
    function.ewdiscard(bot, 86, 'jp', 'us', 2, db)
    function.add_vp(bot, 'jp', 1, db)
    
    #------------------c87----------------------
def c87(bot, db):
    space_list1 = function.within('Axis', [26, 27], 1, db)
    space_list2 = function.control_space_list('jp', db)
    space_list = list(set(space_list1) & set(space_list2))
    count = len(space_list)
    function.ewdiscard(bot, 87, 'jp', 'uk', count, db)

    #------------------c88----------------------
def c88(bot, db):
    function.ewdiscard(bot, 88, 'jp', 'su', 2, db)
    function.add_vp(bot, 'jp', 1, db)

    #------------------c89----------------------
def c89(bot, db):
    function.ewdiscard(bot, 89, 'jp', 'us', 1, db)
    function.add_vp(bot, 'jp', 2, db)
    
    #------------------c90----------------------
def c90(bot, db):
    function.ewdiscard(bot, 90, 'jp', 'uk', 1, db)
    function.add_vp(bot, 'jp', 2, db)

    #------------------c91----------------------
    #------------------c92----------------------
    #------------------c93----------------------
    #------------------c94----------------------
    #------------------c95----------------------
    #------------------c96----------------------
    #------------------c97----------------------
def c97(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    space_list1 = function.filter_space_list(function.within('Axis', [battled_space], 1, db), db, control = 'Allied', space_type = 'land')
    space_list2 = function.within('Axis', function.control_supplied_space_list('jp', db), 1, db)
    space_list = [space for space in space_list1 if space in space_list2]
    lock_id = thread_lock.add_lock()
    info = battlebuild.battle_info(bot, 'jp', space_list, 97, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
    
    #------------------c98----------------------
def c98(bot, handler_id, db):
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()

    #------------------c99----------------------
def c99(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    if function.can_build('jp', battled_space, db):
        battlebuild.build(bot, 'jp', battled_space, 99, db)
    space_list = function.filter_build_list([35, 36, 37], 'jp', db, space_type = 'land')
    if len(space_list) > 0:
        lock_id = thread_lock.add_lock()
        info = battlebuild.build_info(bot, 'jp', space_list, 99, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c100----------------------
def c100(bot, db):
    space_list = function.control_space_list('ch', db)
    if len(space_list) > 0:
        lock_id = thread_lock.add_lock()
        name_list = function.get_name_list(space_list, db)
        chat_id = db.execute("select playerid from country where id = 'jp';").fetchall()
        text = 'Eliminate a Chinese Army:'
        keyboard = [[InlineKeyboardButton(space[1], callback_data="['c100', {}, {}]".format(space[0], lock_id))] for space in name_list]
        keyboard.append([InlineKeyboardButton('Pass', callback_data="['c100','pass', {}]".format(lock_id))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)

def c100_cb(bot, query, query_list, db):
        if query_list[1] == 'pass':
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            thread_lock.release_lock(self.lock_id)
        else:
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            piece_id = db.execute("select pieceid from piece where location = :space and control = 'ch' and type = 'army';", {'space':query_list[1]}).fetchall()
            battlebuild.remove(bot, 'jp', piece_id[0][0], query_list[1], 100, db)
        thread_lock.release_lock(query_list[-1])
    
    #------------------c101----------------------
def c101(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    for i in range(2):
        space_list = function.filter_build_list(function.within('Axis', [battled_space], 1, db), 'jp', db, space_type = 'land')
        if len(space_list) > 0:
            lock_id = thread_lock.add_lock()
            info = battlebuild.build_info(bot, 'jp', space_list, 101, lock_id, db)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)

    #------------------c102----------------------
def c102(bot, db):
    if function.can_remove('jp', 40, db):
        piece_list = db.execute("select country.name, piece.pieceid from piece inner join country on piece.control = country.id where piece.location = '40';").fetchall()
        if len(piece_list) == 1:
            battlebuild.remove(bot, 'jp', piece_list[0][1], 40, 102, db)
        else:
            chat_id = db.execute("select playerid from country where id = 'jp';").fetchall()
            lock_id = thread_lock.add_lock()
            keyboard = [[InlineKeyboardButton(piece[0], callback_data="['c102', {}, {}]".format(piece[1], lock_id))] for piece in piece_list]
            text = "Choose a piece to remove:"
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
            thread_lock.thread_lock(lock_id)
    if function.can_recuit('jp', 40, db):
        battlebuild.recuit(bot, 'jp', 40, 102, db)

def c102_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    battlebuild.remove(bot, 'jp', query_list[1], 40, 102, db)
    thread_lock.release_lock(query_list[-1])


    #------------------c103----------------------
def c103(bot, db):
    if 37 in function.recuit_list('jp', db):
        battlebuild.recuit(bot, 'jp', 37, 103, db)

    #------------------c104----------------------
def c104(bot, db):
    if 32 in function.build_list('jp', db):
            battlebuild.build(bot, 'jp', 32, 104, db)

    #------------------c105----------------------
def c105(bot, db):
    c82(bot, db)
            
    #------------------c106----------------------
def c106(bot, handler_id, db):
    battlebuild.remove(bot, 'jp', buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, 106, db)
    
    #------------------c107----------------------
def c107(bot, handler_id, db):
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()

    #------------------c108----------------------
def c108(bot, db):
    space_list1 = function.within('Axis', [37], 1, db)
    space_list2 = function.battle_list('jp', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    if len(space_list) > 0:
        lock_id = thread_lock.add_lock()
        info = battlebuild.battle_info(bot, 'jp', space_list, 108, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)


    #------------------c109----------------------
def c109(bot, handler_id, db):
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()

    #------------------c110---------------------
def c110(bot, handler_id, db):
    built_space = buffer.handler_list[handler_id].space_id
    for i in range(2):
        space_list1 = function.within('Axis', [built_space], 1, db)
        space_list2 = function.battle_list('jp', db, space_type = 'land')
        space_list = list(set(space_list1) & set(space_list2))
        if len(space_list) > 0:
            lock_id = thread_lock.add_lock()
            info = battlebuild.battle_info(bot, 'jp', space_list, 110, lock_id, db)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)

    #--------------- ---c111----------------------
def c111(bot, handler_id, db):
    built_space = buffer.handler_list[handler_id].space_id
    for i in range(2):
        space_list1 = function.within('Axis', [built_space], 1, db)
        space_list2 = function.build_list('jp', db, space_type = 'land')
        space_list = list(set(space_list1) & set(space_list2))
        if len(space_list) > 0:
            lock_id = thread_lock.add_lock()
            info = battlebuild.build_info(bot, 'jp', space_list, 111, lock_id, db)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)
            
    #------------------c112----------------------
def c112(bot, db):
    space_list = function.battle_list('jp', db, space_type = 'sea')
    if len(space_list) > 0:
        lock_id = thread_lock.add_lock()
        info = battlebuild.battle_info(bot, 'jp', space_list, 112, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    space_list = function.battle_list('jp', db, space_type = 'land')
    if len(space_list) > 0:
        lock_id = thread_lock.add_lock()
        info = battlebuild.battle_info(bot, 'jp', space_list, 112, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c113----------------------
def c113(bot, db):
    if 36 in function.recuit_list('jp', db):
        battlebuild.recuit(bot, 'jp', 36, 113, db)

    #------------------c114---------------------- 
def c114(bot, db):
    db.execute("update card set location = 'turn' where cardid = 114;")
    db.execute("update piece set supply = 1 where control = 'jp' and type = 'navy';")
    db.execute("update piece set supply = 1 where control = 'jp' and type = 'army' and location in (select distinct spaceid from space where adjacency = 44);")
    db.commit()
    
    #------------------c115~118---------------------- 

    #------------------c119---------------------- 
def c119(bot, handler_id, db):
    #TODO discard res
    function.discardresponse(bot, 'jp', 1, db)
    battled_space = buffer.handler_list[handler_id].space_id
    space_list1 = function.within('Axis', [battled_space], 1, db)
    space_list2 = function.battle_list('jp', db, space_type = 'sea')
    space_list = list(set(space_list1) & set(space_list2))
    if len(space_list) > 0:
        lock_id = thread_lock.add_lock()
        info = battlebuild.battle_info(bot, 'jp', space_list, 119, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c120---------------------- 
def c120(bot, handler_id, db):
    #TODO discard res
    function.discardresponse(bot, 'jp', 1, db)
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()

    #------------------c121---------------------- 
def c121(bot, db):
    #TODO discard res
    function.discardresponse(bot, 'jp', 1, db)
    lock_id = thread_lock.add_lock()
    space_list = function.build_list('jp', db, space_type = 'navy')
    info = battlebuild.build_info(bot, 'jp', space_list, 121, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c122---------------------- 
def c122(bot, db):
    #TODO discard res
    function.discardresponse(bot, 'jp', 1, db)
    lock_id = thread_lock.add_lock()
    space_list1 = function.recuit_list('jp', db)
    space_list2 = [33, 39, 45, 46]
    space_list = list(set(space_list1) & set(space_list2))
    info = battlebuild.recuit_info(bot, 'jp', space_list, 122, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c123----------------------

    #------------------c124----------------------
def c124(bot, handler_id, db):
    #TODO discard res
    function.discardresponse(bot, 'jp', 1, db)
    marshalled_space = buffer.handler_list[handler_id].space_id
    space_list1 = function.within('Axis', [marshalled_space], 1, db)
    space_list2 = function.battle_list('jp', db)
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.battle_info(bot, 'jp', space_list, 124, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c125---------------------- 
def c125(bot, db):
    vp_space_count = db.execute("select count(distinct space.spaceid) from space inner join piece on space.spaceid = piece.location where space.name like '%pacific%' and piece.control = 'jp';").fetchall()
    function.add_vp(bot, 'jp', vp_space_count[0][0], db)

    #------------------c126---------------------- 
def c126(bot, handler_id, db):
    marshalled_space = buffer.handler_list[handler_id].space_id
    #TODO discard res
    function.discardresponse(bot, 'jp', 1, db)
    lock_id = thread_lock.add_lock()
    space_list1 = function.within('Axis', [marshalled_space], 1, db)
    space_list2 = function.control_side_air_space_list('Allied', db, space_type = 'all')
    space_list = list(set(space_list1) & set(space_list2))
    battlebuild.self_remove_list.append(battlebuild.self_remove('jp', space_list, 126, lock_id, 'air'))
    print("self_remove_id: " + str(len(battlebuild.self_remove_list)-1))
    self_remove_id = len(battlebuild.self_remove_list)-1
    info = battlebuild.self_remove_list[self_remove_id].self_remove_info(db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
    
    #------------------c127----------------------
def c127(bot, db):
    #TODO discard res
    function.discardresponse(bot, 'jp', 1, db)
    lock_id = thread_lock.add_lock()
    space_list = function.deploy_list('jp', db, space_type = 'sea')
    info = air.deploy_info(bot, 'jp', space_list, 127, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
    
    #------------------c128~131----------------------
def c128(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('it', db), 'it', db, space_type = 'land')
    space_list = function.build_list('it', db, space_type = 'land')
    info = battlebuild.build_info(bot, 'it', space_list, 128, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
    
    #------------------c132~135----------------------
def c132(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('it', db), 'it', db, space_type = 'sea')
    space_list = function.build_list('it', db, space_type = 'sea')
    info = battlebuild.build_info(bot, 'it', space_list, 132, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c136~140----------------------
def c136(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('it', db), 'it', db, space_type = 'land')
    space_list = function.battle_list('it', db, space_type = 'land')
    info = battlebuild.battle_info(bot, 'it', space_list, 136, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c141~142----------------------
def c141(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('it', db), 'it', db, space_type = 'sea')
    space_list = function.battle_list('it', db, space_type = 'sea')
    info = battlebuild.battle_info(bot, 'it', space_list, 141, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c143----------------------
def c143(bot, db):
    #function.discarddeck(bot, 'uk', 1, db)
    function.ewdiscard(bot, 143, 'it', 'uk', 1, db)
    function.add_vp(bot, 'it', 1, db)

    #------------------c144----------------------
def c144(bot, db):
    if 8 in function.control_space_list('uk', db):
        lock_id = thread_lock.add_lock()
        chat_id = db.execute("select playerid from country where id = 'uk';").fetchall()
        keyboard = [[InlineKeyboardButton("Discard the top 3 cards from draw deck", callback_data="['c144', 'discard', {}]".format(lock_id))],
                    [InlineKeyboardButton("Eliminate an Army from the United Kingdom", callback_data="['c144', 'remove', {}]".format(lock_id))]]
        text = "Choose what to do:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
    else:
        function.ewdiscard(bot, 144, 'it', 'uk', 3, db)
    
def c144_cb(bot, query, query_list, db):
    if query_list[1] == 'discard':
        #function.discarddeck(bot, query_list[1], 2, db)
        function.ewdiscard(bot, 144, 'it', 'uk', 3, db)
    elif query_list[1] == 'remove':
        piece = db.execute("select pieceid from piece where location = '8' and control = 'uk' and type = 'army';").fetchall()
        battlebuild.remove(bot, 'uk', piece[0][0], 8, 144, db)
    bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
    thread_lock.release_lock(query_list[-1])

    #------------------c145----------------------
def c145(bot, db):
    space_list = function.within('Allied', function.control_space_list('uk', db, space_type='land'), 2, db)
    if 24 in space_list:
        function.ewdiscard(bot, 145, 'it', 'uk', 2, db)
    function.add_vp(bot, 'it', 1, db)

    
    #------------------c146----------------------
def c146(bot, db):
    space_list = function.control_space_list('it', db)
    if 18 in space_list:
        #function.discarddeck(bot, 'uk', 1, db)
        function.ewdiscard(bot, 146, 'it', 'uk', 1, db)
        function.add_vp(bot, 'it', 2, db)

    #------------------c147----------------------
def c147(bot, db):
    lock_id = thread_lock.add_lock()
    chat_id = db.execute("select playerid from country where id = 'it';").fetchall()
    keyboard = [[InlineKeyboardButton("Recruit a German Army in North Africa", callback_data="['c147', 'na', {}]".format(lock_id))],
                [InlineKeyboardButton("Recruit a German Navy in the Mediterranean", callback_data="['c147', 'm', {}]".format(lock_id))]]
    text = "Choose what to do first:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)

def c147_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] == 'na':
        if function.can_recuit('ge', 19, db):
            battlebuild.recuit(bot, 'ge', 19, 147, db)
        if function.can_recuit('ge', 18, db):
            battlebuild.recuit(bot, 'ge', 18, 147, db)
    elif query_list[1] == 'm':
        if function.can_recuit('ge', 18, db):
            battlebuild.recuit(bot, 'ge', 18, 147, db)
        if function.can_recuit('ge', 19, db):
            battlebuild.recuit(bot, 'ge', 19, 147, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c148----------------------
def c148(bot, db):
    su_response = db.execute("select cardid from card where control = 'su' and location = 'played' and type = 'Response';").fetchall()
    function.facedowndiscardcard(bot, random.choice(su_response)[0], db)
    
    #------------------c149----------------------
def c149(bot, db):
    if 22 in function.remove_list('it', db):
        piece_list = db.execute("select country.name, piece.pieceid from piece inner join country on piece.control = country.id where piece.location = '22' and piece.type = 'army';").fetchall()
        if len(piece_list) == 1:
            battlebuild.remove(bot, 'it', piece_list[0][1], 22, 149, db)
        else:
            chat_id = db.execute("select playerid from country where id = 'it';").fetchall()
            lock_id = thread_lock.add_lock()
            keyboard = [[InlineKeyboardButton(piece[0], callback_data="['c149', {}, {}]".format(piece[1], lock_id))] for piece in piece_list]
            text = "Choose a piece to remove:"
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
            thread_lock.thread_lock(lock_id)
    if 22 in function.recuit_list('ge', db):
        battlebuild.recuit(bot, 'ge', 22, 149, db)


def c149_cb(bot, query, query_list, db):
    battlebuild.remove(bot, 'it', query_list[1], 22, 149, db)
    bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
    thread_lock.release_lock(query_list[-1])

    #------------------c150----------------------
def c150(bot, db):
    country_list = ['ge', 'it', 'jp']
    for country in country_list:
        discard = db.execute("select cardid from card where ((location in ('discardd', 'discardu')) or (location = 'played' and type not in ('Status', 'Response')) or (location = 'used' and type = 'Response')) and control =:country;", {'country':country}).fetchall()
        function.movecardtop(bot, random.choice(discard)[0], db)
    function.add_vp(bot, 'it', 1, db)
    
    #------------------c151----------------------
def c151(bot, db):
    if 17 in function.remove_list('it', db):
        lock_id = thread_lock.add_lock()
        battlebuild.remove_list.append(battlebuild.remove_obj('it', [17], 151, lock_id, 'army'))
        print("remove_id: " + str(len(battlebuild.remove_list)-1))
        remove_id = len(battlebuild.remove_list)-1
        info = battlebuild.remove_list[remove_id].remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c152----------------------
def c152(bot, db):
    lock_id = thread_lock.add_lock()
    chat_id = db.execute("select playerid from country where id = 'it';").fetchall()
    keyboard = [[InlineKeyboardButton("Recruit an Italian Army in North Africa", callback_data="['c152', 'na', {}]".format(lock_id))],
                [InlineKeyboardButton("Recruit an Italian Navy in the Bay of Bengal", callback_data="['c152', 'bob', {}]".format(lock_id))]]
    text = "Choose what to do first:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)

def c152_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] == 'na':
        if function.can_recuit('it', 19, db):
            battlebuild.recuit(bot, 'it', 19, 152, db)
        if function.can_recuit('it', 26, db):
            battlebuild.recuit(bot, 'it', 26, 152, db)
    elif query_list[1] == 'bob':
        if function.can_recuit('it', 26, db):
            battlebuild.recuit(bot, 'it', 26, 152, db)
        if function.can_recuit('it', 19, db):
            battlebuild.recuit(bot, 'it', 19, 152, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c153----------------------
def c153(bot, db):
    for i in range(2):
        space_list = function.filter_build_list([20, 24], 'it', db, space_type = 'land')
        if len(space_list) > 0:
            lock_id = thread_lock.add_lock()
            info = battlebuild.build_info(bot, 'it', space_list, 153, lock_id, db)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)

    #------------------c154----------------------
def c154(bot, db):
    if function.can_recuit('ge', 18, db):
        battlebuild.recuit(bot, 'ge', 18, 154, db)
    if function.can_recuit('it', 18, db):
        battlebuild.recuit(bot, 'it', 18, 154, db)

    #------------------c155----------------------
def c155(bot, db):
    piece = db.execute("select count(*) from piece where control = 'it' and location not in ('none', '17');").fetchall()
    function.add_vp(bot, 'it', piece[0][0], db)

    #------------------c156----------------------
def c156(bot, db):
    if 25 in function.remove_list('it', db):
        lock_id = thread_lock.add_lock()
        battlebuild.remove_list.append(battlebuild.remove_obj('it', [25], 156, lock_id, 'army'))
        print("remove_id: " + str(len(battlebuild.remove_list)-1))
        remove_id = len(battlebuild.remove_list)-1
        info = battlebuild.remove_list[remove_id].remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c157----------------------
def c157(bot, db):
    space_list1 = function.build_list('it', db)
    space_list2 = [12, 19]
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.build_info(bot, 'it', space_list, 157, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
    space_list1 = function.build_list('it', db)
    space_list2 = [9, 18]
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.build_info(bot, 'it', space_list, 157, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

     #------------------c158----------------------
def c158(bot, db):
    if 19 in function.remove_list('it', db):
        lock_id = thread_lock.add_lock()
        battlebuild.remove_list.append(battlebuild.remove_obj('it', [19], 158, lock_id, 'army'))
        print("remove_id: " + str(len(battlebuild.remove_list)-1))
        remove_id = len(battlebuild.remove_list)-1
        info = battlebuild.remove_list[remove_id].remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c159----------------------
    #------------------c160----------------------
    #------------------c161----------------------
def c161(bot, db):
    function.discardhand(bot, 'it', 3, db)
    c136(bot, db)
    
    #------------------c162----------------------
    #------------------c163----------------------
    #------------------c164----------------------
    #------------------c165----------------------
    #------------------c166----------------------
    #------------------c167----------------------
def c167(bot, handler_id, db):
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()
    
    #------------------c168----------------------
def c168(bot, handler_id, db):
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()

    #------------------c169----------------------
def c169(bot, handler_id, db):
    info = db.execute("select info_1, info_2 from status_handler where handler_id = :handler_id;", {'handler_id':handler_id}).fetchall()
    battlebuild.remove(bot, 'it', buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, 169, db)

    #------------------c170----------------------
def c170(bot, handler_id, db):
    removed_space = buffer.handler_list[handler_id].space_id
    if function.can_recuit('it', removed_space, db):
        battlebuild.recuit(bot, 'it', removed_space, 170, db)

    #------------------c171----------------------
c171_used = False
def c171(bot, db):
    global c171_used
    c171_used = True

    #------------------c172~173----------------------

    #------------------c174----------------------

    #------------------c175----------------------
def c175(bot, db):
    function.discardhand(bot, 'it', 1, db)
    chat_id = db.execute("select playerid from country where id = 'it';").fetchall()
    keyboard = [[InlineKeyboardButton('Deploy an Air Force', callback_data="['c175', 'd']")],
                [InlineKeyboardButton('Marshal an Air Force', callback_data="['c175', 'm']")]]
    drawmap.drawmap(db)
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_photo(chat_id = chat_id[0][0], caption = function.countryid2name['it'] + " - Air Force step", reply_markup = reply_markup, photo=open('pic/tmp.jpg', 'rb'))

def c175_cb(bot, query, query_list, db):
    if query_list[1] == 'd':
        lock_id = thread_lock.add_lock()
        space_list = function.deploy_list('it', db, space_type = 'sea')
        info = air.deploy_info(bot, 'it', space_list, 175, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    else:
        lock_id = thread_lock.add_lock()
        space_list = function.control_air_space_list('it', db)
        battlebuild.self_remove_list.append(self_remove('it', space_list, None, lock_id, 'air'))
        print("self_remove_id: " + str(len(battlebuild.self_remove_list)-1))
        self_remove_id = len(battlebuild.self_remove_list)-1
        info = battlebuild.self_remove_list[self_remove_id].self_remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        lock_id = thread_lock.add_lock()
        space_list = function.deploy_list('it', db, space_type = 'sea')
        info = air.marshal_info(bot, 'it', space_list, 175, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    
    #------------------c176----------------------
def c176(bot, db):
    if 25 in function.recuit_list('ge', db):
        battlebuild.recuit(bot, 'ge', 25, 176, db)

    #------------------c177----------------------
def c177(bot, handler_id, db):
    marshalled_space = buffer.handler_list[handler_id].space_id
    function.discardhand(bot, 'it', 2, db)
    lock_id = thread_lock.add_lock()
    space_list1 = function.within('Axis', [marshalled_space], 1, db)
    space_list2 = function.control_side_air_space_list('Allied', db, space_type = 'all')
    space_list = list(set(space_list1) & set(space_list2))
    battlebuild.remove_list.append(battlebuild.remove_obj('it', space_list, 177, lock_id, 'air'))
    print("remove_id: " + str(len(battlebuild.remove_list)-1))
    remove_id = len(battlebuild.remove_list)-1
    info = battlebuild.remove_list[remove_id].remove_info(db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    lock_id = thread_lock.add_lock()

    #------------------c178----------------------
def c178(bot, db):
    hand_list = db.execute("select cardid, name, type, text from card where location = 'hand' and control = 'ge' order by sequence;").fetchall()
    group_chat_id = db.execute("select chatid from game;").fetchall()
    if len(hand_list) == 0:
        text = "<b>" + countryid2name[country] + "</b> finished his hand"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    else:
        lock_id = thread_lock.add_lock()
        chat_id = db.execute("select playerid from country where id = 'ge';").fetchall()
        keyboard = [[InlineKeyboardButton(hand[1], callback_data="['c178', {}, {}]".format(hand[0], lock_id))]for hand in hand_list]
        text = "Discard between 1 and 5 cards:\n\n"
        for card in hand_list:
                text += "<b>" + card[1] + "</b> - " + card[2] + " - " + card[3] + "\n"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup, parse_mode=telegram.ParseMode.HTML)
        thread_lock.thread_lock(lock_id)
    
def c178_cb(bot, query, query_list, db):
    if query_list[2] == 'confirm':
        selected = db.execute("select name, sequence from card where location = 'selected' and control = 'ge' order by sequence;").fetchall()
        db.execute("update card set location = 'discardd' where location = 'selected' and control =:country;", {'country':query_list[1]})
        text = 'Discarded:\n'
        for card in selected:
            text += str(card[0]) + '\n'
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        function.shufflediscard(bot, 'it', db)
        discard_list = db.execute("select cardid from card where ((location in ('discardd', 'discardu')) or (location = 'played' and type not in ('Status', 'Response')) or (location = 'used' and type = 'Response')) and control = 'it' and sequence <= :number;", {'number':len(selected)}).fetchall()
        for discard in discard_list:
            movecardtop(bot, discard[0], db)
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            db.execute("update card set location = 'hand' where location = 'selected' and control = 'ge';")
            hand_list = db.execute("select name, cardid, type, text from card where location = 'hand' and control = 'ge' order by sequence;").fetchall()
            text = "Discard between 1 and 5 cards:\n\n"
            for card in hand_list:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            keyboard = [[InlineKeyboardButton(hand[0], callback_data="['c178', {}, {}]".format(hand[1], query_list[-1]))]for hand in hand_list]
        else:
            db.execute("update card set location = 'selected' where cardid =:id and control = 'ge';", {'id': query_list[1]})
            hand_list = db.execute("select name, cardid, type, text from card where location = 'hand' and control = 'ge' order by sequence;").fetchall()
            selected = db.execute("select name, cardid, type, text from card where location = 'selected' and control = 'ge' order by sequence;").fetchall()
            text = 'Hand:\n'
            for card in hand_list:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            text += '\nDiscarded:\n'
            for card in selected:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            keyboard = []
            if len(selected) < 5:
                keyboard += [[InlineKeyboardButton(hand[0], callback_data="['c178', {}, {}]".format(hand[1], query_list[-1]))] for hand in hand_list]
            if len(selected) > 5:
                keyboard += [[InlineKeyboardButton('Confirm', callback_data="['c178', 'confirm', {}]".format(query_list[-1]))],
                            [InlineKeyboardButton('Back', callback_data="['c178', 'back', {}]".format(query_list[-1]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        db.close()

    #------------------c179----------------------
c179_used = False
def c179(bot, db):
    lock_id = thread_lock.add_lock()
    space_list = function.control_air_space_list(query_list[1], db)
    battlebuild.self_remove_list.append(self_remove(query_list[1], space_list, 179, lock_id, 'air'))
    print("self_remove_id: " + str(len(battlebuild.self_remove_list)-1))
    self_remove_id = len(battlebuild.self_remove_list)-1
    info = battlebuild.self_remove_list[self_remove_id].self_remove_info(db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    c179_used = True
    
    #------------------c180----------------------
def c180(bot, db):
    if 13 in function.recuit_list('it', db):
        battlebuild.recuit(bot, 'it', 13, 180, db)

    #------------------c181----------------------
def c181(bot, db):
    piece = db.execute("select count(*) from piece where control = 'it' and location != 'none' and type = 'navy';").fetchall()
    function.add_vp(bot, 'it', piece[0][0], db)

    #------------------c182~186----------------------
def c182(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('uk', db), 'uk', db, space_type = 'land')
    space_list = function.build_list('uk', db, space_type = 'land')
    info = battlebuild.build_info(bot, 'uk', space_list, 182, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c187~192----------------------
def c187(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('uk', db), 'uk', db, space_type = 'sea')
    space_list = function.build_list('uk', db, space_type = 'sea')
    info = battlebuild.build_info(bot, 'uk', space_list, 187, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c193~196----------------------
def c193(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('uk', db), 'uk', db, space_type = 'land')
    space_list = function.battle_list('uk', db, space_type = 'land')
    info = battlebuild.battle_info(bot, 'uk', space_list, 193, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c197~201----------------------
def c197(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('uk', db), 'uk', db, space_type = 'sea')
    space_list = function.battle_list('uk', db, space_type = 'sea')
    info = battlebuild.battle_info(bot, 'uk', space_list, 197, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c202----------------------
def c202(bot, db):
    lock_id = thread_lock.add_lock()
    chat_id = db.execute("select playerid from country where id = 'uk';").fetchall()
    keyboard = [[InlineKeyboardButton("Germany", callback_data="['c202', 'ge', {}]".format(lock_id))],
                [InlineKeyboardButton("Italy", callback_data="['c202', 'it', {}]".format(lock_id))]]
    text = "Choose a player to discard the top 4 cards of its draw deck:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)
    
def c202_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] == 'ge':
        #function.discarddeck(bot, 'ge', 4, db)
        function.ewdiscard(bot, 202, 'uk', 'ge', 4, db)
    elif query_list[1] == 'it':
        #function.discarddeck(bot, 'it', 4, db)
        function.ewdiscard(bot, 202, 'uk', 'it', 4, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c203----------------------
def c203(bot, db):
    country_list = ['ge', 'it']
    for country in country_list:
        if function.isin(country, 18, db):
            lock_id = thread_lock.add_lock()
            chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
            keyboard = [[InlineKeyboardButton("Discard the top 2 cards", callback_data="['c203', '{}', 'discard', {}]".format(country, lock_id))],
                        [InlineKeyboardButton("Remove a Navy in the Mediterranean", callback_data="['c203', '{}', 'remove', {}]".format(country, lock_id))]]
            text = "Choose what to do:"
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
            thread_lock.thread_lock(lock_id)
        else:
            function.ewdiscard(bot, 203, 'uk', country, 2, db)
    
def c203_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[2] == 'discard':
        #function.discarddeck(bot, query_list[1], 2, db)
        function.ewdiscard(bot, 203, 'uk', query_list[1], 2, db)
    elif query_list[2] == 'remove':
        piece = db.execute("select pieceid from piece where location = '18' and control = :country", {'country':query_list[1]}).fetchall()
        battlebuild.remove(bot, query_list[1], piece[0][0], 18, 203, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c204, 208----------------------
def c204(bot, db):
    lock_id = thread_lock.add_lock()
    space_list = function.build_list('fr', db, space_type = 'land')
    info = battlebuild.build_info(bot, 'fr', space_list, 204, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c205----------------------
def c205(bot, db):
    space_list = {33:'Indonesia', 45:'New Guinea'}
    recuit_list = function.recuit_list('fr', db)
    if not set(space_list).isdisjoint(set(recuit_list)):
        if len(set(space_list) & set(recuit_list)) > 1:
            lock_id = thread_lock.add_lock()
            chat_id = db.execute("select playerid from country where id = 'uk';").fetchall()
            keyboard = [[InlineKeyboardButton("Recruit a French Army in Indonesia", callback_data="['c205', 'in', {}]".format(lock_id))],
            [InlineKeyboardButton("Recruit a French Army in New Guinea", callback_data="['c205', 'gu', {}]".format(lock_id))]]
            text = "Choose what to do first:"
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
            thread_lock.thread_lock(lock_id)
        else:
            battlebuild.recuit(bot, 'fr', list(set(space_list) & set(recuit_list))[0], 205, db)
    if 40 in recuit_list:
        battlebuild.recuit(bot, 'fr', 40, 205, db)
        
def c205_cb(bot, query, query_list, db):
    if query_list[1] == 'in':
        battlebuild.recuit(bot, 'fr', 33, 205, db)
        battlebuild.recuit(bot, 'fr', 45, 205, db)
    elif query_list[1] == 'gu':
        battlebuild.recuit(bot, 'fr', 45, 205, db)
        battlebuild.recuit(bot, 'fr', 33, 205, db)
    bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
    thread_lock.release_lock(query_list[-1])

    #------------------c206----------------------
def c206(bot, db):
    ge_status = db.execute("select name, cardid from card where control = 'ge' and location in ('played', 'used') and type = 'Status';").fetchall()
    if len(ge_status) > 0:
        lock_id = thread_lock.add_lock()
        chat_id = db.execute("select playerid from country where id = 'uk';").fetchall()
        keyboard = [[InlineKeyboardButton(card[0], callback_data="['c206', {}, {}]".format(card[1], lock_id))] for card in ge_status]
        text = "Choose a German Status card on the table and discard it:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
    
def c206_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    function.discardcard(bot, query_list[1], db)
    thread_lock.release_lock(query_list[-1])

    #------------------c207----------------------
def c207(bot, db):
    lock_id = thread_lock.add_lock()
    space_list1 = [13, 14, 19, 25, 36, 45]
    space_list2 = function.recuit_list('fr', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    info = battlebuild.recuit_info(bot, 'fr', space_list, 207, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
     
    #------------------c209----------------------
def c209(bot, db):
    if 12 in function.battle_list('fr', db):
        lock_id = thread_lock.add_lock()
        info = battlebuild.battle_info(bot, 'fr', [12], 209, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    else:
        lock_id = thread_lock.add_lock()
        chat_id = db.execute("select playerid from country where id = 'uk';").fetchall()
        keyboard = [[InlineKeyboardButton("Build a French Army in Western Europe", callback_data="['c209', 'bu', {}]".format(lock_id))],
        [InlineKeyboardButton("Battle an Army in Western Europe", callback_data="['c209', 'ba', {}]".format(lock_id))]]
        text = "Choose what to do:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
    
def c209_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] == 'bu':
        battlebuild.build(bot, 'fr', 12, 209, db)
    elif query_list[1] == 'ba':
        battlebuild.battle(bot, 'fr', 0, 12, 209, db)
    thread_lock.release_lock(query_list[-1])
    
    #------------------c210----------------------
def c210(bot, db):
    lock_id = thread_lock.add_lock()
    space_list1 = [12, 13, 19]
    for i in range(2):
        space_list2 = function.recuit_list('fr', db, space_type = 'land')
        space_list = list(set(space_list1) & set(space_list2))
        info = battlebuild.recuit_info(bot, 'fr', space_list, 210, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c211----------------------
def c211(bot, db):
    space_list = {7:'Southern Ocean', 27:'Indian Ocean'}
    recuit_list = function.recuit_list('uk', db)
    if 13 in recuit_list:
        battlebuild.recuit(bot, 'uk', 13, 211, db)
    if not set(space_list).isdisjoint(set(remove_list)):
        lock_id = thread_lock.add_lock()
        keyboard = []
        for space in space_list:
            if space in recuit_list:
                keyboard.append([InlineKeyboardButton(space_list[space], callback_data="['c211', {}, {}]".format(space, lock_id))])
        chat_id = db.execute("select playerid from country where id = 'uk';").fetchall()
        text = "Recruit a Navy in the Southern Ocean or the Indian Ocean:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)

def c211_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    battlebuild.recuit(bot, 'uk', query_list[1], 211, db)
    thread_lock.release_lock(query_list[-1])
        
    #------------------c212----------------------
def c212(bot, db):
    lock_id = thread_lock.add_lock()
    recuit_space_list = function.recuit_list('uk', db, space_type = 'all')
    space_list = list(set(recuit_space_list) & set([1, 32, 41]))
    #space_list = function.filter_build_list([1, 32, 41] , 'uk', db, space_type = 'all')
    info = battlebuild.recuit_info(bot, 'uk', space_list, 212, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c213----------------------
def c213(bot, db):
    if 22 in function.remove_list('uk', db):
        lock_id = thread_lock.add_lock()
        battlebuild.remove_list.append(battlebuild.remove_obj('uk', [22], 213, lock_id, 'army'))
        print("remove_id: " + str(len(battlebuild.remove_list)-1))
        remove_id = len(battlebuild.remove_list)-1
        info = battlebuild.remove_list[remove_id].remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    if 22 in function.recuit_list('uk', db):
        battlebuild.recuit(bot, 'uk', 22, 213, db)

    #------------------c214, 215----------------------
def c214(bot, db):
    lock_id = thread_lock.add_lock()
    space_list = function.build_list('fr', db, space_type = 'sea')
    info = battlebuild.build_info(bot, 'fr', space_list, 214, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c216----------------------
def c216(bot, db):
    if 21 in function.remove_list('uk', db):
        lock_id = thread_lock.add_lock()
        battlebuild.remove_list.append(battlebuild.remove_obj('uk', [21], 216, lock_id, 'army'))
        print("remove_id: " + str(len(battlebuild.remove_list)-1))
        remove_id = len(battlebuild.remove_list)-1
        info = battlebuild.remove_list[remove_id].remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c217----------------------
def c217(bot, db):
    if 12 in function.remove_list('uk', db):
        lock_id = thread_lock.add_lock()
        battlebuild.remove_list.append(battlebuild.remove_obj('uk', [12], 217, lock_id, 'army'))
        print("remove_id: " + str(len(battlebuild.remove_list)-1))
        remove_id = len(battlebuild.remove_list)-1
        info = battlebuild.remove_list[remove_id].remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c218----------------------
def c218(bot, db):
    lock_id = thread_lock.add_lock()
    space_list = function.battle_list('fr', db, space_type = 'land')
    info = battlebuild.battle_info(bot, 'fr', space_list, 218, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c219----------------------
def c219(bot, db):
    lock_id = thread_lock.add_lock()
    chat_id = db.execute("select playerid from country where id = 'uk';").fetchall()
    keyboard = [[InlineKeyboardButton("Recruit an Army in Southeast Asia", callback_data="['c219', 'sa', {}]".format(lock_id))],
                [InlineKeyboardButton("Recruit a Navy in the South China Sea", callback_data="['c219', 'scs', {}]".format(lock_id))]]
    text = "Choose what to do first:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)

def c219_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] == 'sa':
        if function.can_recuit('uk', 36, db):
            battlebuild.recuit(bot, 'uk', 36, 219, db)
        if function.can_recuit('uk', 40, db):
            battlebuild.recuit(bot, 'uk', 40, 219, db)
    elif query_list[1] == 'scs':
        if function.can_recuit('uk', 40, db):
            battlebuild.recuit(bot, 'uk', 40, 219, db)
        if function.can_recuit('uk', 36, db):
            battlebuild.recuit(bot, 'uk', 36, 219, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c220----------------------
    #------------------c221----------------------
    #------------------c222----------------------
    #------------------c223----------------------
    #------------------c224----------------------
    #------------------c225----------------------
    #------------------c226----------------------
    #------------------c227----------------------
def c227(bot, handler_id, db):
    cardid = buffer.handler_list[handler_id].card_id
    hand = db.execute("select name, cardid from card where control = 'uk' and location = 'hand';").fetchall()
    if len(hand) > 0:
        lock_id = thread_lock.add_lock()
        chat_id = db.execute("select playerid from country where id = 'uk';").fetchall()
        keyboard = [[InlineKeyboardButton(card[0], callback_data="['c227', {}, {}, {}]".format(card[1], cardid, lock_id))] for card in hand]
        keyboard.append([InlineKeyboardButton('Pass', callback_data="['c227', 'pass', {}]".format(lock_id))])
        text = "Choose a different card to discard:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
    
def c227_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] != 'pass':
        card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':query_list[1]}).fetchall()
        text = "<b>" + card_name[0][0] + "</b> discarded"
        bot.send_message(chat_id = query.message.chat_id, text = text, parse_mode=telegram.ParseMode.HTML)
        function.facedowndiscardcard(bot, query_list[1], db)
        card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':query_list[2]}).fetchall()
        text = "<b>" + card_name[0][0] + "</b> move to bottom of deck"
        bot.send_message(chat_id = query.message.chat_id, text = text, parse_mode=telegram.ParseMode.HTML)
        function.movecardbottom(bot, query_list[2], db)
    thread_lock.release_lock(query_list[-1])

    #------------------c228----------------------

    #------------------c229----------------------
def c229(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    function.discardhand(bot, 'uk', 2, db)
    space_list1 = function.within('Allies', [battled_space], 1, db)
    space_list2 = function.battle_list('jp', db, space_type = 'sea')
    space_list = [space for space in space_list1 if space in space_list2]
    lock_id = thread_lock.add_lock()
    info = battlebuild.battle_info(bot, 'uk', space_list, 229, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c230----------------------
def c230(bot, handler_id, db):
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()

    #------------------c231----------------------
def c231(bot, handler_id, db):
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()

    #------------------c232----------------------
def c232(bot, handler_id, db):
    battlebuild.recuit(bot, 'fr', buffer.handler_list[handler_id].space_id, 232, db)

    #------------------c233----------------------
def c233(bot, handler_id, db):
    info = db.execute("select info_1, info_2 from status_handler where handler_id = :handler_id;", {'handler_id':handler_id}).fetchall()
    battlebuild.remove(bot, 'uk', buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, 233, db)
    
    #------------------c234----------------------
def c234(bot, handler_id, db):
    info = db.execute("select info_1, info_2 from status_handler where handler_id = :handler_id;", {'handler_id':handler_id}).fetchall()
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()

    #------------------c235~237----------------------

    #------------------c238----------------------
def c238(bot, db):
    lock_id = thread_lock.add_lock()
    space_list = function.deploy_list('fr', db)
    info = air.deploy_info(bot, 'fr', space_list, 238, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c239----------------------
c239_used = False
def c239(bot, db):
    function.discardhand(bot, 'uk', 2, db)
    global c239_used
    c239_used = True

    #------------------c240----------------------
def c240(bot, db):
    function.discardhand(bot, 'uk', 2, db)
    lock_id = thread_lock.add_lock()
    space_list1 = [19, 25, 33, 36]
    space_list2 = function.recuit_list('uk', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    info = battlebuild.recuit_info(bot, 'uk', space_list, 240, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
    
    #------------------c241----------------------
c241_used = False
def c241(bot, db):
    function.discardhand(bot, 'uk', 2, db)
    global c241_used
    c241_used = True
    
    #------------------c242----------------------
def c242(bot, handler_id, db):
    function.discardhand(bot, 'uk', 4, db)
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()
    
    #------------------c243----------------------
def c243(bot, handler_id, db):
    function.discardhand(bot, 'uk', 3, db)
    lock_id = thread_lock.add_lock()
    space_list1 = [8, 9]
    space_list2 = function.deploy_list('uk', db)
    space_list = list(set(space_list1) & set(space_list2))
    info = air.deploy_info(bot, 'uk', space_list, 243, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
    
    #------------------c244----------------------
def c244(bot, handler_id, db):
    marshalled_space = buffer.handler_list[handler_id].space_id
    function.discardhand(bot, 'uk', 2, db)
    lock_id = thread_lock.add_lock()
    space_list1 = function.within('Axis', [marshalled_space], 1, db)
    space_list2 = function.control_side_air_space_list('Axis', db, space_type = 'all')
    space_list = list(set(space_list1) & set(space_list2))
    battlebuild.self_remove_list.append(battlebuild.self_remove('uk', space_list, 244, lock_id, 'air'))
    print("self_remove_id: " + str(len(battlebuild.self_remove_list)-1))
    self_remove_id = len(battlebuild.self_remove_list)-1
    info = battlebuild.self_remove_list[self_remove_id].self_remove_info(db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    lock_id = thread_lock.add_lock()

    #------------------c245----------------------
def c245(bot, db):
    function.discardhand(bot, 'uk', 2, db)
    if 21 in function.recuit_list('uk', db):
        battlebuild.recuit(bot, 'uk', 21, 245, db)
    
    #------------------c246~254----------------------
def c246(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('su', db), 'su', db, space_type = 'land')
    space_list = function.build_list('su', db, space_type = 'land')
    info = battlebuild.build_info(bot, 'su', space_list, 246, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c255----------------------
def c255(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('su', db), 'su', db, space_type = 'sea')
    space_list = function.build_list('su', db, space_type = 'sea')
    info = battlebuild.build_info(bot, 'su', space_list, 255, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c256~262----------------------
def c256(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('su', db), 'su', db, space_type = 'land')
    space_list = function.battle_list('su', db, space_type = 'land')
    info = battlebuild.battle_info(bot, 'su', space_list, 256, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c263~264----------------------
def c263(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('su', db), 'su', db, space_type = 'sea')
    space_list = function.battle_list('su', db, space_type = 'sea')
    info = battlebuild.battle_info(bot, 'su', space_list, 263, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c265----------------------
def c265(bot, db):
    if 34 in function.recuit_list('su', db):
        battlebuild.recuit(bot, 'su', 34, 265, db)
    space_list = list(set([37, 42])&set(function.battle_list('su', db, space_type = 'land')))
    if len(space_list) > 0:
        lock_id = thread_lock.add_lock()
        info = battlebuild.battle_info(bot, 'su', space_list, 265, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c266----------------------
def c266(bot, db):
    for i in range(2):
        #space_list = function.filter_battle_list([20, 24, 28, 30], 'su', db, space_type = 'land')
        space_list = list(set([20, 24, 28, 30])&set(function.remove_list('su', db, space_type = 'land')))
        if len(space_list) > 0:
            lock_id = thread_lock.add_lock()
            battlebuild.remove_list.append(battlebuild.remove_obj('su', space_list, 266, lock_id, 'army'))
            print("remove_id: " + str(len(battlebuild.remove_list)-1))
            remove_id = len(battlebuild.remove_list)-1
            info = battlebuild.remove_list[remove_id].remove_info(db)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)

    #------------------c267----------------------
def c267(bot, db):
    for i in range(2):
        #space_list = function.filter_build_list([21, 24], 'su', db, space_type = 'land')
        space_list = list(set([21, 24])&set(function.build_list('su', db, space_type = 'land')))
        print(space_list)
        if len(space_list) > 0:
            lock_id = thread_lock.add_lock()
            info = battlebuild.build_info(bot, 'su', space_list, 267, lock_id, db)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)

    #------------------c268----------------------
def c268(bot, db):
    if 43 in function.build_list('su', db):
        battlebuild.build(bot, 'su', 43, 268, db)
    if 38 in function.battle_list('su', db):
        lock_id = thread_lock.add_lock()
        info = battlebuild.battle_info(bot, 'su', [38], 268, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c269----------------------
def c269(bot, db):
    space_list = list(set([35, 37])&set(function.remove_list('su', db, space_type = 'land')))
    if len(space_list) > 0:
        lock_id = thread_lock.add_lock()
        battlebuild.remove_list.append(battlebuild.remove_obj('su', space_list, 269, lock_id, 'army'))
        print("remove_id: " + str(len(battlebuild.remove_list)-1))
        remove_id = len(battlebuild.remove_list)-1
        info = battlebuild.remove_list[remove_id].remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c270----------------------
def c270(bot, db):
    space_list = list(set(function.within('Allied', [30], 1, db))&set(function.recuit_list('su', db, space_type = 'land')))
    if len(space_list) > 0:
        lock_id = thread_lock.add_lock()
        info = battlebuild.recuit_info(bot, 'su', space_list, 270, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
            
    #------------------c271----------------------
def c271(bot, db):
    if 22 in function.remove_list('su', db, space_type = 'land'):
        lock_id = thread_lock.add_lock()
        battlebuild.remove_list.append(battlebuild.remove_obj('su', [22], 271, lock_id, 'army'))
        print("remove_id: " + str(len(battlebuild.remove_list)-1))
        remove_id = len(battlebuild.remove_list)-1
        info = battlebuild.remove_list[remove_id].remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    country_list = {'su':'Soviet Union','uk':"United Kingdom"}
    keyboard = []
    lock_id = thread_lock.add_lock()
    for country in country_list:
        if 22 in function.recuit_list(country, db, space_type = 'land'):
            keyboard.append([InlineKeyboardButton(country_list[country], callback_data="['c271', '{}', {}]".format(country, lock_id))])
    if len(keyboard) > 0:
        text = "Recruit an Army in the Balkans:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)

def c271_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    battlebuild.recuit(bot, query_list[1], 22, 271, db)
    thread_lock.release_lock(query_list[-1])

        #------------------c272----------------------
c272_list = []
def c272(bot, db):
    global _pass
    _pass = True
    global c272_list
    c272_list = function.control_space_list('su', db, space_type = 'land')
    while _pass:
        buffer.space_list = c272_list
        lock_id = thread_lock.add_lock()
        info = c272_info(bot, 'su', c272_list, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

def c272_info(bot, country, space_list, lock_id, db):
    name_list = function.get_name_list(space_list, db)
    chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    text = "Choose a space to remove"
    keyboard = [[InlineKeyboardButton(space[1], callback_data="['c272', '{}', {}, {}]".format(country, space[0], lock_id))] for space in name_list]
    keyboard.append([InlineKeyboardButton('Pass', callback_data="['c272', '{}', 'pass', {}]".format(country, lock_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return chat_id[0][0], text, reply_markup

def c272_cb(bot, query, query_list, db):
    if query_list[2] == 'confirm':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        piece = db.execute("select pieceid from piece where control = 'su' and location = :space;", {'space':query_list[3]}).fetchall()
        battlebuild.remove(bot, 'su', piece[0][0], query_list[3], 272, db)
        c246(bot, db)
        global c272_list
        c272_list.remove(query_list[3])
        thread_lock.release_lock(query_list[-1])
    elif query_list[2] == 'pass':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        global _pass
        _pass = False
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            info = c272_info(bot, query_list[1] , buffer.space_list, query_list[-1], db)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[2]}).fetchall()
            text = 'Removed ' + location[0][0] + ':'
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c272', '{}', 'confirm', {}, {}]".format(query_list[1], query_list[2], query_list[3]))], [InlineKeyboardButton('Back', callback_data="['c164', '{}', 'back', {}]".format(query_list[1], query_list[3]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)
        db.commit()

    #------------------c273----------------------                            
def c273(bot, db):
    lock_id = thread_lock.add_lock()
    chat_id = db.execute("select playerid from country where id = 'su';").fetchall()
    keyboard = [[InlineKeyboardButton("Recruit a Soviet Army in Vladivostok", callback_data="['c273', 'r', {}]".format(lock_id))],
                [InlineKeyboardButton("Battle an Army in China", callback_data="['c273', 'b', {}]".format(lock_id))]]
    text = "Choose what to do first:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)
    
def c273_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] == 'r':
        if 42 in function.recuit_list('su', db):
            battlebuild.recuit(bot, 'su', 42, 273, db)
        if 37 in function.battle_list('su', db):
            lock_id = thread_lock.add_lock()
            info = battlebuild.battle_info(bot, 'su', [37], 273, lock_id, db)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)  
    elif query_list[1] == 'b':
        if 37 in function.battle_list('su', db):
            lock_id = thread_lock.add_lock()
            info = battlebuild.battle_info(bot, 'su', [37], 273, lock_id, db)
            bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
            thread_lock.thread_lock(lock_id)
        if 42 in function.recuit_list('su', db):
            battlebuild.recuit(bot, 'su', 42, 273, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c274----------------------
    #------------------c275----------------------
def c275(bot, db):
    function.discardhand(bot, 'su', 2, db) 
    c246(bot, db)
    
    #------------------c276----------------------
def c276(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    function.discardhand(bot, 'su', 2, db)
    lock_id = thread_lock.add_lock()
    space_list = list(set(function.battle_list('su', db, space_type = 'land')) & set(function.within('Allied', [battled_space], 1, db)))
    info = battlebuild.battle_info(bot, 'su', space_list, 276, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
                    
    #------------------c277----------------------    
    #------------------c278----------------------
def c278(bot, db):
    function.discardhand(bot, 'su', 2, db)
    if db.execute("select count(*) from card where name = 'Build Army' and location in ('discardd', 'discardu') and control = 'su';").fetchall()[0][0] > 0:
        c246(bot, db)
                        
    #------------------c279----------------------
def c279(bot, db):
    build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location = 'hand' and control = 'su';").fetchall()
    function.discardcard(bot, build_army[0][0], db)
    lock_id = thread_lock.add_lock()
    space_list = list(set([34, 35, 37]) & set(function.recuit_list('ch', db, space_type = 'land')))
    info = battlebuild.recuit_info(bot, 'ch', space_list, 279, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c280----------------------
def c280(bot, db):
    build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location = 'hand' and control = 'su';").fetchall()
    function.discardcard(bot, build_army[0][0], db)
    c246(bot, db)

    #------------------c281----------------------
    #------------------c282----------------------
def c282(bot, handler_id, db):
    build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location = 'hand' and control = 'su';").fetchall()
    land_battle = db.execute("select min(cardid) from card where name = 'Land Battle' and location = 'hand' and control = 'su';").fetchall()
    function.discardcard(bot, build_army[0][0], db)    
    function.discardcard(bot, land_battle[0][0], db)
    built_space = buffer.handler_list[handler_id].space_id
    space_list1 = function.within('Allied', [built_space], 1, db)
    space_list2 = function.battle_list('su', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.battle_info(bot, 'su', space_list, 282, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c283----------------------
    #------------------c284----------------------
def c284(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'su', 1, db)
    if space in function.remove_list('su', db, space_type = 'land'):
        piece_list = db.execute("select pieceid from piece where location = :space;", {'space':battled_space}).fetchall()
        for piece in piece_list:
            battlebuild.remove(bot, 'su', piece[0], battled_space, 284, db)

    #------------------c285----------------------
def c285(bot, handler_id, db):
    cardid = buffer.handler_list[handler_id].card_id
    function.movecardtop(bot, cardid, db)
    
    #------------------c286----------------------
def c286(bot, handler_id, db):
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    for space in [30, 31]:
        if db.execute("select count(*) from piece where location = :space and type = 'army' and control = 'su';", {'space':space}).fetchall()[0][0] > 0:
            db.execute("update piece set noremove = 1 where location = :space and type = 'army' and control = 'su';", {'space':space})
    db.commit()

    #------------------c287----------------------
def c287(bot, handler_id, db):
    lock_id = thread_lock.add_lock()
    chat_id = db.execute("select playerid from country where id = :country;", {'country':buffer.handler_list[handler_id].active_country_id}).fetchall()
    keyboard = [[InlineKeyboardButton("Discard 3 cards from your hand", callback_data="['c287', 'd', {}, {}]".format(handler_id, lock_id))],
                [InlineKeyboardButton("Pass", callback_data="['c287', 'pass', {}, {}]".format(handler_id, lock_id))]]
    text = "The attacker must discard 3 cards from its hand or your Army is not removed:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)
    
    
def c287_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] == 'd':
        function.discardhand(bot, buffer.handler_list[query_list[2]].active_country_id, 3, db)
    else:
        info = db.execute("select info_1, info_2 from status_handler where handler_id = :handler_id;", {'handler_id':query_list[2]}).fetchall()
        battlebuild.restore(bot, buffer.handler_list[query_list[2]].piece_id, buffer.handler_list[query_list[2]].space_id, db)
        db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[query_list[2]].piece_id})
        db.commit()
    thread_lock.release_lock(query_list[-1])

    #------------------c288----------------------
def c288(bot, handler_id, db):
    info = db.execute("select info_1, info_2 from status_handler where handler_id = :handler_id;", {'handler_id':handler_id}).fetchall()
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()

    #------------------c289----------------------
def c289(bot, handler_id, db):
    info = db.execute("select info_1, info_2 from status_handler where handler_id = :handler_id;", {'handler_id':handler_id}).fetchall()
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()
                            
    #------------------c290----------------------
def c290(bot, handler_id, db):
    info = db.execute("select info_1, info_2 from status_handler where handler_id = :handler_id;", {'handler_id':handler_id}).fetchall()
    battlebuild.remove(bot, 'su', buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, 290, db)
    
    #------------------c291----------------------
def c291(bot, db):
    if 30 in function.recuit_list('su', db):
        battlebuild.recuit(bot, 'su', 30, 291, db)
    if 31 in function.recuit_list('su', db):
        battlebuild.recuit(bot, 'su', 31, 291, db)

    #------------------c292----------------------
def c292(bot, handler_id, db):
    info = db.execute("select info_1, info_2 from status_handler where handler_id = :handler_id;", {'handler_id':handler_id}).fetchall()
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    db.execute("update piece set noremove = 1 where pieceid = :piece", {'piece':buffer.handler_list[handler_id].piece_id})
    db.commit()

    #------------------c293~294----------------------

    #------------------c295----------------------
def c295(bot, handler_id, db):
    for i in range(2):
        if db.execute("select count(*) from card where name = 'Build Army' and location in('discardu', 'discardd', 'played') and control = 'su';").fetchall()[0][0] > 0:
            build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location in('discardu', 'discardd', 'played') and control = 'su';").fetchall()
            function.movecardhand(bot, build_army[0][0], db)

    #------------------c296----------------------
def c296(bot, db):
    build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location = 'hand' and control = 'su';").fetchall()
    function.discardcard(bot, build_army[0][0], db)
    lock_id = thread_lock.add_lock()
    space_list1 = function.within('Allied', [28], 1, db)
    space_list2 = function.remove_list('su', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    battlebuild.remove_list.append(battlebuild.remove_obj('su', space_list, 296, lock_id, 'army'))
    print("remove_id: " + str(len(battlebuild.remove_list)-1))
    remove_id = len(battlebuild.remove_list)-1
    info = battlebuild.remove_list[remove_id].remove_info(db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c297----------------------
def c297(bot, db):
    build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location = 'hand' and control = 'su';").fetchall()
    function.discardcard(bot, build_army[0][0], db)
    lock_id = thread_lock.add_lock()
    space_list = function.control_space_list('su', db, space_type = 'land')
    battlebuild.self_remove_list.append(battlebuild.self_remove('su', space_list, 297, lock_id, 'army'))
    print("self_remove_id: " + str(len(battlebuild.self_remove_list)-1))
    self_remove_id = len(battlebuild.self_remove_list)-1
    info = battlebuild.self_remove_list[self_remove_id].self_remove_info(db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
    lock_id = thread_lock.add_lock()
    space_list = function.build_list('su', db, space_type = 'land')
    info = battlebuild.build_info(bot, 'su', space_list, 297, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c298----------------------
def c298(bot, db):
    build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location = 'hand' and control = 'su';").fetchall()
    function.discardcard(bot, build_army[0][0], db)
    response_list = db.execute("select cardid, name, type, text from card where location in ('discardu', 'discardd', 'used') and type = 'Response' and control = 'su' order by sequence;").fetchall()
    if len(response_list) > 0:
        chat_id = db.execute("select playerid from country where id = 'su';").fetchall()
        lock_id = thread_lock.add_lock()
        keyboard = [[InlineKeyboardButton(response[1], callback_data="['c298', {}, {}]".format(response[0], lock_id))]for response in response_list]
        text = "Place a Response card from your discard pile face-down on the table:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup, parse_mode=telegram.ParseMode.HTML)
        thread_lock.thread_lock(lock_id)

def c298_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    play_card(bot, query_list[1], 'su', db)
    thread_lock.release_lock(query_list[-1])
    
    #------------------c299----------------------
def c299(bot, db):
    lock_id = thread_lock.add_lock()
    space_list = function.deploy_list('ch', db)
    info = air.deploy_info(bot, 'ch', space_list, 299, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c300----------------------
def c300(bot, handler_id, db):
    build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location = 'hand' and control = 'su';").fetchall()
    function.discardcard(bot, build_army[0][0], db)
    marshalled_space = buffer.handler_list[handler_id].space_id
    space_list1 = function.within('Allied', [marshalled_space], 1, db)
    space_list2 = function.build_list('su', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.build_info(bot, 'su', space_list, 300, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c301----------------------
def c301(bot, db):
    build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location = 'hand' and control = 'su';").fetchall()
    function.discardcard(bot, build_army[0][0], db)
    function.discardhand(bot, 'su', 2, db)
    space_list1 = function.within('Allied', [28], 1, db)
    space_list2 = function.recuit_list('su', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.recuit_info(bot, 'su', space_list, 301, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c302----------------------
def c302(bot, db):
    build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location = 'hand' and control = 'su';").fetchall()
    function.discardcard(bot, build_army[0][0], db)
    function.discardhand(bot, 'su', 2, db)
    space_list1 = [20, 28]
    space_list2 = function.remove_list('su', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    battlebuild.remove_list.append(battlebuild.remove_obj('su', space_list, 302, lock_id, 'army'))
    print("remove_id: " + str(len(battlebuild.remove_list)-1))
    remove_id = len(battlebuild.remove_list)-1
    info = battlebuild.remove_list[remove_id].remove_info(db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c303----------------------
def c303(bot, handler_id, db):
    build_army = db.execute("select min(cardid) from card where name = 'Build Army' and location = 'hand' and control = 'su';").fetchall()
    function.discardcard(bot, build_army[0][0], db)
    battled_space = buffer.handler_list[handler_id].space_id
    battlebuild.build(bot, 'su', battled_space, 303, db)

    #------------------c304~308----------------------
def c304(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('su', db), 'su', db, space_type = 'land')
    space_list = function.build_list('us', db, space_type = 'land')
    info = battlebuild.build_info(bot, 'us', space_list, 304, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c309~313----------------------
def c309(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_build_list(function.control_supplied_space_list('su', db), 'su', db, space_type = 'sea')
    space_list = function.build_list('us', db, space_type = 'sea')
    info = battlebuild.build_info(bot, 'us', space_list, 309, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
                            
    #------------------c314~317----------------------
def c314(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('su', db), 'su', db, space_type = 'land')
    space_list = function.battle_list('us', db, space_type = 'land')
    info = battlebuild.battle_info(bot, 'us', space_list, 314, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c318~321----------------------
def c318(bot, db):
    lock_id = thread_lock.add_lock()
    #space_list = function.filter_battle_list(function.control_supplied_space_list('su', db), 'su', db, space_type = 'sea')
    space_list = function.battle_list('us', db, space_type = 'sea')
    info = battlebuild.battle_info(bot, 'us', space_list, 318, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
       
    #------------------c322~323----------------------
def c322(bot, db):
    axis_home_space = {16:'Germany', 17:'Italy', 38:'Japan'}
    us_space_list = function.within('Allies', function.control_space_list('us', db, space_type = 'land'), 3, db)
    if not set(axis_home_space).isdisjoint(set(us_space_list)):
        lock_id = thread_lock.add_lock()
        keyboard = []
        for space in axis_home_space:
            if space in us_space_list:
                keyboard.append([InlineKeyboardButton(axis_home_space[space], callback_data="['c322', {}, {}]".format(space, lock_id))])
        chat_id = db.execute("select playerid from country where id = 'us';").fetchall()
        text = "Country must discard the top 4 cards of its draw deck:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
        
def c322_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    country = db.execute("select id from country where home = :home;", {'home': query_list[1]}).fetchall()
    #function.discarddeck(bot, country[0][0], 4, db)
    function.ewdiscard(bot, 322, 'us', country[0][0], 4, db)
    thread_lock.release_lock(query_list[-1])
    
    #------------------c324----------------------
def c324(bot, db):
    space_list = function.within('Allied', function.control_space_list('us', db, spacetype = 'sea'), 3, db)
    if 38 in space_list:
        #function.discarddeck(bot, 'uk', 2, db)
        function.ewdiscard(bot, 324, 'us', 'jp', 1, db)
        function.add_vp(bot, 'us', 2, db)
    
    #------------------c325----------------------
def c325(bot, db):
    axis_home_space = {16:'Germany', 17:'Italy', 38:'Japan'}
    us_space_list = function.within('Allies', function.control_space_list('us', db), 1, db)
    if not set(axis_home_space).isdisjoint(set(us_space_list)):
        lock_id = thread_lock.add_lock()
        keyboard = []
        for space in axis_home_space:
            if space in us_space_list:
                keyboard.append([InlineKeyboardButton(axis_home_space[space], callback_data="['c325', {}, {}]".format(space, lock_id))])
        chat_id = db.execute("select playerid from country where id = 'us';").fetchall()
        text = "Country must discard the top 7 cards of its draw deck:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
        
def c325_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    country = db.execute("select id from country where home = :home;", {'home': query_list[1]}).fetchall()
    #function.discarddeck(bot, country[0][0], 7, db)
    function.ewdiscard(bot, 325, 'us', country[0][0], 7, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c326~327----------------------
def c326(bot, db):
    axis_home_space = {16:'Germany', 17:'Italy', 38:'Japan'}
    us_space_list = function.within('Allies', function.control_space_list('us', db, space_type = 'land'), 2, db)
    if not set(axis_home_space).isdisjoint(set(us_space_list)):
        lock_id = thread_lock.add_lock()
        keyboard = []
        for space in axis_home_space:
            if space in us_space_list:
                keyboard.append([InlineKeyboardButton(axis_home_space[space], callback_data="['c326', {}, {}]".format(space, lock_id))])
        chat_id = db.execute("select playerid from country where id = 'us';").fetchall()
        text = "Country must discard the top 5 cards of its draw deck:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
        
def c326_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    country = db.execute("select id from country where home = :home;", {'home': query_list[1]}).fetchall()
    #function.discarddeck(bot, country[0][0], 5, db)
    function.ewdiscard(bot, 198, 'us', country[0][0], 5, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c328----------------------
def c328(bot, db):
    country_list = ['ge', 'jp', 'it']
    for country in country_list:
        lock_id = thread_lock.add_lock()
        chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
        keyboard = [[InlineKeyboardButton("Discard the top 2 cards", callback_data="['c328', '{}', 'discard', {}]".format(country, lock_id))],
                    [InlineKeyboardButton("Remove a piece from the board", callback_data="['c328', '{}', 'remove', {}]".format(country, lock_id))]]
        text = "Choose what to do:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
    
def c328_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[2] == 'discard':
        #function.discarddeck(bot, query_list[1], 2, db)
        function.ewdiscard(bot, 328, 'uk', query_list[1], 2, db)
    elif query_list[2] == 'remove':
        lock_id = thread_lock.add_lock()
        space_list = function.control_space_list(query_list[1], db)
        battlebuild.self_remove_list.append(battlebuild.self_remove(query_list[1], space_list, 328, lock_id, 'air'))
        print("self_remove_id: " + str(len(battlebuild.self_remove_list)-1))
        self_remove_id = len(battlebuild.self_remove_list)-1
        info = battlebuild.self_remove_list[self_remove_id].self_remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    thread_lock.release_lock(query_list[-1])

    #------------------c329----------------------
def c329(bot, db):
    space_list = function.within('Allied', function.control_space_list('us', db, spacetype = 'sea'), 2, db)
    if 38 in space_list:
        function.ewdiscard(bot, 329, 'us', 'jp', 4, db)
        function.add_vp(bot, 'us', 2, db)

    #------------------c330----------------------
def c330(bot, db):
    lock_id = thread_lock.add_lock()
    space_list = function.build_list('ch', db, space_type = 'land')
    info = battlebuild.build_info(bot, 'ch', space_list, 330, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c331----------------------
def c331(bot, db):
    lock_id = thread_lock.add_lock()
    chat_id = db.execute("select playerid from country where id = 'uk';").fetchall()
    keyboard = [[InlineKeyboardButton("Build an Army", callback_data="['c331', 'land', {}]".format(lock_id))],
                [InlineKeyboardButton("Build an Navy", callback_data="['c331', 'sea', {}]".format(lock_id))]]
    text = "Choose what to do first:"
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)

def c331_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] == 'land':
        c182(bot, db)
        c187(bot, db)
    elif query_list[1] == 'sea':
        c187(bot, db)
        c182(bot, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c332----------------------
def c332(bot, db):
    lock_id = thread_lock.add_lock()
    info = c332_info(bot, lock_id, db)
    if info[2] != None:
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    else:
        thread_lock.release_lock(lock_id)

def c332_info(bot, lock_id, db):
    allied_country_list = ['uk', 'su', 'us', 'fr', 'ch']
    chat_id = db.execute("select playerid from country where id = 'us';").fetchall() 
    keyboard = []
    for country in allied_country_list:
        home_space = db.execute("select home from country where id = :country;", {'country':country}).fetchall()
        space_list = list(set(function.recuit_list(country, db)) & set(function.within('Allied', [home_space[0][0]], 1, db)))
        if len(space_list) > 0:
            space_list = function.get_name_list(space_list, db)
            for space in space_list:
                keyboard.append([InlineKeyboardButton(function.countryid2name[country] + ' - ' + space[1], callback_data="['c332', '{}', {}, {}]".format(country, space[0], lock_id))])
    if len(keyboard) > 0:
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        reply_markup = None
    text = "Recruit any one avaliable Allied Army or Navy in or adjacent to the corresponding country's Home space:"
    return chat_id[0][0], text, reply_markup

def c332_cb(bot, query, query_list, db):
    if query_list[1] == 'confirm':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        battlebuild.recuit(bot, query_list[2], query_list[3], 332, db)
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[1] == 'back':
            info = c332_info(bot, query_list[-1], db)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[2]}).fetchall()
            text = 'Recuit in ' + location[0][0] + ':'
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c332', 'confirm', '{}', {}, {}]".format(query_list[1], query_list[2], query_list[-1]))], [InlineKeyboardButton('Back', callback_data="['c332', 1, 'back', '{}', {}, {}]".format(query_list[1], query_list[2], query_list[-1]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id = query.message.chat_id, message_id = query.message.message_id, text = text, reply_markup = reply_markup)

    #------------------c333----------------------
def c333(bot, db):
    space_list = [53,47,48]
    for space in space_list:
        if space in function.build_list('us', db):
            battlebuild.build(bot, 'us', space, 333, db)
            
    #------------------c334----------------------
def c334(bot, db):
    lock_id = thread_lock.add_lock()
    hand = db.execute("select name, cardid from card where type = 'Status' and control ='us' and location in ('discardd', 'discardu');").fetchall()
    hand += db.execute("select name, cardid from card where type = 'Response' and control ='us' and location in ('used', 'discardd', 'discardu');").fetchall()
    hand += db.execute("select name, cardid from card where type not in ('Status', 'Response') and control ='us' and location in ('played', 'discardd', 'discardu');").fetchall()
    playerid = db.execute("select playerid from country where id = 'us';").fetchall()
    keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['c334', 'us', {}, {}]".format(hand[x][1], lock_id))] for x in range(len(hand))]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = playerid[0][0], text = "Play a card", reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)

def c334_cb(bot, query, query_list, db):
    card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':query_list[2]}).fetchall()
    bot.edit_message_text(chat_id = query.message.chat_id, message_id = query.message.message_id, text = "You play " + card_name[0][0])
    play_card(bot, query_list[2], query_list[1], db)
    thread_lock.release_lock(query_list[-1])

    #------------------c335----------------------
def c335(bot, db):
    if db.execute("select count(*) from piece where control in (select id from country where side = 'Allied') and loction = '36';").fecthall()[0][0] > 0:
        lock_id = thread_lock.add_lock()
        keyboard = []
        if not set([35,37]).isdisjoint(set(function.recruit_list('ch', db))):
            keyboard.append([InlineKeyboardButton("Recruit a Chinese Army in China or Szechuan", callback_data="['c335', 'r', {}]".format(lock_id))])
        if not set([35,37]).isdisjoint(set(function.remove_list('us', db))):
            keyboard.append([InlineKeyboardButton("Eliminate an Axis Army in China or Szechuan", callback_data="['c335', 'e', {}]".format(lock_id))])
        if len(keyboard) > 0:
            chat_id = db.execute("select playerid from country where id = 'us';").fetchall()
            text = "Choose what to do:"
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
            thread_lock.thread_lock(lock_id)
    
def c335_cb(bot, query, query_list, db):
    bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
    if query_list[1] == 'r':
        lock_id = thread_lock.add_lock()
        space_list = list(set([35,37]) & set(function.recruit_list('ch', db)))
        info = battlebuild.recruit_info(bot, 'ch', space_list, 335, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    elif query_list[1] == 'e':
        lock_id = thread_lock.add_lock()
        space_list = list(set([35,37]) & set(function.remove_list('us', db)))
        battlebuild.remove_list.append(battlebuild.remove_obj('us', space_list, 335, lock_id, 'army'))
        print("remove_id: " + str(len(battlebuild.remove_list)-1))
        remove_id = len(battlebuild.remove_list)-1
        info = battlebuild.remove_list[remove_id].remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    thread_lock.release_lock(query_list[-1])
    
    #------------------c336----------------------
def c336(bot, db):
    lock_id = thread_lock.add_lock()
    hand = db.execute("select name, cardid from card where location = 'hand' and control = 'uk' order by sequence;").fetchall()
    playerid = db.execute("select playerid from country where id = 'uk';").fetchall()
    keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['c336', 1, {}, {}]".format(hand[x][1], lock_id))] for x in range(len(hand))]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = playerid[0][0], text = "Please play a card", reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)
    lock_id = thread_lock.add_lock()
    playerid = db.execute("select playerid from country where id = 'us';").fetchall()
    text = "You may discard the top 3 cards of your draw deck and place this card on top of your draw deck"
    keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c336', 2, 'confirm', {}]".format(lock_id))]
                , [InlineKeyboardButton('Pass', callback_data="['c336', 2,'pass', {}]".format(lock_id))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = playerid[0][0], text = text, reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)
    
def c336_cb(bot, query, query_list, db):
    if query_list[1] == 1:
        if query_list[2] == 'confirm':
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            cardid = db.execute("select cardid from card where location = 'selected';").fetchall()
            play_card(bot, cardid[0][0], 'uk', db)
            function.drawdeck(bot, 'uk', 1, db)
            db.commit()
            thread_lock.release_lock(query_list[-1])
        else:
            if query_list[2] == 'back':
                db.execute("update card set location = 'hand' where location = 'selected' and control = 'uk';")
                text = 'Please play a card'
                hand = db.execute("select name, cardid from card where location = 'hand' and control = 'uk' order by sequence;").fetchall()
                keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['c336', 1, {}, {}]".format(hand[x][1], query_list[-1]))] for x in range(len(hand))]
            else:
                db.execute("update card set location = 'selected' where cardid =:id and control = 'uk';", {'id': query_list[2]})
                selected = db.execute("select name, type, text from card where location = 'selected' and control = 'uk' order by sequence;").fetchall()
                text = "<b>" + selected[0][0] + "</b> - " + selected[0][1] + " - " + selected[0][2]
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c336', 1, 'confirm', {}]".format(query_list[-1]))], [InlineKeyboardButton('Back', callback_data="['c336', 1, 'back', {}]".format(query_list[-1]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    if query_list[1] == 2:
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        if query_list[2] == 'confirm':
            function.discarddeck(bot, 'us', 3, db)
            function.movecardtop(bot, 336, db)
        thread_lock.release_lock(query_list[-1])
    db.commit()
    
    #------------------c337----------------------
def c337(bot, db):
    jp_status = db.execute("select name, cardid from card where control = 'jp' and location in ('played', 'used') and type = 'Status';").fetchall()
    jp_response = db.execute("select name, cardid from card where control = 'jp' and location == 'played' and type = 'Response';").fetchall()
    if (len(jp_status) > 0) or (len(jp_response) > 0):
        lock_id = thread_lock.add_lock()
        chat_id = db.execute("select playerid from country where id = 'us';").fetchall()
        keyboard = []
        if (len(jp_status) > 0):
            keyboard += [[InlineKeyboardButton(card[0], callback_data="['c337', {}, {}]".format(card[1], lock_id))] for card in jp_status]
        if (len(jp_response) > 0):
            keyboard.append([InlineKeyboardButton("Japanese Response", callback_data="['c337', 'r', {}]".format(lock_id))])
        text = "Discard a Japanese Status or Response card from the table:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)
    
def c337_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[1] == 'r':
        jp_response = db.execute("select cardid from card where control = 'jp' and location = 'played' and type = 'Response';").fetchall()
        function.facedowndiscardcard(bot, random.choice(jp_response)[0], db)
    else:                    
        function.discardcard(bot, query_list[1], db)
    thread_lock.release_lock(query_list[-1])

    #------------------c338----------------------
def c338(bot, db):
    if 20 in function.recuit_list('su', db, space_type = 'land'):
        battlebuild.recuit(bot, 'su', 20, 338, db)
    c246(bot, db)

    #------------------c339----------------------
def c339(bot, db):
    if 12 in function.build_list('us', db, space_type = 'land'):
        battlebuild.build(bot, 'us', 12, 339, db)
    if not set([16, 17]).isdisjoint(set(function.battle_list('us', db, space_type = 'land'))):
        lock_id = thread_lock.add_lock()
        space_list = list(set([16, 17]) & set(function.battle_list('us', db, space_type = 'land')))
        info = battlebuild.battle_info(bot, 'us', space_list, 339, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c340----------------------
def c340(bot, db): 
    lock_id = thread_lock.add_lock()
    info = c340_info(bot, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

def c340_info(bot, lock_id, db):
    space_list = list(set([3, 44, 47, 50, 51, 53]) & set(function.build_list('us', db)))
    name_list = function.get_name_list(space_list, db)
    buffer.space_list = space_list
    chat_id = db.execute("select playerid from country where id = 'us';").fetchall()
    text = "Choose a space to build"
    keyboard = [[InlineKeyboardButton(space[1], callback_data="['c340', {}, {}]".format(space[0], lock_id))] for space in name_list]
    keyboard.append([InlineKeyboardButton('Pass', callback_data="['c340', 'pass', {}, {}]".format(lock_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return chat_id[0][0], text, reply_markup


def c340_cb(bot, query, query_list, db):
    if query_list[1] == 'confirm':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        build(bot, 'us', query_list[2], 340, db)
        thread_lock.release_lock(query_list[-1])
        lock_id = thread_lock.add_lock()
        space_list = list(function.within('Allied', [query_list[2]], 1, db) & set(function.battle_list('us', db, space_type = 'sea')))
        info = battlebuild.battle_info(bot, 'us', space_list, 340, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    elif query_list[1] == 'pass':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[1] == 'back':
            info = c340_info(bot, query_list[-1], db)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[1]}).fetchall()
            text = 'Build in ' + location[0][0] + ':'
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c340', 'confirm', {}, {}]".format(query_list[1], query_list[-1]))], [InlineKeyboardButton('Back', callback_data="['c340', 'back', {}]".format(query_list[-1]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)
        db.commit()

    #------------------c341----------------------
c341_list = []
def c341(bot, db):
    global _pass
    _pass = True
    global c341_list
    c341_list = function.control_space_list('us', db)
    while _pass:
        buffer.space_list = c341_list
        lock_id = thread_lock.add_lock()
        info = c341_info(bot, 'us', c341_list, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

def c341_info(bot, country, space_list, lock_id, db):
    name_list = function.get_name_list(space_list, db)
    chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    text = "Choose a space to remove"
    keyboard = [[InlineKeyboardButton(space[1], callback_data="['c341', '{}', {}, {}]".format(country, space[0], lock_id))] for space in name_list]
    keyboard.append([InlineKeyboardButton('Pass', callback_data="['c341', '{}', 'pass', {}]".format(country, lock_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return chat_id[0][0], text, reply_markup

def c341_cb(bot, query, query_list, db):
    if query_list[2] == 'confirm':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        piece = db.execute("select pieceid from piece where control = 'us' and location = :space;", {'space':query_list[3]}).fetchall()
        battlebuild.remove(bot, 'us', piece[0][0], query_list[3], 341, db)
        if db.execute("select type from space where spaceid = :spaceid;", {'spaceid':query_list[3]}).fetchall()[0][0] == 'land':
            c304(bot, db)
        elif db.execute("select type from space where spaceid = :spaceid;", {'spaceid':query_list[3]}).fetchall()[0][0] == 'sea':
            c309(bot, db)
        global c341_list
        c341_list.remove(query_list[3])
        thread_lock.release_lock(query_list[-1])
    elif query_list[2] == 'pass':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        global _pass
        _pass = False
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            info = c341_info(bot, query_list[1] , buffer.space_list, query_list[-1], db)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[2]}).fetchall()
            text = 'Removed ' + location[0][0] + ':'
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c341', '{}', 'confirm', {}, {}]".format(query_list[1], query_list[2], query_list[3]))], [InlineKeyboardButton('Back', callback_data="['c341', '{}', 'back', {}]".format(query_list[1], query_list[3]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)
        db.commit()

    #------------------c342----------------------
def c342(bot, db):
    space_list = {7:'Southern Ocean', 10:'South Altantic'}
    recuit_list = function.recuit_list('us', db)
    if 6 in recuit_list:
        battlebuild.recuit(bot, 'us', 6, 342, db)
    if not set(space_list).isdisjoint(set(remove_list)):
        lock_id = thread_lock.add_lock()
        keyboard = []
        for space in space_list:
            if space in recuit_list:
                keyboard.append([InlineKeyboardButton(space_list[space], callback_data="['c342', {}, {}]".format(space, lock_id))])
        chat_id = db.execute("select playerid from country where id = 'us';").fetchall()
        text = "Recruit a Navy in the South Atlantic or the Southern Ocean:"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup)
        thread_lock.thread_lock(lock_id)

def c342_cb(bot, query, query_list, db):
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    battlebuild.recuit(bot, 'us', query_list[1], 342, db)
    thread_lock.release_lock(query_list[-1])

    #------------------c343----------------------
def c343(bot, db):
    lock_id = thread_lock.add_lock()
    space_list = function.battle_list('ch', db, space_type = 'land')
    info = battlebuild.battle_info(bot, 'ch', space_list, 343, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c344----------------------
def c344(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'us', 1, db)
    battlebuild.build(bot, 'us', battled_space, 344, db)
                        
    #------------------c345----------------------
    #------------------c346----------------------
def c346(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'us', 1, db)
    battlebuild.build(bot, 'us', battled_space, 346, db)
    
    #------------------c347----------------------
def c347(bot, db):
    function.discardhand(bot, 'jp', 1, db)

    #------------------c348----------------------
def c348(bot, handler_id, db):
    build_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'us', 1, db)
    lock_id = thread_lock.add_lock()
    space_list = list(set(function.build_list('us', db, space_type = 'land')) & set(function.within('Allied', [build_space], 1, db)))
    info = battlebuild.build_info(bot, 'us', space_list, 348, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
    #------------------c349----------------------
def c349(bot, handler_id, db):
    passive_country = buffer.handler_list[handler_id].passive_country_id
    function.discarddeck(bot, passive_country, 1, db)
    
    #------------------c350----------------------
def c350(bot, handler_id, db):
    battlebuild.restore(bot, buffer.handler_list[handler_id].piece_id, buffer.handler_list[handler_id].space_id, db)
    function.discarddeck(bot, 'us', 3, db)
    db.commit()

    #------------------c351----------------------
def c351(bot, db):
    hand = db.execute("select name, cardid, type, text from card where location = 'hand' and control = 'us' order by sequence;").fetchall()
    if len(hand) == 0:
        group_chat_id = db.execute("select chatid from game;").fetchall()
        text = "<b>" + function.countryid2name['us'] + "</b> have no hand"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        db.close()
    else:
        playerid = db.execute("select playerid from country where id = 'us';").fetchall()
        lock_id = thread_lock.add_lock()
        text = "You may take one or two cards from your hand and place them on the bottom of your draw deck:\n\n"
        for card in hand:
            text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
        keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['c351', {}, {}]".format(hand[x][1], lock_id))] for x in range(len(hand))]
        keyboard.append([InlineKeyboardButton('Pass', callback_data="['c351', 'pass', {}]".format(lock_id))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = playerid[0][0], text = text, reply_markup = reply_markup, parse_mode=telegram.ParseMode.HTML)
        thread_lock.thread_lock(lock_id)

def c351_cb(bot, query, query_list, db):
    if query_list[1] == 'confirm' or query_list[1] == 'pass':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        selected = db.execute("select cardid, sequence from card where location = 'selected' and control ='us' order by sequence;").fetchall()
        if selected != None:
            for card in selected:
                card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':card[0]}).fetchall()
                text = "<b>" + card_name[0][0] + "</b> move to bottom of deck"
                bot.send_message(chat_id = query.message.chat_id, text = text, parse_mode=telegram.ParseMode.HTML)
                function.movecardbottom(bot, card[0], db)
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[1] == 'back':
            db.execute("update card set location = 'hand' where location = 'selected' and control = 'us';")
            hand = db.execute("select name, cardid, type, text sequence from card where location = 'hand' and control = 'us' order by sequence;").fetchall()
            text = "You may take one or two cards from your hand and place them on the bottom of your draw deck:\n\n"
            for card in hand:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['c351', {}, {}]".format(hand[x][1], query_list[-1]))] for x in range(len(hand))]
            keyboard.append([InlineKeyboardButton('Pass', callback_data="['c351', 'pass', {}]".format(query_list[-1]))])
        else:
            db.execute("update card set location = 'selected' where cardid =:id and control = 'us';", {'id': query_list[1]})
            hand = db.execute("select name, cardid, type, text from card where location = 'hand' and control = 'us' order by sequence;").fetchall()
            selected = db.execute("select name, cardid, type, text from card where location = 'selected' and control = 'us' order by sequence;").fetchall()
            text = 'Hand:\n'
            for card in hand:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            text += '\nSelected:\n'
            for card in selected:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"    
            if len(selected) < 2:
                keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['c351', {}, {}]".format(hand[x][1], query_list[-1]))] for x in range(len(hand))]
            else:
                keyboard = []
            keyboard.append([InlineKeyboardButton('Confirm', callback_data="['c351', 'confirm', {}]".format(query_list[-1]))])
            keyboard.append([InlineKeyboardButton('Back', callback_data="['c351', 'back', {}]".format(query_list[-1]))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    db.commit()
    
    #------------------c352----------------------
    #------------------c353----------------------
def c353(bot, db):
    function.discarddeck(bot, 'us', 1, db)
    c309(bot, db)

    #------------------c354----------------------
def c354(bot, handler_id, db):
    battled_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'us', 1, db)
    lock_id = thread_lock.add_lock()
    space_list = list(set(function.battle_list('us', db, space_type = 'land')) & set(function.within('Allied', [battled_space], 1, db)))
    info = battlebuild.battle_info(bot, 'us', space_list, 354, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c355----------------------
    #------------------c356----------------------                    
    #------------------c357----------------------
def c357(bot, db):
    function.discarddeck(bot, 'us', 1, db)
    c304(bot, db)

    #------------------c358~361----------------------
    
    #------------------c362----------------------
def c362(bot, handler_id, db):
    built_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'us', 1, db)
    space_list1 = function.within('Allied', [built_space], 1, db)
    space_list2 = function.build_list('us', db)
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.build_info(bot, 'us', space_list, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c363----------------------
def c363(bot, handler_id, db):
    # TODO discard ec
    function.discardew(bot, 'us', 1, db)
    lock_id = thread_lock.add_lock()
    battled_space = buffer.handler_list[handler_id].space_id
    info = battlebuild.battle_info(bot, 'us', [battled_space], 363, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c364----------------------
def c364(bot, db):
    lock_id = thread_lock.add_lock()
    space_list = function.deploy_list('ch', db)
    info = air.deploy_info(bot, 'ch', space_list, 364, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c365----------------------
def c365(bot, db):
    lock_id = thread_lock.add_lock()
    hand_list = db.execute("select name, cardid from card where location = 'hand' and control = 'us' order by sequence;").fetchall()
    playerid = db.execute("select playerid from country where id = 'us';").fetchall()
    keyboard = [[InlineKeyboardButton(hand[0], callback_data="['c365', {}, {}]".format(hand[1], lock_id))] for hand in range(len(hand_list))]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = playerid[0][0], text = "Take a Bolster card from your hand and place it face down on the table:", reply_markup = reply_markup)
    
def c365_cb(bot, query, query_list, db):
    if query_list[1] == 'confirm':
        db.execute("update card set location = 'played' where cardid = :card", {'card':query_list[1]})
        db.commit()
        group_chat = db.execute("select chatid from game;").fetchall()
        text = function.countryid2name['us'] + " place a <b>Bolster</b> face down"
        bot.send_message(chat_id = group_chat[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    else:
        if query_list[1] == 'back':
            hand = db.execute("select name, cardid from card where location = 'hand' and control = 'us' order by sequence;").fetchall()
            playerid = db.execute("select playerid from country where id = 'us';").fetchall()
            text = "Take a Bolster card from your hand and place it face down on the table:"
            keyboard = [[InlineKeyboardButton(hand[0], callback_data="['c365', {}, {}]".format(hand[1], query_list[-1]))] for hand in range(len(hand_list))]
        else:
            selected = db.execute("select name, type, text from card where cardid = :cardid;", {'cardid':query_list[1]}).fetchall()
            text = "<b>" + selected[0][0] + "</b> - " + selected[0][1] + " - " + selected[0][2]
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c365', 'confirm', {}, {}]".format(query_list[1], query_list[-1]))], [InlineKeyboardButton('Back', callback_data="['c365', 'back', {}]".format(query_list[-1]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    

    #------------------c366----------------------
def c366(bot, db):
    function.discarddeck(bot, 'us', 2, db)
    lock_id = thread_lock.add_lock()
    discard_list = db.execute("select name, cardid from card where location in ('discardu', 'discardd', 'used') and type = 'Response' and control = 'uk' order by sequence;").fetchall()
    playerid = db.execute("select playerid from country where id = 'uk';").fetchall()
    keyboard = [[InlineKeyboardButton(discard[0], callback_data="['c366', {}, {}]".format(discard[1], lock_id))] for discard in range(len(discard_list))]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id = playerid[0][0], text = "Play a Response from discard pile:", reply_markup = reply_markup)
    thread_lock.thread_lock(lock_id)
    
def c366_cb(bot, query, query_list, db):
    if query_list[1] == 'confirm':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        play_card(bot, query_list[2], 'uk', db)
        db.commit()
        thread_lock.release_lock(query_list[-1])
    else:
        if query_list[1] == 'back':
            text = "Play a Response from discard pile:"
            discard_list = db.execute("select name, cardid from card where location in ('discardu', 'discardd', 'used') and type = 'Response' and control = 'uk' order by sequence;").fetchall()
            keyboard = [[InlineKeyboardButton(discard[0], callback_data="['c366', {}, {}]".format(discard[1], lock_id))] for discard in range(len(discard_list))]
        else:
            selected = db.execute("select name, type, text from card where cardid = :cardid;", {'cardid':query_list[1]}).fetchall()
            text = "<b>" + selected[0][0] + "</b> - " + selected[0][1] + " - " + selected[0][2]
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['c366', 'confirm', {}, {}]".format(query_list[1], query_list[-1]))], [InlineKeyboardButton('Back', callback_data="['c366', 'back', {}]".format(query_list[-1]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)

    #------------------c367----------------------
def c367(bot, handler_id, db):
    passive_country = buffer.handler_list[handler_id].passive_country_id
    home_space = db.execute("select home from country where id = :country;", {'country':passive_country}).fetchall()
    space_list1 = function.within('Allied', [home_space[0][0]], 2, db)
    space_list2 = function.control_air_space_list('us', db)
    space_list = list(set(space_list1) & set(space_list2))
    if len(space_list) > 0:
        function.discarddeck(bot, passive_country, len(space_list), db)
        
    #------------------c368----------------------
def c368(bot, db):
    function.discarddeck(bot, 'us', 1, db)
    space_list1 = function.within('Allied', [], 1, db)
    space_list2 = function.recuit_list('us', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    info = battlebuild.recuit_info(bot, 'us', space_list, 368, lock_id, db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)

    #------------------c369----------------------
def c369(bot, db):
    function.discarddeck(bot, 'us', 1, db)
    chat_id = db.execute("select playerid from country where id = 'us';").fetchall()
    keyboard = [[InlineKeyboardButton('Deploy an Air Force', callback_data="['c369', 'd']".format(country))],
                [InlineKeyboardButton('Marshal an Air Force', callback_data="['c369', 'm']".format(country))]]
    drawmap.drawmap(db)
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_photo(chat_id = chat_id[0][0], caption = function.countryid2name[country] + " - Air Force step", reply_markup = reply_markup, photo=open('pic/tmp.jpg', 'rb'))

def c369_cb(bot, query, query_list, db):
    if query_list[1] == 'd':
        lock_id = thread_lock.add_lock()
        space_list1 = [39, 45, 46, 48]
        space_list2 = function.deploy_list('us', db)
        space_list = list(set(space_list1) & set(space_list2))
        info = air.deploy_info(bot, 'us', space_list, 369, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)
    else:
        lock_id = thread_lock.add_lock()
        space_list = function.control_air_space_list('us', db)
        battlebuild.self_remove_list.append(battlebuild.self_remove('us', space_list, None, lock_id, 'air'))
        print("self_remove_id: " + str(len(battlebuild.self_remove_list)-1))
        self_remove_id = len(battlebuild.self_remove_list)-1
        info = battlebuild.self_remove_list[self_remove_id].self_remove_info(db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        lock_id = thread_lock.add_lock()
        space_list1 = [39, 45, 46, 48]
        space_list2 = function.deploy_list('us', db)
        space_list = list(set(space_list1) & set(space_list2))
        info = air.marshal_info(bot, 'us', space_list, 369, lock_id, db)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        thread_lock.thread_lock(lock_id)

    #------------------c370----------------------
def c370(bot, handler_id, db):
    marshalled_space = buffer.handler_list[handler_id].space_id
    function.discarddeck(bot, 'us', 1, db)
    space_list1 = function.within('Allied', [marshalled_space], 1, db)
    space_list2 = function.remove_list('us', db, space_type = 'land')
    space_list = list(set(space_list1) & set(space_list2))
    lock_id = thread_lock.add_lock()
    battlebuild.remove_list.append(battlebuild.remove_obj('us', space_list, 370, lock_id, 'army'))
    print("remove_id: " + str(len(battlebuild.remove_list)-1))
    remove_id = len(battlebuild.remove_list)-1
    info = battlebuild.remove_list[remove_id].remove_info(db)
    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
    thread_lock.thread_lock(lock_id)
