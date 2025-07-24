# Utility script for WAV to ZSOUND.py
from dataclasses import dataclass, field
from enum import Enum
import xml.etree.ElementTree as xml


class XMLTags(Enum):
    ABINDEXENTRY = 'abindexentry'
    ABHEADER     = 'abheader'
    ABBANK       = 'abbank'
    ABDRUMLIST   = 'abdrumlist'
    ABSFXLIST    = 'absfxlist'
    INSTRUMENTS  = 'instruments'
    DRUMS        = 'drums'
    ENVELOPES    = 'envelopes'
    SAMPLES      = 'samples'
    ALADPCMLOOPS = 'aladpcmloops'
    ALADPCMBOOKS = 'aladpcmbooks'


@dataclass
class XMLDataEntry:
    enum_tag:  XMLTags
    xml_tag:   str
    xml_list:  list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.parent_tag = self.enum_tag.value


class XMLBank:
    def __init__(self, num_samples, *samples):
        """
        Represents an instrument bank in the SEQ64 XML format.
        
        The abindexentry contains the following fields:
            - u32: Address in `audiobank`
            - u32: Size in `audiobank`
            -  u8: Audio storage medium
            -  u8: Cache Load Type
            -  u8: Sample Bank ID 1
            -  u8: Sample Bank ID 2
            -  u8: Number of instruments
            -  u8: Number of drums
            - u16: Number of effects
        
        Audio Storage Mediums:
            0 = MEIDUM_RAM,
            1 = MEDIUM_UNK,
            2 = MEDIUM_CART,
            3 = MEDIUM_DISK_DRIVE,
            5 = MEDIUM_RAM_UNLOADED
            
        Cache Load Type:
            0 = CACHE_LOAD_PERMANENT,
            1 = CACHE_LOAD_PERSISTENT,
            2 = CACHE_LOAD_TEMPORARY,
            3 = CACHE_LOAD_EITHER,
            4 = CACHE_LOAD_EITHER_NOSYNC
        """
        self.num_samples = num_samples
        self.drumlist_address = 0x10
        self.instrument_address = (0x20 * num_samples)
        self.drum_address = self.instrument_address + 0x20
        self.envelope_address = self.drum_address + (0x10 * num_samples)
        self.sample_address = self.envelope_address + 0x10
        self.codebook_address = self.sample_address + (0x10 * num_samples)
        self.loopbook_address = self.codebook_address + (0x90 * num_samples)
        self.bank_length = self.loopbook_address + (0x10 * num_samples)

        # Store the samples in the class so they do not need to be passed to functions
        self.samples = samples[:3]
        self.bank_length += sum(0x20 for sample in self.samples if sample and sample.loopbook_predictors)

        # The bank is going to be created using dictionaries, so init all of the lists containing them here
        self.abindexentry_xml = [
            {
                "name": "ABIndexentry",
                "field": [
                    {"name": "Audiobank Address", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "Ptr Bank (in Audiobank)", "value": "155648"}, # Just steal bank 0x28's address
                    {"name": "Bank Size", "datatype": "uint32", "ispointer": "0", "isarray": "0", "meaning": "Bank Length", "value": f"{self.bank_length}"},
                    {"name": "Audio Storage Medium", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "None", "defaultval": "2", "value": "2"},
                    {"name": "Cache Load Type", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "None", "defaultval": "2", "value": "2"},
                    {"name": "Sample Bank ID 1", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "Sample Table Number", "defaultval": "0", "value": "0"},
                    {"name": "Sample Bank ID 2", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "Sample Table Number", "defaultval": "255", "value": "255"},
                    {"name": "NUM_INST", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "NUM_INST", "value": "1"},
                    {"name": "NUM_DRUM", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "NUM_DRUM", "value": f"{num_samples}"},
                    {"name": "NUM_SFX", "datatype": "uint16", "ispointer": "0", "isarray": "0", "meaning": "NUM_SFX", "value": "0"}
                ]
            }
        ]

        self.abbank_xml = [
            {
                "name": "ABBank",
                "field": [
                    {"name": "Drum List Pointer", "datatype": "uint32", "ispointer": "1", "ptrto": "ABDrumList", "isarray": "0", "meaning": "Ptr Drum List", "value": f"{self.drumlist_address}"},
                    {"name": "SFX List Pointer", "datatype": "uint32", "ispointer": "1", "ptrto": "ABSFXList", "isarray": "0", "meaning": "Ptr SFX List", "value": "0"},
                    {"name": "Instrument List", "datatype": "uint32", "ispointer": "1", "ptrto": "ABInstrument", "isarray": "1", "arraylenvar": "NUM_INST", "meaning": "List of Ptrs to Insts",
                        "element": [
                            {"datatype": "uint32", "ispointer": "1", "ptrto": "ABInstrument", "value": f"{self.instrument_address}", "index": "0"}
                        ]
                    }
                ]
            }
        ]

        self.instruments_xml = []

        self.abdrumlist_xml = [
            {
                "name": "ABDrumList",
                "field": [
                    {"name": "Drum List", "datatype": "uint32", "ispointer": "1", "ptrto": "ABDrum", "isarray": "1", "arraylenvar": "NUM_DRUM",
                        "element": [
                            {"datatype": "uint32", "ispointer": "1", "ptrto": "ABDrum", "value": f"{self.drum_address + (i * 0x10)}", "index": f"{i}"}
                            for i in range(num_samples)
                        ]
                    }
                ]
            }
        ]

        self.drums_xml = []

        self.absfxlist_xml = [] # Keep empty
        self.effects_xml = [] # Keep empty

        self.envelopes_xml = [
            {
                "address": f"{self.envelope_address}", "name": "General Use Envelope",
                "fields": [
                    {"name": "Attack Time", "datatype": "int16", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "2"},
                    {"name": "Attack Amplitude", "datatype": "int16", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "32700"},
                    {"name": "Hold Time", "datatype": "int16", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "1"},
                    {"name": "Hold Amplitude", "datatype": "int16", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "32700"},
                    {"name": "Decay Time", "datatype": "int16", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "32700"},
                    {"name": "Sustain Amplitude", "datatype": "int16", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "29430"},
                    {"name": "Control Flow", "datatype": "int16", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "-1"},
                    {"name": "Control Value", "datatype": "int16", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "0"}
                ]
            }
        ]

        self.samples_xml      = []
        self.aladpcmloops_xml = []
        self.aladpcmbooks_xml = []

        # Automatically generate the XML since all the information required is in the class already
        self.generate_instrument_xml()
        self.generate_drum_xml()
        self.generate_sample_xml()
        self.generate_loop_xml()
        self.generate_book_xml()

    def generate_instrument_xml(self):
        low_sample, prim_sample, high_sample = (self.samples + tuple([None] * 3))[:3]

        low_sample_index  = 0 if low_sample else -1
        prim_sample_index = 1 if low_sample else 0
        high_sample_index = 2 if high_sample else -1

        low_sample_address  = self.sample_address if low_sample else 0
        prim_sample_address = self.sample_address + (1 * 0x10) if low_sample else self.sample_address
        high_sample_address = self.sample_address + (2 * 0x10) if high_sample else 0

        key_region_low  = prim_sample.root_note - 21 if low_sample else 0
        key_region_high = high_sample.root_note - 21 if high_sample else 127

        self.instruments_xml.append(
            {
                "address": f"{self.instrument_address}", "name": f"{prim_sample.name} [0]",
                "struct": {
                    "name": "ABInstrument",
                    "field": [
                        {"name": "Relocated (Bool)", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "0"},
                        {"name": "Key Region Low (Max Range)", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "Split Point 1", "value": f"{key_region_low}"},
                        {"name": "Key Region High (Min Range)", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "Split Point 2", "value": f"{key_region_high}"},
                        {"name": "Decay Index", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "245"},
                        {"name": "Envelope Pointer","datatype": "uint32","ispointer": "1","ptrto": "ABEnvelope","isarray": "0","meaning": "Ptr Envelope","value": f"{self.envelope_address}","index": "0"},
                        {"name": "Sample Pointer Array", "datatype": "ABSound", "ispointer": "0", "isarray": "1", "arraylenfixed": "3", "meaning": "List of 3 Sounds for Splits",
                            "element": [
                                {"datatype": "ABSound", "ispointer": "0", "value": "0",
                                    "struct": {
                                        "name": "ABSound",
                                        "field": [
                                            {"name": "Sample Pointer", "datatype": "uint32", "ispointer": "1", "ptrto": "ABSample", "isarray": "0", "meaning": "Ptr Sample", "value": f"{low_sample_address}", "index": f"{low_sample_index}"},
                                            {"name": "Sample Tuning", "datatype": "float32", "ispointer": "0", "isarray": "0", "meaning": "None", "value": f"{low_sample.chan_tune if low_sample else 0.0}"}
                                        ]
                                    }
                                },
                                {"datatype": "ABSound", "ispointer": "0", "value": "0",
                                    "struct": {
                                        "name": "ABSound",
                                        "field": [
                                            {"name": "Sample Pointer", "datatype": "uint32", "ispointer": "1", "ptrto": "ABSample", "isarray": "0", "meaning": "Ptr Sample", "value": f"{prim_sample_address}", "index": f"{prim_sample_index}"},
                                            {"name": "Sample Tuning", "datatype": "float32", "ispointer": "0", "isarray": "0", "meaning": "None", "value": f"{prim_sample.chan_tune}"}
                                        ]
                                    }
                                },
                                {"datatype": "ABSound", "ispointer": "0", "value": "0",
                                    "struct": {
                                        "name": "ABSound",
                                        "field": [
                                            {"name": "Sample Pointer", "datatype": "uint32", "ispointer": "1", "ptrto": "ABSample", "isarray": "0", "meaning": "Ptr Sample", "value": f"{high_sample_address}", "index": f"{high_sample_index}"},
                                            {"name": "Sample Tuning", "datatype": "float32", "ispointer": "0", "isarray": "0", "meaning": "None", "value": f"{high_sample.chan_tune if high_sample else 0.0}"}
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        )

    def generate_drum_xml(self):
        index = 0
        for i in range(len(self.samples)):
            sample = self.samples[i]

            if sample is None:
                continue

            self.drums_xml.append(
                {
                    "address": f"{self.drum_address + (index * 0x10)}", "name": f"{sample.name} [{index}]",
                    "struct": {
                        "name": "ABDrum",
                        "field": [
                            {"name": "Decay Index", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "245"},
                            {"name": "Pan", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "64"},
                            {"name": "Relocated (Bool)", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "0"},
                            {"name": "Padding Byte", "datatype": "uint8", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "0"},
                            {"name": "Drum Sound", "datatype": "ABSound", "ispointer": "0", "isarray": "0", "meaning": "Drum Sound",
                                "struct": {
                                    "name": "ABSound",
                                    "field": [
                                        {"name": "Sample Pointer", "datatype": "uint32", "ispointer": "1", "ptrto": "ABSample", "isarray": "0", "meaning": "Ptr Sample", "value": f"{self.sample_address + (index * 0x10)}", "index": f"{index}"},
                                        {"name": "Sample Tuning", "datatype": "float32", "ispointer": "0", "isarray": "0", "meaning": "None", "value": f"{sample.key_tune}"}
                                    ]
                                }
                            },
                            {"name": "Envelope Pointer", "datatype": "uint32", "ispointer": "1", "ptrto": "ABEnvelope", "isarray": "0", "meaning": "Ptr Envelope", "value": f"{self.envelope_address}", "index": "0"}
                        ]
                    }
                }
            )

            index += 1

    def generate_sample_xml(self):
        index = 0
        for i in range(len(self.samples)):
            sample = self.samples[i]

            if sample is None:
                continue

            # A sample with loop_start of 0 is always assumed to be non-looping
            if sample.loop_start == 0:
                loop_size = 0x10
            else:
                loop_size = 0x30

            # Create the bitfield value
            bits = (1 & 1) << 25 | (0 & 1) << 24 | (sample.size & 0xFFFFFF)

            self.samples_xml.append(
                {
                    "address": f"{self.sample_address + (index * 0x10)}", "name": f"{sample.name} [{index}]",
                    "struct": {
                        "name": "ABSample",
                        # Leave this comment formatted as-is, it adds a nice prettified comment to each sample item explaining the bitfield
                        "__comment__": f"""
                 Below are the bitfield values for each bit they represent.
                 Each of these values takes up a specific amount of the 32 bits representing the u32 value.
                  1 Bit(s): Unk_0       (Bit(s) 1):    0
                  3 Bit(s): Codec       (Bit(s) 2-4):  CODEC_ADPCM (0)
                  2 Bit(s): Medium      (Bit(s) 5-6):  MEDIUM_RAM (0)
                  1 Bit(s): Cached      (Bit(s) 7):    True (1)
                  1 Bit(s): Relocated   (Bit(s) 8):    False (0)
                 24 Bit(s): Binary size (Bit(s) 9-32): {sample.size}
             """,
                        "field": [
                            {"name": "Bitfield", "datatype": "uint32", "ispointer": "0", "isarray": "0", "meaning": "None", "value": f"{bits}"},
                            {"name": "Audiotable Address", "datatype": "uint32", "ispointer": "0", "ptrto": "ATSample", "isarray": "0", "meaning": "Sample Address (in Sample Table)", "value": f"{int(sample.temp_addr, 16)}"},
                            {"name": "Loop Pointer", "datatype": "uint32", "ispointer": "1", "ptrto": "ALADPCMLoop", "isarray": "0", "meaning": "Ptr ALADPCMLoop", "value": f"{self.loopbook_address + (index * loop_size)}", "index": f"{index}"},
                            {"name": "Book Pointer", "datatype": "uint32", "ispointer": "1", "ptrto": "ALADPCMBook", "isarray": "0", "meaning": "Ptr ALADPCMBook", "value": f"{self.codebook_address + (index * 0x10)}", "index": f"{index}"}
                        ]
                    }
                }
            )

            index += 1

    def generate_loop_xml(self):
        index = 0
        for i in range(len(self.samples)):
            sample = self.samples[i]

            if sample is None:
                continue

            loop_size = 0x10
            loopbook_field = []

            if sample.loop_start != 0:
                loop_size = 0x30
                loopbook_field = [
                    {
                        "datatype": "ALADPCMTail", "ispointer": "0", "value": "0",
                        "struct": {
                            "name": "ALADPCMTail",
                            "field": [
                                {"name": "data", "datatype": "int16", "ispointer": "0", "isarray": "1", "arraylenfixed": "16", "meaning": "None",
                                    "element": [
                                        {"datatype": "int16", "ispointer": "0", "value": f"{predictor}"}
                                        for predictor in sample.loopbook_predictors
                                    ]
                                }
                            ]
                        }
                    }
                ]

            self.aladpcmloops_xml.append(
                {
                    "address": f"{self.loopbook_address + (index * loop_size)}", "name": f"{sample.name} Loop [{index}]",
                    "struct": {
                        "name": "ALADPCMLoop", "HAS_TAIL": f"{1 if sample.loop_start != 0 else 0}",
                        "field": [
                            {"name": "Loop Start", "datatype": "uint32", "ispointer": "0", "isarray": "0", "meaning": "Loop Start", "value": f"{sample.loop_start}"},
                            {"name": "Loop End (Sample Length if Count = 0)", "datatype": "uint32", "ispointer": "0", "isarray": "0", "meaning": "Loop End", "value": f"{sample.loop_end if sample.loop_start != 0 else sample.num_samples}"},
                            {"name": "Loop Count", "datatype": "int32", "ispointer": "0", "isarray": "0", "meaning": "Loop Count", "defaultval": "-1", "value": f"{-1 if sample.loop_start != 0 else 0}"},
                            {"name": "Number of Samples", "datatype": "uint32", "ispointer": "0", "isarray": "0", "meaning": "None", "value": f"{sample.num_samples if sample.loop_start != 0 else 0}"},
                            {"name": "Loopbook", "datatype": "ALADPCMTail", "ispointer": "0", "isarray": "1", "arraylenvar": "HAS_TAIL", "meaning": "Tail Data (if Loop Start != 0)", "element": loopbook_field}
                        ]
                    }
                }
            )

            index += 1

    def generate_book_xml(self):
        index = 0
        for i in range(len(self.samples)):
            sample = self.samples[i]

            if sample is None:
                continue

            codebooks = [
                {
                    "datatype": "ALADPCMPredictor", "ispointer": "0", "value": "0",
                    "struct": {
                        "name": "ALADPCMPredictor",
                        "field" : [
                            {"name": "data", "datatype": "int16", "ispointer": "0", "isarray": "1", "arraylenfixed": "16", "meaning": "None",
                                "element": [
                                    {"datatype": "int16", "ispointer": "0", "value": f"{predictor}"}
                                    for predictor in predictors
                                ]
                            }
                        ]
                    }
                }
                for predictors in sample.codebook_predictors
            ]

            self.aladpcmbooks_xml.append(
                {
                    "address": f"{self.codebook_address + (index * 0x10)}", "name": f"{sample.name} Book [{index}]",
                    "struct": {
                        "name": "ALADPCMBook", "NUM_PRED": "4",
                        "field": [
                            {"name": "Order", "datatype": "int32", "ispointer": "0", "isarray": "0", "meaning": "None", "value": "2"},
                            {"name": "Number of Predictors", "datatype": "int32", "ispointer": "0", "isarray": "0", "meaning": "NUM_PRED", "value": "4"},
                            {"name": "Codebook", "datatype": "ALADPCMPredictor", "ispointer": "0", "isarray": "1", "arraylenvar": "NUM_PRED", "meaning": "Array of Predictors", "element": codebooks}
                        ]
                    }
                }
            )

            index += 1

    def dict_to_xml(self, tag: str, d: dict, parent: xml.Element = None) -> xml.Element:
        element = xml.Element(tag)

        for key, value in d.items():
            if key == '__comment__':
                comment = xml.Comment(value)
                element.append(comment)

            elif isinstance(value, dict):
                self.dict_to_xml(key, value, element)

            elif isinstance(value, list):
                for item in value:
                    child = self.dict_to_xml(key, item)
                    element.append(child)

            else:
                element.set(key, str(value) if value is not None else "")

        if parent is not None:
            parent.append(element)

        return element

    def create_xml_bank(self, filename: str) -> None:
        xml_root = xml.Element('bank')

        xml_root.set('NUM_INST', '1')
        xml_root.set('NUM_DRUM', f'{self.num_samples}')
        xml_root.set('NUM_SFX',  '0')
        xml_root.set('ATnum',    '0')

        xml_tree = xml.ElementTree(xml_root)

        xml_data = [
            XMLDataEntry(XMLTags.ABINDEXENTRY, 'struct', self.abindexentry_xml),
            XMLDataEntry(XMLTags.ABHEADER,     'struct', [{"name": 'ABHeader'}]),
            XMLDataEntry(XMLTags.ABBANK,       'struct', self.abbank_xml),
            XMLDataEntry(XMLTags.ABDRUMLIST,   'struct', self.abdrumlist_xml),
            XMLDataEntry(XMLTags.ABSFXLIST,    'struct', self.absfxlist_xml),
            XMLDataEntry(XMLTags.INSTRUMENTS,  'item',   self.instruments_xml),
            XMLDataEntry(XMLTags.DRUMS,        'item',   self.drums_xml),
            XMLDataEntry(XMLTags.ENVELOPES,    'item',   self.envelopes_xml),
            XMLDataEntry(XMLTags.SAMPLES,      'item',   self.samples_xml),
            XMLDataEntry(XMLTags.ALADPCMBOOKS, 'item',   self.aladpcmbooks_xml),
            XMLDataEntry(XMLTags.ALADPCMLOOPS, 'item',   self.aladpcmloops_xml)
        ]

        for entry in xml_data:
            element = xml.Element(entry.parent_tag)

        if entry.parent_tag == 'abdrumlist':
            element.set('address', '16')

        for item in entry.xml_list:
            self.dict_to_xml(entry.xml_tag, item, element)

        xml_root.append(element)

        with open(f'{filename}_BANK.xml', 'wb') as f:
            xml.indent(xml_tree)
            xml_tree.write(f, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    print('This is a utility script meant to be used with the WAV to ZSOUND main script. On its own it has no functionality.')
