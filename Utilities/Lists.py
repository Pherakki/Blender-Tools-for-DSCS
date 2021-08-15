def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def flip_dict(dct):
    return {v: k for k, v in dct.items()}
