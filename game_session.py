import os
import shutil
import traceback
import sqlite3

class session:
    def __init__(self, group_chat_id):
        self._session_id = len(session_list) - 1
        self._group_chat_id = group_chat_id
        self._game_id = None
        self._exp_enable = False
        self.player_name = {}
        self._axis_player_id_list = {'ge':None, 'jp':None, 'it':None}
        self._allied_player_id_list = {'uk':None, 'su':None, 'us':None}
        self._player_id_list = {'ge':None, 'jp':None, 'it':None, 'uk':None, 'su':None, 'us':None}
        self.started = False

        
        self._dir = None
        self._db_dir = None

        self.space_list_buffer = []
        self.space_buffer = None
        self.handler_list = []
    
    def get_session_id(self):
        return self._session_id
    
    def get_group_chat_id(self):
        return self._group_chat_id

    def get_game_id(self):
        return self._game_id

    def set_game_id(self, new_game_id):
        self._game_id = new_game_id

    def get_db_dir(self):
        return self._db_dir

    def get_dir(self):
        return self._dir

    def get_axis_player_id_list(self):
        return self._axis_player_id_list

    def set_axis_player_id_list(self, country, new_player_id):
        self._axis_player_id_list[country] = new_player_id

    def get_allied_player_id_list(self):
        return self._allied_player_id_list

    def set_allied_player_id_list(self, country, new_player_id):
        self._allied_player_id_list[country] = new_player_id

    def get_player_id_list(self):
        return self._player_id_list

    def set_player_id_list(self, country, new_player_id):
        self._player_id_list[country] = new_player_id

    def create_dir(self):
        print('Creating dir-' + str(self._game_id))
        os.mkdir(str(self._game_id))
        self._dir = org_dir + '/' + str(self._game_id)
        os.mkdir(self._dir + '/pic')
        print('Created dir-' + str(self._game_id))
        
    def create_db(self):
        print('Creating db-' + str(self._game_id))
        src = org_dir + '/database.db'
        dst = org_dir + '/' + str(self._game_id) + '/database.db'
        shutil.copy2(src, dst)
        os.chdir(org_dir)
        self._db = sqlite3.connect(dst)
        db = self._db
        db.execute("update game set group_chat_id = :group_chat_id;", {'group_chat_id':self._group_chat_id})
        for country in self._player_id_list:
            db.execute("update country set playerid =:id, status = 'filled' where id = :country ;", {'id': self._player_id_list[country], 'country': country})
            if country == 'uk':
                db.execute("update country set playerid =:id, status = 'filled' where id = 'fr' ;", {'id': self._player_id_list[country]})
            if country == 'us':
                db.execute("update country set playerid =:id, status = 'filled' where id = 'ch' ;", {'id': self._player_id_list[country]})
        db.commit()
        self._db_dir = org_dir + '/' + str(self._game_id) + '/database.db'
        game_db = sqlite3.connect('game_session.db')
        game_db.execute("insert into game_session values (:game_id, :group_chat_id, 1, :ge, :jp, :it, :uk, :su, :us)", {'game_id':self._game_id, 'group_chat_id':self._group_chat_id, 'ge':self._player_id_list['ge'], 'jp':self._player_id_list['jp'], 'it':self._player_id_list['it'], 'uk':self._player_id_list['uk'], 'su':self._player_id_list['su'], 'us':self._player_id_list['us']})
        game_db.commit()
        print('Created db-' + str(self._game_id))

    def load_db(self):
        game_db = sqlite3.connect('game_session.db')
        print('Loading Game-' + str(self._game_id))
        self.started = True
        self._db_dir = org_dir + '/' + str(self._game_id) + '/database.db'
        self._dir = org_dir + '/' + str(self._game_id)
        for country in self._player_id_list:
            new_player_id = game_db.execute("select {} from game_session where game_id = :game_id;".format(country+'_player_id'), {'game_id':self._game_id}).fetchall()[0][0]
            self.set_player_id_list(country, new_player_id)
        print('Loaded Game-' + str(self._game_id))

        
    def save_session(self):
        os.chdir(self._dir)
        try:
            shutil.copy2('database.db', 'database_backup.db')
        except Exception as e:
            print(e)
            os.chdir(org_dir)
            return False
        else:
            os.chdir(org_dir)
            return True

    def save_session_turn(self, country):
        os.chdir(self._dir)
        try:
            shutil.copy2('database.db', 'database_turn_' + country + '.db')
        except Exception as e:
            print(e)
            os.chdir(org_dir)
            return False
        else:
            os.chdir(org_dir)
            return True

    def load_session(self):
        os.chdir(self._dir)
        try:
            shutil.copy2('database_backup.db', 'database.db')
        except Exception as e:
            print(e)
            os.chdir(org_dir)
            return False
        else:
            os.chdir(org_dir)
            return True    

    def load_session_turn(self, country):
        os.chdir(self._dir)
        try:
            shutil.copy2('database_turn_' + country + '.db', 'database.db')
        except Exception as e:
            print(e)
            os.chdir(self._dir)
            return False
        else:
            os.chdir(self._dir)
            return True    

    def set_inactive(self):
        game_db = sqlite3.connect('game_session.db')
        game_db.execute("update game_session set active = 0 where game_id = :game_id;", {'game_id':self._game_id})
        game_db.commit()


org_dir = os.getcwd()
session_list = []

game_db = sqlite3.connect('game_session.db')
active_game_list = game_db.execute("select game_id, group_chat_id from game_session where active = 1;").fetchall()
for game in active_game_list:
    new_session = session(game[1])
    session_list.append(new_session)
    new_session.set_game_id(game[0])
    new_session.load_db()



def get_new_game_id():
    game_db = sqlite3.connect('game_session.db')
    max_game_id = game_db.execute("select MAX(game_id) from game_session;").fetchall()[0][0]
    return max_game_id + 1


def get_all_active_player():
    active_player_list = []
    for session in session_list:
        if session.started:
            for player_id in session.get_player_id_list():
                active_player_list.append(session.get_player_id_list()[player_id])
    print(active_player_list)
    return active_player_list

def find_session(group_chat_id):
    for session in session_list:
        #print('session.get_group_chat_id() ' + str(session.get_group_chat_id()))
        #print('session.get_player_id_list() ' + str(session.get_player_id_list()))
        if session.get_group_chat_id() == group_chat_id or group_chat_id in session.get_player_id_list().values():
            return session
    return None

