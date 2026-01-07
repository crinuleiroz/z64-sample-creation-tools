'''
PitchDetection
=====
Offers a set of functions to detect the root key for a given `.wav` file using the Fast Fourier Transform (FFT).

Functions
-----
`hz_to_root()`:
  Converts a note's Hertz frequency value to its corresponding MIDI note value.

`detect_pitch()`:
  Uses the Fast Fourier Transform (FFT) to detect the dominant frequency for a given `.wav` file.

`detect_pitch_from_wav()`:
  Import wrapper for `detect_pitch()`.
'''

from pathlib import Path


def hz_to_root(hz: int) -> int:
    '''
    Converts a note's Hertz frequency value to its corresponding MIDI note value.

    Args:
      hz (int): The Hertz frequency value for a musical note.

    Returns:
      Corresponding MIDI note value.
    '''
    import numpy as np
    return round(69 + 12 * np.log2(hz / 440))


def detect_pitch(wav_file: Path) -> int:
    '''
    Uses the Fast Fourier Transform (FFT) to detect the dominant frequency for a given `.wav` file.

    Args:
      wav_file (str): The `.wav` file to calculate a root key for.

    Returns:
      The `.wav` file's root key as a MIDI note value.
    '''
    import numpy as np
    import scipy.io.wavfile as wavfile
    import warnings

    wav_file = wav_file.resolve()

    # Scipy does not support anything other than RIFF, fmt, data, and LIST chunks
    # So skip warnings about unknown chunks from wavfile.read()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        sample_rate, data = wavfile.read(wav_file)

    if data.ndim == 2:
        data = data.mean(axis=1)

    # if len(data.shape) == 2:
    #     data = data.mean(axis=1)

    data = np.array(data, np.float32)
    data = data / np.max(np.abs(data), axis=0)

    n = len(data)
    freqs = np.fft.fftfreq(n, 1 / sample_rate)
    fft_values = np.fft.fft(data)

    positive_freqs = freqs[:n // 2]
    positive_fft_values = np.abs(fft_values[:n // 2])

    dominant_freq = positive_freqs[np.argmax(positive_fft_values)]

    return hz_to_root(dominant_freq)


def detect_pitch_from_wav(wav_file: Path, root_key: int) -> int:
    '''
    Import wrapper for `detect_pitch()`.

    Args:
      wav_file (str): The `.wav` file to process.
      root_key (int): The value to return if the module import fails.

    Returns:
      root_key (int): The detected MIDI note, or the input root key if importing fails.
    '''
    try:
        return detect_pitch(wav_file)
    except ImportError:
        return root_key
    except Exception:
        return root_key


if __name__ == '__main__':
    pass
