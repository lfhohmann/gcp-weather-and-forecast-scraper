def convert_inches_to_hpa(inches):
    return round(inches * 33.86, 2)


def convert_inches_to_mm(inches):
    return round(inches * 25.4, 2)


def convert_mph_to_kph(mph):
    return round(mph * 1.6, 1)


def convert_kph_to_mph(mph):
    return round(mph / 1.6, 1)


def convert_f_to_c(f):
    return round((f - 32) * (5 / 9), 1)


def convert_c_to_f(c):
    return round(c * (9 / 5) + 32, 1)
