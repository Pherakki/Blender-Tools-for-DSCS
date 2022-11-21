def iter_bitvector(uint8_vector):
    for elem in uint8_vector:
        for bit_index in range(8):  # or range(7, 0, -1)
            yield (elem & bit_index) >> bit_index


def chunk_bitvector(uint8_vector, chunksize):
    total_bits = len(uint8_vector)*8
    chunk_count = (total_bits) // chunksize
    remainder = total_bits - (chunk_count*chunksize)
    bitvector_iterator = iter_bitvector(uint8_vector)
    for _ in range(chunk_count):
        yield [next(bitvector_iterator) for _ in range(chunksize)]
    yield [next(bitvector_iterator) for _ in range(remainder)]
