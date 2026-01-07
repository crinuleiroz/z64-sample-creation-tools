from pathlib import Path
from datetime import datetime, timezone

from .audio_processor import AudioProcessor
from .models import InstrumentData, DrumData, EffectData, SampleData
from .helpers import calc_tuning, create_temp_address
from .pitch_detection import detect_pitch_from_wav
from .xml_bank import XMLBank


class FileProcessor:
    def __init__(
        self,
        base_folder: Path,
        out_folder: Path,
        sample_container: InstrumentData | DrumData | EffectData
    ) -> None:
        self.sample_container: InstrumentData | DrumData | EffectData = sample_container
        self.auto_detect_pitch: bool = sample_container.auto_detect_pitch
        self.tuning_type: str = sample_container.tuning_type

        # Folders
        self.base_folder: Path = base_folder
        self.out_folder: Path = out_folder

    def cleanup_files(self, vadpcm_book_file: Path, vadpcm_loop_file: Path | None) -> None:
        config = self.base_folder / 'config.toml'
        if config.exists():
            config.unlink()

        if vadpcm_book_file.exists():
            vadpcm_book_file.unlink()

        if vadpcm_loop_file and vadpcm_loop_file.exists():
            vadpcm_loop_file.unlink()

    def process_audio_file(
        self,
        tuning_type: str,
        prim_sample: SampleData,
        low_sample: SampleData = None,
        high_sample: SampleData = None
    ) -> None:
        temp_address = create_temp_address()

        if prim_sample:
            prim_sample.sample.address = temp_address
        if low_sample:
            low_sample.sample.address = temp_address - 1
        if high_sample:
            high_sample.sample.address = temp_address + 1

        samples = [
            s for s in (low_sample, prim_sample, high_sample)
            if s is not None
        ]

        for s_data in samples:
            file_path = Path(s_data.path)
            file_name, _, _ = self.prepare_file(file_path)
            s_data.name = file_name

            a_processor = AudioProcessor(
                file_name,
                file_path,
                s_data.sample_rate,
                s_data.root_key,
            )

            (
                s_data.sample_rate,
                s_data.root_key,
                s_data.sample.loop_start,
                s_data.sample.loop_end,
                s_data.sample.num_samples,
            ) = a_processor.extract_wav_data()

            if self.auto_detect_pitch:
                s_data.root_key = detect_pitch_from_wav(
                    file_path,
                    s_data.root_key,
                )

            s_data.sample.tuning = calc_tuning(
                tuning_type,
                s_data.sample_rate,
                s_data.root_key,
                s_data.coarse_tune,
                s_data.fine_tune,
            )

            a_processor.run_z64audio()

            vadpcm_bin = self.base_folder / f'{file_name}.vadpcm.bin'
            vadpcm_book = self.base_folder / f'{file_name}.book.bin'
            vadpcm_loop = self.base_folder / f'{file_name}.loopbook.bin'

            vadpcm_loop = vadpcm_loop if vadpcm_loop.exists() else None

            s_data.sample.size = vadpcm_bin.stat().st_size

            # target = self.out_folder / f'{file_name}.zsound'
            target = self.out_folder / f'{file_name}_{s_data.sample.address:X}.zsound'
            vadpcm_bin.rename(target)

            (
                s_data.sample.vadpcm_book_pred,
                s_data.sample.vadpcm_loop_pred,
            ) = self.process_vadpcm_predictor_coefficients(
                vadpcm_book,
                vadpcm_loop,
            )

            self.cleanup_files(vadpcm_book, vadpcm_loop)

    def process_files(self) -> None:
        # TODO: Move this and cleanup when/how data is processed
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
        if isinstance(self.sample_container, InstrumentData):
            name = self.sample_container.prim_sample.name
        elif isinstance(self.sample_container, DrumData):
            name = self.sample_container.sample.name
        elif isinstance(self.sample_container, EffectData):
            name = self.sample_container.sample.name

        self.out_folder: Path = self.out_folder / f"{name}_{timestamp}"
        self.out_folder.mkdir(parents=True, exist_ok=True)

        # Handle instruments
        if isinstance(self.sample_container, InstrumentData):
            self.process_audio_file(
                self.sample_container.tuning_type,
                self.sample_container.prim_sample,
                self.sample_container.low_sample,
                self.sample_container.high_sample,
            )

        # Handle drums
        if isinstance(self.sample_container, DrumData):
            self.process_audio_file(
                self.sample_container.tuning_type,
                self.sample_container.sample,
            )

        # Handle effects
        if isinstance(self.sample_container, EffectData):
            self.process_audio_file(
                self.sample_container.tuning_type,
                self.sample_container.sample,
            )

        XMLBank(self.out_folder, self.sample_container).create_bank()

    @staticmethod
    def check_for_outfolder(out_folder: Path) -> bool:
        return out_folder.is_dir()

    @staticmethod
    def prepare_file(file: Path) -> tuple[str, str, Path]:
        return file.stem, file.suffix, file.resolve()

    @staticmethod
    def process_vadpcm_predictor_coefficients(vadpcm_book_file: Path, vadpcm_loop_file: Path | None = None) -> tuple[list[list[int]], list[int]]:
        import struct

        predictor_files = [(vadpcm_book_file, 'vadpcm_book')]
        if vadpcm_loop_file:
            predictor_files.append((vadpcm_loop_file, 'vadpcm_loop'))

        vadpcm_book_predictors = []
        vadpcm_loop_predictors = []

        for f_path, f_type in predictor_files:
            try:
                with f_path.open('rb') as file:
                    file_buffer = file.read()

                iter_index = 8 if f_type == 'vadpcm_book' else 0
                current_group = []

                for value, in struct.iter_unpack('>h', file_buffer[iter_index:]):
                    if f_type == 'vadpcm_book':
                        current_group.append(value)
                        if len(current_group) == 16:
                            vadpcm_book_predictors.append(current_group)
                            current_group = []

                    elif f_type == 'vadpcm_loop':
                        vadpcm_loop_predictors.append(value)

            except FileNotFoundError:
                raise FileNotFoundError(f'{f_type} not found!')
            except Exception as ex:
                raise Exception(f'An error occurred with {f_type}: {ex}')

            return vadpcm_book_predictors, vadpcm_loop_predictors


if __name__ == '__main__':
    pass
