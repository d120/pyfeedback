# coding=utf-8

class Parser(object):
    @staticmethod
    def _mapping(mapping, data):
        try:
            return mapping[data]
        except KeyError:
            return ''

    @staticmethod
    def parse_fach(data):
        return Parser._mapping({'1': 'inf', '2': 'winf', '3': 'math', '4': 'etit', '5': 'ist',
                                '6': 'ce', '7': 'sonst'}, data)

    @staticmethod
    def parse_fach_16(data):
        return Parser._mapping({'1': 'inf', '2': 'winf', '3': 'math', '4': 'etit', '5': 'ist',
                                '6': 'ce', '7': 'psyit', '8': 'sonst'}, data)

    @staticmethod
    def parse_abschluss(data):
        return Parser._mapping({'1': 'bsc', '2': 'msc', '3': 'dipl', '4': 'lehr', '5': 'sonst'},
                               data)

    @staticmethod
    def parse_abschluss_16(data):
        return Parser._mapping({'1': 'bsc', '2': 'msc', '4': 'lehr', '5': 'sonst'},
                               data)

    @staticmethod
    def parse_semester(data):
        return Parser._mapping({'1': '1-2', '2': '3-4', '3': '5-6', '4': '>=7'}, data)

    @staticmethod
    def parse_semester_16(data):
        return Parser._mapping({'1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9', '10': '>=10'}, data)

    @staticmethod
    def parse_geschwindigkeit(data):
        return Parser._mapping({'1': 's', '2': 'l'}, data)

    @staticmethod
    def parse_geschwindigkeit16(data):
        return Parser._mapping({'1': '3', '2': '2', '3':'1', '4':'2', '5':'3'}, data)

    @staticmethod
    def parse_niveau(data):
        return Parser._mapping({'1': 'h', '2': 'n'}, data)

    @staticmethod
    def parse_empfehlung(data):
        return Parser._mapping({'1': 'j', '2': 'n'}, data)

    @staticmethod
    def parse_geschlecht(data):
        return Parser._mapping({'1': 'w', '2': 'm'}, data)

    @staticmethod
    def parse_geschlecht_16(data):
        return Parser._mapping({'1': 'w', '2': 'm', '3': 's'}, data)

    @staticmethod
    def parse_studienberechtigung(data):
        return Parser._mapping({'1': 'd', '2': 'o'}, data)

    @staticmethod
    def parse_veranstaltung_gehoert(data):
        return Parser._mapping(
        {'1': '1', '3': '3', '2': '2', '4': '<=4'}, data)

    @staticmethod
    def parse_klausur_angetreten(data):
        return Parser._mapping(
        {'1': '1', '0': '0', '2': '2'}, data)

    @staticmethod
    def parse_boolean(data):
        return Parser._mapping({'1': 'j', '0': 'n'}, data)

    @staticmethod
    def parse_int(data):
        try:
            return int(data)
        except(ValueError):
            return None

    @staticmethod
    def parse_extrazeit(data):
        return Parser._mapping({'1': '0.5', '0': '0', '3': '2', '2': '1', '5': '4', '4': '3', '7': '>=5', '6': '5'}, data)
