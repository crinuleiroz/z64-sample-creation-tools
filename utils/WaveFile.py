'''
Utility for parsing binary WAV file data.
'''
import ctypes
import struct

class DataChunk(ctypes.Structure):
  _fields_ = [
    ('chunk_id',   ctypes.c_char * 4),
    ('chunk_size', ctypes.c_uint32)
  ]

  def __init__(self):
    self.chunk_id   = b'data'
    self.chunk_size = 0

class LoopStruct(ctypes.Structure):
  _fields_ = [
    ('loop_id',       ctypes.c_uint32),
    ('loop_type',     ctypes.c_uint32),
    ('loop_start',    ctypes.c_uint32),
    ('loop_end',      ctypes.c_uint32),
    ('loop_fraction', ctypes.c_uint32),
    ('loop_count',    ctypes.c_uint32)
  ]

  def __init__(self, loop_id, loop_type, loop_start, loop_end, loop_fraction, loop_count):
    self.loop_id       = loop_id
    self.loop_type     = loop_type
    self.loop_start    = loop_start
    self.loop_end      = loop_end
    self.loop_fraction = loop_fraction
    self.loop_count    = loop_count

class SmplChunk(ctypes.Structure):
  _fields_ = [
    ('chunk_id',            ctypes.c_char * 4),
    ('chunk_size',          ctypes.c_uint32),
    ('manufacturer',        ctypes.c_char * 4),
    ('product',             ctypes.c_char * 4),
    ('midi_unity_note',     ctypes.c_uint32),
    ('midi_pitch_fraction', ctypes.c_uint32),
    ('smpte_format',        ctypes.c_uint32),
    ('smpte_delay',         ctypes.c_uint32),
    ('num_loops',           ctypes.c_uint32),
    ('sample_data',         ctypes.c_uint32),
    ('loops',               ctypes.POINTER(LoopStruct))
  ]

  def __init__(self, manufacturer=b'', product=b'', sample_period=0, midi_unity_note=0, midi_pitch_fraction=0, smpte_format=0, smpte_delay=0, num_loops=0, sample_data=0, loops=None):
    if loops is None:
      loops = []
    self.chunk_id            = b'smpl'
    self.chunk_size          = 0
    self.manufacturer        = manufacturer.ljust(4, b'\x00')
    self.product             = product.ljust(4, b'\x00')
    self.sample_period       = sample_period
    self.midi_unity_note     = midi_unity_note
    self.midi_pitch_fraction = midi_pitch_fraction
    self.smpte_format        = smpte_format
    self.smpte_delay         = smpte_delay
    self.num_loops           = num_loops
    self.sample_data         = sample_data
    self.loops               = (LoopStruct * len(loops))(*loops) # This will generally just be a single array

class FmtChunk(ctypes.Structure):
  _fields_ = [
    ('chunk_id',        ctypes.c_char * 4),
    ('chunk_size',      ctypes.c_uint32),
    ('audio_format',    ctypes.c_uint16),
    ('num_channels',    ctypes.c_uint16),
    ('sample_rate',     ctypes.c_uint32),
    ('byte_rate',       ctypes.c_uint32),
    ('block_align',     ctypes.c_uint16),
    ('bits_per_sample', ctypes.c_uint16),
    ('extra_params',    ctypes.c_void_p)
  ]

  def __init__(self, audio_format=1, num_channels=2, sample_rate=44100, byte_rate=0, block_align=0, bits_per_sample=16, extra_params=None):
    self.chunk_id        = b'fmt '
    self.chunk_size      = 0
    self.audio_format    = audio_format
    self.num_channels    = num_channels
    self.sample_rate     = sample_rate
    self.byte_rate       = byte_rate
    self.block_align     = block_align
    self.bits_per_sample = bits_per_sample
    self.extra_params    = extra_params

class WaveFile:
  '''
  Parses and stores information about a given WAV file.
  '''
  def __init__(self, filename):
    self.filename    = filename
    self.wav_data    = None
    self.file        = None

    # 'fmt ' chunk
    self.fmt_chunk      = None
    self.fmt_chunk_addr = -1
    self.fmt_chunk_size = 0

    # 'data' chunk
    self.data_chunk      = None
    self.data_chunk_adrr = -1
    self.data_chunk_size = 0

    # 'smpl' chunk
    self.smpl_chunk      = None
    self.smpl_chunk_addr = -1
    self.smpl_chunk_size = 0

  def _scan_for_chunk(self, chunk_id: bytes) -> tuple[int, int]:
    self.file.seek(12)

    while True:
      header = self.file.read(8)
      if len(header) < 8:
        return -1, 0

      curr_id, size = struct.unpack('<4sI', header)
      curr_offset = self.file.tell() - 8

      if curr_id == chunk_id:
        return curr_offset, size

      self.file.seek(size, 1)
      if size % 2 == 1:
        self.file.seek(1, 1)

  def open(self):
    self.file = open(self.filename, 'r+b')

  def close(self):
    if self.file:
      self.file.close()
      self.file = None

  def read_header(self):
    header = self.file.read(12)
    if len(header) < 12:
      raise ValueError('File too small to be a WAV file.')

    chunk_id, chunk_size, format = struct.unpack('<4s1I4s', header)

    if chunk_id != b'RIFF' or format != b'WAVE':
      raise ValueError(f'Invalid WAV file. Expected RIFF and WAVE format got: {chunk_id} and {format}.')

    self.chunk_size = chunk_size

  def find_fmt_chunk(self):
    self.fmt_chunk_addr, self.fmt_chunk_size = self._scan_for_chunk(b'fmt ')
    if self.fmt_chunk_addr == -1:
      raise ValueError('No fmt chunk in RIFF!')

    self.fmt_chunk = FmtChunk()
    self.fmt_chunk.chunk_id = b'fmt '
    self.parse_fmt()

  def parse_fmt(self):
    self.file.seek(self.fmt_chunk_addr + 8)
    fmt_data = self.file.read(self.fmt_chunk_size)

    self.fmt_chunk.audio_format, self.fmt_chunk.num_channels, self.fmt_chunk.sample_rate, \
    self.fmt_chunk.byte_rate, self.fmt_chunk.block_align, self.fmt_chunk.bits_per_sample \
    = struct.unpack('<2H2I2H', fmt_data[0:16])

    if self.fmt_chunk.audio_format != 1:
      self.fmt_chunk.extra_params = fmt_data[16:]

  def find_smpl_chunk(self):
    self.smpl_chunk_addr, self.smpl_chunk_size = self._scan_for_chunk(b'smpl')
    if self.smpl_chunk_addr == -1:
      return

    self.smpl_chunk = SmplChunk()
    self.smpl_chunk.chunk_id = b'smpl'
    self.parse_smpl()

  def parse_smpl(self):
    self.file.seek(self.smpl_chunk_addr + 8)
    smpl_data = self.file.read(self.smpl_chunk_size)

    self.smpl_chunk.manufacturer, self.smpl_chunk.product, \
    self.smpl_chunk.sample_period, \
    self.smpl_chunk.midi_unity_note, self.smpl_chunk.midi_pitch_fraction, \
    self.smpl_chunk.smpte_format, self.smpl_chunk.smpte_delay, \
    self.smpl_chunk.num_loops, self.smpl_chunk.sample_data \
    = struct.unpack('<4s4s7I', smpl_data[0:0x24])

    loop_offset = 36
    loops = []
    for _ in range(self.smpl_chunk.num_loops):
      loop_data = struct.unpack('<6I', smpl_data[loop_offset:loop_offset+24])
      loop = LoopStruct(*loop_data)
      loops.append(loop)
      loop_offset += 24

    self.smpl_chunk.loops = (LoopStruct * len(loops))(*loops)

  def fix_loop(self):
    if self.smpl_chunk_addr == -1:
      raise ValueError('No smpl chunk in RIFF!')

    smpl_data = bytearray(struct.pack('<4s1I4s4s7I',
      self.smpl_chunk.chunk_id,
      self.smpl_chunk.chunk_size,
      b'wav2',
      b'zsnd',
      self.smpl_chunk.sample_period,
      self.smpl_chunk.midi_unity_note,
      self.smpl_chunk.midi_pitch_fraction,
      self.smpl_chunk.smpte_format,
      self.smpl_chunk.smpte_delay,
      0,
      self.smpl_chunk.sample_data
    ))

    for i in range(self.smpl_chunk.num_loops):
      smpl_data.extend(bytearray(struct.pack('<6I', 0, 0, 0, 0, 0, 0)))

      self.smpl_chunk.loops[i].loop_id       = 0
      self.smpl_chunk.loops[i].loop_type     = 0
      self.smpl_chunk.loops[i].loop_start    = 0
      self.smpl_chunk.loops[i].loop_end      = 0
      self.smpl_chunk.loops[i].loop_fraction = 0
      self.smpl_chunk.loops[i].loop_count    = 0

    self.file.seek(self.smpl_chunk_addr)
    self.file.write(smpl_data)

  def find_data_chunk(self):
      offset, size = self._scan_for_chunk(b'data')
      if offset == -1:
        raise ValueError('No data chunk in RIFF!')

      self.data_chunk = DataChunk()
      self.data_chunk.chunk_id = b'data'
      self.data_chunk.chunk_size = size

  def save(self):
    self.file.flush()

  def parse_wave(self):
    self.open()
    self.read_header()
    self.find_fmt_chunk()
    self.find_smpl_chunk()
    self.find_data_chunk()

if __name__ == '__main__':
  pass
