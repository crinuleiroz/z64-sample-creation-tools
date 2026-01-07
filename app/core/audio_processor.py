'''
Utility for handling audio files.
'''


from pathlib import Path


class AudioProcessor:
    def __init__(self, file_name: str, file_path: Path, sample_rate: int = -1, root_key: int = -1):
        self.file_name: str = file_name
        self.file_path: Path = file_path
        self.wav_data = None
        self.sample_rate: int = sample_rate
        self.root_key: int = root_key
        self.num_samples: int = 0

    def extract_wav_data(self) -> tuple[int, int, int, int, int]:
        from .wave_file import WaveFile

        wav = WaveFile(self.file_path)

        try:
            wav.open()
        except FileNotFoundError:
            raise FileNotFoundError()
        except Exception as ex:
            raise RuntimeError()

        wav.parse_wave()

        if wav.smpl_chunk:
            loop_start = wav.smpl_chunk.loops[0].loop_start
            loop_end = wav.smpl_chunk.loops[0].loop_end

            if loop_start == 0x00000000 and loop_end == 0xFFFFFFFF:
                wav.fix_loop()
                wav.save()

        wav.close()

        self.sample_rate = (
            self.sample_rate
            if self.sample_rate != -1
            else wav.fmt_chunk.sample_rate
        )
        self.root_key = (
            self.root_key
            if self.root_key != -1
            else wav.smpl_chunk.midi_unity_note if wav.smpl_chunk
            else 60
        )
        self.loop_start = wav.smpl_chunk.loops[0].loop_start if wav.smpl_chunk else 0
        self.loop_end = wav.smpl_chunk.loops[0].loop_end if wav.smpl_chunk else 0
        self.num_samples = (
            wav.data_chunk.chunk_size
            // (wav.fmt_chunk.num_channels * wav.fmt_chunk.bits_per_sample // 8)
        )

        return (
            self.sample_rate,
            self.root_key,
            self.loop_start,
            self.loop_end,
            self.num_samples,
        )

    def run_z64audio(self) -> None:
        import subprocess

        script_dir = Path(__file__).resolve().parent
        z64audio_exe = script_dir / 'z64audio' / 'z64audio'

        try:
            subprocess.run(
                [
                    str(z64audio_exe),
                    '-i',
                    str(self.file_path),
                    '-o',
                    f'{self.file_name}.bin',
                    '-I',
                    '50',
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as ex:
            print(f'An error ocurred during z64audio execution: {ex.stderr.decode()}')
        except FileNotFoundError:
            print(f'Error: z64audio executable not found.')
        except Exception as ex:
            print(f'An unexpected error occured: {ex}')
