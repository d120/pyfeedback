from csv import reader, Sniffer
from typing import Dict, List

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
        if row[0] not in data:
            data[row[0]] = [tan]
        else:
            data[row[0]].append(tan)

    return data