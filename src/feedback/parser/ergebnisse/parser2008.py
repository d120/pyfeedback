# coding = utf-8

from feedback.models import Fragebogen2008
from feedback.parser.ergebnisse.parser import Parser


class Parser2008(Parser):
    @classmethod
    def create_fragebogen(cls, veranst, frageb):
        Fragebogen2008.objects.create(
            veranstaltung=veranst,
            fach=cls.parse_fach(frageb[1]),
            abschluss=cls.parse_abschluss(frageb[3]),
            semester=cls.parse_int(frageb[4]),
            v_wie_oft_besucht=cls.parse_int(frageb[5]),
            v_besuch_qualitaet=cls.parse_boolean(frageb[6]),
            v_besuch_privat=cls.parse_boolean(frageb[7]),
            v_besuch_sonstiges=cls.parse_boolean(frageb[8]),
            v_besuch_verhaeltnisse=cls.parse_boolean(frageb[9]),
            v_besuch_ueberschneidung=cls.parse_boolean(frageb[10]),
            v_a=cls.parse_int(frageb[12]),
            v_b=cls.parse_int(frageb[13]),
            v_c=cls.parse_int(frageb[14]),
            v_d=cls.parse_int(frageb[15]),
            v_e=cls.parse_int(frageb[16]),
            v_f=cls.parse_int(frageb[17]),
            v_f2=cls.parse_geschwindigkeit(frageb[18]),
            v_g=cls.parse_int(frageb[19]),
            v_h=cls.parse_int(frageb[20]),
            v_i=cls.parse_int(frageb[21]),
            v_j=cls.parse_int(frageb[22]),
            v_k=cls.parse_int(frageb[23]),
            v_l=cls.parse_int(frageb[24]),
            v_m=cls.parse_int(frageb[25]),
            v_gesamt=cls.parse_int(frageb[26]),
            ue_wie_oft_besucht=cls.parse_int(frageb[27]),
            ue_besuch_ueberschneidung=cls.parse_boolean(frageb[28]),
            ue_besuch_qualitaet=cls.parse_boolean(frageb[29]),
            ue_besuch_verhaeltnisse=cls.parse_boolean(frageb[30]),
            ue_besuch_privat=cls.parse_boolean(frageb[31]),
            ue_besuch_sonstiges=cls.parse_boolean(frageb[32]),
            ue_a=cls.parse_int(frageb[34]),
            ue_b=cls.parse_int(frageb[35]),
            ue_c=cls.parse_int(frageb[36]),
            ue_d=cls.parse_int(frageb[37]),
            ue_e=cls.parse_int(frageb[38]),
            ue_f=cls.parse_int(frageb[39]),
            ue_g=cls.parse_int(frageb[40]),
            ue_h=cls.parse_int(frageb[41]),
            ue_i=cls.parse_int(frageb[42]),
            ue_i2=cls.parse_niveau(frageb[43]),
            ue_j=cls.parse_int(frageb[44]),
            ue_gesamt=cls.parse_int(frageb[45]),
            zusaetzliche_zeit=cls.parse_int(frageb[46]),
            vorwissen_aussreichend=cls.parse_int(frageb[47]),
            empfehlung=cls.parse_empfehlung(frageb[48]),
        )
