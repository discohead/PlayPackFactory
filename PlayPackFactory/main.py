import os
from pathlib import Path
import random
import shutil
from operator import floordiv
from typing import Generator
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from pydub.silence import detect_silence

'''
Refactor / abstract this Python script to accept an arbitrary list of arbitrarily deep directories
from which to collect all possible audio .wav files to be considered for a specified
folder of a Polyend Play sample pack. 

i.e. KICK = ["/my/909/kicks", "/my/808/kicks", "/my/other/weird/sample/pack/kicks"]

Then we recursively walk all of the directories and collect the paths to all audio .wav files found
Then randomly select from those to populate the "Kick" sub-folder of a sample pack.
As below, do the work to ensure the pack will meet the Polyend Play's limitations and sample pack requirements
Convert everything to 44.1 KHz sample rate and 16-bit depth, convert all samples from drum and percussion folders to mono, leave synth and bass samples as stereo
<= 20 Folders per sample pack, <= 255 Files per sample pack, <400kb per file, use reserved Fill keys
synth and bass samples should be C notes, use regex on the filenames, i.e. r"\sC[0-9\s]"
'''

PLAY_PACKS_DIR = "/Users/jaredmcfarland/Music/Samples/Play_Packs"
MASCHINE_DIR = "/Users/jaredmcfarland/Music/Samples/Maschine"
DRUMS = "Drums"
INSTRUMENTS = "Instruments"
ONE_SHOTS = "One Shots"

FILL_KEYS = ["Kick", "Snare", "HiHat", "Synth", "Bass"]
PERCUSSION_KEYS = ["Wooden", "Click"]
BLIP_KEYS = ["Blip & Blop", "Buzz", "Glitch", "Laser", "Zap"]
KEEPER_KINDS = FILL_KEYS + ["Percussion", "Tom", "Cymbal", "Metal", "Blip", "Vocal", "Hand Drum", "Mallet Drum", "Noise", "Chord", "Stab & Hit"]
IGNORE_KINDS = ["Combo", "Lick", "Scratch"]
LIBRARY_MAP = {}

REBUILD_ALL = False
NEW_PACKS = {"Infinite Escape", "Higher Place"}

def detect_silence_at_end(audio: AudioSegment, silence_thresh: float = -48.0, min_silence_len: int = 250) -> bool:
    """
    Detects if the audio ends with silence.

    Args:
        audio (AudioSegment): The audio segment to analyze.
        silence_thresh (float): The silence threshold in dBFS (default: -50 dBFS).
        min_silence_len (int): The minimum length of silence in milliseconds (default: 500 ms).

    Returns:
        bool: True if the end of the audio contains silence, False otherwise.
    """
    # Check if there is silence in the last segment of the audio
    end_silence = detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

    if end_silence:
        # Get the last silent range
        last_silence_start, last_silence_end = end_silence[-1]

        # Check if the last silent segment extends to the end of the file
        if last_silence_end == len(audio):  # Length of the audio in milliseconds
            return True

    return False


def trim_silence_from_end(audio: AudioSegment, silence_thresh: float = -48.0,
                          min_silence_len: int = 250) -> AudioSegment:
    """
    Trims silence only from the end of an audio file, ensuring that non-silent sections
    are not removed.

    Args:
        audio (AudioSegment): The audio file to trim.
        silence_thresh (float): The silence threshold in dBFS (default: -50 dBFS).
        min_silence_len (int): The minimum length of silence in milliseconds (default: 500 ms).

    Returns:
        AudioSegment: The audio file with silence trimmed from the end.
    """
    if detect_silence_at_end(audio, silence_thresh, min_silence_len):
        # Detect silent parts
        silent_ranges = detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

        # Get the start time of the last silent section
        end_of_last_non_silent = silent_ranges[-1][0]

        # Trim the audio up to that point (cutting off the silence at the end)
        return audio[:end_of_last_non_silent]

    return audio  # Return the original audio if no trailing silence is detected


def convert_to_441khz_16bit(wav_file_path: str, is_drum: bool) -> None:
    """
    Converts the input .wav file to 44.1 kHz sample rate and 16-bit depth.

    Args:
        wav_file_path (str): The path to the input .wav file.
        :param wav_file_path:
        :param is_drum:
    """
    # Load the audio file
    audio = AudioSegment.from_wav(wav_file_path)

    trimmed_audio = trim_silence_from_end(audio)

    trimmed_audio.set_frame_rate(44100)
    trimmed_audio.set_sample_width(2)

    if is_drum:
        trimmed_audio.set_channels(1)

    trimmed_audio.export(wav_file_path, format="wav")

def list_files_in_directory(directory_path: str) -> Generator[str, None, None]:
    """
    Recursively lists all files in a given directory and its subdirectories.

    Args:
        directory_path (str): The absolute path to the directory.

    Yields:
        str: The full path to each file found.
    """
    for dirpath, _, filenames in os.walk(directory_path):
        for filename in filenames:
            folders = dirpath.split("/")
            category = ""
            kind = ""
            library = ""
            if len(folders) > 8 and not folders[6] == "Loops" and folders[7] not in IGNORE_KINDS and filename[-3:] == "wav":
                category = folders[6]
                kind = folders[7]
                for fill_key in FILL_KEYS:
                    if fill_key.lower() in kind.lower():
                        kind = fill_key
                    elif kind == "Clap":
                        kind = "Snare"
                    elif kind == "Shaker":
                        kind = "HiHat"
                    elif "bass " in filename.lower() or "sub " in filename.lower():
                        kind = "Bass"
                    elif "tamb" in filename.lower():
                        kind = "HiHat"
                    elif kind in PERCUSSION_KEYS:
                        kind = "Percussion"
                    elif kind in BLIP_KEYS:
                        kind = "Blip"
                    elif "Metal" in kind or kind == "Strike":
                        kind = "Metal"
                    elif category == "Instruments" or kind == "Guitar" or kind == "Keys":
                        kind = "Synth"
                    elif "note" in kind.lower():
                        kind = "Synth"
                library = folders[8][:-8]
                yield category, kind, library, filename, os.path.join(dirpath, filename)

def build_library_map(source_directory: str, target_directory: str) -> None:
    """
    Copies all files from the source directory to the target directory, maintaining
    the directory structure.

    Args:
        source_directory (str): The directory to copy files from.
        target_directory (str): The directory to copy files to.
    """
    for category, kind, library, filename, file_path in list_files_in_directory(source_directory):
        # TODO: Toggle NEW_PACKS check when necessary
        if library in NEW_PACKS or REBUILD_ALL:
            destination_path = os.path.join(target_directory, library, kind)

            if library not in LIBRARY_MAP:
                LIBRARY_MAP[library] = {}

            if kind not in LIBRARY_MAP[library]:
                LIBRARY_MAP[library][kind] = []

            if os.path.getsize(file_path) < 400 * 1024:
                LIBRARY_MAP[library][kind].append([Path(file_path), Path(destination_path+"/"), category == "Drums"])

    to_remove = []
    for lib_key, lib_val in LIBRARY_MAP.items():
        for kind_key, kind_val in lib_val.items():
            if len(kind_val) == 0:
                to_remove.append([lib_key, kind_key])

    for x in to_remove:
        del LIBRARY_MAP[x[0]][x[1]]


def main():
    build_library_map(MASCHINE_DIR, PLAY_PACKS_DIR)
    for lib_key, lib_val in LIBRARY_MAP.items():
        all_kinds = list(lib_val.keys())
        total_kinds = len(all_kinds)
        print(f'{lib_key}: {total_kinds}')
        if len(all_kinds) > 20:
            print(f'total_kinds = {total_kinds}')
            for k in all_kinds:
                if k not in KEEPER_KINDS:
                    all_kinds.remove(k)
                    print(f'removed kind {k} - new len {len(all_kinds)}')
                    if len(all_kinds) <= 20:
                        break

            if len(all_kinds) > 20:
                print('kinds STILL > 20')
                for k in all_kinds:
                    if k not in FILL_KEYS:
                        all_kinds.remove(k)
                        print(f'removed kind {k} - new len {len(all_kinds)}')
                        if len(all_kinds) <= 20:
                            break

            if len(all_kinds) > 20:
                print("!!! ALL KINDS STILL GREATER THAN 20 !!!")

        files_per_kind = floordiv(255, len(all_kinds))
        files_inserted = 0
        files_left = 255
        i = 1
        not_empty = True
        while files_left > 0 and not_empty:
            files_per_kind = floordiv(files_per_kind, i)
            not_empty = False
            for kind_key, kind_val in lib_val.items():
                if kind_key in all_kinds:
                    sample_num = min(files_per_kind, len(kind_val))
                    if sample_num > 0:
                        not_empty = True
                        files_left -= sample_num
                        if files_left > 0:
                            random_subset = random.sample(kind_val, sample_num)
                            lib_val[kind_key] = [x for x in kind_val if x not in random_subset]
                            for file_pair in random_subset:
                                file_path = file_pair[0]
                                destination_path = file_pair[1]
                                is_drum = file_pair[2]
                                os.makedirs(destination_path, exist_ok=True)
                                new_file = shutil.copy2(file_path, destination_path)
                                files_inserted += 1
                                try:
                                    convert_to_441khz_16bit(new_file, is_drum)
                                except CouldntDecodeError:
                                    pass
            i += 1
        print(f'{lib_key} - files inserted {files_inserted} - files left {files_left}')


if __name__ == '__main__':
    main()
