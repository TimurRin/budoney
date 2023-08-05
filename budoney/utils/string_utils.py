def edits1(word: str) -> "set[str]":
    "All edits that are one edit away from `word`."
    letters = "abcdefghijklmnopqrstuvwxyz"
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes: list[str] = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)


def sql_search(word: str) -> "set[str]":
    print(word)
    if len(word) == 1:
        return set(word)
    original = [word]
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    print("splits", splits)
    deletes = len(word) > 2 and [L + R[1:] for L, R in splits if R] or []
    print("deletes", deletes)
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    print("transposes", transposes)
    replaces = [L + "_" + R[1:] for L, R in splits if R]
    print("replaces", replaces)
    inserts = [L + "_" + R for L, R in splits]
    print("inserts", inserts)

    replaces2 = len(word) > 2 and [L + "__" + R[2:] for L, R in splits if R] or []
    print("replaces2", replaces2)
    replaces3 = len(word) > 2 and [L + "_" + R[2:] for L, R in splits if R] or []
    print("replaces3", replaces3)

    inserts2 = [L + "__" + R for L, R in splits]
    print("inserts2", inserts2)
    total = set(
        original + deletes + transposes + replaces + inserts
        # + replaces2 + replaces3 + inserts2
    )
    print(total)
    return total
