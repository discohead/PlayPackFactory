#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import random
import shutil
from typing import List, Dict, Any
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from pydub.silence import detect_silence
import re
from faker import Faker

'''
Refactored Python script to generalize the conversion of audio samples from Native Instruments Maschine Expansion packs into the folder structure expected by the Polyend Play for its sample packs.

This script allows specifying arbitrary lists of directories for each subfolder of the resulting Polyend Play sample pack. It recursively collects all .wav files from the specified source directories for each subfolder, processes them to meet the Polyend Play's requirements, and populates the sample pack folders accordingly.

Features:
- Define any number of subfolders with their respective source directories.
- Convert audio files to 44.1 kHz sample rate and 16-bit depth.
- Convert specified subfolders to mono; others remain stereo.
- Ensure sample pack limitations: <= 20 folders, <= 255 files, <400KB per file.
- Use reserved Fill keys.
- For synth and bass samples, select only C notes based on filename regex.
- Exclude specified directories when collecting samples for certain subfolders.
- Include only directories containing specified substrings when collecting samples for certain subfolders.
- Automatically generate unique two-word names for new sample packs.
'''

KICK_DIRS = [
    "/Users/jaredmcfarland/Music/Samples/Riemann/Ethno Afro Deep House/OneShots (WAV)/ASHRAM Ethno Deep House Kicks",
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/Kickdrums",
    "/Users/jaredmcfarland/Music/Samples/JoMoX Alpha Base/1 - Kicks",
    "/Users/jaredmcfarland/Music/Samples/Elektron/Thump_Smack/MoKicks909",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Kicks",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Kicks/arkicks",
    "/Users/jaredmcfarland/Music/Samples/Fridell Samples/kicks",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Packs/Electronisounds/Kicks",
    "/Users/jaredmcfarland/Music/Samples/Goldbaby/StompBox_VolcaKick",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Drum Kits/Kicks",
    "/Users/jaredmcfarland/Music/Samples/CardOne/BOOMIN/Kicks",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/1. Kick",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Factory Drums/1. Kick",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/CR78 From Mars/One Shots/Individual Hits/Re-Pitched/Kick",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/CR78 From Mars/One Shots/Individual Hits/Re-Pitched/Hi Kick",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Rhythm From Mars/Individual Hits/SP-Rhythm/Kick",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Rhythm From Mars/Individual Hits/Rhythm 700/Kick",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SDSV From Mars/1. Kick",
    "/Users/jaredmcfarland/Music/Samples/Too Many DFAM Kicks by Tony Tyson",
    "/Users/jaredmcfarland/Music/Samples/Disting EX/StompBox_VolcaKick",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Irrupt/Irrupt Eurorack/Drum Hits/Kicks",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/EAR Gothenburg Drums/Kicks",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/Kicks",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Vocal Drums and Percussion/Vocal kick",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Nektar's Acoustic Drums/Kicks",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Raw Cutz/Raw Cutz Sampler 1/Kicks",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EFM/EFM Kicks",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Kicks",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/PI/PI Kicks",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/TRX/TRX Kicks",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/FR909/FR909 Kicks",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/Kick",
    "/Users/jaredmcfarland/Music/Samples/ARC Noise/kicks",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/Drums/Kick",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/kicks",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/kicks",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/kicks",
]

SNARE_DIRS = [
    "/Users/jaredmcfarland/Music/Samples/Riemann/Ethno Afro Deep House/OneShots (WAV)/ASHRAM Ethno Deep House Claps",
    "/Users/jaredmcfarland/Music/Samples/Riemann/Ethno Afro Deep House/OneShots (WAV)/ASHRAM Ethno Deep House Snares",
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/Claps",
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/Snares",
    "/Users/jaredmcfarland/Music/Samples/JoMoX Alpha Base/4 - Clap_Rim",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/909/SNARE",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/808/SNARE",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Snares",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Claps",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Perc Synth/arrims",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Packs/Electronisounds/Claps",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Packs/Electronisounds/Snares",
    "/Users/jaredmcfarland/Music/Samples/Goldbaby/DecoClapTrap",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Drum Kits/claps",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Drum Kits/Snares",
    "/Users/jaredmcfarland/Music/Samples/CardOne/BOOMIN/Claps",
    "/Users/jaredmcfarland/Music/Samples/CardOne/BOOMIN/Snares",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX/13. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX/11. Rimshot",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX 612/13. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX 612/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX 612/11. Rimshot",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/2. Snare",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/6. Rim",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/3. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Factory Drums/2. Snare",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/07. Rim Shot",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/03. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC60 From Mars/04. Rim",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC60 From Mars/03. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC60 From Mars/02. Snare",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/04. Rim",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/03. Clap & Snap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/03. SP1200/08. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/03. SP1200/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/03. SP1200/06. Rimshot",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/08. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/14. Combo Hits/04. Rimshot",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/14. Combo Hits/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/14. Combo Hits/06. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/06. Rimshot",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/909 From Mars/05. Hand Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/909 From Mars/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/909 From Mars/04. Rim Shot",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/CR78 From Mars/One Shots/Individual Hits/Re-Pitched/Rim",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/CR78 From Mars/One Shots/Individual Hits/Re-Pitched/Snare",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Rhythm From Mars/Individual Hits/SP-Rhythm/Snare",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Rhythm From Mars/Individual Hits/Rhythm 700/Snare",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Drumulator From Mars/Drumulator MPC/03. Rim",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Drumulator From Mars/Drumulator MPC/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Drumulator From Mars/Drumulator MPC/07. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SDSV From Mars/2. Snare",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/14. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/06. Rim Shot",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/14. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/06. Rim Shot",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/03. Rim Shot",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/02. Snare Drum",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/04. Clap",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DX100 From Mars/Xylo Snare",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SDS800 From Mars/Snare",
    "/Users/jaredmcfarland/Music/Samples/Disting EX/DecoClapTrap",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Cristian Vogel/Cristian Vogel Bitwig Lab/KSP8 Rims",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Cristian Vogel/Cristian Vogel Bitwig Lab/10 NeverEngine Snares",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Cristian Vogel/Cristian Vogel Bitwig Lab/Moog Gravel Snare",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Irrupt/Irrupt Eurorack/Drum Hits/Snares",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/EAR Gothenburg Drums/Claps",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/EAR Gothenburg Drums/Snares",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/EAR Gothenburg Drums/Rims",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/Claps",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/Snares",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Vocal Drums and Percussion/Vocal snare",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Nektar's Acoustic Drums/Snares",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Raw Cutz/Raw Cutz Sampler 1/Snares",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EFM/EFM Rims",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EFM/EFM Claps",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EFM/EFM Snares",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Rims",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Claps",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Snares",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/PI/PI Rims",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/PI/PI Snares",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/TRX/TRX Rims",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/TRX/TRX Snares",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/TRX/TRX Claps",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/FR909/FR909 Rims",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/FR909/FR909 Snares",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/FR909/FR909 Claps",
    "/Users/jaredmcfarland/Music/Samples/DMD_Packs/DMD/Snare",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/Snare",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/Clap",
    "/Users/jaredmcfarland/Music/Samples/ARC Noise/snares",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/Drums/Snare",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/Drums/Clap",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/snares",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/snares",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/snares",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/claps",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/claps",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/claps",
]

HIHAT_DIRS = [
    "/Users/jaredmcfarland/Music/Samples/Riemann/Ethno Afro Deep House/OneShots (WAV)/ASHRAM Ethno Deep House HiHats",
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/HiHats",
    "/Users/jaredmcfarland/Music/Samples/JoMoX Alpha Base/3 - Hats",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/909/HIHAT",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/808/HIHAT",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Hats",
    "/Users/jaredmcfarland/Music/Samples/Fridell Samples/hi-hats",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Packs/Electronisounds/Hats",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Packs/Electronisounds/Shakers",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Drum Kits/Hihats",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Percussion/Shaker",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Percussion/Tambourine",
    "/Users/jaredmcfarland/Music/Samples/CardOne/BOOMIN/Hi Hats",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX/12. Shaker",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX/10. Tamb",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX 612/12. Shaker",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX 612/10. Tamb",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/9. Shaker",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/8. Tambourine",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Factory Drums/8. Tambourine",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/09. Shaker",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC60 From Mars/06. Cabasa Tamb",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC60 From Mars/05. HH/CH/CH Tambo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/05. Hi Hat",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/05. Hi Hat/CH Tamb",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/07. Shaker & Cabasa",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/11. Tambourine",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/03. SP1200/09. Tambourine",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/09. Tambourine",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/909 From Mars/06. Hi Hat",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Rhythm From Mars/Individual Hits/SP-Rhythm/Tambo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SDSV From Mars/4. Hi Hat",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/Maracas",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/09. Tambourine",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/05. Closed Hat",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/06. Open Hat",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Irrupt/Irrupt Eurorack/Drum Hits/Hats",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/EAR Gothenburg Drums/Hi-Hats",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/Hi Hats",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Tolcha's Tambourines",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Tolcha's Shakers",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Nektar's Acoustic Drums/Hi-Hats",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Raw Cutz/Raw Cutz Sampler 1/Hi-Hats",
    "/Users/jaredmcfarland/Music/Samples/batches_dirt/hat",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EFM/EFM Hats",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Shakers",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Tamborine",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Hats",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/PI/PI Maracas",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/PI/PI Hats",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/TRX/TRX Maracas",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/TRX/TRX Hats",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/FR909/FR909 Hats",
    "/Users/jaredmcfarland/Music/Samples/DMD_Packs/DMD/HiHat",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/Shaker",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/HiHat",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/Tambourine",
    "/Users/jaredmcfarland/Music/Samples/ARC Noise/hats",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/Drums/Shaker",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/Drums/HiHat",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/cybmals/closed hats",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/cybmals/closed hats",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/cybmals/closed hats",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/cybmals/open hats",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/cybmals/open hats",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/cybmals/open hats",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/percussion/shakers",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/percussion/shakers",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/percussion/shakers",
]

PERC_DIRS = [
    "/Users/jaredmcfarland/Music/Samples/Riemann/Ethno Afro Deep House/OneShots (WAV)/ASHRAM Ethno Deep House Perc",
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/Percussion",
    "/Users/jaredmcfarland/Music/Samples/Found Percussion",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/909/PERCUSSION",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/808/CONGA",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/808/PERCUSSION",
    "/Users/jaredmcfarland/Music/Samples/Musicradar/percussion-samples",
    "/Users/jaredmcfarland/Music/Samples/fingerperc",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Hats/metalic_hts",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Perc Real",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Perc Synth",
    "/Users/jaredmcfarland/Music/Samples/Fridell Samples/percussion",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Packs/Electronisounds/Perc",
    "/Users/jaredmcfarland/Music/Samples/CardOne/OmegaGMGS2/DrumPerc",
    "/Users/jaredmcfarland/Music/Samples/CardOne/Basimilus Iteritas Alter/BIA_METAL",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Drum Kits/Timbales",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Ethnic/Tabla",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Ethnic/Samples/Tabla",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Ethnic/Samples/Percussion 2",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Ethnic/Samples/Percussion 1",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Percussion",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MS10 From Mars/Triangle",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/10. Congas",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/15. Perc",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/11. Cowbell",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Factory Drums/9. Cowbell",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/11. Bell/Bell Virtual/Bell Wood",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/05. CH/CH Metal",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/08. Clave",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/15. Resonant Hits/Resonant Hits Wood",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/15. Resonant Hits/Resonant Hits Metal",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/10. Cymbal/Cymbal Metal",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC60 From Mars/07. Percussion",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/10. Conga & Bongo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/09. Cowbell",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/13. Ride/Cymbal Modular Metal",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/08. Clave & Woodblock",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/03. SP1200/07. Cowbell",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/14. Combo Hits/05. Cowbell",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/07. Cowbell",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/CR78 From Mars/One Shots/Individual Hits/Re-Pitched/Conga",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/CR78 From Mars/One Shots/Individual Hits/Re-Pitched/Various Percussion",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Rhythm From Mars/Individual Hits/SP-Rhythm/Perc",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Rhythm From Mars/Individual Hits/Rhythm 700/Perc",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Drumulator From Mars/Drumulator MPC/09. Cowbell",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Drumulator From Mars/Drumulator MPC/08. Clave",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/12. Cowbell Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/13. Cowbell Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/09. Conga Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/11. Timbale",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/10. Conga Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/12. Cowbell Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/13. Cowbell Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/09. Conga Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/11. Timbale",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/10. Conga Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/03. Kits/10. Bongos",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/03. Kits/04. Congas 1",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/03. Kits/05. Congas 2",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/03. Kits/06. Congas & Cabasas",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/03. Kits/09. Timbales",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/01. Clean/02. Flams/Conga Lo Flam",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/01. Clean/02. Flams/Timbale Hi Flam",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/01. Clean/02. Flams/Conga Hi Mute Flam",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/01. Clean/02. Flams/Conga Hi Open Flam",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/01. Clean/02. Flams/Timbale Lo Flam",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/01. Unpitched/02. Flams/Conga Lo Flam",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/01. Unpitched/02. Flams/Timbale Hi Flam",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/01. Unpitched/02. Flams/Conga Hi Mute Flam",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/01. Unpitched/02. Flams/Conga Hi Open Flam",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/01. Unpitched/02. Flams/Timbale Lo Flam",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/02. Flams/Conga Hi Open Pitched Flams",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/02. Flams/Timbale Hi Pitched Flams",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/02. Flams/Conga Hi Mute Pitched Flams",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/02. Flams/Conga Lo Pitched Flams",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/02. Flams/Timbale Lo Pitched Flams",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/Agogo Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/Bongo Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/Timbale Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/Conga Hi Open",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/Bongo Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/Timbale Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/Agogo Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/Conga Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/Conga Hi Mute",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/10. Claves",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/12. Cowbell",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/11. Wood Block",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DX100 From Mars/Metal Tube",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DX100 From Mars/Wood Piano",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SK1 From Mars/Sampler/ThreePercs",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Found Sounds From Mars/Wood",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Found Sounds From Mars/Metal",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/2600 From Mars/One Hits/Drums/Kits/Synth Perc",
    "/Users/jaredmcfarland/Music/Samples/Echo Sound Works/Organic Percussion",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Cristian Vogel/Cristian Vogel Bitwig Lab/Morphed Percussive Things",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Cristian Vogel/Cristian Vogel Bitwig Lab/Pedros Conga",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bajaao/Drums and Indian Percussion/Indian Percussion",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Irrupt/Irrupt Eurorack/Drum Hits/Percussion",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/EAR Gothenburg Drums/Percussion",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/EAR Gothenburg Drums/Cowbells",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/Artificial Percussion",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/Bio Percussion",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Tolcha's Timbales",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Tolcha's Conga",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Tolcha's Djembe",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Vocal Drums and Percussion/Vocal mid percussion",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Vocal Drums and Percussion/Vocal hi percussion",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Tolcha's Cowbells",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Tolcha's Bongos",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Tolcha's Woodblocks",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EFM/EFM Cowbells",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Triangles",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Bonga Conga",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Cowbell",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/PI/PI Metal",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/TRX/TRX Claves",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/TRX/TRX Congas",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/TRX/TRX Cowbell",
    "/Users/jaredmcfarland/Music/Samples/Caelum Audio/Household Percussion Vol. II",
    "/Users/jaredmcfarland/Music/Samples/Caelum Audio/Household Percussion [Vol 1]",
    "/Users/jaredmcfarland/Music/Samples/DMD_Packs/DMD/Percussion",
    "/Users/jaredmcfarland/Music/Samples/CO5MA Freaking Percs",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/Metallic",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/Wooden",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/Percussion",
    "/Users/jaredmcfarland/Music/Samples/Maschine/One Shots/Metal",
    "/Users/jaredmcfarland/Music/Samples/ARC Noise/percussion",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/Drums/Metallic",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/Drums/Wooden",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/percussion/blocks & cowbells",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/percussion/blocks & cowbells",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/percussion/blocks & cowbells",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/percussion/dissonant hits",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/percussion/dissonant hits",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/percussion/dissonant hits",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/percussion/plucks",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/percussion/plucks",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/percussion/plucks",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/percussion/pops, snaps & rim shots",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/percussion/pops, snaps & rim shots",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/percussion/pops, snaps & rim shots",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/percussion/soft & dark hits",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/percussion/soft & dark hits",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/percussion/soft & dark hits",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/percussion/tubes",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/percussion/tubes",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/percussion/tubes",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/conga & bongo",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/conga & bongo",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/conga & bongo",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/exotic",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/exotic",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/exotic",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/imaginary-drums",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/imaginary-drums",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/imaginary-drums",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/strikes",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/strikes",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/strikes",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/stabs",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/stabs",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/stabs",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/swells",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/swells",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/swells",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/bass/percussive bass",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/bass/percussive bass",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/bass/percussive bass",
]

TOM_DIRS = [
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/Toms",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/909/TOM",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/808/TOM",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Toms",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Drum Kits/Toms",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX/07. Tom B",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX/06. Tom A",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX 612/07. Tom B",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX 612/06. Tom A",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/7. Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Factory Drums/6. Toms",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/04. Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC60 From Mars/08. Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/06. Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/03. SP1200/05. Tom Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/03. SP1200/03. Tom Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/03. SP1200/04. Tom Mid",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/05. Tom Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/14. Combo Hits/03. Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/03. Tom Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/02. Modified/04. Tom Mid",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/909 From Mars/03. Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Rhythm From Mars/Individual Hits/SP-Rhythm/Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Rhythm From Mars/Individual Hits/Rhythm 700/Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Voyetra From Mars/Syn Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SH5 From Mars/Syn Toms",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Drumulator From Mars/Drumulator MPC/11. Tom Mid",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Drumulator From Mars/Drumulator MPC/12. Tom Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Drumulator From Mars/Drumulator MPC/10. Tom Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SDSV From Mars/3. Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/05. Tom Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/03. Tom Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505/04. Tom Mid",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/05. Tom Hi",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/03. Tom Lo",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/505 From Mars/505 SP1200/04. Tom Mid",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/07. Tom",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/2600 From Mars/One Hits/Drums/Individual Hits/Toms",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SDS800 From Mars/Toms",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Synare From Mars/01. One Hits/03. Tom",
    "/Users/jaredmcfarland/Music/Samples/Disting EX/LABS Drm_Toms Sq [6T]",
    "/Users/jaredmcfarland/Music/Samples/Disting EX/LABS Drm_Toms Mx [6T]",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Cristian Vogel/Cristian Vogel Bitwig Lab/Low Tom Musician Room",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/EAR Gothenburg Drums/Toms",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/Toms",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Nektar's Acoustic Drums/Toms",
    "/Users/jaredmcfarland/Music/Samples/batches_dirt/tom",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EFM/EFM Toms",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Toms",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/PI/PI Toms",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/TRX/TRX Toms",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/FR909/FR909 Toms",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/Tom",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/Drums/Tom",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/toms",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/toms",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/toms",
]

CYMBAL_DIRS = [
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/Rides",
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/Crashes",
    "/Users/jaredmcfarland/Music/Samples/JoMoX Alpha Base/5 - Ride",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/909/CYMBAL",
    "/Users/jaredmcfarland/Music/Samples/Caught On Tape/808/CYMBAL",
    "/Users/jaredmcfarland/Music/Samples/DMD-3/DMD3 Cymbals",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Packs/Electronisounds/Rides",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Drum Kits/Ride",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX/09. Crash",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX/08. Ride",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX 612/09. Crash",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DMX From Mars/DMX 612/08. Ride",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/13. Cymbal",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Custom Drums/12. Crash",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Factory Drums/10. Crash",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Drums/Factory Drums/11. Cymbal",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Modular Drums From Mars/WAV/01. Individual Hits/10. Cymbal",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC60 From Mars/09. Cymbal",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/14. Crash",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MPC3000 From Mars/13. Ride",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/03. SP1200/13. Ride",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/707 From Mars/03. SP1200/12. Crash",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/RIde Chime",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/727 From Mars/02. Tape/02. Pitched/01. Hits/RIde Chime",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/14. Crash",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Drums/13. Ride",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/EAR Gothenburg Drums/Cymbals",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Bitwig Drum Machines/Crashes And Rides",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Percussion/Tolcha's Crashbox",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Nektar's Acoustic Drums/Cymbals",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Nektar's Acoustic Drums/Cymbals/Crashes",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EFM/EFM Cymbals",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Crashes",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/EP12/EP12 Rides",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/PI/PI Rides",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/PI/PI Crashes",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/FR909/FR909 Rides",
    "/Users/jaredmcfarland/Music/Samples/DMD-MD/FR909/FR909 Crashes",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Drums/Cymbal",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/Drums/Cymbal",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/cymbals/crash & splash",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/cymbals/crash & splash",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/cymbals/crash & splash",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/cymbals/effect cymbals",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/cymbals/effect cymbals",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/cymbals/effect cymbals",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/processed drums/cymbals/rides",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/unprocessed drums/cymbals/rides",
    "/Users/jaredmcfarland/Music/Samples/wa_synth_drums/special processed drums/cymbals/rides",
]

SYNTH_DIRS = [
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/Basses",
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/Synth",
    "/Users/jaredmcfarland/Music/Samples/JoMoX Alpha Base/6 - FM Synth",
    "/Users/jaredmcfarland/Music/Samples/Hainbach/Synth Test",
    "/Users/jaredmcfarland/Music/Samples/Hainbach/Synths",
    "/Users/jaredmcfarland/Music/Samples/MPC Instruments",
    "/Users/jaredmcfarland/Music/Samples/Plughugger/BASS",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Synths",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Packs/Electronisounds/Basses",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Packs/Electronisounds/Synths",
    "/Users/jaredmcfarland/Music/Samples/Goldbaby/MoogMG1vsAD_SynthFX",
    "/Users/jaredmcfarland/Music/Samples/CardOne/OmegaGMGS2/Bass",
    "/Users/jaredmcfarland/Music/Samples/CardOne/OmegaGMGS2/Synth",
    "/Users/jaredmcfarland/Music/Samples/CardOne/OmegaGMGS2/Vocal",
    "/Users/jaredmcfarland/Music/Samples/CardOne/OmegaGMGS2/DrumPerc",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Strings",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Bassoon",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Bass",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Synth",
    "/Users/jaredmcfarland/Music/Samples/CardOne/synthetic",
    "/Users/jaredmcfarland/Music/Samples/Goldbaby",
    "/Users/jaredmcfarland/Music/Samples/Loopmasters",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Synths",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Acid From Mars/Acid Synths",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Voyetra From Mars",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SH5 From Mars",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Soviet Synths From Mars",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Mini From Mars",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Synths",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DX100 From Mars",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SK1 From Mars/Synthesizer",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/101 From Mars",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/2600 From Mars",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SDS800 From Mars/Bass",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/MS10 From Mars",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Synare From Mars/02. Chromatic",
    "/Users/jaredmcfarland/Music/Samples/Benn Jordan/Moog Bass",
    "/Users/jaredmcfarland/Music/Samples/Electromagnetic Recordings/Synths",
    "/Users/jaredmcfarland/Music/Samples/Disting EX"
    "/Users/jaredmcfarland/Music/Samples/Legowelt/BASS",
    "/Users/jaredmcfarland/Music/Samples/Legowelt/SYNTH",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Irrupt/Irrupt System/SYNTHS",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Irrupt/Irrupt System/BASS",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Sneaky's Acoustic Bass",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Sampled Synths Vol. 1",
    "/Users/jaredmcfarland/Music/Samples/Maschine/One Shots/Synth Note",
    "/Users/jaredmcfarland/Music/Samples/Maschine/One Shots/Bass",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Instruments/Bass",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Instruments/Synth",
    "/Users/jaredmcfarland/Music/Samples/ARC Noise/bass",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/One Shots/Synth Note",
]

VOCAL_DIRS = [
    "/Users/jaredmcfarland/Music/Samples/Riemann/Ethno Afro Deep House/Loops (WAV)/ASHRAM Ethno Deep House Vocal Loops",
    "/Users/jaredmcfarland/Music/Samples/Loopmasters/Loopmasters Past/SOUL/Underground Soul Vocals 2",
    "/Users/jaredmcfarland/Music/Samples/Loopmasters/Loopmasters Past/SOUL/Underground Soul Vocals 2/VOCALS",
    "/Users/jaredmcfarland/Music/Samples/Loopmasters/Loopmasters Future/AFRICAN/Vocal Africa",
    "/Users/jaredmcfarland/Music/Samples/Hainbach/Files/Vocals",
    "/Users/jaredmcfarland/Music/Samples/CardOne/OmegaGMGS2/Vocal",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Synth/Samples/Vocal Padds",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Synth/Samples/Synth Vox 2",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Synths/Glitch Leads/Vox Choir",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/S612 From Mars/Synths/Various Vocals",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SK1 From Mars/Sampler/BasicVox",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SK1 From Mars/Sampler/VoxHarmony",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SK1 From Mars/Sampler/VoxBass",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SK1 From Mars/Sampler/DreamyVox",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Business Class Refugees/EM BoyeBoye Cm 122Bpm/Vocals",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Dubstep India Bundle/EM Dubstep India Vocals",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Voice Of India Bundle/EM Mantra Vocals",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Voice Of India Bundle/EM Mantra Vocals/Female Mantra vocals D freestyle",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Voice Of India Bundle/EM Mantra Vocals/Male Mantra vocals E 70bpm",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Voice Of India Bundle/EM Baul Vocals",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Voice Of India Bundle/EM Baul Vocals/Male Baul Vocals F 90bpm",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Voice Of India Bundle/EM Rajasthani Vocals",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Voice Of India Bundle/EM Rajasthani Vocals/Male Rajasthani vocals F 90bpm",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Voice Of India Bundle/EM Bollywood Vocals",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Earth Moments/Earth Moments Loops (teaser)/Voice Of India Bundle/EM Bollywood Vocals/Female Bollywood Vocals C 80bpm",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Capsun ProAudio/Capsun ProAudio Loops (teaser)/Vox - The Vocal Toolkit Vol 1",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Prime Loops/Prime Loops Bass Music (teaser)/Total Samples - Revolvr Twerk Revolution/Vox",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Prime Loops/Prime Loops Bass Music (teaser)/Prime Loops - Total Drum & Bass Volume 7/SFX/Vox",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Prime Loops/Prime Loops Deeper (teaser)/Future Koncept - Baile - Future Chill/Vox Samples",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Prime Loops/Prime Loops Deeper (teaser)/Toneworxx - Pure House Vocals",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Prime Loops/Prime Loops Deeper (teaser)/Toneworxx - Pure House Vocals/Male Vox FX",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Prime Loops/Prime Loops Deeper (teaser)/Toneworxx - Pure House Vocals/Female Vox FX",
    "/Users/jaredmcfarland/Music/Samples/batches_dirt/vox",
    "/Users/jaredmcfarland/Music/Samples/batches_dirt/sir",
    "/Users/jaredmcfarland/Music/Samples/Maschine/One Shots/Vocal",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Instruments/Vocal",
    "/Users/jaredmcfarland/Music/Samples/Maschine/Loops/Vocal",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/One Shots/Vocal",
    "/Users/jaredmcfarland/Music/Samples/Jamie Lidell/Vocal"
]

CHORD_DIRS = [
    "/Users/jaredmcfarland/Music/Samples/Barker Chords",
    "/Users/jaredmcfarland/Music/Samples/Riemann/Ethno Afro Deep House/Loops (WAV)/ASHRAM Deep House Chord Loops",
    "/Users/jaredmcfarland/Music/Samples/Riemann/Techno Oneshots 2/Chords",
    "/Users/jaredmcfarland/Music/Samples/Elektron/Lo-Fi_Hip-Hop/Chord",
    "/Users/jaredmcfarland/Music/Samples/Fridell Samples/chords & stabs",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory/Packs/Electronisounds/Chords",
    "/Users/jaredmcfarland/Music/Samples/CardOne/No Budget Orchestra/Harpsichord",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Synths/DX100 Dusty Chords",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Synths/DX100 Xylo Chord",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Synths/DX100 Dark Chord",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Synths/DX100 Classic Chord",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SP1200 From Mars/Synths/Polysix Chord LFO",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Voyetra From Mars/New Age Harpsichord",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/SH5 From Mars/Sync Pulse Chord",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/Soviet Synths From Mars/04. Keys and Chords",
    "/Users/jaredmcfarland/Music/Samples/Samples From Mars/DX100 From Mars/Harpsichord",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Cristian Vogel/Cristian Vogel Bitwig Lab/EMS Filtered chords (2008)",
    "/Users/jaredmcfarland/Music/Samples/Bitwig/Bitwig/Sampled Synths Vol. 1/ASM Chords",
    "/Users/jaredmcfarland/Music/Samples/Maschine/One Shots/Chord",
    "/Users/jaredmcfarland/Music/Samples/Battery 4/One Shots/Chord"
]

MISC_DIRS = [
    "/Users/jaredmcfarland/Music/Samples/ARC Noise",
    "/Users/jaredmcfarland/Music/Samples/Abandoned Factory",
    "/Users/jaredmcfarland/Music/Samples/Ableton",
    "/Users/jaredmcfarland/Music/Samples/Buchla Drums",
    "/Users/jaredmcfarland/Music/Samples/CO5MA Freaking Percs",
    "/Users/jaredmcfarland/Music/Samples/Caelum Audio",
    "/Users/jaredmcfarland/Music/Samples/CardOne",
    "/Users/jaredmcfarland/Music/Samples/DSP Seasons",
    "/Users/jaredmcfarland/Music/Samples/Dirtywave Factory",
    "/Users/jaredmcfarland/Music/Samples/Echo Sound Works",
    "/Users/jaredmcfarland/Music/Samples/Elektron",
    "/Users/jaredmcfarland/Music/Samples/Fridell Samples",
    "/Users/jaredmcfarland/Music/Samples/Goldbaby",
    "/Users/jaredmcfarland/Music/Samples/HAND",
    "/Users/jaredmcfarland/Music/Samples/Hainbach",
    "/Users/jaredmcfarland/Music/Samples/Jamie Lidell",
    "/Users/jaredmcfarland/Music/Samples/Legowelt",
    "/Users/jaredmcfarland/Music/Samples/Modbase 09",
    "/Users/jaredmcfarland/Music/Samples/Musicradar",
    "/Users/jaredmcfarland/Music/Samples/Oneven - FM",
    "/Users/jaredmcfarland/Music/Samples/Phoenix Industrial",
    "/Users/jaredmcfarland/Music/Samples/Plughugger",
    "/Users/jaredmcfarland/Music/Samples/Polyplex",
    "/Users/jaredmcfarland/Music/Samples/QUADRANT_SAMPLES",
    "/Users/jaredmcfarland/Music/Samples/RCA WA-44",
    "/Users/jaredmcfarland/Music/Samples/Riemann",
    "/Users/jaredmcfarland/Music/Samples/S-Layer",
    "/Users/jaredmcfarland/Music/Samples/batches_dirt",
]

ALL_DRUM_DIRS = PERC_DIRS + SNARE_DIRS + HIHAT_DIRS + CYMBAL_DIRS + TOM_DIRS
ALL_NOTE_DIRS = SYNTH_DIRS + CHORD_DIRS + VOCAL_DIRS
ALL_DIRS = ALL_DRUM_DIRS + ALL_NOTE_DIRS + MISC_DIRS


C_NOTES_SYNTH = r"(^|[_\s])C[3-6](?=[_\s]?$)"
C_NOTES_BASS = r"(^|[_\s])C[0-2](?=[_\s]?$)"
C_NOTES_ALL = r"(^|[_\s])C-?[0-9](?=[_\s]?$)"
DSHARP_NOTES_ALL = r"(^|[_\s])(D#|Eb)-?[0-6](?=[_\s]?$)"
G_NOTES_ALL = r"(^|[_\s])G[0-6](?=[_\s]?$)"
F_NOTES_ALL = r"(^|[_\s])F[0-6](?=[_\s]?$)"
ASHARP_NOTES_ALL = r"(^|[_\s])(A#|Bb)-?[0-6](?=[_\s]?$)"

HQ_DIRS = [
    "Maschine",
    "Battery",
    "DMD",
    "Mars",
    "Bitwig",
    "Dirtywave",
    "Disting",
    "Elektron",
    "Caught",
    "JoMoX",
    "Disting",
    "wa_synth_drums"
]

# Configuration mapping for each subfolder in the Polyend Play sample pack
SUBFOLDER_CONFIG: Dict[str, Dict[str, Any]] = {
    "Kick": {
        "source_dirs": KICK_DIRS,
        "channels": 1,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Snare": {
        "source_dirs": SNARE_DIRS,
        "channels": 1,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "HiHat": {
        "source_dirs": HIHAT_DIRS,
        "channels": 1,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Synth": {
        "source_dirs": SYNTH_DIRS,
        "channels": 2,
        "regex": C_NOTES_SYNTH,
        "include_dirs": [],
        "exclude_dirs": ["chord"],
    },
    "Bass": {
        "source_dirs": SYNTH_DIRS,
        "channels": 1,
        "regex": C_NOTES_BASS,
        "include_dirs": [],
        "exclude_dirs": ["chord"],
    },
    "Percussion": {
        "source_dirs": PERC_DIRS,
        "channels": 1,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Tom": {
        "source_dirs": TOM_DIRS,
        "channels": 1,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Cymbal": {
        "source_dirs": CYMBAL_DIRS,
        "channels": 1,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Vocal": {
        "source_dirs": VOCAL_DIRS,
        "channels": 2,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Chord": {
        "source_dirs": CHORD_DIRS,
        "channels": 2,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Third": {
        "source_dirs": ALL_NOTE_DIRS,
        "channels": 2,
        "regex": DSHARP_NOTES_ALL,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Fourth": {
        "source_dirs": ALL_NOTE_DIRS,
        "channels": 2,
        "regex": F_NOTES_ALL,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Fifth": {
        "source_dirs": ALL_NOTE_DIRS,
        "channels": 2,
        "regex": G_NOTES_ALL,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "XDrum": {
        "source_dirs": ALL_DRUM_DIRS,
        "channels": 1,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Misc": {
        "source_dirs": MISC_DIRS,
        "channels": 1,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    },
    "Random": {
        "source_dirs": ALL_DIRS,
        "channels": 1,
        "regex": None,
        "include_dirs": [],
        "exclude_dirs": [],
    }
    # Add more subfolders as needed
}

PLAY_PACKS_DIR = "/Users/jaredmcfarland/Music/Samples/Play_Factory"

MAX_FOLDERS_PER_PACK = 20
MAX_FILES_PER_PACK = 255
MAX_FILE_SIZE_KB = 400

# Define the number of new packs to create
NUM_NEW_PACKS = 5  # Change this number as needed

# Toggle to determine whether to rebuild all packs or only new ones
REBUILD_ALL = False

# Initialize Faker
fake = Faker()


def generate_unique_two_word_names(n: int, existing_names: set = None) -> set:
    """
    Generates a set of unique two-word names.

    Args:
        n (int): Number of unique names to generate.
        existing_names (set, optional): A set of names to exclude from generation to ensure uniqueness.

    Returns:
        set: A set containing n unique two-word names.
    """
    if existing_names is None:
        existing_names = set()

    names = set()
    while len(names) < n:
        word1 = fake.unique.word().capitalize()
        word2 = fake.unique.word().capitalize()
        name = f"{word1} {word2}"
        if name not in existing_names:
            names.add(name)
    return names


def detect_silence_at_end(audio: AudioSegment, silence_thresh: float = -48.0, min_silence_len: int = 250) -> bool:
    """
    Detects if the audio ends with silence.

    Args:
        audio (AudioSegment): The audio segment to analyze.
        silence_thresh (float): The silence threshold in dBFS (default: -48.0).
        min_silence_len (int): The minimum length of silence in milliseconds (default: 250 ms).

    Returns:
        bool: True if the end of the audio contains silence, False otherwise.
    """
    # Detect silent parts in the audio
    silent_ranges = detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

    if silent_ranges:
        # Get the last silent range
        last_silence_start, last_silence_end = silent_ranges[-1]
        # Check if silence extends to the end of the audio
        if last_silence_end >= len(audio):
            return True
    return False

def trim_silence_from_end(audio: AudioSegment, silence_thresh: float = -48.0, min_silence_len: int = 250) -> AudioSegment:
    """
    Trims silence only from the end of an audio file, ensuring that non-silent sections are not removed.

    Args:
        audio (AudioSegment): The audio file to trim.
        silence_thresh (float): The silence threshold in dBFS (default: -48.0).
        min_silence_len (int): The minimum length of silence in milliseconds (default: 250 ms).

    Returns:
        AudioSegment: The audio file with silence trimmed from the end.
    """
    if detect_silence_at_end(audio, silence_thresh, min_silence_len):
        silent_ranges = detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
        last_silence_start, _ = silent_ranges[-1]
        return audio[:last_silence_start]
    return audio

def convert_audio(wav_file_path: Path, channels: int) -> None:
    """
    Converts the input .wav file to 44.1 kHz sample rate, 16-bit depth, and specified number of channels.
    Trims silence from the end.

    Args:
        wav_file_path (Path): The path to the input .wav file.
        channels (int): Number of audio channels (1 for mono, 2 for stereo).
    """
    try:
        # Load the audio file
        audio = AudioSegment.from_wav(wav_file_path)

        # Trim silence from the end
        trimmed_audio = trim_silence_from_end(audio)

        # Set frame rate and sample width
        trimmed_audio = trimmed_audio.set_frame_rate(44100).set_sample_width(2)

        # Set channels
        trimmed_audio = trimmed_audio.set_channels(channels)

        # Export the processed audio
        trimmed_audio.export(wav_file_path, format="wav")
    except CouldntDecodeError:
        print(f"Could not decode audio file: {wav_file_path}")
    except Exception as e:
        print(f"Error processing file {wav_file_path}: {e}")


def collect_wav_files(source_dirs: List[str], regex: str = None, include_dirs: List[str] = None, exclude_dirs: List[str] = None) -> List[Path]:
    """
    Recursively collects all .wav files from the specified source directories.
    If a regex is provided, only files matching the regex are included.
    Optionally includes only directories containing specified substrings.
    Optionally excludes directories containing specified substrings.

    Args:
        source_dirs (List[str]): List of source directories to search.
        regex (str, optional): Regular expression to filter filenames.
        include_dirs (List[str], optional): List of substrings; directories must contain at least one of these.
        exclude_dirs (List[str], optional): List of substrings; directories containing any of these will be excluded.

    Returns:
        List[Path]: List of paths to .wav files.
    """
    wav_files = []
    pattern = re.compile(regex, re.IGNORECASE) if regex else None

    for source_dir in source_dirs:
        for dirpath, dirnames, filenames in os.walk(source_dir):
            current_dir_path_lower = str(dirpath).lower()

            # Apply include_dirs filter
            if include_dirs:
                if not any(incl.lower() in current_dir_path_lower for incl in include_dirs):
                    continue  # Skip directories that don't include required substrings

            # Apply exclude_dirs filter
            if exclude_dirs:
                if any(excl.lower() in current_dir_path_lower for excl in exclude_dirs):
                    continue  # Skip directories containing excluded substrings

            for filename in filenames:
                if filename.lower().endswith(".wav"):
                    file_path = Path(dirpath) / filename
                    try:
                        file_size_kb = file_path.stat().st_size / 1024
                    except FileNotFoundError:
                        print(f"File not found: {file_path}")
                        continue

                    if file_size_kb <= MAX_FILE_SIZE_KB:
                        if pattern:
                            if pattern.search(filename):
                                wav_files.append(file_path)
                        else:
                            wav_files.append(file_path)
    return wav_files

def build_sample_map(subfolder_config: Dict[str, Dict[str, Any]]) -> Dict[str, List[Path]]:
    """
    Builds a mapping from subfolder names to lists of .wav file paths based on the configuration.

    Args:
        subfolder_config (Dict[str, Dict[str, Any]]): Configuration for each subfolder.

    Returns:
        Dict[str, List[Path]]: Mapping from subfolder names to lists of .wav file paths.
    """
    sample_map = {}
    for subfolder, config in subfolder_config.items():
        source_dirs = config.get("source_dirs", [])
        regex = config.get("regex")
        include_dirs = config.get("include_dirs", [])
        exclude_dirs = config.get("exclude_dirs", [])
        wav_files = collect_wav_files(source_dirs, regex, include_dirs, exclude_dirs)
        sample_map[subfolder] = wav_files
        print(f"Collected {len(wav_files)} files for subfolder '{subfolder}'")
    return sample_map

def create_sample_pack(pack_name: str, sample_map: Dict[str, List[Path]], output_dir: str) -> None:
    """
    Creates a sample pack by selecting random samples from each subfolder's list and processing them.

    Args:
        pack_name (str): Name of the sample pack.
        sample_map (Dict[str, List[Path]]): Mapping from subfolder names to lists of .wav file paths.
        output_dir (str): Directory where the sample pack will be created.
    """
    pack_dir = Path(output_dir) / pack_name
    pack_dir.mkdir(parents=True, exist_ok=True)

    # Initialize tracking variables
    total_files_inserted = 0
    files_left = MAX_FILES_PER_PACK
    selected_files = {subfolder: [] for subfolder in sample_map}

    # Filter out subfolders with no available files
    available_subfolders = [k for k, v in sample_map.items() if len(v) > 0]

    # If more than MAX_FOLDERS_PER_PACK, prioritize subfolders based on some criteria (e.g., FILL_KEYS first)
    if len(available_subfolders) > MAX_FOLDERS_PER_PACK:
        # Prioritize FILL_KEYS (assuming FILL_KEYS are the primary subfolders)
        FILL_KEYS = ["Kick", "Snare", "HiHat", "Synth", "Bass"]
        prioritized_subfolders = [k for k in FILL_KEYS if k in available_subfolders]
        remaining_subfolders = [k for k in available_subfolders if k not in prioritized_subfolders]
        selected_subfolders = prioritized_subfolders[:MAX_FOLDERS_PER_PACK]
        if len(selected_subfolders) < MAX_FOLDERS_PER_PACK:
            selected_subfolders += remaining_subfolders[:MAX_FOLDERS_PER_PACK - len(selected_subfolders)]
    else:
        selected_subfolders = available_subfolders.copy()

    print(f"Selected {len(selected_subfolders)} subfolders for pack '{pack_name}'")

    # Initialize the list of kinds to include
    all_kinds = selected_subfolders.copy()

    # Implement the iterative selection to approach MAX_FILES_PER_PACK
    files_inserted = 0
    files_left = MAX_FILES_PER_PACK
    i = 1
    not_empty = True

    # Make a copy of sample_map to manipulate
    remaining_samples = {k: v.copy() for k, v in sample_map.items() if k in all_kinds}

    while files_left > 0 and not_empty:
        if len(all_kinds) == 0:
            break  # Prevent division by zero
        files_per_kind = MAX_FILES_PER_PACK // len(all_kinds)
        if i > 0:
            files_per_kind = files_per_kind // i
        not_empty = False

        for kind_key in all_kinds:
            kind_val = remaining_samples.get(kind_key, [])
            if not kind_val:
                continue
            sample_num = min(files_per_kind, len(kind_val))
            if sample_num > 0:
                not_empty = True
                files_left -= sample_num
                if files_left < 0:
                    sample_num += files_left  # Adjust to not exceed the limit
                    files_left = 0
                if sample_num > 0:
                    random_subset = random.sample(kind_val, sample_num)
                    remaining_samples[kind_key] = [x for x in kind_val if x not in random_subset]
                    selected_files[kind_key].extend(random_subset)
                    files_inserted += sample_num
        i += 1

    print(f"Creating sample pack '{pack_name}' with {files_inserted} files")

    for subfolder, files in selected_files.items():
        if not files:
            continue
        dest_subfolder = pack_dir / subfolder
        dest_subfolder.mkdir(parents=True, exist_ok=True)
        channels = SUBFOLDER_CONFIG[subfolder].get("channels", 2)

        for file_path in files:
            dest_file_path = dest_subfolder / file_path.name
            try:
                shutil.copy2(file_path, dest_file_path)
                convert_audio(dest_file_path, channels)
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
                # Attempt to delete the destination file if it exists
                try:
                    if dest_file_path.exists():
                        dest_file_path.unlink()
                        print(f"Deleted incomplete file: {dest_file_path}")
                except Exception as delete_error:
                    print(f"Failed to delete {dest_file_path}: {delete_error}")

    print(f"Sample pack '{pack_name}' created at {pack_dir}")


def delete_hidden_files(directory: str) -> None:
    """
    Recursively deletes hidden files from the given directory and its subdirectories.

    Hidden files are considered as files starting with a dot (e.g., .DS_Store).

    Args:
        directory (str): The path to the directory from which hidden files should be deleted.
    """
    # Walk through directory and subdirectories
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Check if the file is hidden (starts with a dot)
            if file.startswith('.'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted hidden file: {file_path}")
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

def main():
    # Setup command-line argument parsing
    parser = argparse.ArgumentParser(description="Generate Polyend Play sample packs from Native Instruments Maschine Expansion packs.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Define 'pack' subcommand
    pack_parser = subparsers.add_parser('pack', help='Generate new sample packs')
    pack_parser.add_argument('num_packs', type=int, help='Number of sample packs to generate')

    args = parser.parse_args()

    if args.command == 'pack':
        num_packs = args.num_packs

        if num_packs <= 0:
            print("Number of packs must be a positive integer.")
            return

        # Generate unique two-word names for new packs
        existing_packs = set()

        # Optionally, scan the PLAY_PACKS_DIR to avoid name collisions
        if os.path.exists(PLAY_PACKS_DIR):
            existing_packs = set(os.listdir(PLAY_PACKS_DIR))

        try:
            new_pack_names = generate_unique_two_word_names(num_packs, existing_names=existing_packs)
        except Exception as e:
            print(f"Error generating pack names: {e}")
            return

        print(f"Generated new pack names: {new_pack_names}")

        # Build the sample map based on configuration
        sample_map = build_sample_map(SUBFOLDER_CONFIG)

        # Iterate over each pack to be created
        for pack_name in new_pack_names:
            create_sample_pack(pack_name, sample_map, PLAY_PACKS_DIR)

        delete_hidden_files(PLAY_PACKS_DIR)

        print("All sample packs have been created successfully.")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()