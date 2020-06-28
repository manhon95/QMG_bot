import telegram
import sqlite3
import random
import function
import drawmap
import os
import status_handler
import cardfunction
import thread_lock
import air
import battlebuild
import traceback
import game_session


from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
message_id = None
next_turn = {'ge':'uk','uk':'jp','jp':'su','su':'it','it':'us','us':'ge'}
#------------------------------------------Setup------------------------------------------
    
def setup(bot, session):
    country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us', 'fr', 'ch']
    db = sqlite3.connect(session.get_db_dir())
    # reset
    db.execute("update game set turn = 1;")
    db.execute("update card set location = 'deck';")
    db.execute("update piece set location = 'none';")
    db.execute("update space set control = 'neutral';")
    db.execute("update country set mulligan = 'not_used';")
    for country in country_list:
        # update point
        db.execute("update country set point = 0 where id = :country;", {'country':country})
        # update homecountry
        info = db.execute("select home, side from country where id = :country;", {'country':country}).fetchall()
        db.execute("update piece set location = :home where pieceid = (select min(pieceid) from piece where control = :country);", {'home':info[0][0], 'country':country})
        function.updatecontrol(bot, db)
        function.updatesupply(db)
    country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us']
    for country in country_list:
        # shuffle
        function.shuffledeck(bot, country, db)
        # draw 10
        function.drawdeck(bot, country, 12, db)
        hand = db.execute("select name, cardid, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':country}).fetchall()
        playerid = db.execute("select playerid from country where id =:country;", {'country':country}).fetchall()
        keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['setup', '{}', {}]".format(country, hand[x][1]))] for x in range(len(hand))]
        keyboard.append([InlineKeyboardButton('Mulligan', callback_data="['setup', '{}', 'mu']".format(country))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = function.countryid2name[country] + " - Discard 5 card from hand\n"
        for card in hand:
            text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
        bot.send_message(chat_id = playerid[0][0], text = text, reply_markup = reply_markup, parse_mode=telegram.ParseMode.HTML)
    # draw map
    try:
        session.draw_map()
        chatid = db.execute("select chatid from game;").fetchall()
        bot.send_chat_action(chat_id=chatid[0][0], action=telegram.ChatAction.TYPING)
        bot.send_photo(chat_id=chatid[0][0], photo=open(session.get_dir() + '/tmp.jpg', 'rb'))
    except Exception:
        pass

def setup_cb(bot, query, query_list, db):
    if query_list[2] == 'confirm':
        db.execute("update card set location = 'discardd' where location = 'selected' and control =:country;", {'country':query_list[1]})
        db.execute("update country set status = 'inactive' where id =:country;", {'country':query_list[1]})
        db.commit()
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=function.countryid2name[query_list[1]] + " - Waiting other player...")
        group_chat_id = db.execute("select chatid from game;").fetchall()
        text = "<b>" + function.countryid2name[query_list[1]] + "</b> ready"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        if db.execute("select count(*) from country where status = 'filled';").fetchall()[0][0] == 2:
            db.execute("update country set status = 'play' where id = 'ge';")
            db.commit()
            session = game_session.find_session(query.message.chat_id)
            play(bot, 'ge', session)
    else:
        if query_list[2] == 'back':
            db.execute("update card set location = 'hand' where location = 'selected' and control =:country;", {'country':query_list[1]})
        else:
            db.execute("update card set location = 'selected' where cardid =:id and control =:country;", {'id': query_list[2], 'country':query_list[1]})
        hand = db.execute("select name, cardid, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
        if query_list[2] == 'back':
            text = function.countryid2name[query_list[1]] + " - Discard 5 card from hand\n"
            for card in hand:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['setup', '{}', {}]".format(query_list[1], hand[x][1]))] for x in range(len(hand))]
            if db.execute("select mulligan from country where id = :country;", {'country':query_list[1]}).fetchall()[0][0] != 'used':
                keyboard.append([InlineKeyboardButton('Mulligan', callback_data="['setup', '{}', 'mu']".format(query_list[1]))])
        elif query_list[2] == 'mu':
            if len(query_list) == 4:
                bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=function.countryid2name[query_list[1]] + " - Processing...")
                db.execute("update country set mulligan = 'used' where id =:country;", {'country':query_list[1]})
                group_chat_id = db.execute("select chatid from game;").fetchall()
                text = "<b>" + function.countryid2name[query_list[1]] + "</b> declared a mulligan"
                bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
                db.execute("update card set location = 'deck' where control =:country;", {'country':query_list[1]})
                # shuffle
                function.shuffledeck(bot, query_list[1], db)
                # draw 15
                function.drawdeck(bot, query_list[1], 12, db)
                hand = db.execute("select name, cardid, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
                keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['setup', '{}', {}]".format(query_list[1], hand[x][1]))] for x in range(len(hand))]
                text = function.countryid2name[query_list[1]] + " - Discard 5 card from hand\n"
                for card in hand:
                    text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            else:
                text = function.countryid2name[query_list[1]] + " - <b>Once</b> per setup, put hand back into deck and draw a new hand\n"
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['setup', '{}', 'mu', 'confirm']".format(query_list[1]))], [InlineKeyboardButton('Back', callback_data="['setup', '{}', 'back']".format(query_list[1]))]]
        else:
            selected = db.execute("select name, type, text from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            text =  function.countryid2name[query_list[1]] + " - Discarded:\n"
            for card in selected:
                text += "<b>" + card[0] + "</b> - " + card[1] + " - " + card[2] + "\n"
            text += "\nHand:\n"
            for card in hand:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            if len(selected) >= 5:
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['setup', '{}', 'confirm']".format(query_list[1]))], [InlineKeyboardButton('Back', callback_data="['setup', '{}', 'back']".format(query_list[1]))]]
            else:
                keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['setup', '{}', {}]".format(query_list[1], hand[x][1]))] for x in range(len(hand))]
                if db.execute("select mulligan from country where id = :country;", {'country':query_list[1]}).fetchall()[0][0] != 'used':
                    keyboard.append([InlineKeyboardButton('Mulligan', callback_data="['setup', '{}', 'mu']".format(query_list[1]))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        db.commit()


#------------------------------------------normal game round------------------------------------------
    #------------------------------------------Play Step------------------------------------------
r_r_used = False

def play(bot, country, session):
    if session.save_session_turn(country):
        print("Autosave success - TURN")
    else:
        print("Autosave fail - TURN")
    if session.save_session():
        print("Autosave success - play")
    else:
        print("Autosave fail - play")
    if session.save_session_turn2(country):
        print("Autosave2 success - TURN")
    else:
        print("Autosave2 fail - TURN")
    if session.save_session2():
        print("Autosave2 success - play")
    else:
        print("Autosave2 fail - play")
    global r_r_used
    r_r_used = False
    db = sqlite3.connect(session.get_db_dir())
    group_chat_id = db.execute("select chatid from game;").fetchall()
    text = "<b>" + function.countryid2name[country] + "</b> Play step"
    session.message_id = bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML).message_id
    lock_id = session.add_lock()
    status_handler.send_status_card(bot, country, 'Beginning of Play step', lock_id, session, card_id = None)
    session.draw_map()
    hand = db.execute("select name, cardid, control, type from card where location = 'hand' and control = :country order by sequence;", {'country':country}).fetchall()
    playerid = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    if len(hand) != 0:
        keyboard = [[InlineKeyboardButton(hand[x][3] + ' - ' + hand[x][0], callback_data="['play', '{}', {}]".format(hand[x][2], hand[x][1]))] for x in range(len(hand))]
    else:
        keyboard = []
    if len(hand) >= 4:
        keyboard += [[InlineKeyboardButton('Reallocate Resources', callback_data="['play', '{}', 'r_r']".format(country))]]
    keyboard += [[InlineKeyboardButton('Pass and discard 1 card', callback_data="['play', '{}', 'pass']".format(country))]]
    extra_keyboard = status_handler.status_play_keyboard(country, db)
    if extra_keyboard != None:
        keyboard += extra_keyboard
    reply_markup = InlineKeyboardMarkup(keyboard)
    #bot.send_message(chat_id = playerid[0][0], text = function.countryid2name[country] + " - Play a card", reply_markup = reply_markup)
    bot.send_photo(chat_id = playerid[0][0], caption = function.countryid2name[country] + " - Play a card", reply_markup = reply_markup, photo=open(session.get_dir() + '/tmp.jpg', 'rb'))
    db.commit()

def status_play_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    session = game_session.find_session(query.message.chat_id)
    cardfunction.play_status(bot, query_list[2], query_list[1], None, db)
    bot.edit_message_caption(chat_id=query.message.chat_id, message_id=query.message.message_id, caption='After play...')
    lock_id = session.add_lock()
    status_handler.send_status_card(bot, query_list[1], 'After Playing a card', lock_id, session, card_id = query_list[2])
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    db.execute("update country set status = 'supply' where id = :country;", {'country':query_list[1]})
    db.commit()
    air_force(bot, query_list[1], session)
    
def play_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':query_list[3]}).fetchall()
        bot.edit_message_caption(chat_id = query.message.chat_id, message_id = query.message.message_id, caption = "You play " + card_name[0][0])
        cardfunction.play_card(bot, query_list[3], query_list[1], session)
        bot.edit_message_caption(chat_id=query.message.chat_id, message_id=query.message.message_id, caption='After play...')
        lock_id = session.add_lock()
        status_handler.send_status_card(bot, query_list[1], 'After Playing a card', lock_id, session, card_id = query_list[3])
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        bot.delete_message(chat_id = db.execute("select chatid from game;").fetchall()[0][0], message_id = session.message_id)
        db.execute("update country set status = 'air_force' where id = :country;", {'country':query_list[1]})
        db.commit()
        air_force(bot, query_list[1], session)
    elif query_list[2] == 'pass':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        function.discardhand(bot, query_list[1], 1, session)
        db.commit()
        #supply(bot, query_list[1])
        session = game_session.find_session(query.message.chat_id)
        air_force(bot, query_list[1], session)
    elif query_list[2] == 'r_r_confirm':
        bot.delete_message(chat_id= query.message.chat_id, message_id = query.message.message_id)
        cardfunction.r_r(bot, query_list[1], session)
        global r_r_used
        r_r_used = True
        hand = db.execute("select name, cardid, control, type from card where location = 'hand' and control = :country order by sequence;", {'country':query_list[1]}).fetchall()
        playerid = db.execute("select playerid from country where id = :country;", {'country':query_list[1]}).fetchall()
        if len(hand) != 0:
            keyboard = [[InlineKeyboardButton(hand[x][3] + ' - ' + hand[x][0], callback_data="['play', '{}', {}]".format(hand[x][2], hand[x][1]))] for x in range(len(hand))]
        else:
            keyboard = []
        keyboard += [[InlineKeyboardButton('Pass and discard 1 card', callback_data="['play', '{}', 'pass']".format(query_list[1]))]]
        extra_keyboard = status_handler.status_play_keyboard(query_list[1], db)
        if extra_keyboard != None:
            keyboard += extra_keyboard
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_photo(chat_id = query.message.chat_id, caption = function.countryid2name[query_list[1]] + " - Play a card", reply_markup = reply_markup, photo=open(session.get_dir() + '/tmp.jpg', 'rb'))
    elif query_list[2] == 'r_r':
        text = "Reallocate Resources - Once per turn discard 4 cards from your hand to search your draw deck for a 'Build Army', 'Build Navy', 'Land Battle', 'Sea Battle', or 'Deploy Air Force' and add it to your hand."
        keyboard = [[InlineKeyboardButton('Confirm', callback_data="['play', '{}', 'r_r_confirm']".format(query_list[1]))],
                    [InlineKeyboardButton('Back', callback_data="['play', '{}', 'back']".format(query_list[1]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_caption(chat_id=query.message.chat_id, message_id=query.message.message_id, caption=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    else:
        if query_list[2] == 'back':
            #db.execute("update card set location = 'hand' where location = 'selected' and control =:country;", {'country':query_list[1]})
            text = function.countryid2name[query_list[1]] + " - Play a card"
            hand = db.execute("select name, cardid, control, type from card where location = 'hand' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            if len(hand) != 0:
                keyboard = [[InlineKeyboardButton(hand[x][3] + ' - ' + hand[x][0], callback_data="['play', '{}', {}]".format(hand[x][2], hand[x][1]))] for x in range(len(hand))]
            else:
                keyboard = []
            if len(hand) >= 4 and not r_r_used:
                keyboard += [[InlineKeyboardButton('Reallocate Resources', callback_data="['play', '{}', 'r_r']".format(query_list[1]))]]
            keyboard += [[InlineKeyboardButton('Pass and discard 1 card', callback_data="['play', '{}', 'pass']".format(query_list[1]))]]
            extra_keyboard = status_handler.status_play_keyboard(query_list[1], db)
            if extra_keyboard != None:
                keyboard += extra_keyboard  
        else:
            #db.execute("update card set location = 'selected' where cardid =:id and control =:country;", {'id': query_list[2], 'country':query_list[1]})
            selected = db.execute("select name, type, text from card where cardid = :cardid;", {'cardid':query_list[2]}).fetchall()
            text = "<b>" + selected[0][0] + "</b> - " + selected[0][1] + " - " + selected[0][2]
            keyboard = []
            if not selected[0][1] in ['Bolster', 'Deploy Air Force']:
                keyboard += [[InlineKeyboardButton('Confirm', callback_data="['play', '{}', 'confirm', {}]".format(query_list[1], query_list[2]))]]
            keyboard += [[InlineKeyboardButton('Back', callback_data="['play', '{}', 'back']".format(query_list[1]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            bot.edit_message_caption(chat_id=query.message.chat_id, message_id=query.message.message_id, caption=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        except:
            traceback.print_exc()
            pass
        db.commit()


    #------------------------------------------Air Force Step------------------------------------------

def air_force(bot, country, session):
    if session.save_session():
        print("Autosave success - air_force")
    else:
        print("Autosave fail - air_force")
    if session.save_session2():
        print("Autosave2 success - air_force")
    else:
        print("Autosave2 fail - air_force")
    db = sqlite3.connect(session.get_db_dir())
    group_chat_id = db.execute("select chatid from game;").fetchall()
    text = "<b>" + function.countryid2name[country] + "</b> Air Force step"
    session.message_id = bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML).message_id
    lock_id = session.add_lock()
    status_handler.send_status_card(bot, country, 'Beginning of Air step', lock_id, session)
    hand_count = db.execute("select count(*) from card where location = 'hand' and control = :country;", {'country':country}).fetchall()
    deploy_air_count = db.execute("select count(*) from card where type = 'Deploy Air Force' and location = 'hand' and control = :country;", {'country':country}).fetchall()
    playerid = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    keyboard = []
    if deploy_air_count[0][0] > 0:
        keyboard += [[InlineKeyboardButton('Deploy an Air Force', callback_data="['air', '{}', 'd']".format(country))]]
    if hand_count[0][0] > 0 and len(function.control_air_space_list(country, db)):
        keyboard += [[InlineKeyboardButton('Marshal an Air Force', callback_data="['air', '{}', 'm']".format(country))]]
    if len(keyboard) > 0:
        keyboard += [[InlineKeyboardButton('Pass', callback_data="['air', '{}', 'pass']".format(country))]]
        '''extra_keyboard = status_handler.status_play_keyboard(country, db)
        if extra_keyboard != None:
            keyboard += extra_keyboard'''
        session.draw_map()
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_photo(chat_id = playerid[0][0], caption = function.countryid2name[country] + " - Air Force step", reply_markup = reply_markup, photo=open(session.get_dir() + '/tmp.jpg', 'rb'))
        db.commit()
    else:
        bot.delete_message(chat_id = group_chat_id[0][0], message_id = session.message_id)
        db.commit()
        supply(bot, country, session)
                                

def air_force_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    if query_list[2] == 'd':
        deploy_air = db.execute("select min(cardid) from card where type = 'Deploy Air Force' and location = 'hand' and control = :country order by sequence;", {'country':query_list[1]}).fetchall()
        function.discardcard(bot, deploy_air[0][0], db)
        lock_id = session.add_lock()
        space_list = function.deploy_list(query_list[1], db)
        info = air.deploy_info(bot, query_list[1], space_list, deploy_air[0][0], lock_id, session)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        session.thread_lock(lock_id)
    elif query_list[2] == 'm':
        function.discardhand(bot, query_list[1], 1, session)
        lock_id = session.add_lock()
        space_list = function.control_air_space_list(query_list[1], db)
        session.self_remove_list.append(battlebuild.self_remove(query_list[1], space_list, None, lock_id, 'air', session))
        print("self_remove_id: " + str(len(session.self_remove_list)-1))
        self_remove_id = len(session.self_remove_list)-1
        info = session.self_remove_list[self_remove_id].self_remove_info(session)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        session.thread_lock(lock_id)
        lock_id = session.add_lock()
        space_list = function.deploy_list(query_list[1], db)
        info = air.marshal_info(bot, query_list[1], space_list, None, lock_id, session)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        session.thread_lock(lock_id)
    bot.delete_message(chat_id = db.execute("select chatid from game;").fetchall()[0][0], message_id = session.message_id)
    db.execute("update country set status = 'supply' where id = :country;", {'country':query_list[1]})
    db.commit()
    session = game_session.find_session(query.message.chat_id)
    supply(bot, query_list[1], session)

    #------------------------------------------Supply Step------------------------------------------
def supply(bot, country, session):
    if session.save_session():
        print("Autosave success - supply")
    else:
        print("Autosave fail - supply")
    if session.save_session2():
        print("Autosave2 success - supply")
    else:
        print("Autosave2 fail - supply")
    db = sqlite3.connect(session.get_db_dir())
    function.updatecontrol(bot, db)
    function.updatesupply(db)
    lock_id = session.add_lock()
    status_handler.send_status_card(bot, country, 'Checking Supply', lock_id, session)   
    out_of_supply_list = db.execute("select distinct space.name from piece inner join space on space.spaceid = piece.location where piece.control = :country and piece.supply = 0;", {'country':country}).fetchall()
    db.execute("update piece set location = 'none' where control = :country and type != 'air' and supply = 0;", {'country':country})
    db.commit()
    chatid = db.execute("select chatid from game;").fetchall()
    if len(out_of_supply_list) > 0:
        text = "Piece in "
        for space in out_of_supply_list:
            text += "<b>" + space[0] + "</b> "
        text += "out of supply"
        bot.send_message(chat_id = chatid[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    air.check_reposition(bot, session)
    if country == 'uk':
        supply(bot, 'fr', session)
    if country == 'us':
        supply(bot, 'ch', session)
    if country not in ['fr', 'ch']:
            #draw map
        try:
            session.draw_map()
            bot.send_chat_action(chat_id=chatid[0][0], action=telegram.ChatAction.TYPING)
            bot.send_photo(chat_id=chatid[0][0], photo=open(session.get_dir() + '/tmp.jpg', 'rb'), timeout=1000)
        except Exception:
            pass
        db.execute("update country set status = 'victory' where id = :country;", {'country':country})
        db.commit()
        victory(bot, country, session)


    #------------------------------------------Victory Step------------------------------------------
def victory(bot, country, session):
    if session.save_session():
        print("Autosave success - victory")
    else:
        print("Autosave fail - victory")
    if session.save_session2():
        print("Autosave2 success - victory")
    else:
        print("Autosave2 fail - victory")
    db = sqlite3.connect(session.get_db_dir())
    chatid = db.execute("select chatid from game;").fetchall()
    if country not in ['fr', 'ch']:
        text = "<b>" + function.countryid2name[country] + "</b> Victory step"
        session.message_id = bot.send_message(chat_id = chatid[0][0], text = text, parse_mode=telegram.ParseMode.HTML).message_id
        lock_id = session.add_lock()
        status_handler.send_status_card(bot, country, 'Beginning of Victory step', lock_id, session)
    if db.execute("select enemy from country where id = :country", {'country':country}).fetchall() == db.execute("select distinct control from space where spaceid = (select home from country where id = :country);", {'country':country}).fetchall():
        text = "<b>" + function.countryid2name[country] + "</b> home space occupied by enemy"
    else:
        vp_space_list = function.control_vp_space_list(country, db)
        print(vp_space_list)
        control_point = len(vp_space_list[0]) * 2
        round_point = control_point
        text = function.countryid2name[country] + " gain " + str(control_point) + " point from controlling:\n"
        for space in function.get_name_list(vp_space_list[0], db):
            text += "<b>" + space[1] + "</b>\n"
        if len(vp_space_list[1]) > 0:
            shared_point = len(vp_space_list[1])
            round_point += shared_point
            text += function.countryid2name[country] + " gain " + str(shared_point) + " point from sharing control:\n"
            for space in function.get_name_list(vp_space_list[1], db):
                text += "<b>" + space[1] + "</b>\n"
        extra_point = status_handler.status_extra_victory_point(country, db)
        if extra_point != None:
            round_point += extra_point[0]
            text += extra_point[1]
        #function.add_vp(bot, country, round_point, db)
        db.execute("update country set point = point + :vp where id = :country;", {'vp':round_point, 'country':country})
    bot.send_message(chat_id = chatid[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    db.commit()
    if country == 'uk':
        victory(bot, 'fr', session)
    if country == 'us':
        victory(bot, 'ch', session)
    if country not in ['fr', 'ch']:
        side_pt = function.side_pt(db)
        game_turn = db.execute("select turn from game;").fetchall()
        text = "<b>" + function.countryid2name[country] + "</b> Turn - " + str(game_turn[0][0]) + " Axis: <b>" + str(side_pt[0]) + "</b> Allies: <b>" + str(side_pt[1]) + "</b>"
        vp_message = bot.send_message(chat_id = chatid[0][0], text = text, parse_mode=telegram.ParseMode.HTML).message_id
        bot.pin_chat_message(chat_id = chatid[0][0], message_id = vp_message, disable_notification=True)
        bot.delete_message(chat_id = chatid[0][0], message_id = session.message_id)
        db.execute("update country set status = 'discard' where id = :country;", {'country':country})
        db.commit()
        discard(bot, country, session)
    

    #------------------------------------------Discard Step------------------------------------------
def discard(bot, country, session):
    if session.save_session():
        print("Autosave success - discard")
    else:
        print("Autosave fail - discard")
    if session.save_session2():
        print("Autosave2 success - discard")
    else:
        print("Autosave2 fail - discard")
    db = sqlite3.connect(session.get_db_dir())
    group_chat_id = db.execute("select chatid from game;").fetchall()
    text = "<b>" + function.countryid2name[country] + "</b> Discard step"
    session.message_id = bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML).message_id
    lock_id = session.add_lock()
    status_handler.send_status_card(bot, country, 'Beginning of Discard step', lock_id, session)
    hand = db.execute("select name, cardid, type, text from card where location = 'hand' and control = :country order by sequence;", {'country':country}).fetchall()
    if len(hand) == 0:
        group_chat_id = db.execute("select chatid from game;").fetchall()
        text = "<b>" + function.countryid2name[country] + "</b> have no hand"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        function.deduct_vp(bot, country, 1, db)
        db.commit()
        draw(bot, country, session)
    else:
        playerid = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
        keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['discard', '{}', {}, \"draw(bot, '{}')\"]".format(country, hand[x][1], country))] for x in range(len(hand))]
        keyboard.append([InlineKeyboardButton('Pass and Loss 1 Victory Point', callback_data="['discard', '{}', 'confirm', \"draw(bot, '{}')\"]".format(country, country))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = function.countryid2name[country] + " - You may discard cards\n"
        for card in hand:
            text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
        bot.send_message(chat_id = playerid[0][0], text = text, reply_markup = reply_markup, parse_mode=telegram.ParseMode.HTML)
        db.commit()

def discard_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        discard_count = db.execute("select count(*) from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
        selected = db.execute("select cardid, sequence from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
        if discard_count[0][0] == 0:
            function.deduct_vp(bot, query_list[1], 1, db)
        else:
            db.execute("update card set location = 'discardd' where location = 'selected' and control =:country;", {'country':query_list[1]})
        bot.delete_message(chat_id = db.execute("select chatid from game;").fetchall()[0][0], message_id = session.message_id)
        db.execute("update country set status = 'draw' where id = :country;", {'country':query_list[1]})
        db.commit()
        session = game_session.find_session(query.message.chat_id)
        draw(bot, query_list[1], session)
    else:
        if query_list[2] == 'back':
            db.execute("update card set location = 'hand' where location = 'selected' and control =:country;", {'country':query_list[1]})
            hand = db.execute("select name, cardid, type, text from card where location = 'hand' and control = :country order by sequence;", {'country':query_list[1]}).fetchall()
            keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['discard', '{}', {}, \"draw(bot, '{}')\"]".format(query_list[1], hand[x][1], query_list[1]))] for x in range(len(hand))]
            keyboard.append([InlineKeyboardButton('Pass and Loss 1 Victory Point', callback_data="['discard', '{}', 'confirm', \"draw(bot, '{}')\"]".format(query_list[1], query_list[1]))])
            text = function.countryid2name[query_list[1]] + " - You may discard cards\n"
            for card in hand:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
        else:
            db.execute("update card set location = 'selected' where cardid =:id and control =:country;", {'id': query_list[2], 'country':query_list[1]})
            hand = db.execute("select name, cardid, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            selected = db.execute("select name, type, text from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            text = function.countryid2name[query_list[1]] + " - Hand:\n"
            for card in hand:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            text += "\nDiscard:\n"
            for card in selected:
                text += "<b>" + card[0] + "</b> - " + card[1] + " - " + card[2] + "\n" 
            #text += 'Hand:\n'
            #for card in hand:
                #text += str(card[0]) + '\n'
            keyboard = [[InlineKeyboardButton(hand[x][0], callback_data="['discard', '{}', {}, \"draw(bot, '{}')\"]".format(query_list[1], hand[x][1], query_list[1]))] for x in range(len(hand))]
            keyboard.append([InlineKeyboardButton('Confirm', callback_data="['discard', '{}', 'confirm', \"draw(bot, '{}')\"]".format(query_list[1], query_list[1]))])
            keyboard.append([InlineKeyboardButton('Back', callback_data="['discard', '{}', 'back', \"draw(bot, {})\"]".format(query_list[1], query_list[1]))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        db.commit()
    

    #------------------------------------------Draw Step------------------------------------------
def draw(bot, country, session):
    if session.save_session():
        print("Autosave success - draw")
    else:
        print("Autosave fail - draw")
    if session.save_session2():
        print("Autosave2 success - draw")
    else:
        print("Autosave2 fail - draw")
    db = sqlite3.connect(session.get_db_dir())
    lock_id = session.add_lock()
    status_handler.send_status_card(bot, country, 'Beginning of Draw step', lock_id, session)
    playerid = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    hand_count = db.execute("select count(*) from card where location = 'hand' and control = :country;", {'country':country}).fetchall()
    if hand_count[0][0] < 7:
        difference = 7 - hand_count[0][0]
        function.drawdeck(bot, country, difference, db)
    game_turn = db.execute("select turn from game;").fetchall()
    deck_count = db.execute("select count(*) from card where location = 'deck' and control =:country;", {'country':country}).fetchall()
    discard_count = db.execute("select count(*) from card where ((location in ('discardd', 'discardu')) or (location = 'played' and type not in ('Status', 'Response', 'Bolster')) or (location = 'used' and type in ('Response', 'Bolster'))) and control =:country;", {'country':country}).fetchall()
    response_list = db.execute("select name, text from card where location == 'played' and type == 'Response' and control =:country;", {'country':country}).fetchall()
    status_list = db.execute("select name from card where location in ('played','turn') and type == 'Status' and control =:country;", {'country':country}).fetchall()
    hand = db.execute("select name from card where location = 'hand' and control =:country order by sequence;", {'country':country}).fetchall()
    text = function.countryid2name[country] + '\n'
    text += 'Turn - ' + str(game_turn[0][0]) + '\n'
    text += 'Deck: ' + str(deck_count[0][0]) + '    Discard: ' + str(discard_count[0][0]) + '\n'
    text += 'Response in play:\n'
    for card in response_list:
        text += "<b>" + card[0] + "</b> - " + card[1] + "\n"
    text += 'Status in play:\n'
    for card in status_list:
        text += "<b>" + card[0] + "</b>\n"
    text += 'Hand:\n'
    for card in hand:
        text += "<b>" + card[0] + "</b>\n"
    bot.send_message(chat_id = playerid[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    group_chat_id = db.execute("select chatid from game;").fetchall()
    username = bot.get_chat_member(group_chat_id[0][0],playerid[0][0]).user.full_name
    text = function.countryid2name[country] + ' - <b>' + username + '</b>\n'
    text += 'Turn - ' + str(game_turn[0][0]) + '\n'
    text += 'Deck: ' + str(deck_count[0][0]) + '    Discard: ' + str(discard_count[0][0]) + '\n'
    text += 'Hand: ' + str(len(hand)) + '\n'
    text += 'Response in play:'
    for card in response_list:
        text += "&#9646"
    text += '\nStatus in play:\n'
    for card in status_list:
        text += "<b>" + card[0] + "</b>\n"
    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    db.execute("update card set location = 'played' where location = 'turn'")
    db.execute("update piece set noremove = 0 where noremove = 1")
    db.execute("update country set status = 'inactive' where id = :country;", {'country':country})
    db.execute("update country set status = 'play' where id = :next_turn;", {'next_turn':next_turn[country]})
    game_end = False
    cardfunction.c59_used = False
    cardfunction.c62_used = False
    if country == 'us':
        side_pt = function.side_pt(db)
        turn = db.execute("select turn from game;").fetchall()
        text = "Turn - " + str(turn[0][0]) + "\n"
        if (turn[0][0] == 20 and side_pt[0] >= side_pt[1]) or (side_pt[0] - side_pt[1] >= 30):
            text = "<b>Axis</b> win"
            game_end = True
        elif (turn[0][0] == 20 and side_pt[0] < side_pt[1]) or (side_pt[1] - side_pt[0] >= 30):
            text = "<b>Allies</b> win"
            game_end = True
        else:
            text = "Game carry on"
            session.turn += 1
            session.create_turn_dir()
            db.execute("update game set turn = turn + 1;")
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    db.commit()
    session.clear_lock()
    if not game_end:
        play(bot, next_turn[country], session)
    else:
        end(bot, session)


#------------------------------------------Game End------------------------------------------
def end(bot, session):
    session.set_inactive()
    session_id = session.get_session_id()
    game_session.session_list.pop(session_id)
    print('delete session-'+str(session_id))
    return
