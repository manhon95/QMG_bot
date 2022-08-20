import telegram
import sqlite3
import function
import thread_lock
import status_handler

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters


    #------------------------------------------Battle------------------------------------------
def battle_info(bot, country, space_list, card_id, lock_id, session):
    print('battle info')
    print(space_list)
    db = sqlite3.connect(session.get_db_dir())  
    name_list = function.get_name_list(space_list, db)
    print(name_list)
    session.space_list_buffer = space_list
    chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    text = 'Choose a space to battle'
    keyboard = []
    for space in name_list:
        piece_list = db.execute("select country.name from piece inner join country on piece.control = country.id where piece.location = :location and piece.type != 'air';", {'location':space[0]}).fetchall()
        if len(piece_list) == 0:
            keyboard.append([InlineKeyboardButton(space[1] + " - empty", callback_data="['battle', '{}', {}, {}, {}]".format(country, space[0], card_id, lock_id))])
        else:
            button = space[1] + " - "
            for piece in piece_list:
                button += piece[0] + " "
            keyboard.append([InlineKeyboardButton(button, callback_data="['battle', '{}', {}, {}, {}]".format(country, space[0], card_id, lock_id))])              
    keyboard.append([InlineKeyboardButton('Pass', callback_data="['battle', '{}', 'pass', {}, {}]".format(country, card_id, lock_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return chat_id[0][0], text, reply_markup


def battle_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        battle(bot, query_list[1], query_list[3], query_list[4], query_list[5], session)
        session.release_lock(query_list[-1])
    elif query_list[2] == 'pass':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        session.release_lock(query_list[-1])
    else:  
        if query_list[2] == 'back':
            info = battle_info(bot, query_list[1] , session.space_list_buffer, query_list[3], query_list[-1], session)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[2]}).fetchall()
            text = 'Battle ' + location[0][0] + ':'
            piece_list = db.execute("select country.name, piece.pieceid from piece inner join country on piece.control = country.id where piece.location = :location and piece.type != 'air';", {'location':query_list[2]}).fetchall()
            if len(piece_list) == 0:
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['battle', '{}', 'confirm', 0, {}, {}, {}]".format(query_list[1], query_list[2], query_list[3], query_list[-1]))], [InlineKeyboardButton('Back', callback_data="['battle', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[-1]))]]
            elif len(piece_list) == 1:
                keyboard = [[InlineKeyboardButton('Confirm', callback_data="['battle', '{}', 'confirm', {}, {}, {}, {}]".format(query_list[1], piece_list[0][1], query_list[2], query_list[3], query_list[-1]))], [InlineKeyboardButton('Back', callback_data="['battle', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[-1]))]]                
            else:
                keyboard = [[InlineKeyboardButton(piece[0], callback_data="['battle', '{}', 'confirm', {}, {}, {}, {}]".format(query_list[1], piece[1], query_list[2], query_list[3], query_list[-1]))] for piece in piece_list]
                keyboard.append([InlineKeyboardButton('Back', callback_data="['battle', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[-1]))])
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup)
        db.commit()


def battle(bot, active_country, piece, space, card_id, session):
    db = sqlite3.connect(session.get_db_dir())
    function.updatesupply(db)
    space_name = db.execute("select distinct name from space where spaceid = :space;", {'space':space}).fetchall()
    active_country_name = db.execute("select name from country where id = :country;", {'country':active_country}).fetchall()
    passive_country = db.execute("select control from piece where pieceid = :piece;", {'piece':piece}).fetchall()
    group_chat = db.execute("select chatid from game;").fetchall()
    if piece == 0:
        db.execute("update piece set location = :space where pieceid = :piece;", {'space':space, 'piece':piece})
        db.commit()
        text =" Empty space " + space_name[0][0] + " is battled by " + active_country_name[0][0]
    else:
        country_name = db.execute("select id, name from country where id = (select control from piece where pieceid = :piece);", {'piece':piece}).fetchall()
        status_handler.status_battle_handler(bot, active_country, country_name[0][0], space, session)
        if db.execute("select noremove from piece where pieceid = :piece;", {'piece':piece}).fetchall()[0][0] == 0:
            db.execute("update piece set location = 'none' where pieceid = :piece;", {'piece':piece})
            db.commit()
            text = country_name[0][1] + " piece in " + space_name[0][0] + " is battled by " + active_country_name[0][0]
        else:
            text = country_name[0][1] + " piece in " + space_name[0][0] + " is not removed"
    bot.send_message(chat_id = group_chat[0][0], text = text)        
    function.updatecontrol(bot, db)
    lock_id = session.add_lock()
    status_handler.send_status_card(bot, active_country, 'Battle', lock_id, session, passive_country_id = passive_country[0][0], piece_id = piece, space_id = space, card_id = card_id)
    import air
    air.check_reposition(bot, session)
    db.commit()
    

    
    #------------------------------------------Remove------------------------------------------
class remove_obj():
    def __init__(self, country, space_list, card_id, lock_id, piece_type, session):
        self.remove_id = len(session.remove_list)
        self.country = country
        self.space_list = space_list
        self.card_id = card_id
        self.lock_id = lock_id
        self.piece_type = piece_type
        self.space_id = None
        self.piece_list = None
        self.piece_id = None
        text = "remove buffer add: "
        info_list = {"remove_id":self.remove_id, "country":country, "space_list":space_list, "card_id":card_id, "lock_id":lock_id, "piece_type":piece_type}
        for info in info_list:
            if info_list[info] != None:
                text += " [" + info + ": " + str(info_list[info]) + "]"
        print(text)

    def remove_info(self, session):
        db = sqlite3.connect(session.get_db_dir())
        print('remove info')
        print(self.space_list)
        name_list = function.get_name_list(self.space_list, db)
        chat_id = db.execute("select playerid from country where id = :country;", {'country':self.country}).fetchall()
        text = 'Choose a space to remove'
        keyboard = [[InlineKeyboardButton(space[1], callback_data="['remove', {}, {}]".format(space[0], self.remove_id))] for space in name_list]
        keyboard.append([InlineKeyboardButton('Pass', callback_data="['remove','pass', {}]".format(self.remove_id))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        return chat_id[0][0], text, reply_markup


    def remove_cb(self, bot, query, query_list, session):
        db = sqlite3.connect(session.get_db_dir())
        if query_list[1] == 'confirm':
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            self.piece_id = query_list[2]
            remove(bot, self.country, self.piece_id, self.space_id, self.card_id, session)
            session.release_lock(self.lock_id)
            session.remove_list.pop(self.remove_id)
        elif query_list[1] == 'pass':
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            session.release_lock(self.lock_id)
            session.remove_list.pop(self.remove_id)
        else:  
            if query_list[1] == 'back':
                self.space_id = None
                info = self.remove_info(session)
                text = info[1]
                reply_markup = info[2]
            else:
                self.space_id = query_list[1]
                location = db.execute("select name from space where spaceid = :id", {'id':self.space_id}).fetchall()
                text = 'Remove ' + location[0][0] + ':'
                if self.piece_type == 'all':
                    self.piece_list = db.execute("select country.name, piece.pieceid, piece.type from piece inner join country on piece.control = country.id where piece.location = :location;", {'location':self.space_id}).fetchall()
                else:
                    self.piece_list = db.execute("select country.name, piece.pieceid, piece.type from piece inner join country on piece.control = country.id where piece.location = :location and piece.type = :type;", {'location':self.space_id, 'type':self.piece_type}).fetchall()
                if len(self.piece_list) == 0:
                    keyboard = [[InlineKeyboardButton('Confirm', callback_data="['remove', 'confirm', 0, {}]".format(self.remove_id))], 
                                [InlineKeyboardButton('Back', callback_data="['remove', 'back', {}]".format(self.remove_id))]]
                elif len(self.piece_list) == 1:
                    keyboard = [[InlineKeyboardButton('Confirm', callback_data="['remove', 'confirm', {}, {}]".format(self.piece_list[0][1], self.remove_id))], 
                                [InlineKeyboardButton('Back', callback_data="['remove', 'back', {}]".format(self.remove_id))]]              
                else:
                    keyboard = [[InlineKeyboardButton(piece[0] + function.piece_type_name[piece[2]], callback_data="['remove', 'confirm', {}, {}]".format(piece[1], self.remove_id))] for piece in self.piece_list]
                    keyboard.append([InlineKeyboardButton('Back', callback_data="['remove', 'back', {}]".format((self.remove_id)))])
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup)

def remove(bot, active_country, piece, space, card_id, session):
    db = sqlite3.connect(session.get_db_dir())
    function.updatesupply(db)
    space_name = db.execute("select distinct name from space where spaceid = :space;", {'space':space}).fetchall()
    piece_type = db.execute("select type from piece where pieceid = :piece;", {'piece':piece}).fetchall()
    active_country_name = db.execute("select name from country where id = :country;", {'country':active_country}).fetchall()
    group_chat = db.execute("select chatid from game;").fetchall()
    if piece == 0:
        db.execute("update piece set location = :space where pieceid = :piece;", {'space':space, 'piece':piece})
        db.commit()
        text =" Empty space " + space_name[0][0] + " is removed by " + active_country_name[0][0]
    else:
        country_name = db.execute("select name from country where id = (select control from piece where pieceid = :piece);", {'piece':piece}).fetchall()
        if db.execute("select noremove from piece where pieceid = :piece;", {'piece':piece}).fetchall()[0][0] == 0:
            db.execute("update piece set location = 'none' where pieceid = :piece;", {'piece':piece})
            db.commit()
            text = country_name[0][0] + " " + function.piece_type_name[piece_type[0][0]] + " in " + space_name[0][0] + " is removed by " + active_country_name[0][0]
        else:
            text = country_name[0][0] + " piece in " + space_name[0][0] + " is not removed"
    bot.send_message(chat_id = group_chat[0][0], text = text)
    function.updatecontrol(bot, db)
    lock_id = session.add_lock()
    status_handler.send_status_card(bot, active_country, 'Remove', lock_id, session, piece_id = piece, space_id = space, card_id = card_id)
    import air
    air.check_reposition(bot, session)
    db.commit()
    
    #------------------------------------------Self_Remove------------------------------------------
class self_remove():
    def __init__(self, country, space_list, card_id, lock_id, piece_type, session):
        self.self_remove_id = len(session.self_remove_list)
        self.country = country
        self.space_list = space_list
        self.card_id = card_id
        self.lock_id = lock_id
        self.piece_type = piece_type
        self.space_id = None
        self.piece_list = None
        self.piece_id = None
        text = "self_remove buffer add: "
        info_list = {"self_remove_id":self.self_remove_id, "country":country, "space_list":space_list, "card_id":card_id, "lock_id":lock_id, "piece_type":piece_type}
        for info in info_list:
            if info_list[info] != None:
                text += " [" + info + ": " + str(info_list[info]) + "]"
        print(text)

    def self_remove_info(self, session):
        db = sqlite3.connect(session.get_db_dir())
        print('self_remove info')
        print(self.space_list)
        name_list = function.get_name_list(self.space_list, db)
        print(name_list)
        chat_id = db.execute("select playerid from country where id = :country;", {'country':self.country}).fetchall()
        text = 'Choose a space to remove'
        keyboard = [[InlineKeyboardButton(space[1], callback_data="['self_remove', {}, {}]".format(space[0], self.self_remove_id))] for space in name_list]
        #keyboard.append([InlineKeyboardButton('Pass', callback_data="['self_remove','pass', {}]".format(self.self_remove_id))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        return chat_id[0][0], text, reply_markup


    def self_remove_cb(self, bot, query, query_list, session):
        db = sqlite3.connect(session.get_db_dir())
        if query_list[1] == 'confirm':
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            self.piece_id = query_list[2]
            remove(bot, self.country, self.piece_id, self.space_id, self.card_id, session)
            session.release_lock(self.lock_id)
            session.self_remove_list.pop(self.self_remove_id)
        elif query_list[1] == 'pass':
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            session.release_lock(self.lock_id)
            session.self_remove_list.pop(self.self_remove_id)
        else:  
            if query_list[1] == 'back':
                self.space_id = None
                info = self.self_remove_info(session)
                text = info[1]
                reply_markup = info[2]
            else:
                self.space_id = query_list[1]
                location = db.execute("select name from space where spaceid = :id", {'id':self.space_id}).fetchall()
                text = 'Remove ' + location[0][0] + ':'
                if self.piece_type == 'all':
                    self.piece_list = db.execute("select pieceid, type from piece where location = :location and control = :country;", {'location':self.space_id, 'country':self.country}).fetchall()
                else:
                    self.piece_list = db.execute("select pieceid, type from piece where location = :location and type = :type and control = :country;", {'location':self.space_id, 'type':self.piece_type, 'country':self.country}).fetchall()
                if len(self.piece_list) == 1:
                    keyboard = [[InlineKeyboardButton('Confirm', callback_data="['self_remove', 'confirm', {}, {}]".format(self.piece_list[0][0], self.self_remove_id))], 
                                [InlineKeyboardButton('Back', callback_data="['self_remove', 'back', {}]".format(self.self_remove_id))]]              
                else:
                    keyboard = [[InlineKeyboardButton(function.piece_type_name[piece[1]], callback_data="['self_remove', 'confirm', {}, {}]".format(piece[0], self.self_remove_id))] for piece in self.piece_list]
                    keyboard.append([InlineKeyboardButton('Back', callback_data="['self_remove', 'back', {}]".format((self.self_remove_id)))])
                reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup)
            db.commit()

    #------------------------------------------Move------------------------------------------
class move_obj():
    def __init__(self, country, space_list, card_id, lock_id, piece_type, session):
        self.move_id = len(session.move_list)
        self.country = country
        self.space_list = space_list
        self.card_id = card_id
        self.lock_id = lock_id
        self.piece_type = piece_type
        self.space_id = None
        self.piece_list = None
        self.piece_id = None
        text = "move buffer add: "
        info_list = {"move_id":self.move_id, "country":country, "space_list":space_list, "card_id":card_id, "lock_id":lock_id, "piece_type":piece_type}
        for info in info_list:
            if info_list[info] != None:
                text += " [" + info + ": " + str(info_list[info]) + "]"
        print(text)

    def move_info(self, db):
        print('move info')
        print(self.space_list)
        name_list = function.get_name_list(self.space_list, db)
        print(name_list)
        chat_id = db.execute("select playerid from country where id = :country;", {'country':self.country}).fetchall()
        text = 'Pick up a piece:'
        keyboard = [[InlineKeyboardButton(space[1], callback_data="['move', {}, {}]".format(space[0], self.move_id))] for space in name_list]
        keyboard.append([InlineKeyboardButton('Pass', callback_data="['move','pass', {}]".format(self.move_id))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        return chat_id[0][0], text, reply_markup


    def move_cb(self, bot, query, query_list, session):
        db = sqlite3.connect(session.get_db_dir())
        if query_list[1] == 'confirm':
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            self.piece_id = query_list[3]
            move(bot, self.country, self.piece_id, self.space_id, session)
            session.release_lock(self.lock_id)
            session.move_list.pop(self.move_id)
        elif query_list[1] == 'pass':
            bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
            session.release_lock(self.lock_id)
            session.move_list.pop(self.move_id)
        else:  
            if query_list[1] == 'back':
                self.space_id = None
                info = self.move_info(db)
                text = info[1]
                reply_markup = info[2]
            else:
                self.space_id = query_list[1]
                location = db.execute("select name from space where spaceid = :id", {'id':self.space_id}).fetchall()
                text = 'Pick up piece in ' + location[0][0] + ':'
                if self.piece_type == 'all':
                    self.piece_list = db.execute("select pieceid, type from piece where location = :location;", {'location':self.space_id}).fetchall()
                else:
                    self.piece_list = db.execute("select pieceid from piece where location = :location and type = :type;", {'location':self.space_id, 'type':self.piece_type}).fetchall()
                if len(self.piece_list) == 1:
                    keyboard = [[InlineKeyboardButton('Confirm', callback_data="['move', 'confirm', {}, {}]".format(self.piece_list[0][0], self.move_id))], 
                                [InlineKeyboardButton('Back', callback_data="['move', 'back', {}]".format(self.move_id))]]              
                else:
                    keyboard = [[InlineKeyboardButton(piece[1], callback_data="['move', 'confirm', {}, {}]".format(piece[1], self.move_id))] for piece in self.piece_list]
                    keyboard.append([InlineKeyboardButton('Back', callback_data="['move', 'back', {}]".format((self.move_id)))])
                reply_markup = InlineKeyboardMarkup(keyboard)
            bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text=text, reply_markup=reply_markup)
            db.commit()

def move(bot, active_country, piece, space, session):
    db = sqlite3.connect(session.get_db_dir())
    function.updatesupply(db)
    space_name = db.execute("select distinct name from space where spaceid = :space;", {'space':space}).fetchall()
    active_country_name = db.execute("select name from country where id = :country;", {'country':active_country}).fetchall()
    group_chat = db.execute("select chatid from game;").fetchall()
    country_name = db.execute("select name from country where id = (select control from piece where pieceid = :piece);", {'piece':piece}).fetchall()
    db.execute("update piece set location = 'none' where pieceid = :piece;", {'piece':piece})
    db.commit()
    text = country_name[0][0] + " piece in " + space_name[0][0] + " is picked up by " + active_country_name[0][0]
    function.updatecontrol(bot, db)
    import air
    air.check_reposition(bot, session)
    bot.send_message(chat_id = group_chat[0][0], text = text)
    

        
    #------------------------------------------Build------------------------------------------
def build_info(bot, country, space_list, card_id, lock_id, session):
    print('build info')
    print(space_list) 
    db = sqlite3.connect(session.get_db_dir())
    name_list = function.get_name_list(space_list, db)
    print(name_list)
    session.space_list_buffer = space_list
    remain_army_count = db.execute("select count(*) from piece where control = :country and type = 'army' and location = 'none';", {'country':country}).fetchall()[0][0]
    remain_navy_count = db.execute("select count(*) from piece where control = :country and type = 'navy' and location = 'none';", {'country':country}).fetchall()[0][0]
    remain_air_count = db.execute("select count(*) from piece where control = :country and type = 'air' and location = 'none';", {'country':country}).fetchall()[0][0]
    chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    text = "Choose a space to build\n"
    text += "Remain army:" + str(remain_army_count) + "\n"
    text += "Remain navy:" + str(remain_navy_count) + "\n"
    text += "Remain air force:" + str(remain_air_count) + "\n"
    keyboard = [[InlineKeyboardButton(space[1], callback_data="['build', '{}', {}, {}, {}]".format(country, space[0], card_id, lock_id))] for space in name_list]
    keyboard.append([InlineKeyboardButton('Pass', callback_data="['build', '{}', 'pass', {}, {}]".format(country, card_id, lock_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return chat_id[0][0], text, reply_markup


def build_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        build(bot,query_list[1], query_list[3], query_list[4], session)
        session.release_lock(query_list[-1])
    elif query_list[2] == 'pass':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        session.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            info = build_info(bot, query_list[1] , session.space_list_buffer, query_list[3], query_list[-1], session)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[2]}).fetchall()
            text = 'Build in ' + location[0][0] + ':'
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['build', '{}', 'confirm', {}, {}, {}]".format(query_list[1], query_list[2], query_list[3], query_list[-1]))], [InlineKeyboardButton('Back', callback_data="['build', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[-1]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)
        db.commit()


def build(bot, active_country, space, card_id, session):
    db = sqlite3.connect(session.get_db_dir())
    space_info = db.execute("select distinct name, type from space where spaceid = :space;", {'space':space}).fetchall()
    active_country_name = db.execute("select name from country where id = :country;", {'country':active_country}).fetchall()
    group_chat = db.execute("select chatid from game;").fetchall()
    if over_build_handler(bot, active_country, space_info[0][1], session):
        text = active_country_name[0][0] + " do not remove piece to build"
        bot.send_message(chat_id = group_chat[0][0], text = text)
    else:
        status_handler.status_build_handler(bot, active_country, session)
        piece = db.execute("select min(pieceid) from piece where location = 'none' and control = :country and type = :piece_type;", {'country':active_country, 'piece_type':function.terrain2type[space_info[0][1]]}).fetchall()
        db.execute("update piece set location = :location where pieceid = :piece;", {'location':space, 'piece':piece[0][0]})
        text = active_country_name[0][0] + " build in " + space_info[0][0]
        bot.send_message(chat_id = group_chat[0][0], text = text)
        function.updatecontrol(bot, db)
        function.updatesupply(db)
        lock_id = session.add_lock()
        status_handler.send_status_card(bot, active_country, 'Build', lock_id, session, piece_id = piece[0][0], space_id = space, card_id = card_id)
        import air
        air.check_reposition(bot, session)
        db.commit()



    #------------------------------------------Recuit------------------------------------------
def recuit_info(bot, country, space_list, card_id, lock_id, session):
    print('recuit info')
    print(space_list) 
    db = sqlite3.connect(session.get_db_dir())
    name_list = function.get_name_list(space_list, db)
    print(name_list)
    remain_army_count = db.execute("select count(*) from piece where control = :country and type = 'army' and location = 'none';", {'country':country}).fetchall()[0][0]
    remain_navy_count = db.execute("select count(*) from piece where control = :country and type = 'navy' and location = 'none';", {'country':country}).fetchall()[0][0]
    remain_air_count = db.execute("select count(*) from piece where control = :country and type = 'air' and location = 'none';", {'country':country}).fetchall()[0][0]
    session.space_list_buffer = space_list
    chat_id = db.execute("select playerid from country where id = :country;", {'country':country}).fetchall()
    text = "Choose a space to recuit\n"
    text += "Remain army:" + str(remain_army_count) + "\n"
    text += "Remain navy:" + str(remain_navy_count) + "\n"
    text += "Remain air force:" + str(remain_air_count) + "\n"
    keyboard = [[InlineKeyboardButton(space[1], callback_data="['recuit', '{}', {}, {}, {}]".format(country, space[0], card_id, lock_id))] for space in name_list]
    keyboard.append([InlineKeyboardButton('Pass', callback_data="['recuit', '{}', 'pass', {}, {}]".format(country, card_id, lock_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return chat_id[0][0], text, reply_markup


def recuit_cb(bot, query, query_list, session):
    db = sqlite3.connect(session.get_db_dir())
    if query_list[2] == 'confirm':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        recuit(bot,query_list[1], query_list[3], query_list[4], session)
        session.release_lock(query_list[-1])
    elif query_list[2] == 'pass':
        bot.delete_message(chat_id = query.message.chat_id, message_id = query.message.message_id)
        session.release_lock(query_list[-1])
    else:
        if query_list[2] == 'back':
            info = recuit_info(bot, query_list[1] , session.space_list_buffer, query_list[3], query_list[-1], session)
            text = info[1]
            reply_markup = info[2]
        else:
            location = db.execute("select name from space where spaceid = :id", {'id':query_list[2]}).fetchall()
            text = 'Recuit in ' + location[0][0] + ':'
            keyboard = [[InlineKeyboardButton('Confirm', callback_data="['recuit', '{}', 'confirm', {}, {}, {}]".format(query_list[1], query_list[2], query_list[3], query_list[-1]))], [InlineKeyboardButton('Back', callback_data="['recuit', '{}', 'back', {}, {}]".format(query_list[1], query_list[3], query_list[-1]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id, text = text, reply_markup = reply_markup)
        db.commit()


def recuit(bot, active_country, space, card_id, session):
    db = sqlite3.connect(session.get_db_dir())
    space_info = db.execute("select distinct name, type from space where spaceid = :space;", {'space':space}).fetchall()
    active_country_name = db.execute("select name from country where id = :country;", {'country':active_country}).fetchall()
    group_chat = db.execute("select chatid from game;").fetchall()
    if over_build_handler(bot, active_country, space_info[0][1], session):
        text = active_country_name[0][0] + " do not remove piece to recuit"
        bot.send_message(chat_id = group_chat[0][0], text = text)
    else:
        status_handler.status_recuit_handler(bot, active_country, session)
        piece = db.execute("select min(pieceid) from piece where location = 'none' and control = :country and type = :piece_type;", {'country':active_country, 'piece_type':function.terrain2type[space_info[0][1]]}).fetchall()
        db.execute("update piece set location = :location where pieceid = :piece;", {'location':space, 'piece':piece[0][0]})
        text = active_country_name[0][0] + " recuit in " + space_info[0][0]
        bot.send_message(chat_id = group_chat[0][0], text = text)
        function.updatecontrol(bot, db)
        function.updatesupply(db)
        lock_id = session.add_lock()
        status_handler.send_status_card(bot, active_country, 'Recruit', lock_id, session, piece_id = piece[0][0], space_id = space, card_id = card_id)
        import air
        air.check_reposition(bot, session)
        db.commit()



    #------------------------------------------Over_Build_Handler------------------------------------------
def over_build_handler(bot, active_country, space_type, session):
    db = sqlite3.connect(session.get_db_dir())
    if db.execute("select count(*) from piece where location = 'none' and control = :country and type = :piece_type;", {'country':active_country, 'piece_type':function.terrain2type[space_type]}).fetchall()[0][0] == 0:
        lock_id = session.add_lock()
        space_list = function.control_space_list(active_country, db, space_type = space_type)
        session.self_remove_list.append(self_remove(active_country, space_list, None, lock_id, function.terrain2type[space_type], session))
        self_remove_id = len(session.self_remove_list)-1
        info = session.self_remove_list[self_remove_id].self_remove_info(session)
        bot.send_message(chat_id = info[0], text = info[1], reply_markup = info[2])
        session.thread_lock(lock_id)
    return (db.execute("select count(*) from piece where location = 'none' and control = :country and type = :piece_type;", {'country':active_country, 'piece_type':function.terrain2type[space_type]}).fetchall()[0][0] == 0)

    #------------------------------------------Restore------------------------------------------
def restore(bot, piece, space, session):
    db = sqlite3.connect(session.get_db_dir())
    space_info = db.execute("select distinct name, type from space where spaceid = :space;", {'space':space}).fetchall()
    group_chat = db.execute("select chatid from game;").fetchall()
    db.execute("update piece set location = :location where pieceid = :piece;", {'location':space, 'piece':piece})
    function.updatecontrol(bot, db)
    import air
    air.check_reposition(bot, session)
    text = "Piece in " + space_info[0][0] + " not removed"
    bot.send_message(chat_id = group_chat[0][0], text = text)
    db.commit()
