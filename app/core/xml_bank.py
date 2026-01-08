from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import xml.etree.ElementTree as xml

from app.core.models import DrumData, EffectData, InstrumentData, SampleData


HEADER_SIZE = 0x10
DRUMLIST_SIZE = 0x10
SFXLIST_SIZE = 0x10
INSTRUMENT_SIZE = 0x20
DRUM_SIZE = 0x10
ENVELOPE_SIZE = 0x10
SAMPLE_SIZE = 0x10
CODEBOOK_SIZE = 0x90
LOOPBOOK_HEADER = 0x10
LOOPBOOK_TAIL = 0x20


class XMLTags(Enum):
    ABINDEXENTRY = 'abindexentry'
    ABHEADER = 'abheader'
    ABBANK = 'abbank'
    ABDRUMLIST = 'abdrumlist'
    ABSFXLIST = 'absfxlist'
    INSTRUMENTS = 'instruments'
    DRUMS = 'drums'
    ENVELOPES = 'envelopes'
    SAMPLES = 'samples'
    ALADPCMLOOPS = 'aladpcmloops'
    ALADPCMBOOKS = 'aladpcmbooks'


@dataclass
class XMLDataEntry:
    enum_tag: XMLTags
    xml_tag: str
    xml_list: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.parent_tag = self.enum_tag.value


# I fucking hate XML~
class XMLBank:
    """
    Represents an instrument bank in the SEQ64 XML format.

    #### ABIndexEntry
    ```c
    typedef struct AudiobankIndexEntry {
        /* 0x00 */ uintptr_t romAddress;
        /* 0x04 */ size_t size;
        /* 0x08 */ unsigned char medium;
        /* 0x09 */ unsigned char cacheLoadType;
        /* 0x0A */ unsigned char sampleBankId1;
        /* 0x0B */ unsigned char sampleBankId2;
        /* 0x0C */ unsigned char numInstruments;
        /* 0x0D */ unsigned char numDrums;
        /* 0x0E */ signed short int numEffects;
    } AudiobankIndexEntry;
    ```

    #### Audio Storage Mediums
    ```c
    typdef enum AudioStorageMedium {
        /* 0 */ MEDIUM_RAM,
        /* 1 */ MEDIUM_UNK,
        /* 2 */ MEDIUM_CART,
        /* 3 */ MEDIUM_DISK_DRIVE,
        /* 5 */ MEDIUM_RAM_UNLOADED = 5,
    } AudioStorageMedium;
    ```

    #### Cache Load Types
    ```c
    typdef enum AudioCacheLoadType {
        /* 0 */ CACHE_LOAD_PERMANENT,
        /* 1 */ CACHE_LOAD_PERSISTENT,
        /* 2 */ CACHE_LOAD_TEMPORARY,
        /* 3 */ CACHE_LOAD_EITHER,
        /* 4 */ CACHE_LOAD_EITHER_NOSYNC,
    } AudioCacheLoadType;
    ```
    """
    def __init__(self, output_folder: Path, sample_container: InstrumentData | DrumData | EffectData):
        self.output_name = output_folder / 'bank.xml'
        self.sample_container = sample_container

        if isinstance(sample_container, InstrumentData):
            self.samples = [
                s for s in (
                    sample_container.low_sample,
                    sample_container.prim_sample,
                    sample_container.high_sample,
                ) if s is not None
            ]
        else:
            self.samples = [sample_container.sample]

        self.num_samples = len(self.samples)

        if isinstance(sample_container, InstrumentData):
            self.instrument_type = 'Instrument'
        elif isinstance(sample_container, DrumData):
            self.instrument_type = 'Drum'
        elif isinstance(sample_container, EffectData):
            self.instrument_type = 'Effect'
        else:
            raise Exception()

        self.num_instruments = 1 if self.instrument_type == 'Instrument' else 0
        self.num_drums = 1 if self.instrument_type == 'Drum' else 0
        self.num_effects = 1 if self.instrument_type == 'Effect' else 0

        self._calcuate_addresses()
        self._create_lists()
        self._populate_lists()

    def _calcuate_addresses(self) -> None:
        self.drumlist_address = HEADER_SIZE
        self.sfxlist_address = self.drumlist_address + (DRUMLIST_SIZE * self.num_effects)
        self.instrument_address = self.sfxlist_address + (SFXLIST_SIZE * self.num_instruments)
        self.drum_address = self.instrument_address + (INSTRUMENT_SIZE * self.num_instruments)
        self.envelope_address = self.drum_address + (DRUM_SIZE * self.num_drums)
        self.sample_address = self.envelope_address + ENVELOPE_SIZE
        self.codebook_address = self.sample_address + (SAMPLE_SIZE * self.num_samples)
        self.loopbook_address = self.codebook_address + (CODEBOOK_SIZE * self.num_samples)

        self.bank_length = self.loopbook_address + (LOOPBOOK_HEADER * self.num_samples)
        self.bank_length += sum(LOOPBOOK_TAIL for s in self.samples if s and s.sample.loop_start != 0)

    def _create_lists(self) -> None:
        self.abindexentry_xml = []
        self.abbank_xml = []
        self.abdrumlist_xml = []
        self.absfxlist_xml = []
        self.instruments_xml = []
        self.drums_xml = []
        self.effects_xml = [] # KEEP EMPTY!
        self.envelopes_xml = []
        self.samples_xml = []
        self.aladpcmloops_xml = []
        self.aladpcmbooks_xml = []

    def _populate_lists(self) -> None:
        self._create_table_entry_dict()
        self._create_abbank_dict()

        # TODO: Effects
        if self.num_instruments > 0:
            self._create_instrument_dict()
        if self.num_drums > 0:
            self._create_abdrumlist_dict()
            self._create_drum_dict()
        if self.num_effects > 0:
            self._create_absfxlist_dict()

        self._create_envelope_dict()
        self._create_sample_dict()
        self._create_loop_dict()
        self._create_book_dict()

    def create_bank(self) -> None:
        xml_root = xml.Element('bank')

        xml_root.set('NUM_INST', f'{self.num_instruments}')
        xml_root.set('NUM_DRUM', f'{self.num_drums}')
        xml_root.set('NUM_SFX', f'{self.num_effects}')
        xml_root.set('ATnum', '0')

        xml_tree = xml.ElementTree(xml_root)
        xml_data = [
            XMLDataEntry(XMLTags.ABINDEXENTRY, 'struct', self.abindexentry_xml),
            XMLDataEntry(XMLTags.ABHEADER,     'struct', [{"name": "ABHeader"}]),
            XMLDataEntry(XMLTags.ABBANK,       'struct', self.abbank_xml),
            XMLDataEntry(XMLTags.ABDRUMLIST,   'struct', self.abdrumlist_xml),
            XMLDataEntry(XMLTags.ABSFXLIST,    'struct', self.absfxlist_xml),
            XMLDataEntry(XMLTags.INSTRUMENTS,  'item',   self.instruments_xml),
            XMLDataEntry(XMLTags.DRUMS,        'item',   self.drums_xml),
            XMLDataEntry(XMLTags.ENVELOPES,    'item',   self.envelopes_xml),
            XMLDataEntry(XMLTags.SAMPLES,      'item',   self.samples_xml),
            XMLDataEntry(XMLTags.ALADPCMBOOKS, 'item',   self.aladpcmbooks_xml),
            XMLDataEntry(XMLTags.ALADPCMLOOPS, 'item',   self.aladpcmloops_xml),
        ]

        for entry in xml_data:
            element = xml.Element(entry.parent_tag)

            if entry.parent_tag == 'abdrumlist' and self.num_drums > 0:
                element.set('address', '16')

            for item in entry.xml_list:
                self._dict_to_xml(entry.xml_tag, item, element)

            xml_root.append(element)

        with self.output_name.open('wb') as f:
            xml.indent(xml_tree)
            xml_tree.write(f, encoding='utf-8', xml_declaration=True)

    def _dict_to_xml(self, tag: str, d: dict, parent: xml.Element = None) -> xml.Element:
        element = xml.Element(tag)

        for key, value in d.items():
            if key == '__comment__':
                comment = xml.Comment(value)
                element.append(comment)

            elif isinstance(value, dict):
                self._dict_to_xml(key, value, element)

            elif isinstance(value, list):
                for item in value:
                    child = self._dict_to_xml(key, item)
                    element.append(child)

            else:
                element.set(key, str(value) if value is not None else '')

        if parent is not None:
            parent.append(element)

        return element

    def _create_table_entry_dict(self) -> None:
        self.abindexentry_xml.append ({
            "name": "ABIndexEntry",
            "field": [
                # Address
                {
                    "name": "Address",
                    "datatype": "uint32",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "Ptr Bank (in Audiobank)",
                    "value": "155648", # Steal 0x28's address
                },
                # Size
                {
                    "name": "Size",
                    "datatype": "uint32",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "Bank Length",
                    "value": f"{self.bank_length}",
                },
                # Audio Storage Medium
                {
                    "name": "Audio Storage Medium",
                    "datatype": "uint8",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "None",
                    "defaultval": "2",
                    "value": "2",
                },
                # Cache Load Type
                {
                    "name": "Cache Load Type",
                    "datatype": "uint8",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "None",
                    "defaultval": "2",
                    "value": "2"
                },
                # Sample Bank ID 1
                {
                    "name": "Sample Bank ID 1",
                    "datatype": "uint8",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "Sample Table Number",
                    "defaultval": "0",
                    "value": "0",
                },
                # Sample Bank ID 2
                {
                    "name": "Sample Bank ID 2",
                    "datatype": "uint8",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "Sample Table Number",
                    "defaultval": "255",
                    "value": "255"
                },
                # Number of Instruments
                {
                    "name": "NUM_INST",
                    "datatype": "uint8",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning":
                    "NUM_INST",
                    "value": f"{self.num_instruments}",
                },
                # Number of Drums
                {
                    "name": "NUM_DRUM",
                    "datatype": "uint8",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "NUM_DRUM",
                    "value": f"{self.num_drums}",
                },
                # Number of Effects
                {
                    "name": "NUM_SFX",
                    "datatype": "int16",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "NUM_SFX",
                    "value": f"{self.num_effects}",
                },
            ],
        })

    def _create_abbank_dict(self) -> None:
        self.abbank_xml.append({
            "name": "ABBank",
            "field": [
                {
                    "name": "Drum List Pointer",
                    "datatype": "uint32",
                    "ispointer": "1",
                    "ptrto": "ABDrumList",
                    "isarray": "0",
                    "meaning": "Ptr Drum List",
                    "value": f"{self.drumlist_address if self.num_drums > 0 else 0}",
                },
                {
                    "name": "SFX List Pointer",
                    "datatype": "uint32",
                    "ispointer": "1",
                    "ptrto": "ABSFXList",
                    "isarray": "0",
                    "meaning": "Ptr SFX List",
                    "value": f"{self.sfxlist_address if self.num_effects > 0 else 0}",
                },
                {
                    "name": "Instrument List",
                    "datatype": "uint32",
                    "ispointer": "1",
                    "ptrto": "ABInstrument",
                    "isarray": "1",
                    "arraylenvar": "NUM_INST",
                    "meaning": "List of Ptrs to Insts",
                    **(
                        {
                            "element": [{
                                    "datatype": "uint32",
                                    "ispointer": "1",
                                    "ptrto": "ABInstrument",
                                    "value": f"{self.instrument_address}",
                                    "index": "0",
                                }],
                        } if self.num_instruments > 0 else {}
                    ),
                },
            ],
        })

    def _create_abdrumlist_dict(self) -> None:
        self.abdrumlist_xml.append({
            "name": "ABDrumList",
            "field": [
                {
                    "name": "Drum List",
                    "datatype": "uint32",
                    "ispointer": "1",
                    "ptrto": "ABDrum",
                    "isarray": "1",
                    "arraylenvar": "NUM_DRUM",
                    **(
                        {
                            "element": [{
                                "datatype": "uint32",
                                "ispointer": "1",
                                "ptrto": "ABDrum",
                                "value": f"{self.drum_address}",
                                "index": "0",
                            }],
                        } if self.num_drums > 0 else {}
                    ),
                },
            ],
        })

    def _create_absfxlist_dict(self) -> None:
        # TODO: Effects
        ...

    def _create_instrument_dict(self) -> None:
        instrument = self.sample_container

        if not instrument.prim_sample:
            raise Exception()

        low_sample_index = 0 if instrument.low_sample else -1
        prim_sample_index = 1 if low_sample_index == 0 else 0
        high_sample_index = (
            2 if prim_sample_index == 1
            else (1 if instrument.high_sample else -1)
        )

        low_sample_address = self.sample_address if instrument.low_sample else 0
        prim_sample_address = low_sample_address + 0x10 if instrument.low_sample else self.sample_address
        high_sample_address = prim_sample_address + 0x10 if instrument.high_sample else 0

        sample_info = [
            ("low_sample", low_sample_address, low_sample_index),
            ("prim_sample", prim_sample_address, prim_sample_index),
            ("high_sample", high_sample_address, high_sample_index),
        ]

        elements = []
        for attr_name, addr, index in sample_info:
            sample_obj: SampleData = getattr(instrument, attr_name)
            elements.append({
                "datatype": "ABSound",
                "ispointer": "0",
                "value": "0",
                "struct": {
                    "name": "ABSound",
                    "field": [
                        {
                            "name": "Sample Pointer",
                            "datatype": "uint32",
                            "ispointer": "1",
                            "ptrto": "ABSample",
                            "isarray": "0",
                            "meaning": "Ptr Sample",
                            "value": f"{addr}",
                            "index": f"{index}",
                        },
                        {
                            "name": "Sample Tuning",
                            "datatype": "float32",
                            "ispointer": "0",
                            "isarray": "0",
                            "meaning": "None",
                            "value": f"{sample_obj.sample.tuning if sample_obj else 0.0}",
                        },
                    ],
                },
            })

        self.instruments_xml.append({
            "address": f"{self.instrument_address}",
            "name": f"{instrument.name}",
            "struct" : {
                "name": "ABInstrument",
                "field": [
                    {
                        "name": "Relocated (Bool)",
                        "datatype": "uint8",
                        "ispointer": "0",
                        "isarray": "0",
                        "meaning": "None",
                        "value": "0",
                    },
                    {
                        "name": "Key Region Low (Max Range)",
                        "datatype": "uint8",
                        "ispointer": "0",
                        "isarray": "0",
                        "meaning": "Split Point 1",
                        "value": f"{instrument.key_region_low}",
                    },
                    {
                        "name": "Key Region High (Min Range)",
                        "datatype": "uint8",
                        "ispointer": "0",
                        "isarray": "0",
                        "meaning": "Split Point 1",
                        "value": f"{instrument.key_region_high}",
                    },
                    {
                        "name": "Decay Index",
                        "datatype": "uint8",
                        "ispointer": "0",
                        "isarray": "0",
                        "meaning": "None",
                        "value": f"{instrument.decay_index}",
                    },
                    {
                        "name": "Envelope Pointer",
                        "datatype": "uint32",
                        "ispointer": "1",
                        "ptrto": "ABEnvelope",
                        "isarray": "0",
                        "meaning": "Ptr Envelope",
                        "value": f"{self.envelope_address}",
                        "index": "0",
                    },
                    {
                        "name": "Sample Pointer Array",
                        "datatype": "ABSound",
                        "ispointer": "0",
                        "isarray": "1",
                        "arraylenfixed": "3",
                        "meaning": "List of 3 Sounds for Splits",
                        "element": elements,
                    },
                ]
            }
        })

    def _create_drum_dict(self) -> None:
        drum = self.sample_container

        if not drum.sample:
            raise Exception()

        self.drums_xml.append({
            "address": f"{self.drum_address}",
            "name": f"{drum.name} [0]",
            "struct": {
                "name": "ABDrum",
                "field": [
                    {
                        "name": "Decay Index",
                        "datatype": "uint8",
                        "ispointer": "0",
                        "isarray": "0",
                        "meaning": "None",
                        "value": f"{drum.decay_index}",
                    },
                    {
                        "name": "Pan",
                        "datatype": "uint8",
                        "ispointer": "0",
                        "isarray": "0",
                        "meaning": "None",
                        "value": f"{drum.pan}",
                    },
                    {
                        "name": "Relocated (Bool)",
                        "datatype": "uint8",
                        "ispointer": "0",
                        "isarray": "0",
                        "meaning": "None",
                        "value": "0",
                    },
                    {
                        "name": "Padding Byte",
                        "datatype": "uint8",
                        "ispointer": "0",
                        "isarray": "0",
                        "meaning": "None",
                        "value": "0",
                    },
                    {
                        "name": "Drum Sound",
                        "datatype": "ABSound",
                        "ispointer": "0",
                        "isarray": "0",
                        "meaning": "Drum Sound",
                        "struct": {
                            "name": "ABSound",
                            "field": [
                                {
                                    "name": "Sample Pointer",
                                    "datatype": "uint32",
                                    "ispointer": "1",
                                    "ptrto": "ABSample",
                                    "isarray": "0",
                                    "meaning": "Ptr Sample",
                                    "value": f"{self.sample_address}",
                                    "index": "0"
                                },
                                {
                                    "name": "Sample Tuning",
                                    "datatype": "float32",
                                    "ispointer": "0",
                                    "isarray": "0",
                                    "meaning": "None",
                                    "value": f"{drum.sample.sample.tuning}",
                                },
                            ],
                        },
                    },
                    {
                        "name": "Envelope Pointer",
                        "datatype": "uint32",
                        "ispointer": "1",
                        "ptrto": "ABEnvelope",
                        "isarray": "0",
                        "meaning": "Ptr Envelope",
                        "value": f"{self.envelope_address}",
                        "index": "0",
                    },
                ],
            },
        })

    def _create_envelope_dict(self) -> None:
        self.envelopes_xml.append({
            "address": f"{self.envelope_address}",
            "name": "General Use Envelope",
            "fields": [
                {
                    "name": "Time or Opcode [1]",
                    "datatype": "int16",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "None",
                    "value": "2"
                },
                {
                    "name": "Amp or Index [1]",
                    "datatype": "int16",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "None",
                    "value": "32700"
                },
                {
                    "name": "Time or Opcode [2]",
                    "datatype": "int16",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "None",
                    "value": "1"
                },
                {
                    "name": "Amp or Index [2]",
                    "datatype": "int16",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "None",
                    "value": "32700"
                },
                {
                    "name": "Time or Opcode [3]",
                    "datatype": "int16",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "None",
                    "value": "32700"
                },
                {
                    "name": "Amp or Index [3]",
                    "datatype": "int16",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "None",
                    "value": "29430"
                },
                {
                    "name": "Time or Opcode [4]",
                    "datatype": "int16",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "None",
                    "value": "-1"
                },
                {
                    "name": "Amp or Index [4]",
                    "datatype": "int16",
                    "ispointer": "0",
                    "isarray": "0",
                    "meaning": "None",
                    "value": "0"
                }
            ]
        })

    def _create_sample_dict(self) -> None:
        for i in range(len(self.samples)):
            sample = self.samples[i]

            loop_size = 0x30 if sample.sample.loop_start != 0 else 0x10
            bits = (1 & 1) << 25 | (0 & 1) << 24 | (sample.sample.size & 0xFFFFFF)

            self.samples_xml.append({
                "address": f"{self.sample_address + (i * 0x10)}",
                "name": f"{sample.name}",
                "struct": {
                    "name": "ABSample",
                    "__comment__": f"""
                Below are the bitfield values for each bit they represent.
                Each of these values takes up a specific amount of the 32 bits representing the u32 value.
                 4 Bit(s): Codec       (Bit(s) 1-4):  CODEC_ADPCM (0)
                 2 Bit(s): Medium      (Bit(s) 5-6):  MEDIUM_RAM (0)
                 1 Bit(s): Cached      (Bit(s) 7):    True (1)
                 1 Bit(s): Relocated   (Bit(s) 8):    False (0)
                24 Bit(s): Binary size (Bit(s) 9-32): {sample.sample.size}
            """,
                    "field": [
                        {
                            "name": "Bitfield",
                            "datatype": "uint32",
                            "ispointer": "0",
                            "isarray": "0",
                            "meaning": "None",
                            "value": f"{bits}",
                        },
                        {
                            "name": "Audiotable Address",
                            "datatype": "uint32",
                            "ispointer": "0", # Points to data inside bank
                            "ptrto": "ATSample",
                            "isarray": "0",
                            "meaning": "Sample Address (in Sample Table)",
                            "value": f"{sample.sample.address}",
                        },
                        {
                            "name": "Loop Pointer",
                            "datatype": "uint32",
                            "ispointer": "1",
                            "ptrto": "ALADPCMLoop",
                            "isarray": "0",
                            "meaning": "Ptr ALADPCMLoop",
                            "value": f"{self.loopbook_address + (i * loop_size)}",
                            "index": f"{i}",
                        },
                        {
                            "name": "Book Pointer",
                            "datatype": "uint32",
                            "ispointer": "1",
                            "ptrto": "ALADPCMBook",
                            "isarray": "0",
                            "meaning": "Ptr ALADPCMBook",
                            "value": f"{self.codebook_address + (i * CODEBOOK_SIZE)}",
                            "index": f"{i}",
                        },
                    ],
                },
            })

    def _create_loop_dict(self) -> None:
        for i in range(len(self.samples)):
            sample = self.samples[i]

            loop_size = 0x10
            tail = []
            if sample.sample.loop_start != 0:
                loop_size = 0x30
                tail = [{
                    "datatype": "ALADPCMTail",
                    "ispointer": "0",
                    "value": "0",
                    "struct": {
                        "name": "ALADPCMTail",
                        "field": [
                            {
                                "name": "data",
                                "datatype": "int16",
                                "ispointer": "0",
                                "isarray": "1",
                                "arraylenfixed": "16",
                                "meaning": "None",
                                "element": [
                                    {
                                        "datatype": "int16",
                                        "ispointer": "0",
                                        "value": f"{predictor}",
                                    }
                                    for predictor in sample.sample.vadpcm_loop_pred
                                ]
                            },
                        ],
                    },
                }]

            self.aladpcmloops_xml.append({
                "address": f"{self.loopbook_address + (i * loop_size)}",
                "name": f"{sample.name} Loop",
                "struct": {
                    "name": "ALADPCMLoop",
                    "HAS_TAIL": f"{1 if sample.sample.loop_start != 0 else 0}",
                    "field": [
                        {
                            "name": "Loop Start",
                            "datatype": "uint32",
                            "ispointer": "0",
                            "isarray": "0",
                            "meaning": "Loop Start",
                            "value": f"{sample.sample.loop_start}",
                        },
                        {
                            "name": "Loop End (Sample Length if Count = 0)",
                            "datatype": "uint32",
                            "ispointer": "0",
                            "isarray": "0",
                            "meaning": "Loop End",
                            "value": f"{sample.sample.loop_end if sample.sample.loop_start != 0 else sample.sample.num_samples}",
                        },
                        {
                            "name": "Loop Count",
                            "datatype": "int32",
                            "ispointer": "0",
                            "isarray": "0",
                            "meaning": "Loop Count",
                            "defaultval": "-1",
                            "value": f"{-1 if sample.sample.loop_start != 0 else 0}",
                        },
                        {
                            "name": "Number of Samples",
                            "datatype": "uint32",
                            "ispointer": "0",
                            "isarray": "0",
                            "meaning": "None",
                            "value": f"{sample.sample.num_samples if sample.sample.loop_start != 0 else 0}",
                        },
                        {
                            "name": "Loopbook",
                            "datatype": "uint32",
                            "ispointer": "0",
                            "isarray": "1",
                            "arraylenvar": "HAS_TAIL",
                            "meaning": "Tail Data (if Loop Start != 0)",
                            "element": tail,
                        },
                    ],
                },
            })

    def _create_book_dict(self) -> None:
        for i in range(len(self.samples)):
            sample = self.samples[i]

            codebooks = [
                {
                    "datatype": "ALADPCMPredictor",
                    "ispointer": "0",
                    "value": "0",
                    "struct": {
                        "name": "data",
                        "datatype": "int16",
                        "ispointer": "0",
                        "isarray": "1",
                        "arraylenfixed": "16",
                        "meaning": "None",
                        "element": [
                            {
                                "datatype": "int16",
                                "ispointer": "0",
                                "value": f"{predictor}",
                            }
                            for predictor in predictors
                        ],
                    },
                }
                for predictors in sample.sample.vadpcm_book_pred
            ]

            self.aladpcmbooks_xml.append({
                "address": f"{self.codebook_address + (i * CODEBOOK_SIZE)}",
                "name": f"{sample.name} Book",
                "struct": {
                    "name": "ALADPCMBook",
                    "NUM_PRED": "4",
                    "field": [
                        {
                            "name": "Order",
                            "datatype": "int32",
                            "ispointer": "0",
                            "isarray": "0",
                            "meaning": "None",
                            "value": "2",
                        },
                        {
                            "name": "Number of Predictors",
                            "datatype": "int32",
                            "ispointer": "0",
                            "isarray": "0",
                            "meaning": "NUM_PRED",
                            "value": "4",
                        },
                        {
                            "name": "Codebook",
                            "datatype": "ALADPCMPredictor",
                            "ispointer": "0",
                            "isarray": "1",
                            "arraylenvar": "NUM_PRED",
                            "meaning": "Array of predictors",
                            "element": codebooks,
                        },
                    ],
                },
            })