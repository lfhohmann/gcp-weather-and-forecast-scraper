def f_to_c(f):
    # Converts Farenheit to Celsius
    return round((f - 32) * (5 / 9), 1)


def c_to_f(c):
    # Converts Celsius to Farenheit
    return round(c * (9 / 5) + 32, 1)


def mph_to_kmph(mph):
    # Converts Miles per Hour to Kilometers per Hour
    return round(mph * 1.6, 1)


def mph_to_mps(mph):
    # Converts Miles per Hour to Meters per Second
    return round(mph / 2.237, 1)


def kmph_to_mph(kmph):
    # Converts Kilometers per Hour to Miles per Hour
    return round(kmph / 1.6, 1)


def kmph_to_mps(kmph):
    # Converts Kilometers per Hour to Miles per Hour
    return round(kmph / 3.6, 1)


def inches_to_hpa(inches):
    # Converts Inches of Mercury to Hectopascal
    return round(inches * 33.86, 2)


def inches_to_mm(inches):
    # Converts Inches to Milimeters
    return round(inches * 25.4, 2)
