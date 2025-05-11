import re

NATURAL_SORT_PATTERN = re.compile('([0-9]+)')


def natural_sort(l, accessor=lambda x: x):
    """
    Adapted from https://stackoverflow.com/a/4836734
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in NATURAL_SORT_PATTERN.split(key)]
    return sorted(l, key=lambda x: alphanum_key(accessor(x)))

