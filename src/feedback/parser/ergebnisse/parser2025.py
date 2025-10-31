# coding = utf-8

from feedback.models import Fragebogen2025
from feedback.parser.ergebnisse.parser import Parser


class Parser2025(Parser):
    @classmethod
    def create_fragebogen(cls, veranst, frageb):
        Fragebogen2025.objects.create(
            veranstaltung=veranst,
            fach=cls.parse_fach_16(frageb[1]),
            abschluss=cls.parse_abschluss_16(frageb[3]),
            semester=cls.parse_semester_16(frageb[4]),
            geschlecht=cls.parse_geschlecht_16(frageb[5]),
            studienberechtigung=cls.parse_studienberechtigung(frageb[6]),
            pflichveranstaltung=cls.parse_boolean(frageb[7]),
            male_veranstaltung_gehoert=cls.parse_veranstaltung_gehoert(frageb[8]),
            pruefung_angetreten=cls.parse_klausur_angetreten(frageb[9]),

            v_wie_oft_besucht=cls.parse_int(frageb[10]),
            v_besuch_ueberschneidung=cls.parse_boolean(frageb[11]),
            v_besuch_qualitaet=cls.parse_boolean(frageb[12]),
            v_besuch_verhaeltnisse=cls.parse_boolean(frageb[13]),
            v_besuch_privat=cls.parse_boolean(frageb[14]),
            v_besuch_elearning=cls.parse_boolean(frageb[15]),
            v_besuch_zufrueh=cls.parse_boolean(frageb[16]),
            v_besuch_sonstiges=cls.parse_boolean(frageb[17]),
            v_vorwissen_ausreichend=cls.parse_int(frageb[19]),
            v_technisch_moeglich=cls.parse_int(frageb[20]),

            v_3_1=cls.parse_int(frageb[21]),
            v_3_2=cls.parse_int(frageb[22]),
            v_3_3=cls.parse_int(frageb[23]),
            v_3_4=cls.parse_int(frageb[24]),
            v_3_6=cls.parse_int(frageb[26]),
            v_3_7=cls.parse_int(frageb[27]),

            v_4_1=cls.parse_int(frageb[28]),
            v_4_2=cls.parse_int(frageb[29]),
            v_4_3=cls.parse_int(frageb[30]),
            v_4_4=cls.parse_int(frageb[31]),
            v_4_5=cls.parse_int(frageb[32]),
            v_4_6=cls.parse_int(frageb[33]),
            v_4_7=cls.parse_int(frageb[34]),

            v_5_1=cls.parse_int(frageb[35]),
            v_5_2=cls.parse_int(frageb[36]),
            v_5_3=cls.parse_int(frageb[37]),
            v_5_4=cls.parse_int(frageb[38]),
            v_5_5=cls.parse_int(frageb[39]),
            v_5_6=cls.parse_int(frageb[40]),
            v_5_7=cls.parse_int(frageb[41]),

            v_6_1=cls.parse_int(frageb[42]),
            v_6_2=cls.parse_int(frageb[43]),
            v_6_3=cls.parse_int(frageb[44]),
            v_6_4=cls.parse_int(frageb[45]),
            v_6_5=cls.parse_int(frageb[46]),
            v_6_6=cls.parse_int(frageb[47]),

            v_8_1=cls.parse_extrazeit(frageb[50]),
            v_8_4=cls.parse_geschwindigkeit16(frageb[53]),
        )
