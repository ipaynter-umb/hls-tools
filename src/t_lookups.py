# Exceptions
# If you reach row C, and column is <= 30, check for tile A
# If column is > 30, check tile B

# If you reach row X, and column is <= 30, check for tile Y
# If column is > 30, check tile Z

# A dictionary of exceptions where you want to check additional tiles, or tiles counter-intuitive to the overall order
to_check_northwards = {
    '31U': ['31V', '32V'],
    '32V': ['31W', '32W'],
    '32W': ['31X', '33X'],
    '34W': ['33X', '35X'],
    '36W': ['35X', '37X']
}

to_check_southwards = {
    '31X': ['31W', '32W'],
    '33X': ['32W', '33W', '34W'],
    '35X': ['34W', '35W', '36W'],
    '37X': ['36W', '37W'],
    '31W': ['31V', '32V']
}

to_check_eastwards = {
    '31X': ['33X'],
    '33X': ['35X'],
    '35X': ['37X']
}

to_check_westwards = {
    '37X': ['35X'],
    '35X': ['33X'],
    '33X': ['31X']
}

westward_intermajor_minor = {}

eastward_intermajor_minor = {}

southward_intermajor_minor = {}

northward_intermajor_minor = {}
