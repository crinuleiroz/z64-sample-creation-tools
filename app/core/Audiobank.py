'''
Utility for
'''
from dataclasses import dataclass

from app.core.models import AudioSample, DrumData, EffectData, InstrumentData, SampleData


@dataclass
class PredictorArray:
    array: list[int]

    def __post_init__(self):
        if len(self.array) != 16:
            raise ValueError()


class VadpcmLoop:
    def __init__(self, loop_start: int, loop_end: int, loop_count: int, num_samples: int, p_array: list[int]):
        self.loop_start: int = loop_start
        self.loop_end: int = loop_end
        self.loop_count: int = loop_count
        self.num_samples: int = num_samples
        self.predictor_array: PredictorArray = PredictorArray(p_array)


class VadpcmBook:
    def __init__(self, num_predictors: int, p_array: list[list[int]]):
        self.order: int = 2
        self.num_predictors: int = num_predictors
        self.predictors: list[PredictorArray] = []

        for p in p_array[:self.num_predictors]:
            self.predictors.append(PredictorArray(p))


class Sample:
    def __init__(self, data: AudioSample):
        # Pack the bitfield
        bits = 0
        bits |= (0 & 0b1111) << 28
        bits |= (0 & 0b11) << 26
        bits |= (1 & 1) << 25
        bits |= (0 & 1) << 24
        bits |= (data.size & 0b111111111111111111111111)

        self.bitfield: int = bits
        self.address: int = data.address
        self.vadpcm_loop: VadpcmLoop = VadpcmLoop(
            data.loop_start,
            data.loop_end,
            data.loop_count,
            data.num_samples,
            data.vadpcm_loop_pred
        )
        self.vadpcm_book: VadpcmBook = VadpcmBook(
            data.num_predictors,
            data.vadpcm_book_pred
        )


class TunedSample:
    def __init__(self, sample_data: SampleData):
        self.address: int = sample_data.sample.address
        self.tuning: float = sample_data.sample.tuning
        self.sample: Sample = Sample(sample_data.sample)


class Instrument:
    def __init__(self, instrument_data: InstrumentData):
        self.is_relocated: bool = False
        self.Key_region_low: int = instrument_data.key_region_low
        self.Key_region_high: int = instrument_data.key_region_high
        self.decay_index: int = instrument_data.decay_index

        # Samples
        self.low_sample: TunedSample = (
            TunedSample(instrument_data.low_sample)
            if instrument_data.low_sample is not None
            else None
        )
        self.prim_sample: TunedSample = TunedSample(instrument_data.prim_sample)
        self.high_sample: TunedSample = (
            TunedSample(instrument_data.high_sample)
            if instrument_data.high_sample is not None
            else None
        )


class Drum:
    def __init__(self, drum_data: DrumData):
        self.decay_index: int = 240
        self.pan: int = 64
        self.is_relocated: bool = False

        # Sample
        self.sample: TunedSample = None


class Effect:
    def __init__(self, effect_data: EffectData):
        self.sample: TunedSample = None
