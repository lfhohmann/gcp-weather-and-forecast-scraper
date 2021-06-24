def mph_to_kmph(mph):
    # Converts Miles per Hour to Kilometers per Hour
    return round(mph * 1.6, 1)


def kmph_to_mph(kmph):
    # Converts Kilometers per Hour to Miles per Hour
    return round(kmph / 1.6, 1)


def f_to_c(f):
    # Converts Farenheit to Celsius
    return round((f - 32) * (5 / 9), 1)


def c_to_f(c):
    # Converts Celsius to Farenheit
    return round(c * (9 / 5) + 32, 1)
