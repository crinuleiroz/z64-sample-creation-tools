'''
Helpers
=====
Extra utility functions.

Functions
-----
`create_temp_address()`:
  Imports `os` and generates a random signed 32-bit hex-formatted integer.

`calc_tuning()`:
  Calculates the tuning value for the given arguments.
'''


def create_temp_address() -> int:
    '''
    Imports `os` and generates a random signed 32-bit hex-formatted integer.

    Returns:
      temp_addr (str): Signed 32-bit hex-formatted integer.
    '''
    import os

    min_addr = 0x50000000
    max_addr = 0x7FFFFFFF
    range_size = max_addr - min_addr + 1

    rand = int.from_bytes(os.urandom(4), 'big')
    return min_addr + (rand % range_size)


def calc_tuning(tuning_type: str, sample_rate: int, root_key: int, coarse_tune: int, fine_tune: int) -> float:
    '''
    Calculates the tuning value for the given arguments.

    Args:
      tuning_type (str): The type of tuning, CHAN (channel-based tuning) or KEY (key-based tuning).
      sample_rate (int): The audio sample file's sample rate.
      root_key (int): The audio sample file's root key.
      coarse_tune (int): Semitone tuning adjustment.
      fine_tune (int): Cent tuning adjustment.

    Returns:
      tuning_value (float): The resulting tuning value.
    '''
    tuning_value = 1.0

    if tuning_type == 'CHAN':
        tuning_value = pow(2, ((root_key + coarse_tune - (0.01 * fine_tune)) - 60) / -12) * (sample_rate / 32000)
    if tuning_type == 'KEY':
        tuning_value = pow(2, (coarse_tune + (0.01 * fine_tune) / 12)) * (sample_rate / 32000)

    return tuning_value
