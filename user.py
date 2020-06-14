user_name_list = {}

class user:
    def __init__(self, tg_id, tg_name):
        self._tg_id = tg_id
        self._tg_name = tg_name
    
    def get_tg_id(self):
        return self._tg_id

    def get_tg_name(self):
        return self._tg_name

    def set_tg_name(self, tg_name):
        self._tg_name = tg_name
