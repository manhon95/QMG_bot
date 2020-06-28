import telegram
import sqlite3
import function
import battlebuild
import thread_lock
import status_handler


from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

    #------------------Deploy----------------------
def deploy_info(bot, country, space_list, card_id, lock_id, session):
    print('deploy_info')
    print(space_list) 
    db = sqlite3.connect(session.get_db_dir())
    name_list = function.get_name_list(space_list, db)
    print(name_list)
    session.space_list_buffer = space_list
    chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    text = "Choose a space to Deploy"
    keyboard = [[InlineKeyboardButton(space[1], callback_data="['deploy', '{}', {}, {}, {}]".format(country, space[0], card_id, lock_id))] for space in name_list]
    keyboard.append([InlineKeyboardButton('Pass', callback_data="['deploy', '{}', 'pass', {}, {}]".format(country, card_id, lock_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return chat_id[0][0], text, reply_markup


def deploy_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        deploy(bot, query_list[1], query_list[3], query_list[4], session)
        session.release_lock(query_list[-1])
    elif query_list[2] == 'pass':
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text='Passed')
        session.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            info = deploy_info(bot, query_list[1] , session.space_list_buffer, query_list[3], query_list[4], session)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[2]}).fetchall()
            text = 'Deploy in ' + location[0][0] + ':'
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['deploy', '{}', 'confirm', {}, {}, {}]".format(query_list[1], query_list[2], query_list[3], query_list[4]))]
                        , [InlineKeyboardButton('Back', callback_data="['deploy', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[4]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)
        db.commit()

def deploy(bot, active_country, space, card_id, session):
    db = sqlite3.connect(session.get_db_dir())
    space_info = db.execute("select distinct name, type from space where spaceid = :space;", {'space':space}).fetchall()
    active_country_name = db.execute("select name from country where id = :country;", {'country':active_country}).fetchall()
    group_chat = db.execute("select chatid from game;").fetchall()
    if over_deploy_handler(bot, active_country, session):
        text = active_country_name[0][0] + " do not remove Air Force to Deploy"
        bot.send_message(chat_id = group_chat[0][0], text = text)
    else:
        piece = db.execute("select min(pieceid) from piece where location = 'none' and control = :country and type = 'air';", {'country':active_country}).fetchall()
        db.execute("update piece set location = :location where pieceid = :piece;", {'location':space, 'piece':piece[0][0]})
        text = active_country_name[0][0] + " Deploy in " + space_info[0][0]
        bot.send_message(chat_id = group_chat[0][0], text = text)
        function.updatecontrol(bot, db)
        check_reposition(bot, session)
        function.updatesupply(db)
        lock_id = session.add_lock()
        status_handler.send_status_card(bot, active_country, 'Deploy/Marshal', lock_id, session, piece_id = piece[0][0], space_id = space, card_id = card_id)
        db.commit()
        
    #------------------Marshal----------------------
def marshal_info(bot, country, space_list, card_id, lock_id, session):
    print('marshal_info')
    print(space_list) 
    db = sqlite3.connect(session.get_db_dir())
    name_list = function.get_name_list(space_list, db)
    print(name_list)
    session.space_list_buffer = space_list
    chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    text = "Choose a space to Marshal"
    keyboard = [[InlineKeyboardButton(space[1], callback_data="['marshal', '{}', {}, {}, {}]".format(country, space[0], card_id, lock_id))] for space in name_list]
    keyboard.append([InlineKeyboardButton('Pass', callback_data="['marshal', '{}', 'pass', {}]".format(country, lock_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return chat_id[0][0], text, reply_markup


def marshal_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        marshal(bot, query_list[1], query_list[3], query_list[4], session)
        session.release_lock(query_list[-1])
    elif query_list[2] == 'pass':
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text='Passed')
        session.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            info = marshal_info(bot, query_list[1] , session.space_list_buffer, query_list[3], query_list[4], session)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[2]}).fetchall()
            text = 'Marshal in ' + location[0][0] + ':'
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['marshal', '{}', 'confirm', {}, {}, {}]".format(query_list[1], query_list[2], query_list[3], query_list[4]))]
                        , [InlineKeyboardButton('Back', callback_data="['marshal', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[4]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)
        db.commit()

def marshal(bot, active_country, space, card_id, session):
    db = sqlite3.connect(session.get_db_dir())
    space_info = db.execute("select distinct name, type from space where spaceid = :space;", {'space':space}).fetchall()
    active_country_name = db.execute("select name from country where id = :country;", {'country':active_country}).fetchall()
    group_chat = db.execute("select chatid from game;").fetchall()
    piece = db.execute("select min(pieceid) from piece where location = 'none' and control = :country and type = 'air';", {'country':active_country}).fetchall()
    db.execute("update piece set location = :location where pieceid = :piece;", {'location':space, 'piece':piece[0][0]})
    text = active_country_name[0][0] + " Marshal in " + space_info[0][0]
    bot.send_message(chat_id = group_chat[0][0], text = text)
    function.updatecontrol(bot, db)
    check_reposition(bot, session)
    function.updatesupply(db)
    lock_id = session.add_lock()
    status_handler.send_status_card(bot, active_country, 'Deploy/Marshal', lock_id, session, piece_id = piece[0][0], space_id = space, card_id = card_id)
    db.commit()

    #------------------------------------------Over_Deploy_Handler------------------------------------------
def over_deploy_handler(bot, active_country, session):
    db = sqlite3.connect(session.get_db_dir())
    if db.execute("select count(*) from piece where location = 'none' and control = :country and type = 'air';", {'country':active_country}).fetchall()[0][0] == 0:
        lock_id = session.add_lock()
        space_list = function.control_air_space_list(active_country, db)
        session.self_remove_list.append(battlebuild.self_remove(active_country, space_list, None, lock_id, 'air', session))
        self_remove_id = len(session.self_remove_list)-1
        info = session.self_remove_list[self_remove_id].self_remove_info(session)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        session.thread_lock(lock_id)
    return (db.execute("select count(*) from piece where location = 'none' and control = :country and type = 'air';", {'country':active_country}).fetchall()[0][0] == 0)

    #------------------------------------------Reposition------------------------------------------
def check_reposition(bot, session):
    db = sqlite3.connect(session.get_db_dir())
    for country in ['ge', 'it', 'jp', 'uk', 'su', 'us', 'fr', 'ch']:
        no_control_air_list = db.execute("select pieceid, location from piece where type = 'air' and location not in (select location from piece where type in ('army', 'navy') and control = :country) and location != 'none' and control = :country;", {'country':country}).fetchall()
        if len(no_control_air_list) > 0:
            for piece in no_control_air_list:
                lock_id = session.add_lock()
                info = reposition_info(country, piece[1], piece[0], lock_id, session)
                if info != None:
                    bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
                    session.thread_lock(lock_id)
                else:
                    battlebuild.remove(bot, country, piece[0] ,piece[1] , None, session)
    
def reposition_info(country, space_id, piece_id, lock_id, session):
    print('reposition_info')
    db = sqlite3.connect(session.get_db_dir())
    side = function.getside[country]
    space_list1 = function.within(side, [space_id], 1, db)
    space_list2 = function.control_supplied_space_list(country, db)
    space_list = list(set(space_list1) & set(space_list2))
    if len(space_list) > 0:
        print(space_list) 
        name_list = function.get_name_list(space_list, db)
        print(name_list)
        session.space_list_buffer = space_list
        chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
        text = "Choose a space to Reposition"
        keyboard = [[InlineKeyboardButton(space[1], callback_data="['reposition', '{}', {}, {}, {}]".format(country, space[0], piece_id, lock_id))] for space in name_list]
        keyboard.append([InlineKeyboardButton('Pass', callback_data="['reposition', '{}', 'pass', {}, {}, {}]".format(country, space_id, piece_id, lock_id))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        return chat_id[0][0], text, reply_markup
    else:
        return None


def reposition_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        reposition(bot, query_list[1], query_list[3], query_list[4], db)
        session.release_lock(query_list[-1])
    elif query_list[2] == 'pass':
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text='Passed')
        battlebuild.remove(bot, query_list[1], query_list[4], query_list[3], None, session)
        session.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            info = reposition_info(bot, query_list[1] , session.space_list_buffer, query_list[3], session)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[2]}).fetchall()
            text = 'Reposition in ' + location[0][0] + ':'
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['reposition', '{}', 'confirm', {}, {}, {}]".format(query_list[1], query_list[2], query_list[3], query_list[4]))], [InlineKeyboardButton('Back', callback_data="['marshal', '{}', 'back', {}]".format(query_list[1], query_list[3]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)
        db.commit()

def reposition(bot, active_country, space_id, piece_id, db):
    space_info = db.execute("select distinct name, type from space where spaceid = :space;", {'space':space_id}).fetchall()
    active_country_name = db.execute("select name from country where id = :country;", {'country':active_country}).fetchall()
    group_chat = db.execute("select chatid from game;").fetchall()
    db.execute("update piece set location = :location where pieceid = :piece;", {'location':space_id, 'piece':piece_id})
    text = active_country_name[0][0] + " Reposition in " + space_info[0][0]
    bot.send_message(chat_id = group_chat[0][0], text = text)
    db.commit()
    
    
    #------------------------------------------Air Defense------------------------------------------
    #TODO remove air
def air_defense(bot, handler_id, session):
    db = sqlite3.connect(session.get_db_dir())
    session.handler_list[handler_id].air_defense = True
    group_chat = db.execute("select chatid from game;").fetchall()
    text = function.countryid2name[session.handler_list[handler_id].passive_country_id] + " uesd Air Defense"
    bot.send_message(chat_id = group_chat[0][0], text = text)
    air_id = db.execute("select pieceid from piece where location = :location and control = :country and type = 'air';", {'location':session.handler_list[handler_id].space_id, 'country':session.handler_list[handler_id].passive_country_id}).fetchall()
    battlebuild.remove(bot, session.handler_list[handler_id].passive_country_id, air_id[0][0], session.handler_list[handler_id].space_id, None, session)
    battlebuild.restore(bot, session.handler_list[handler_id].piece_id, session.handler_list[handler_id].space_id, session)
    
    #------------------------------------------Air Attack------------------------------------------
    #TODO remove air
air_attack_list = []
class air_attack():
    def __init__(self, handler_id, lock_id, session):
        self.air_attack_id = len(air_attack_list)
        self.country = session.handler_list[handler_id].active_country_id
        #side = {'ge':'Axis', 'jp':'Axis', 'it':'Axis', 'uk':'Allied', 'su':'Allied', 'us':'Allied', 'fr':'Allied', 'ch':'Allied'}
        #self.space_list = list(set(function.control_air_space_list(session.handler_list[handler_id].active_country, db)) & set(within(session.handler_list[handler_id].active_country, [session.handler_list[handler_id].space_id], 1, db)))
        self.space_list = None
        self.lock_id = lock_id
        self.handler_id = handler_id
        self.space_id = None
        self.piece_id = None
        text = "air_attack buffer add: "
        info_list = {"air_attack_id":self.air_attack_id, "country":self.country, "lock_id":self.lock_id, "handler_id":self.handler_id}
        for info in info_list:
            if info_list[info] != None:
                text += " [" + info + ": " + str(info_list[info]) + "]"
        print(text)

    def air_attack_info(self, session):
        db = sqlite3.connect(session.get_db_dir())
        side = db.execute("select side from country where id = :country;", {'country':session.handler_list[self.handler_id].active_country_id}).fetchall()
        self.space_list = list(set(function.control_air_space_list(session.handler_list[self.handler_id].active_country_id, db)) & set(function.within(side[0][0], [session.handler_list[self.handler_id].space_id], 1, db)))
        #name_list = function.get_name_list(list(set(function.control_air_space_list(session.handler_list[self.handler_id].active_country_id, db)) & set(function.within(side[0][0], [session.handler_list[self.handler_id].space_id], 1, db))))
        name_list = function.get_name_list(self.space_list, db)
        chat_id = db.execute("select playerid from country where id = :country;", {'country':session.handler_list[self.handler_id].active_country_id}).fetchall()
        text = 'Remove a Air Force'
        keyboard = [[InlineKeyboardButton(space[1], callback_data="['air_attack', {}, {}, {}]".format(space[0], self.handler_id, self.air_attack_id))] for space in name_list]
        keyboard.append([InlineKeyboardButton('Pass', callback_data="['air_attack','pass', {}]".format(self.air_attack_id))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        return chat_id[0][0], text, reply_markup

    def air_attack_cb(self, bot, query, query_list, session):
        db = sqlite3.connect(session.get_db_dir())
        if query_list[1] == 'confirm':
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            session.handler_list[query_list[-1]].air_defense = False
            group_chat = db.execute("select chatid from game;").fetchall()
            text = function.countryid2name[session.handler_list[self.handler_id].active_country_id] + " uesd Air Attack"
            bot.send_message(chat_id = group_chat[0][0], text = text)
            air_id = db.execute("select pieceid from piece where location = :space and control = :country and type = 'air';", {'space':self.space_id, 'country':session.handler_list[self.handler_id].active_country_id}).fetchall()
            battlebuild.remove(bot, session.handler_list[self.handler_id].active_country_id, air_id[0][0], self.space_id, None, session)
            battlebuild.remove(bot, session.handler_list[self.handler_id].active_country_id, session.handler_list[self.handler_id].piece_id, session.handler_list[self.handler_id].space_id, None, session)
            session.handler_list[self.handler_id].air_attack = True
            session.release_lock(self.lock_id)
            air_attack_list.pop(self.air_attack_id)
        elif query_list[1] == 'pass':
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            session.release_lock(self.lock_id)
            air_attack_list.pop(self.air_attack_id)
        else:
            if query_list[1] == 'back':
                self.space_id = None
                info = self.air_attack_info(self, session)
                text = info[2]
                reply_markup = info[3]
            else:
                self.space_id = query_list[1]
                location = db.execute("select name from space where spaceid = :id", {'id':self.space_id}).fetchall()
                text = 'Remove Air Force in ' + location[0][0] + ':'
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['air_attack', 'confirm', {}, 0]".format(self.air_attack_id))], 
                            [InlineKeyboardButton('Back', callback_data="['air_attack', 'back', {}]".format(self.air_attack_id))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup)
                
