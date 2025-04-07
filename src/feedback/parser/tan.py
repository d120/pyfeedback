from csv import reader, Sniffer
from typing import Dict, List
import re

def parse(csv: bytes) -> Dict[str, List[str]]:
    data: Dict[str, List[str]] = {}
    csvfile = csv.read().decode('utf-8')
    dialect = Sniffer().sniff(csvfile[0:1024])
    csvreader = reader(csvfile.split("\n")[1:], dialect)
    data: Dict[str, List[str]] = {}
    for row in csvreader:
        if row == []:
            break
        tan = ''
        # is this a TAN lecture?
        if row[2] != '':
            # short tan is in the third field
            tan = row[2]
        else:
            # codewords are saved in the second field
            tan = row[1]
        
        pattern = r"\(\d{2}-\d{2}-.*\)"

        dic = {
            "&amp;" : "&",
            "&auml;" : "ä",
            "&Auml;" : "Ä",
            "&ouml;" : "ö",
            "&Ouml;" : "Ö",
            "&uuml;" : "ü",
            "&Uuml;" : "Ü",
            "&szlig;" : "ß",
        }

        # remove suffix with modul number
        row_0 = re.sub(pattern, "", row[0]).strip()

        # replace html characters
        for ch in dic.keys() :
            if ch in row_0 :
                row_0 = row_0.replace(ch, dic.get(ch))

        if row_0 not in data:
            data[row_0] = [tan]
        else:
            data[row_0].append(tan)

    return data