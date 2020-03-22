space_list = []
space = None

handler_list = []
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


