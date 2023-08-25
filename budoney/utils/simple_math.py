def calculate(expression: str) -> float:
    expression = expression.replace(" ", "")
    splitted = expression.split("+")
    sum = 0
    for part in splitted:
        if part.isnumeric():
            sum += float(part)
    return sum
