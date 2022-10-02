def chunk_list(lst, chunksize):
    return [lst[i:i + chunksize] for i in range(0, len(lst), chunksize)]


def flatten_list(lst):
    return [subitem for item in lst for subitem in item]
