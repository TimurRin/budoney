def calculate(expression: str) -> float:
    expression = expression.replace(" ", "")
    splitted = expression.split("+")
    sum = 0
    print("calculate", "expression", expression, "splitted", splitted)
    for part in splitted:
        try:
            sum += float(part)
        except:
            pass
    return sum
