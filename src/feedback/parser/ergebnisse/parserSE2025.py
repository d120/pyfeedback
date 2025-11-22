
# coding = utf-8

from feedback.models import FragebogenSE2025
from feedback.parser.ergebnisse.parser import Parser


class ParserSE2025(Parser):
    @classmethod
    def create_fragebogen(cls, veranst, frageb):
        FragebogenSE2025.objects.create(
            veranstaltung=veranst,
            fach=cls.parse_fach_16(frageb[1]),
            abschluss=cls.parse_abschluss_16(frageb[3]),
            semester=cls.parse_semester_16(frageb[4]),
            geschlecht=cls.parse_geschlecht_16(frageb[5]),
            studienberechtigung=cls.parse_studienberechtigung(frageb[6]),
            male_veranstaltung_gehoert=cls.parse_veranstaltung_gehoert(frageb[7]),

            s_wie_oft_besucht=cls.parse_int(frageb[8]),
            s_besuch_ueberschneidung=cls.parse_boolean(frageb[9]),
            s_besuch_qualitaet=cls.parse_boolean(frageb[10]),
            s_besuch_verhaeltnisse=cls.parse_boolean(frageb[11]),
            s_besuch_privat=cls.parse_boolean(frageb[12]),
            s_besuch_elearning=cls.parse_boolean(frageb[13]),
            s_besuch_zufrueh=cls.parse_boolean(frageb[14]),
            s_besuch_sonstiges=cls.parse_boolean(frageb[15]),

            s_3_1=cls.parse_int(frageb[17]),
            s_3_2=cls.parse_int(frageb[18]),
            s_3_3=cls.parse_int(frageb[19]),
            s_3_4=cls.parse_int(frageb[20]),
            s_3_6=cls.parse_int(frageb[21]),
            s_3_7=cls.parse_int(frageb[22]),
            s_3_8=cls.parse_int(frageb[23]),
            s_3_9=cls.parse_int(frageb[24]),
            s_3_10=cls.parse_int(frageb[25]),

            s_4_1=cls.parse_boolean(frageb[26]),
            s_4_2=cls.parse_int(frageb[27]),
            s_4_3=cls.parse_int(frageb[28]),
            s_4_4=cls.parse_int(frageb[29]),
            s_4_5=cls.parse_int(frageb[30]),
            s_4_6=cls.parse_extrazeit(frageb[31]),

            s_5_1=cls.parse_boolean(frageb[32]),
            s_5_2=cls.parse_int(frageb[33]),
            s_5_3=cls.parse_int(frageb[34]),
            s_5_4=cls.parse_int(frageb[35]),
            s_5_5=cls.parse_int(frageb[36]),
            s_5_6=cls.parse_int(frageb[37]),
            s_5_7=cls.parse_extrazeit(frageb[38]),

            s_6_1=cls.parse_int(frageb[39]),
            s_6_2=cls.parse_int(frageb[40]),
            s_6_3=cls.parse_int(frageb[41]),
            s_6_4=cls.parse_int(frageb[42]),
            s_6_5=cls.parse_int(frageb[43]),
            s_6_6=cls.parse_int(frageb[44]),
            s_6_7=cls.parse_int(frageb[45]),
            s_6_8=cls.parse_int(frageb[46]),
            s_6_9=cls.parse_int(frageb[47]),
            s_6_10=cls.parse_int(frageb[48]),

            s_7_1=cls.parse_int(frageb[49]),
            s_7_2=cls.parse_int(frageb[50]),

            s_9_1=cls.parse_niveau(frageb[54]),
            s_9_2=cls.parse_niveau(frageb[55]),
            s_9_3=cls.parse_niveau(frageb[56]),
            s_9_4=cls.parse_int(frageb[57]),
            s_9_5=cls.parse_int(frageb[58]),
        )
