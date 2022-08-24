abcCyr = [
    'а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у',
    'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я',
    'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У',
    'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Б', 'Э', 'Ю', 'Я'
]

abcLat = [
    "a", "b", "v", "g", "d", "e", "yo", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r", "s", "t",
    "u", "f", "kh", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "A", "B", "V", "G", "D", "E", "Yo",
    "Zh", "Z", "I", "Y", "K", "L", "M", "N", "O", "P", "R", "S", "T", "U", "F", "Kh", "Ts", "Ch", "Sh", "Sch",
    "", "Y", "", "E", "Yu", "Ya"
]


def russian_to_latin(message: str):
    builder = ""
    for i in range(len(message)):
        applied = False
        for x in range(len(abcCyr)):
            if message[i] == abcCyr[x]:
                builder = builder + abcLat[x]
                applied = True
                break
        if not applied:
            builder = builder + str(message[i])
    return str(builder)
