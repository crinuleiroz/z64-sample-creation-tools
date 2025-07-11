import os
import sys
import struct
import subprocess
from dataclasses import dataclass

# Import utility modules/scripts
try:
    from utils.SysMsg import SystemMessages
    from utils.WaveFile import WaveFile
    from utils.XMLBank import XMLBank
except ImportError as e:
    raise ImportError(f'Required utility module is missing: {e.name}. Please ensure all utility scripts are properly located in the "utils" folder.')

"""
Most recent changes: 2025.03.13

MULTI-SAMPLE INSTRUMENTS:
  Added functionality for dragging and dropping entire folders. Not tested much, and is recursive.
  However, with this new functionality, if there are <= 3 samples in a folder it will be marked as a
  multi-sample instrument and a bank with the samples attached to a single instrument will be created.
  This feature was only really tested to ensure it was working, and has not been extensively tested.
  Instruments should automatically order samples going from lowest sample to highest sample based on
  their root note.

  A word of warning, there is no check to make sure the samples are linked in any way other than them
  being in the same folder when there are <= 3 samples. So if you have subfolders in the directory, then
  it will go through each directory. As such, be careful when using this feature.

UTILITY SCRIPTS:
  In order to keep the code clean and organized (somewhat), some scripts that are mainly for utility have
  been added into a "utils" folder. If the script cannot import the utilities, then it will throw an error.
  This is not modularity, none of the utility scripts do anything on their own.
"""

FILES = sys.argv[1:]

# Sample defaults
DEFAULT_SAMPLE_RATE = 32000
DEFAULT_ROOT_NOTE = 60

"""
#-----------------------#
#         CLASS         #
#-----------------------#
"""
@dataclass
class Sample:
    name: str
    size: str
    sample_rate: int
    root_note: int
    chan_tune: int
    key_tune: int
    temp_addr: int
    loop_start: int
    loop_end: int
    num_samples: int
    codebook_predictors: list[list[int]]
    loopbook_predictors: list[int]


class FileProcessor:
    def __init__(self, files: list) -> None:
        self.files = files

    def process_file(self, outfolder: str, file: str) -> None:
        filename, fileext, filepath = self.prepare_file(file)

        if self.validate_file(outfolder, filename, fileext):
            return

        sample_rate, root_note, chan_tune, key_tune, loop_start, loop_end, num_wav_samples = self.process_audio_file(filename, filepath)

        bin_file = f'{filename}.vadpcm.bin'
        codebook = f'{filename}.book.bin'
        loopbook = f'{filename}.loopbook.bin'

        # Create the zsound file and convert the ADPCM predictors to XML
        SystemMessages.renaming_sample(bin_file)
        temp_addr = create_temp_addr()
        zsound = f'{filename.replace('_', '-').replace(' ', '-')}_{temp_addr.upper()}.zsound'
        os.rename(bin_file, zsound)

        if os.path.exists(loopbook):
            SystemMessages.converting_predictors(codebook, loopbook)
            codebook_predictors, loopbook_predictors = self.convert_predictors(codebook, loopbook)
        else:
            SystemMessages.converting_predictors(codebook)
            codebook_predictors, loopbook_predictors = self.convert_predictors(codebook)

        sample_file = Sample(
            name=filename,
            size=os.path.getsize(zsound),
            sample_rate=sample_rate,
            root_note=root_note,
            chan_tune=chan_tune,
            key_tune=key_tune,
            temp_addr=temp_addr,
            loop_start=loop_start,
            loop_end=loop_end,
            num_samples=num_wav_samples,
            codebook_predictors=codebook_predictors,
            loopbook_predictors=loopbook_predictors
        )

        return sample_file, codebook, loopbook, zsound

    @staticmethod
    def check_for_outfolder(outfolder: str) -> bool:
        """
        Validates the folder containing sample files does not already exist.
        """
        if os.path.isdir(outfolder):
            SystemMessages.existing_folder(outfolder)
            return True

        return False

    @staticmethod
    def prepare_file(file: str) -> tuple[str, str, str]:
        """
        Extracts path related data from file, and sets up outfolder path.
        """
        filename = os.path.splitext(os.path.basename(file))[0]
        fileext = os.path.splitext(os.path.basename(file))[1]
        filepath = os.path.abspath(file)

        return filename, fileext, filepath

    @staticmethod
    def validate_file(outfolder: str, file: str, fileext: str) -> bool:
        """
        Validates the file being processed is WAV and has not already been processed.
        """
        if fileext != '.wav':
            SystemMessages.handle_non_wav_file()
            return True

        if os.path.exists(os.path.join(outfolder, file)):
            SystemMessages.existing_file(file)
            return True

        return False

    def process_audio_file(self, filename: str, filepath: str) -> None:
        audio_processor = AudioProcessor(filepath)
        sample_rate, root_note, loop_start, loop_end, num_samples = audio_processor.extract_wave_data()
        chan_tune, key_tune = audio_processor.calc_tuning()

        SystemMessages.z64audio_start(filepath, filename)
        audio_processor.run_z64audio(filename)

        return sample_rate, root_note, chan_tune, key_tune, loop_start, loop_end, num_samples

    @staticmethod
    def convert_predictors(codebook: str, *loopbook: str) -> None:
        predictor_files = [
            (codebook, 'codebook')] + [(loopbook[0],
            'loopbook')] if loopbook else [(codebook, 'codebook')
        ]

        codebook_predictors = []
        loopbook_predictors = []

        for filepath, filetype in predictor_files:
            try:
                with open(filepath, 'rb') as file:
                    file_buffer = file.read()

                    iter_index = 8 if filetype == 'codebook' else 0
                    current_group = []

                    for iter_data in struct.iter_unpack('>h', file_buffer[iter_index:]):
                        number = iter_data[0]

                        if filetype == 'codebook':
                            current_group.append(number)

                            if len(current_group) == 16:
                                codebook_predictors.append(current_group)
                                current_group = []

                        else:
                            loopbook_predictors.append(number)

                        iter_index += 2

            except FileNotFoundError:
                raise FileNotFoundError(f'{file} not found!')
            except Exception as e:
                print(f'An error occurred with {file}: {e}')

        return codebook_predictors, loopbook_predictors

    def cleanup_files(self, codebook: str, loopbook: str) -> None:
        """
        Remove temporary and unecessary files created by the script and z64audio.
        """
        os.remove('config.toml')
        os.remove(codebook)
        try:
            os.remove(loopbook)
        except FileNotFoundError:
            pass

    def move_processed_files(self, outfolder: str, filename: str, zsound: str) -> None:
        """
        Moves processed sample file into the output folder.
        """
        os.rename(zsound, os.path.join(outfolder, zsound))

    def move_bank_xml(self, outfolder: str, filename: str) -> None:
        os.rename(f'{filename}_BANK.xml', os.path.join(
            outfolder, f'{filename}_BANK.xml'))

    def process_directory(self, file, outfolder=None):
        filename = os.path.basename(file.rstrip('/'))
        basefolder = os.path.join(os.path.dirname(os.path.realpath(__file__)))
        outfolder = f'{basefolder}/WAV to ZSOUND - {filename}'

        if self.check_for_outfolder(outfolder):
            return

        dir_files = next(os.walk(file))[2]

        if len(dir_files) <= 3:
            processed_samples = []
            SystemMessages.processing_multi(file)

            for f in dir_files:
                SystemMessages.processing_file(f)
                filepath = os.path.abspath(os.path.join(file, f))
                result = self.process_file(outfolder, filepath)

                if result is None:
                    continue

                sample, codebook, loopbook, zsound = result

                SystemMessages.moving_files(outfolder)
                os.makedirs(outfolder, exist_ok=True)

                self.cleanup_files(codebook, loopbook)
                self.move_processed_files(outfolder, f, zsound)
                processed_samples.append(sample)

                SystemMessages.sample_processed()

            SystemMessages.writing_xml_bank(filename)
            write_bank(filename, *processed_samples)

            SystemMessages.moving_files(outfolder)
            self.move_bank_xml(outfolder, filename)
            SystemMessages.multi_sample_processed(outfolder)

        else:
            SystemMessages.processing_folder(file)
            for f in dir_files:
                SystemMessages.processing_file(f)
                filepath = os.path.abspath(os.path.join(file, f))
                name = os.path.splitext(f)[0]
                result = self.process_file(outfolder, filepath)

                if result is None:
                    continue

                sample, codebook, loopbook, zsound = result

                SystemMessages.moving_files(f'{outfolder}/{name}')
                os.makedirs(outfolder, exist_ok=True)

                self.cleanup_files(codebook, loopbook)
                self.move_processed_files(outfolder, f, zsound)

                SystemMessages.writing_xml_bank(name)
                write_bank(name, sample)
                self.move_bank_xml(outfolder, filename)
                SystemMessages.sample_processed()

        for dirpath, dirnames, filenames in os.walk(file):
            for dirname in dirnames:
                subfolder = os.path.join(dirpath, dirname)
                self.process_directory(subfolder, outfolder)

    def process_all_files(self) -> None:
        """
        Process every file in the files list.
        """
        SystemMessages.header()

        for file in self.files:
            if os.path.isdir(file):
                self.process_directory(file)

            else:
                filename = os.path.splitext(os.path.basename(file))[0]
                basefolder = os.path.join(os.path.dirname(os.path.realpath(__file__)))
                outfolder = f'{basefolder}/WAV to ZSOUND - {filename}'

                SystemMessages.processing_file(file)
                if self.check_for_outfolder(outfolder):
                    continue

                result = self.process_file(outfolder, file)

                if result is None:
                    continue

                sample, codebook, loopbook, zsound = result

                SystemMessages.moving_files(outfolder)
                # Create output folder if it does not exist
                os.makedirs(outfolder, exist_ok=True)

                self.cleanup_files(codebook, loopbook)
                self.move_processed_files(outfolder, file, zsound)

                SystemMessages.writing_xml_bank(filename)
                write_bank(filename, sample)
                self.move_bank_xml(outfolder, filename)

                SystemMessages.sample_processed()

        SystemMessages.completion()
        os.system('pause')


class AudioProcessor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.wave_data = None
        self.sample_rate = None
        self.root_note = None
        self.num_samples = None

    def extract_wave_data(self) -> tuple[int, int]:
        """
        Extracts the sample rate and MIDI unity note from a WAV file.
        Also ensures that z64audio will properly handle the sample.
        """
        wav = WaveFile(self.filepath)

        try:
            wav.open()
        except FileNotFoundError:
            raise FileNotFoundError(f'Cannot find WAV file: {self.filepath}')
        except Exception as e:
            raise RuntimeError(
                f'An error occurred while extracting WAV data: {e}')

        wav.parse_wave()

        # Ensure Polyphone did not ruin the sample before sending it to z64audio
        if wav.smpl_chunk:
            if wav.smpl_chunk.loops[0].loop_start == 0x00000000 and wav.smpl_chunk.loops[0].loop_end == 0xFFFFFFFF:
                wav.fix_loop()
                wav.save()

        wav.close()

        self.sample_rate = wav.fmt_chunk.sample_rate
        self.root_note = wav.smpl_chunk.midi_unity_note if wav.smpl_chunk else DEFAULT_ROOT_NOTE
        self.loop_start = wav.smpl_chunk.loops[0].loop_start if wav.smpl_chunk else 0
        self.loop_end = wav.smpl_chunk.loops[0].loop_end if wav.smpl_chunk else 0
        self.num_samples = wav.data_chunk.chunk_size // (wav.fmt_chunk.num_channels * wav.fmt_chunk.bits_per_sample // 8)

        # Ensure Polyphone will not ruin the tuning of the sample
        if self.root_note != DEFAULT_ROOT_NOTE:
            self.root_note = self.detect_pitch_from_wave(self.filepath, self.root_note)

        return self.sample_rate, self.root_note, self.loop_start, self.loop_end, self.num_samples

    @staticmethod
    def detect_pitch_from_wave(wave, root_note: int) -> int:
        """
        Tries to call the modules and return the root note of the pitch detected in the WAV file.
        If it can not it returns the root note inptu into the function.
        """
        try:
            import numpy as np
            import scipy.io.wavfile as wavfile
            return __class__.detect_pitch(wave) if root_note != 60 else root_note
        except ImportError:
            return root_note
        except Exception as e:
            print(f'Error detecting pitch: {e}')
            return root_note

    @staticmethod
    def hz_to_root(hz):
        """
        Converts the dominant hz frequency of the WAV file to a midi note number.
        """
        import numpy as np

        midi_note = 69 + 12 * np.log2(hz / 440)
        return round(midi_note)

    @staticmethod
    def detect_pitch(filepath):
        """
        Detects the frequency of a WAV file using the fast fourier transform.
        """
        import numpy as np
        import scipy.io.wavfile as wavfile
        import warnings

        # Scipy does not support anything other than RIFF, fmt, data, and LIST chunks
        # so skip warnings about unknown chunks from wavefile.read()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            sample_rate, data = wavfile.read(filepath)

        if len(data.shape) == 2:
            data = data.mean(axis=1)

        data = np.array(data, np.float32)
        data = data / np.max(np.abs(data), axis=0)

        n = len(data)
        freqs = np.fft.fftfreq(n, 1 / sample_rate)
        fft_values = np.fft.fft(data)

        positive_freqs = freqs[:n//2]
        positive_fft_values = np.abs(fft_values[:n//2])

        dominant_freq = positive_freqs[np.argmax(positive_fft_values)]

        note = __class__.hz_to_root(dominant_freq)

        return note

    def calc_tuning(self) -> tuple[float]:
        """
        Calculates the tuning float value used by the Nintendo 64 to pitch shift samples.
        """
        # Channel-based Instrument tuning value, higher pitch > 1 and lower pitch is < 1
        # Key-based Intrument tuning value, higher pitch is < 1 and lower pitch is > 1
        # Math is hard sometimes...
        chan_tune = pow(2, (self.root_note - 60) / -12) * (self.sample_rate / 32000)
        key_tune = pow(2, (0 / 12)) * (self.sample_rate / 32000)

        return chan_tune, key_tune

    def run_z64audio(self, filename: str) -> None:
        """
        Invokes z64audio with the terminal.
        """
        try:
            subprocess.run(
                [
                    'z64audio', '-i', self.filepath, '-o',
                    f'{filename}.bin', '-I', '50'
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            print(f'Error during z64audio execution: {e.stderr.decode()}')
        except FileNotFoundError:
            print(f'Error: z64audio executable not found.')
        except Exception as e:
            print(f'An unexpected error occured: {e}')


"""
#-----------------------#
#       FUNCTIONS       #
#-----------------------#
"""
def create_temp_addr() -> str:
    """
    Creates a random temp address for a custom sample.
    """
    rand = int.from_bytes(os.urandom(4), byteorder="big")

    # Ensure the random number is within a safe range, this caps at 0x7FFFFFFF
    # because seq64 signs u32 values for whatever reason...
    temp_addr = (0x10000000 + (rand % (0x7FFFFFFF - 0x10000000 + 1)))

    return temp_addr.to_bytes(4, "big").hex()

# Unsure if I want this in the FileProcessor class or not...


def write_bank(filename: str, *samples) -> None:
    """
    Writes a template bank for the converted WAV file for use with seq64.
    """

    sorted_samples = sorted(samples, key=lambda x: x.root_note)

    low_sample, prim_sample, high_sample = (
        sorted_samples[0] if len(sorted_samples) > 1 else None,
        sorted_samples[1] if len(sorted_samples) > 1 else sorted_samples[0],
        sorted_samples[2] if len(sorted_samples) > 2 else None,
    )

    num_samples = 3 if low_sample and high_sample else 2 if low_sample or high_sample else 1

    bank = XMLBank(num_samples, low_sample, prim_sample, high_sample)
    bank.create_xml_bank(filename)


def main() -> None:
    processor = FileProcessor(FILES)
    processor.process_all_files()


if __name__ == '__main__':
    main()
