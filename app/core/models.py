from pathlib import Path


class AudioSample:
    '''
    Attributes:
      size (int):
      address (int):
      tuning (float):
      loop_start (int):
      loop_end (int):
      num_samples (int):
      num_predictors (int):
      vadpcm_book_pred (list[list[in]]):
      vadpcm_loop_pred (list[int]):
    '''

    def __init__(self):
        self.size: int = 0
        self.address: int = 0
        self.tuning: float = 0.0
        self.loop_start: int = 0
        self.loop_end: int = 0
        self.loop_count: int = -1
        self.num_samples: int = 0
        self.num_predictors: int = 4
        self.vadpcm_book_pred: list[list[int]] = []
        self.vadpcm_loop_pred: list[int] = []


class SampleData:
    '''
    Attributes:
      name (str):
      path (str):
      sample_rate (int):
      root_key (int):
      coarse_tune (int):
      fine_tune (int):
      sample (Sample):
    '''

    def __init__(self):
        self.name: str = ''
        self.path: Path = None
        self.sample_rate: int = 32000
        self.root_key: int = 60
        self.coarse_tune: int = 0
        self.fine_tune: int = 0
        self.sample: AudioSample = AudioSample()


class InstrumentData:
    '''
    Attributes:
      name (str):
      tuning_type (str): CHAN
      auto_detect_tuning (bool):
      use_low_sample (bool):
      use_high_sample (bool):
      key_region_low (int):
      key_region_high (int):
      decay_index (int):
      low_sample (SampleData):
      prim_sample (SampleData):
      high_sample (SampleData):
    '''

    def __init__(self):
        self.name: str = ''
        self.tuning_type: str = 'CHAN'
        self.auto_detect_pitch: bool = False
        self.use_low_sample: bool = False
        self.use_high_sample: bool = False
        self.key_region_low: int = 0
        self.key_region_high: int = 127
        self.decay_index: int = 240
        self.low_sample: SampleData = SampleData()
        self.prim_sample: SampleData = SampleData()
        self.high_sample: SampleData = SampleData()


class DrumData:
    '''
    Attributes:
      type (str): KEY
      auto_detect_tuning (bool):
      decay_index (int):
      pan (int):
      sample (SampleData):
    '''

    def __init__(self):
        self.tuning_type: str = 'KEY'
        self.auto_detect_pitch: bool = False
        self.decay_index: int = 240
        self.pan: int = 64
        self.sample: SampleData = SampleData()


class EffectData:
    '''
    Attributes:
      tuning_type (str): KEY
      auto_detect_tuning (bool):
      sample (SampleData):
    '''

    def __init__(self):
        self.tuning_type: str = 'KEY'
        self.auto_detect_pitch: bool = False
        self.sample: SampleData = SampleData()
