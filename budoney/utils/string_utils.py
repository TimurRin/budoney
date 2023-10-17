def edits1(word: str) -> "set[str]":
    "All edits that are one edit away from `word`."
    letters = "abcdefghijklmnopqrstuvwxyz"
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes: list[str] = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)


def sql_search(word: str) -> "list[str]":
    print("sql_search", word)
    if len(word) == 1:
        return list(word)
    original = [word]
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    print("sql_search", "splits", splits)
    deletes = len(word) > 2 and [L + R[1:] for L, R in splits if R] or []
    print("sql_search", "deletes", deletes)
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    print("sql_search", "transposes", transposes)
    replaces = [L + "_" + R[1:] for L, R in splits if R]
    print("sql_search", "replaces", replaces)
    inserts = [L + "_" + R for L, R in splits]
    print("sql_search", "inserts", inserts)

    replaces2 = len(word) > 2 and [L + "__" + R[2:] for L, R in splits if R] or []
    print("sql_search", "replaces2", replaces2)
    replaces3 = len(word) > 2 and [L + "_" + R[2:] for L, R in splits if R] or []
    print("sql_search", "replaces3", replaces3)

    inserts2 = [L + "__" + R for L, R in splits]
    print("sql_search", "inserts2", inserts2)

    total = list(set(
        original
        + deletes
        + transposes
        + replaces
        + inserts
        + replaces2
        + replaces3
        + inserts2
    ))
    print("sql_search", total)
    return total
