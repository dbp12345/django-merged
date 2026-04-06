# This file is distributed under the same license as the Django package.
#
# The *_FORMAT strings use the Django date format syntax,
# see https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date

# Formatting for date objects.
DATE_FORMAT = "m/d/Y"
# Formatting for time objects.
# TIME_FORMAT = "P"
TIME_FORMAT = "H:i"
# Formatting for datetime objects.
# DATETIME_FORMAT = "N j, Y, P"
DATETIME_FORMAT = "m/d/Y H:i"
# Formatting for date objects when only the year and month are relevant.
YEAR_MONTH_FORMAT = "F Y"
# Formatting for date objects when only the month and day are relevant.
MONTH_DAY_FORMAT = "F j"
# Short formatting for date objects.
SHORT_DATE_FORMAT = "m/d/Y"
# Short formatting for datetime objects.
# SHORT_DATETIME_FORMAT = "m-d-Y P"
SHORT_DATETIME_FORMAT = "m/d/Y H:i"
# First day of week, to be used on calendars.
# 0 means Sunday, 1 means Monday...
FIRST_DAY_OF_WEEK = 1

# Formats to be used when parsing dates from input boxes, in order.
# The *_INPUT_FORMATS strings use the Python strftime format syntax,
# see https://docs.python.org/library/datetime.html#strftime-strptime-behavior
# Note that these format strings are different from the ones to display dates.
# Kept ISO formats as they are in first position
DATE_INPUT_FORMATS = [
    # "%m-%d-%Y",
    "%m/%d/%Y",
    # "%m-%d-%Y %H:%M",
    # "%m-%d-%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    # "%m/%d/%Y %H:%M:%S",
]
DATETIME_INPUT_FORMATS = [
    # "%m-%d-%Y",
    "%m/%d/%Y",
    # "%m-%d-%Y %H:%M",
    # "%m-%d-%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    # "%m/%d/%Y %H:%M:%S",
]
TIME_INPUT_FORMATS = [
    # "%H:%M:%S",  # '14:30:59'
    # "%H:%M:%S.%f",  # '14:30:59.000200'
    "%H:%M",  # '14:30'
]

# Decimal separator symbol.
DECIMAL_SEPARATOR = "."
# Thousand separator symbol.
THOUSAND_SEPARATOR = ","
# Number of digits that will be together, when splitting them by
# THOUSAND_SEPARATOR. 0 means no grouping, 3 means splitting by thousands.
NUMBER_GROUPING = 3
