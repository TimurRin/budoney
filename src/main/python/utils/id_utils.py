import utils.transliterate as transliterate
import math
import re


def generate_id(data: dict, name: str):
    # int(math.log10(n))+1

    transliterated = transliterate.russian_to_latin(name).upper()
    code = re.sub(r"[^A-Z0-9]+", "", transliterated)
    id = code[:14]
    id_len = len(id)

    if id not in data:
        return id
    else:
        loop = 0
        while loop <= 9999999:
            digits = loop > 0 and (int(math.log10(loop)) + 1) or 1
            temp_id = None
            if id_len + digits > 7:
                temp_id = id[:-digits] + str(loop)
            else:
                temp_id = id + str(loop)
            if temp_id not in data:
                return temp_id
            else:
                loop = loop + 1
