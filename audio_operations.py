import sys
from datetime import timedelta
from pydub import AudioSegment

def loop_audio(audio_file, file_name, number_of_hours):
    """
    Function loops an audio file till it has reached the hour limit given by the user
    :param audio_file: the AudioSegment object into which the audio has been loaded
    :param file_name: name of the original audio file
    :param number_of_hours: number of hours the looped audio must reach
    :return: exported audio file
    """
    if number_of_hours > 5:
        print("The limit for looping is 5 hours")
        return

    target_time = timedelta(hours=number_of_hours)

    final_audio = AudioSegment.empty()

    while timedelta(seconds=final_audio.duration_seconds) < target_time:
        final_audio += audio_file

    file_type = get_file_type()

    # Working around the inherent m4a limitation in the ffmpeg library
    export_format = ""
    if file_type == "m4a":
        export_format = "ipod"
    else:
        export_format = file_type

    return final_audio, file_type, export_format

def get_file_name(file_path):
    """
    Function gets the file name from the file path
    :param file_path: relative path of the audio file
    :return: the file name of the audio file, excluding the file type
    """
    file_length = len(file_path)
    file_name = ""

    for i in range(1, file_length + 1):
        if file_path[-i] == "/":
            break
        else:
            file_name += file_path[-i]

    return (file_name[::-1])[:-4]

def get_file_type():
    # dummy value
    return "m4a"