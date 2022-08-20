import telegram
import sqlite3
import thread_lock
import status_handler
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

terrain2type = {'land':'army', 'sea':'navy'}
countryid2name = {'ge':'Germany', 'jp':'Japan', 'it':'Italy', 'uk':'United Kingdom', 'su':'Soviet Union', 'us':'United States', 'fr':'France', 'ch':'China'}
getside = {'ge':'Axis', 'jp':'Axis', 'it':'Axis', 'uk':'Allied', 'su':'Allied', 'us':'Allied', 'fr':'Allied', 'ch':'Allied'}
piece_type_name = {'army':'Army', 'navy':'Navy', 'air':'Air Force'}
player_country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us']
country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us', 'fr', 'ch']
axis_list = ['ge', 'jp', 'it']
allied_list = ['uk', 'su', 'us', 'fr', 'ch']

    #------------------------------------------Supply------------------------------------------
def updatesupply(db):
    print('update supply')
    #country_list = ['ge', 'jp', 'it', 'uk', 'su', 'us']
    axis_list = ['ge', 'jp', 'it']
    allies_list = ['uk', 'su', 'us', 'fr', 'ch']
    db.execute("update piece set supply = 0;")
    vp_space_list = db.execute("select distinct spaceid from space where supply = 1").fetchall()
    vp_space_list = [space[0] for space in vp_space_list]
    db.execute("update piece set supply = 1 where pieceid in (select piece.pieceid from piece inner join space on piece.location = space.spaceid where space.supply = 1 group by piece.pieceid);")
    #status_handler.status_supply(db)
    for country in axis_list:
        print(vp_space_list)
        country_vp_space_list = list(status_handler.status_vp_location(country, vp_space_list, db))
        print(country_vp_space_list)
        questionmarks = '?' * len(country_vp_space_list)
        db.execute("update piece set supply = 1 where control = '{}' and location in ({});".format(country, ','.join(questionmarks)), (country_vp_space_list))
        while db.execute("select count(*) from piece where supply = 0 and control = :country and location in (select distinct adjacency from space where spaceid in (select location from piece where supply = 1 and control = :country) and (straits in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or straits = 'none') and (status in (select cardid from card where location = 'used') or status = 'none')) and pieceid not in (select pieceid from piece where type = 'navy' and control = :country and location not in (select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.control in (select id from country where side = 'Axis') and piece.type = 'army' and (space.straits in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or space.straits = 'none')));", {'country':country}).fetchall()[0][0] > 0:
            db.execute("update piece set supply = 1 where supply = 0 and control = :country and location in (select distinct adjacency from space where spaceid in (select location from piece where supply = 1 and control = :country) and (straits in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or straits = 'none') and (status in (select cardid from card where location = 'used') or status = 'none')) and pieceid not in (select pieceid from piece where type = 'navy' and control = :country and location not in (select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.control in (select id from country where side = 'Axis') and piece.type = 'army' and (space.straits in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or space.straits = 'none')));", {'country':country})
    for country in allies_list:
        print(vp_space_list)
        country_vp_space_list = list(status_handler.status_vp_location(country, vp_space_list, db))
        print(country_vp_space_list)
        questionmarks = '?' * len(country_vp_space_list)
        db.execute("update piece set supply = 1 where control = '{}' and location in ({});".format(country, ','.join(questionmarks)), (country_vp_space_list))
        if country in ['uk', 'us', 'fr'] and db.execute("select location from card where cardid = 352;").fetchall()[0][0] == 'played':
            while db.execute("select count(*) from piece where supply = 0 and control = :country and location in (select distinct adjacency from space where spaceid in (select location from piece where supply = 1 and control in ('uk', 'us', 'fr')) and (straits not in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or straits = 'none') and (status not in (select cardid from card where location = 'used' and cardid = 165) or status = 'none')) and pieceid not in (select pieceid from piece where type = 'navy' and control = :country and location not in (select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.control in (select id from country where side = 'Allied') and piece.type = 'army' and (space.straits not in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or space.straits = 'none')));", {'country':country}).fetchall()[0][0] > 0:
                db.execute("update piece set supply = 1 where supply = 0 and control = :country and location in (select distinct adjacency from space where spaceid in (select location from piece where supply = 1 and control in ('uk', 'us', 'fr')) and (straits not in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or straits = 'none') and (status not in (select cardid from card where location = 'used' and cardid = 165) or status = 'none')) and pieceid not in (select pieceid from piece where type = 'navy' and control = :country and location not in (select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.control in (select id from country where side = 'Allied') and piece.type = 'army' and (space.straits not in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or space.straits = 'none')));", {'country':country})
        else:
            while db.execute("select count(*) from piece where supply = 0 and control = :country and location in (select distinct adjacency from space where spaceid in (select location from piece where supply = 1 and control = :country) and (straits not in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or straits = 'none') and (status not in (select cardid from card where location = 'used' and cardid = 165) or status = 'none')) and pieceid not in (select pieceid from piece where type = 'navy' and control = :country and location not in (select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.control in (select id from country where side = 'Allied') and piece.type = 'army' and (space.straits not in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or space.straits = 'none')));", {'country':country}).fetchall()[0][0] > 0:
                db.execute("update piece set supply = 1 where supply = 0 and control = :country and location in (select distinct adjacency from space where spaceid in (select location from piece where supply = 1 and control = :country) and (straits not in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or straits = 'none') and (status not in (select cardid from card where location = 'used' and cardid = 165) or status = 'none')) and pieceid not in (select pieceid from piece where type = 'navy' and control = :country and location not in (select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.control in (select id from country where side = 'Allied') and piece.type = 'army' and (space.straits not in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or space.straits = 'none')));", {'country':country})
    #for country in country_list:
    #    extra_space = status_handler.status_vp_location(country, db)
    #    if extra_space != None:
    #        questionmarks = '?' * len(extra_space)
    #        db.execute("update piece set supply = 1 where control = {} and location in ({});".format(','.join(questionmarks)), (country, extra_space))
    #    while db.execute("select count(*) from piece where supply = 0 and control = :country and location in (select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.supply = 1 and piece.control = :country and (space.straits in (select location from piece where control = :country) or space.straits = 'none')) and pieceid not in (select pieceid from piece where type = 'navy' and control = :country and location not in (select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.control in (select id from country where side = (select side from country where id = :country)) and piece.type = 'army' and (space.straits in (select location from piece where control = :country) or space.straits = 'none')));", {'country':country}).fetchall()[0][0] > 0:
    #        db.execute("update piece set supply = 1 where supply = 0 and control = :country and location in (select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.supply = 1 and piece.control = :country and (space.straits in (select location from piece where control = :country) or space.straits = 'none')) and pieceid not in (select pieceid from piece where type = 'navy' and control = :country and location not in (select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.control in (select id from country where side = (select side from country where id = :country)) and piece.type = 'army' and (space.straits in (select location from piece where control = :country) or space.straits = 'none')));", {'country':country})
    db.commit()

    #------------------------------------------Control------------------------------------------
def updatecontrol(bot, db):
    if db.execute("select location from card where cardid = 222;").fetchall()[0][0] == 'played' and 12 in control_side_space_list('Axis', db, space_type = 'all'):
        db.execute("update country set home = 8 where id = 'fr';")
    else:
        db.execute("update country set home = 12 where id = 'fr';")
    if db.execute("select location from card where cardid = 277;").fetchall()[0][0] == 'played':
        db.execute("update space set supply = 0 where spaceid = 28;")
        db.execute("update country set home = 30 where id = 'su';")
    else:
        db.execute("update space set supply = 1 where spaceid = 28;")
        db.execute("update country set home = 28 where id = 'su';")
    if db.execute("select location from card where cardid = 345;").fetchall()[0][0] == 'played':
        db.execute("update country set home = 35 where id = 'ch';")
    else:
        db.execute("update country set home = 37 where id = 'ch';")
    print('update control')
    db.execute("update space set control = 'neutral'")
    db.execute("update space set control = 'Axis' where spaceid in (select location from piece where control in ('ge', 'it', 'jp') and type in ('army', 'navy'));")
    db.execute("update space set control = 'Allied' where spaceid in (select location from piece where control in ('uk', 'su', 'us', 'fr', 'ch') and type in ('army', 'navy'));")
    db.commit()

    #------------------------------------------Shuffle------------------------------------------
def shuffledeck(bot, country, db):
    group_chat_id = db.execute("select chatid from game;").fetchall()
    text = "<b>" + countryid2name[country] + "</b> shuffle his deck"
    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    cardid = db.execute("select cardid from card where location = 'deck' and control = :country;", {'country':country}).fetchall()
    ransq = [x for x in range(1, len(cardid)+1)]
    random.shuffle(ransq)
    for i in range (len(cardid)):
        db.execute('update card set sequence =:sq where cardid =:id and control =:country;', {'sq': ransq[i], 'id': cardid[i][0], 'country':country})

def shufflediscard(bot, country, db):
    group_chat_id = db.execute("select chatid from game;").fetchall()
    text = "<b>" + countryid2name[country] + "</b> shuffle his deck"
    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    discard = db.execute("select cardid from card where ((location in ('discardd', 'discardu')) or (location = 'played' and type not in ('Status', 'Response', 'Bolster')) or (location = 'used' and type in ('Response', 'Bolster'))) and control =:country;", {'country':country}).fetchall()
    ransq = [x for x in range(1, len(discard)+1)]
    random.shuffle(ransq)
    for i in range (len(discard)):
        db.execute('update card set sequence =:sq where cardid =:id and control =:country;', {'sq': ransq[i], 'id': discard[i][0], 'country':country})

    #------------------------------------------Draw------------------------------------------
def reorderdeck(bot, country, db):
    cardid = db.execute("select cardid from card where location = 'deck' and control = :country order by sequence;", {'country':country}).fetchall()
    for i in range (len(cardid)):
        db.execute('update card set sequence =:sq where cardid =:id and control =:country;', {'sq': i + 1, 'id': cardid[i][0], 'country':country})


def drawdeck(bot, country, number, db):
    reorderdeck(bot, country, db)
    group_chat_id = db.execute("select chatid from game;").fetchall()
    cardcount = db.execute("select count(*) from card where location = 'deck' and control =:country;", {'country':country}).fetchall()
    if number > cardcount[0][0]:
        db.execute("update card set location = 'hand' where location = 'deck' and control =:country;", {'country':country})
        text = "<b>" + countryid2name[country] + "</b> finished his deck"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        number = cardcount[0][0]
    else:
        db.execute("update card set location = 'hand' where location = 'deck' and sequence <= :number and control =:country;", {'number':number, 'country':country})
        for j in range (1, cardcount[0][0] - number + 1):
            db.execute("update card set sequence =:new where sequence =:old and location = 'deck' and control =:country;", {'new': j, 'old': j + number, 'country':country})
    text = "<b>" + countryid2name[country] + "</b> draw " + str(number) + " card(s) from his deck"
    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    db.commit()

    #------------------------------------------Move Card------------------------------------------
def movecardbottom(bot, cardid, db):
    group_chat_id = db.execute("select chatid from game;").fetchall()
    card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':cardid}).fetchall()
    text = "<b>" + card_name[0][0] + "</b> move to bottom of deck"
    #bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    db.execute("update card set location = 'deck', sequence = (select max(sequence) from card where control = (select control from card where cardid = :cardid) and location = 'deck') + 1 where cardid = :cardid;", {'cardid':cardid})
    db.commit()

def movecardtop(bot, cardid, db):
    group_chat_id = db.execute("select chatid from game;").fetchall()
    card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':cardid}).fetchall()
    text = "<b>" + card_name[0][0] + "</b> move to top of deck"
    #bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    cardcount = db.execute("select count(*) from card where location = 'deck' and control = (select control from card where cardid = :cardid);", {'cardid':cardid}).fetchall()
    for j in reversed(range(1, cardcount[0][0] + 1)):
        db.execute("update card set sequence =:new where sequence =:old and location = 'deck' and control = (select control from card where cardid = :cardid);", {'new': j + 1, 'old': j, 'cardid':cardid})
    db.execute("update card set location = 'deck', sequence = 1 where cardid = :cardid;", {'cardid':cardid})
    db.commit()

def movecardhand(bot, cardid, db):
    #chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':cardid}).fetchall()
    text = "<b>" + card_name[0][0] + "</b> move to your hand"
    #bot.send_message(chat_id = chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    db.execute("update card set location = 'hand', sequence = (select max(sequence) from card where control = (select control from card where cardid = :cardid) and location = 'hand') + 1 where cardid = :cardid;", {'cardid':cardid})
    db.commit()
    
    #------------------------------------------Discard Hand------------------------------------------
def discardhand(bot, country, number, session):
    db = sqlite3.connect(session.get_db_dir())
    hand_list = db.execute("select cardid, name, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':country}).fetchall()
    group_chat_id = db.execute("select chatid from game;").fetchall()
    if len(hand_list) <= number:
        if len(hand_list) != 0:
            db.execute("update card set location = 'discardd' where location = 'hand' and control =:country;", {'country':country})
            db.commit()
        text = "<b>" + countryid2name[country] + "</b> finished his hand"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        if len(hand_list) < number:
            short = number - len(hand_list)
            discarddeck_no_hand(bot, country, short, db)
    else:
        text = "<b>" + countryid2name[country] + "</b> discarded " + str(number) + " card(s) from his hand"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        lock_id = session.add_lock()
        chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
        keyboard = [[InlineKeyboardButton(hand[1], callback_data="['dh', '{}', {}, {}, {}]".format(country, hand[0], number, lock_id))]for hand in hand_list]
        text = "Discard " + str(number) + " card(s):\n\n"
        for card in hand_list:
                text += "<b>" + card[1] + "</b> - " + card[2] + " - " + card[3] + "\n"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup, parse_mode=telegram.ParseMode.HTML)
        session.thread_lock(lock_id)
    
def discardhand_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        selected = db.execute("select name, sequence from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
        db.execute("update card set location = 'discardd' where location = 'selected' and control =:country;", {'country':query_list[1]})
        text = 'Discarded:\n'
        for card in selected:
            text += str(card[0]) + '\n'
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        session.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            db.execute("update card set location = 'hand' where location = 'selected' and control =:country;", {'country':query_list[1]})
            hand_list = db.execute("select name, cardid, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            text = "Discard " + str(query_list[3]) + " card(s):\n\n"
            for card in hand_list:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            keyboard = [[InlineKeyboardButton(hand[0], callback_data="['dh', '{}', {}, {}, {}]".format(query_list[1], hand[1], query_list[3], query_list[4]))]for hand in hand_list]
        else:
            db.execute("update card set location = 'selected' where cardid =:id and control =:country;", {'id': query_list[2], 'country':query_list[1]})
            hand_list = db.execute("select name, cardid, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            selected = db.execute("select name, cardid, type, text from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            text = 'Hand:\n'
            for card in hand_list:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            text += '\nDiscarded:\n'
            for card in selected:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            if len(selected) < query_list[3]:
                keyboard = [[InlineKeyboardButton(hand[0], callback_data="['dh', '{}', {}, {}, {}]".format(query_list[1], hand[1], query_list[3], query_list[4]))]for hand in hand_list]        
            else:
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['dh', '{}', 'confirm', {}]".format(query_list[1], query_list[4]))],
                            [InlineKeyboardButton('Back', callback_data="['dh', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[4]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        db.close()

def discardhand_no_deck(bot, country, number, session):
    db = sqlite3.connect(session.get_db_dir())
    hand_list = db.execute("select cardid, name, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':country}).fetchall()
    group_chat_id = db.execute("select chatid from game;").fetchall()
    if len(hand_list) <= number:
        if len(hand_list) != 0:
            db.execute("update card set location = 'discardd' where location = 'hand' and control =:country;", {'country':country})
            db.commit()
        text = "<b>" + countryid2name[country] + "</b> finished his hand"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        if len(hand_list) < number:
            short = number - len(hand_list)
            deduct_vp(bot, country, short, db)
    else:
        text = "<b>" + countryid2name[country] + "</b> discarded " + str(number) + " card(s) from his hand"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        lock_id = session.add_lock()
        chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
        keyboard = [[InlineKeyboardButton(hand[1], callback_data="['dh_nd', '{}', {}, {}, {}]".format(country, hand[0], number, lock_id))]for hand in hand_list]
        text = "Discard " + str(number) + " card(s):\n\n"
        for card in hand_list:
                text += "<b>" + card[1] + "</b> - " + card[2] + " - " + card[3] + "\n"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup, parse_mode=telegram.ParseMode.HTML)
        session.thread_lock(lock_id)
    
def discardhand_no_deck_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        selected = db.execute("select name, sequence from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
        db.execute("update card set location = 'discardd' where location = 'selected' and control =:country;", {'country':query_list[1]})
        text = 'Discarded:\n'
        for card in selected:
            text += str(card[0]) + '\n'
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        session.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            db.execute("update card set location = 'hand' where location = 'selected' and control =:country;", {'country':query_list[1]})
            hand_list = db.execute("select name, cardid, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            text = "Discard " + str(query_list[3]) + " card(s):\n\n"
            for card in hand_list:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            keyboard = [[InlineKeyboardButton(hand[0], callback_data="['dh_nd', '{}', {}, {}, {}]".format(query_list[1], hand[1], query_list[3], query_list[4]))]for hand in hand_list]
        else:
            db.execute("update card set location = 'selected' where cardid =:id and control =:country;", {'id': query_list[2], 'country':query_list[1]})
            hand_list = db.execute("select name, cardid, type, text from card where location = 'hand' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            selected = db.execute("select name, cardid, type, text from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            text = 'Hand:\n'
            for card in hand_list:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            text += '\nDiscarded:\n'
            for card in selected:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            if len(selected) < query_list[3]:
                keyboard = [[InlineKeyboardButton(hand[0], callback_data="['dh_nd', '{}', {}, {}, {}]".format(query_list[1], hand[1], query_list[3], query_list[4]))]for hand in hand_list]        
            else:
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['dh_nd', '{}', 'confirm', {}]".format(query_list[1], query_list[4]))],
                            [InlineKeyboardButton('Back', callback_data="['dh_nd', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[4]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        db.close()

    #------------------------------------------Discard Response------------------------------------------
def discardresponse(bot, country, number, session):
    db = sqlite3.connect(session.get_db_dir())
    response_list = db.execute("select cardid, name, type, text from card where location = 'hand' and type = 'Response' and control =:country order by sequence;", {'country':country}).fetchall()
    group_chat_id = db.execute("select chatid from game;").fetchall()
    if len(response_list) != 0:
        text = "<b>" + countryid2name[country] + "</b> discarded " + str(number) + " Response card(s) from his hand"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        lock_id = session.add_lock()
        chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
        keyboard = [[InlineKeyboardButton(response[1], callback_data="['dr', '{}', {}, {}, {}]".format(country, response[0], number, lock_id))]for response in response_list]
        text = "Discard " + str(number) + " Response card(s):\n\n"
        for card in response_list:
                text += "<b>" + card[1] + "</b> - " + card[2] + " - " + card[3] + "\n"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup, parse_mode=telegram.ParseMode.HTML)
        session.thread_lock(lock_id)
    
def discardresponse_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        selected = db.execute("select name, sequence from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
        db.execute("update card set location = 'discardd' where location = 'selected' and control =:country;", {'country':query_list[1]})
        text = 'Discarded:\n'
        for card in selected:
            text += str(card[0]) + '\n'
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        session.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            db.execute("update card set location = 'hand' where location = 'selected' and control =:country;", {'country':query_list[1]})
            response_list = db.execute("select name, cardid, type, text from card where location = 'hand' and type = 'Response' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            text = "Discard " + query_list[3] + " Response card(s):\n\n"
            for card in response_list:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            keyboard = [[InlineKeyboardButton(response[0], callback_data="['dr', '{}', {}, {}, {}]".format(query_list[1], response[1], query_list[3], query_list[4]))]for response in response_list]
        else:
            db.execute("update card set location = 'selected' where cardid =:id and control =:country;", {'id': query_list[2], 'country':query_list[1]})
            response_list = db.execute("select name, cardid, type, text from card where location = 'hand' and type = 'Response' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            selected = db.execute("select name, cardid, type, text from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            text = 'Hand:\n'
            for card in response_list:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            text += '\nDiscarded:\n'
            for card in selected:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            if len(selected) < query_list[3]:
                keyboard = [[InlineKeyboardButton(response[0], callback_data="['dr', '{}', {}, {}, {}]".format(query_list[1], response[1], query_list[3], query_list[4]))]for response in response_list]        
            else:
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['dr', '{}', 'confirm', {}]".format(query_list[1], query_list[4]))],
                            [InlineKeyboardButton('Back', callback_data="['dr', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[4]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        db.close()

    #------------------------------------------Discard EW------------------------------------------
def discardew(bot, country, number, session):
    db = sqlite3.connect(session.get_db_dir())
    response_list = db.execute("select cardid, name, type, text from card where location = 'hand' and type = 'Economic Warfare' and control =:country order by sequence;", {'country':country}).fetchall()
    group_chat_id = db.execute("select chatid from game;").fetchall()
    if len(response_list) != 0:
        text = "<b>" + countryid2name[country] + "</b> discarded " + str(number) + " Economic Warfare card(s) from his hand"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        lock_id = session.add_lock()
        chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
        keyboard = [[InlineKeyboardButton(response[1], callback_data="['dec', '{}', {}, {}, {}]".format(country, response[0], number, lock_id))]for response in response_list]
        text = "Discard " + str(number) + " Economic Warfare card(s):\n\n"
        for card in response_list:
                text += "<b>" + card[1] + "</b> - " + card[2] + " - " + card[3] + "\n"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id = chat_id[0][0], text = text, reply_markup = reply_markup, parse_mode=telegram.ParseMode.HTML)
        session.thread_lock(lock_id)
    
def discardew_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        selected = db.execute("select name, sequence from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
        db.execute("update card set location = 'discardd' where location = 'selected' and control =:country;", {'country':query_list[1]})
        text = 'Discarded:\n'
        for card in selected:
            text += str(card[0]) + '\n'
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        session.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            db.execute("update card set location = 'hand' where location = 'selected' and control =:country;", {'country':query_list[1]})
            response_list = db.execute("select name, cardid, type, text from card where location = 'hand' and type = 'Economic Warfare' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            text = "Discard " + query_list[3] + " Economic Warfare card(s):\n\n"
            for card in response_list:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            keyboard = [[InlineKeyboardButton(response[0], callback_data="['dec', '{}', {}, {}, {}]".format(query_list[1], response[1], query_list[3], query_list[4]))]for response in response_list]
        else:
            db.execute("update card set location = 'selected' where cardid =:id and control =:country;", {'id': query_list[2], 'country':query_list[1]})
            response_list = db.execute("select name, cardid, type, text from card where location = 'hand' and type = 'Economic Warfare' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            selected = db.execute("select name, cardid, type, text from card where location = 'selected' and control =:country order by sequence;", {'country':query_list[1]}).fetchall()
            text = 'Hand:\n'
            for card in response_list:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            text += '\nDiscarded:\n'
            for card in selected:
                text += "<b>" + card[0] + "</b> - " + card[2] + " - " + card[3] + "\n"
            if len(selected) < query_list[3]:
                keyboard = [[InlineKeyboardButton(response[0], callback_data="['dec', '{}', {}, {}, {}]".format(query_list[1], response[1], query_list[3], query_list[4]))]for response in response_list]        
            else:
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['dec', '{}', 'confirm', {}]".format(query_list[1], query_list[4]))],
                            [InlineKeyboardButton('Back', callback_data="['dec', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[4]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        db.commit()
        db.close()
        
    #------------------------------------------Discard------------------------------------------
def ewdiscard(bot, cardid, active_country, passive_country, number, session):    #ew discard that call respone
    db = sqlite3.connect(session.get_db_dir())
    group_chat_id = db.execute("select chatid from game;").fetchall()
    lock_id = session.add_lock()
    status_handler.send_status_card(bot, active_country, 'Economic Warfare', lock_id, session, passive_country_id = passive_country, card_id = cardid) 
    extra_number = status_handler.status_ew_handler(bot, cardid, active_country, passive_country, session) 
    number += extra_number
    if number > 0:
        import cardfunction
        card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':cardid}).fetchall()
        if cardfunction.c171_used or cardfunction.c179_used:
            cardfunction.c171_used = False
            cardfunction.c179_used = False
            text = "<b>" + card_name[0][0] + "</b> ignored"
            bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        else:
            text = "<b>" + countryid2name[passive_country]  + "</b> is attacked by " + card_name[0][0]
            bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
            discarddeck(bot, passive_country, number, session)
        
def discarddeck(bot, country, number, session):
    db = sqlite3.connect(session.get_db_dir())
    cardcount = db.execute("select count(*) from card where location = 'deck' and control =:country;", {'country':country}).fetchall()
    group_chat_id = db.execute("select chatid from game;").fetchall()
    text = "<b>" + countryid2name[country] + "</b> discarded " + str(number) + " card(s) from his deck"
    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    if number > cardcount[0][0]:
        db.execute("update card set location = 'discardd' where location = 'deck' and control =:country;", {'number':number, 'country':country})
        db.commit()
        text = "<b>" + countryid2name[country] + "</b> finished his deck"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        short = number - cardcount[0][0]
        discardhand_no_deck(bot, country, short, session)
    else:
        db.execute("update card set location = 'discardd' where location = 'deck' and sequence <= :number and control =:country;", {'number':number, 'country':country})
        for j in range (1, cardcount[0][0] - number + 1):
            db.execute("update card set sequence =:new where sequence =:old and location = 'deck' and control =:country;", {'new': j, 'old': j + number, 'country':country})
    db.commit()

def discarddeck_no_hand(bot, country, number, db):
    cardcount = db.execute("select count(*) from card where location = 'deck' and control =:country;", {'country':country}).fetchall()
    group_chat_id = db.execute("select chatid from game;").fetchall()
    text = "<b>" + countryid2name[country] + "</b> discarded " + str(number) + " card(s) from his deck"
    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    if number > cardcount[0][0]:
        db.execute("update card set location = 'discardd' where location = 'deck' and control =:country;", {'number':number, 'country':country})
        db.commit()
        text = "<b>" + countryid2name[country] + "</b> finished his deck"
        bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
        short = number - cardcount[0][0]
        deduct_vp(bot, country, short, db)
    else:
        db.execute("update card set location = 'discardd' where location = 'deck' and sequence <= :number and control =:country;", {'number':number, 'country':country})
        for j in range (1, cardcount[0][0] - number + 1):
            db.execute("update card set sequence =:new where sequence =:old and location = 'deck' and control =:country;", {'new': j, 'old': j + number, 'country':country})
    db.commit()

def discardcard(bot, cardid, db):
    group_chat_id = db.execute("select chatid from game;").fetchall()
    card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':cardid}).fetchall()
    text = "<b>" + card_name[0][0] + "</b> discarded"
    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    db.execute("update card set location = 'discardu' where cardid = :cardid;", {'cardid':cardid})
    db.commit()

def facedowndiscardcard(bot, cardid, db):
    group_chat_id = db.execute("select chatid from game;").fetchall()
    card_control = db.execute("select control, type from card where cardid = :cardid;", {'cardid':cardid}).fetchall()
    text = "<b>" + countryid2name[card_control[0][0]] + "</b> " + card_control[0][1] + " discarded"
    card_name = db.execute("select name from card where cardid = :cardid;", {'cardid':cardid}).fetchall()
    db.execute("update card set location = 'discardd' where cardid = :cardid;", {'cardid':cardid})
    db.commit()
    
    #------------------------------------------Add/Deduct vp------------------------------------------
def add_vp(bot, country, vp, db):
    group_chat_id = db.execute("select chatid from game;").fetchall()
    text = "<b>" + countryid2name[country] + "</b> gain " + str(vp) + " point"
    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    db.execute("update country set point = point + :vp where id = :country;", {'vp':vp, 'country':country})
    db.commit()

def deduct_vp(bot, country, vp, db):
    group_chat_id = db.execute("select chatid from game;").fetchall()
    text = "<b>" + countryid2name[country] + "</b> lose " + str(vp) + " point"
    bot.send_message(chat_id = group_chat_id[0][0], text = text, parse_mode=telegram.ParseMode.HTML)
    db.execute("update country set point = point - :vp where id = :country;", {'vp':vp, 'country':country})
    db.commit()
    #------------------------------------------Can Build------------------------------------------
def can_build(country, space, db):
    space_list = within(getside[country], control_supplied_space_list(country, db), 1, db)
    xspace = db.execute("select distinct location from piece where control in (select id from country where id = :country or side = (select enemy from country where id = :country)) and location != 'none' and type != 'air';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    return (space not in xspace_list and space in space_list)

def build_list(country, db, space_type = 'all'): 
    axis_list = ['ge', 'jp', 'it']
    allies_list = ['uk', 'su', 'us']
    space_list = within(getside[country], control_supplied_space_list(country, db), 1, db)
    home_country = db.execute("select home from country where id = :country;", {'country':country}).fetchall()
    space_list.append(home_country[0][0])
    extra_list = status_handler.status_build_location(country, db)
    if extra_list != None:
        space_list += extra_list
    xspace = db.execute("select distinct location from piece where control in (select id from country where id = :country or side = (select enemy from country where id = :country)) and location != 'none' and type != 'air';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    space_list = list(set(space_list) - set(xspace_list))
    space_list2 =[]
    questionmarks = '?' * len(space_list)
    if space_type != 'sea':
        space = db.execute("select distinct spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list2 += [s[0] for s in space]
    if space_type != 'land':
        space = db.execute("select distinct spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
        if country in axis_list:
            supply_space = db.execute("select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.control in (select id from country where side = 'Axis') and piece.type = 'army' and (space.straits in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or space.straits = 'none');").fetchall()
        else:
            supply_space = db.execute("select distinct space.adjacency from piece inner join space on piece.location = space.spaceid where piece.control in (select id from country where side = 'Allied') and piece.type = 'army' and (space.straits not in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or space.straits = 'none');").fetchall()
        supply_space_list = [s[0] for s in supply_space]
        space_list2 += list(set(space_list) & set(supply_space_list))
    return space_list2



    #------------------------------------------Can Recuit------------------------------------------
def can_recuit(country, space, db):
    xspace = db.execute("select distinct location from piece where control in (select id from country where id = :country or side = (select enemy from country where id = :country)) and location != 'none' and type != 'air';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    return space not in xspace_list

def recuit_list(country, db, space_type = 'all'):
    space =  db.execute("select distinct spaceid from space;").fetchall()
    space_list = [s[0] for s in space]
    xspace = db.execute("select distinct location from piece where control in (select id from country where id = :country or side = (select enemy from country where id = :country)) and location != 'none' and type != 'air';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    space_list = list(set(space_list) - set(xspace_list))
    questionmarks = '?' * len(space_list)
    if space_type == 'land':
        space = db.execute("select distinct spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    if space_type == 'sea':
        space = db.execute("select distinct spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    return space_list

    #------------------------------------------Can Battle------------------------------------------
def can_battle(country, space, db):
    space_list = within(getside[country], control_supplied_space_list(country, db), 1, db)
    xspace = db.execute("select distinct location from piece where control in (select id from country where side = (select side from country where id = :country)) and location != 'none' and type != 'air';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    return (space not in xspace_list and space in space_list)

def battle_list(country, db, space_type = 'all'):
    space_list = within(getside[country], control_supplied_space_list(country, db), 1, db)
    extra_list = status_handler.status_battle_location(country, db)
    if extra_list != None:
        space_list += extra_list
    xspace = db.execute("select distinct location from piece where control in (select id from country where side = (select side from country where id = :country)) and location != 'none' and type != 'air';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    space_list = list(set(space_list) - set(xspace_list))
    questionmarks = '?' * len(space_list)
    if space_type == 'land':
        space = db.execute("select distinct spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    if space_type == 'sea':
        space = db.execute("select distinct spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    return space_list

    #------------------------------------------Can Remove------------------------------------------
def can_remove(country, space, db):
    xspace = db.execute("select distinct location from piece where control in (select id from country where side = (select side from country where id = :country)) and location != 'none' and type != 'air';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    return space not in xspace_list

def remove_list(country, db, space_type = 'all'):
    space = db.execute("select distinct location from piece where control in (select id from country where side = (select enemy from country where id = :country)) and location != 'none' and type != 'air';", {'country':country}).fetchall()
    space_list = [eval(s[0]) for s in space]
    questionmarks = '?' * len(space_list)
    if space_type == 'land':
        space = db.execute("select distinct spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    if space_type == 'sea':
        space = db.execute("select distinct spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    return space_list

    #------------------------------------------Can Deploy------------------------------------------
def deploy_list(country, db, space_type = 'all'):
    space_list = control_supplied_space_list(country, db, space_type = space_type)
    xspace_list = control_air_space_list(country, db, space_type = space_type)
    space_list = list(set(space_list) - set(xspace_list))
    return space_list

    #------------------------------------------Is in------------------------------------------
def isin_list(country, space_list, db):
    #space_list = array
    questionmarks = '?' * len(space_list)
    count = db.execute("select count(*) from piece where control = ? and location in ({});".format(','.join(questionmarks)), (country, space_list)).fetchall()
    #if count[0][0] == 0:
    #    return False
    #else:
    #    return True
    return count[0][0] != 0

def isin(country, space, db):
    count = db.execute("select count(*) from piece where control = :country and location = :location", {'country':country, 'location':space}).fetchall()
    #if count[0][0] == 0:
    #    return False
    #else:
    #    return True
    return count[0][0] != 0
    
    #------------------------------------------Within------------------------------------------
def within(side, space_list, number, db):
    #space_list = array
    for i in range(number):
        questionmarks = '?' * len(space_list)
        if side == 'Allied':
            adjacency = db.execute("select spaceid from space where adjacency in ({}) and (straits not in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or straits = 'none') and (status not in (select cardid from card where location = 'used') or status = 'none');".format(','.join(questionmarks)), (space_list)).fetchall()
        else:
            adjacency = db.execute("select spaceid from space where adjacency in ({}) and (straits in (select location from piece where control in (select id from country where side = 'Axis') and location != 'none') or straits = 'none') and (status in (select cardid from card where location = 'used') or status in ('none', '165'));".format(','.join(questionmarks)), (space_list)).fetchall()
        for j in adjacency:
            space_list.append(j[0])
    space_list = list(set(space_list))
    return space_list

    #------------------------------------------Control list------------------------------------------
def control_space_list(country, db, space_type = 'all'):
    if space_type == 'land':
        control = db.execute("select distinct location from piece where location != 'none' and type = 'army' and control = :country;", {'country':country}).fetchall()
    elif space_type == 'sea':
        control = db.execute("select distinct location from piece where location != 'none' and type = 'navy' and control = :country;", {'country':country}).fetchall()
    else:
        control = db.execute("select distinct location from piece where location != 'none' and control = :country;", {'country':country}).fetchall()
    control_list = [eval(space[0]) for space in control]
    return control_list

def control_side_space_list(side, db, space_type = 'all'):
    if space_type == 'land':
        control = db.execute("select distinct location from piece where location != 'none' and type = 'army' and control in (select id from country where side = :side);", {'side':side}).fetchall()
    elif space_type == 'sea':
        control = db.execute("select distinct location from piece where location != 'none' and type = 'navy' and control in (select id from country where side = :side);", {'side':side}).fetchall()
    else:
        control = db.execute("select distinct location from piece where location != 'none' and in (select id from country where side = :side);", {'side':side}).fetchall()
    control_list = [eval(space[0]) for space in control]
    return control_list

def control_air_space_list(country, db, space_type = 'all'):
    control = db.execute("select distinct location from piece where location != 'none' and type = 'air' and control = :country;", {'country':country}).fetchall()
    control_list = [eval(space[0]) for space in control]
    questionmarks = '?' * len(control_list)
    if space_type == 'land':
        space = db.execute("select distinct spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (control_list)).fetchall()
        space_list = [s[0] for s in space]
    elif space_type == 'sea':
        space = db.execute("select distinct spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (control_list)).fetchall()
        space_list = [s[0] for s in space]
    else:
        space_list = control_list
    return space_list

def control_side_air_space_list(side, db, space_type = 'all'):
    control = db.execute("select distinct location from piece where control in (select id from country where side = :side) and type = 'air' and location != 'none';", {'side':side}).fetchall()
    control_list = [eval(space[0]) for space in control]
    questionmarks = '?' * len(control_list)
    if space_type == 'land':
        space = db.execute("select distinct spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (control_list)).fetchall()
        space_list = [s[0] for s in space]
    elif space_type == 'sea':
        space = db.execute("select distinct spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (control_list)).fetchall()
        space_list = [s[0] for s in space]
    else:
        space_list = control_list
    return space_list

def control_supplied_space_list(country, db, space_type = 'all'):
    updatesupply(db)
    if space_type == 'land':
        control = db.execute("select location from piece where supply = 1 and location != 'none' and type = 'army' and control = :country;", {'country':country}).fetchall()
    elif space_type == 'sea':
        control = db.execute("select location from piece where supply = 1 and location != 'none' and type = 'navy' and control = :country;", {'country':country}).fetchall()
    else:
        control = db.execute("select location from piece where supply = 1 and location != 'none' and type != 'air' and control = :country;", {'country':country}).fetchall()
    control_list = [eval(space[0]) for space in control]
    print('---control_supplied_space_list---')
    print(control_list)
    return control_list

def control_vp_space_list(country, db):
    db.execute("update piece set location = 'none' where pieceid = 0;")
    db.commit()
    vp_space = db.execute("select distinct spaceid from space where supply = 1;").fetchall()
    vp_space_list = [space[0] for space in vp_space]
    vp_space_list = status_handler.status_vp_location(country, vp_space_list, db)
    shared = shared_vp_space_list(country, vp_space_list, db)
    if shared != None:
        vp_space_list = list(set(vp_space_list) - set(shared))
    control = db.execute("select location from piece where location != 'none' and control = :country;", {'country':country}).fetchall()
    control_list = [eval(space[0]) for space in control]
    control_vp_list = list(set(control_list) & set(vp_space_list))
    if shared != None:
        control_shared_vp_list = list(set(control_list) & set(shared))
        return control_vp_list, control_shared_vp_list
    else:
        return control_vp_list, 'none'

def shared_vp_space_list(country, vp_space_list, db):
    questionmarks = '?' * len(vp_space_list)
    shared_vp_space = db.execute("select location from (select location , count(location) as c from piece where location in ({}) and type != 'air' group by location) where c > 1;".format(','.join(questionmarks)), (vp_space_list)).fetchall()
    shared_vp_space_list = [eval(space[0]) for space in shared_vp_space]
    return shared_vp_space_list

    #------------------------------------------Filter list------------------------------------------
def filter_space_list(space_list, db, control = 'all', space_type = 'all'):
    questionmarks = '?' * len(space_list)
    if space_type == 'land':
        space = db.execute("select spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    if space_type == 'sea':
        space = db.execute("select spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    questionmarks = '?' * len(space_list)
    if control == 'Axis':
        space = db.execute("select spaceid from space where spaceid in (select location from piece where control in ('ge', 'jp', 'it') and location != 'none') and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    if control == 'Allied':
        space = db.execute("select spaceid from space where spaceid in (select location from piece where control in ('uk', 'su', 'us') and location != 'none') and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    if control == 'neutral':
        space = db.execute("select spaceid from space where spaceid not in (select location from piece where control in ('ge', 'jp', 'it', 'uk', 'su', 'us') and location != 'none') and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    space_list = list(set(space_list))
    return space_list

def filter_build_list(space_list, country, db, space_type = 'all'):
    questionmarks = '?' * len(space_list)
    if space_type == 'land':
        space = db.execute("select distinct spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    if space_type == 'sea':
        space = db.execute("select distinct spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    xspace = db.execute("select distinct location from piece where control in (select id from country where id = :country or side = (select enemy from country where id = :country)) and location != 'none';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    space_list =  [space for space in space_list if space not in xspace_list]
    space_list2 = within(getside[country], control_supplied_space_list(country, db), 1, db)
    space_list = list(set(space_list) & set(space_list2))
    return space_list

def filter_recuit_list(space_list, country, db, space_type = 'all'):
    questionmarks = '?' * len(space_list)
    if space_type == 'land':
        space = db.execute("select distinct spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    if space_type == 'sea':
        space = db.execute("select distinct spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    xspace = db.execute("select distinct location from piece where control in (select id from country where id = :country or side = (select enemy from country where id = :country)) and location != 'none';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    space_list =  [space for space in space_list if space not in xspace_list]
    space_list = list(set(space_list))
    return space_list

def filter_battle_list(space_list, country, db, space_type = 'all'):
    questionmarks = '?' * len(space_list)
    if space_type == 'land':
        space = db.execute("select distinct spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    if space_type == 'sea':
        space = db.execute("select distinct spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    #xspace = db.execute("select distinct spaceid from space where control in (select side from country where id = :country);", {'country':country}).fetchall()
    xspace = db.execute("select distinct location from piece where control in (select id from country where side = (select side from country where id = :country)) and location != 'none';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    space_list =  [space for space in space_list if space not in xspace_list]
    space_list2 = within(getside[country], control_supplied_space_list(country, db), 1, db)
    space_list = list(set(space_list) & set(space_list2))
    return space_list

def filter_remove_list(space_list, country, db, space_type = 'all'):
    questionmarks = '?' * len(space_list)
    if space_type == 'land':
        space = db.execute("select distinct spaceid from space where type = 'land' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    if space_type == 'sea':
        space = db.execute("select distinct spaceid from space where type = 'sea' and spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
        space_list = [s[0] for s in space]
    #xspace = db.execute("select distinct spaceid from space where control in (select side from country where id = :country);", {'country':country}).fetchall()
    xspace = db.execute("select distinct location from piece where control in (select id from country where side = (select side from country where id = :country)) and location != 'none';", {'country':country}).fetchall()
    xspace_list = [eval(s[0]) for s in xspace]
    space_list =  [space for space in space_list if space not in xspace_list]
    space_list = list(set(space_list))
    return space_list

    #------------------------------------------Get name list------------------------------------------
def get_name_list(space_list, db):
    questionmarks = '?' * len(space_list)
    name_list = db.execute("select distinct spaceid, name from space where spaceid in ({});".format(','.join(questionmarks)), (space_list)).fetchall()
    return name_list

    
    #------------------------------------------Side VP------------------------------------------
def side_pt(db):
    db.execute("update game set axispt = (select sum(point) from country where id in ('ge', 'it', 'jp'));")
    db.execute("update game set alliespt = (select sum(point) from country where id in ('uk', 'su', 'us', 'fr', 'ch'));")
    axispt = db.execute("select axispt from game;").fetchall()
    alliespt = db.execute("select alliespt from game;").fetchall()
    return axispt[0][0], alliespt[0][0]

def update_allies_pt(db):
    db.execute("update game set alliespt = (select sum(point) from country where id in ('uk', 'su', 'us', 'fr', 'ch'));")
    alliespt = db.execute("select alliespt from game;")
    return alliespt[0][0]

    #------------------------------------------Supplied list------------------------------------------
def supplied_space_list(country, db, space_type = 'all'):
    supplied_space_list = list(set(control_supplied_space_list(country, db, space_type = space_type)).union(set(build_list(country, db, space_type = space_type))))
    print('---supplied_space_list---')
    print(supplied_space_list)
    return supplied_space_list



    
