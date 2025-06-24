import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfilt

def butter_bandpass(lowcut, highcut, fs, order):
    return butter(order, [lowcut, highcut], btype='band', fs=fs, output='sos')

def phone(input_path, output_path, order, gain):
    sample_rate, audio_data = wav.read(input_path)
    audio_data = audio_data.astype(float)

    if audio_data.ndim == 2 and gain == 0:
        left = audio_data[:, 0]
        right = audio_data[:, 1]
        mid = (left + right) / 2
        side = (left - right) / 2 * 0.3
        left = mid + side
        right = mid - side
        sos = butter_bandpass(800, 12000, sample_rate, order)
        left_filtered = sosfilt(sos, left)
        right_filtered = sosfilt(sos, right)
        filtered = np.vstack([left_filtered, right_filtered]).T
    else:
        sos = butter_bandpass(800, 12000, sample_rate, order)
        filtered = sosfilt(sos, audio_data)

    filtered = np.clip(filtered, -32768, 32767).astype(np.int16)
    wav.write(output_path, sample_rate, filtered)


def car(input_path, output_path, order, gain):
    sample_rate, audio_data = wav.read(input_path)
    audio_data = audio_data.astype(float)

    if audio_data.ndim == 2:
        left = audio_data[:, 0]
        right = audio_data[:, 1]
        mid = (left + right) / 2
        side = (left - right) / 2 * gain
        left = mid + side
        right = mid - side
        sos = butter(order, 3000, btype='low', fs=sample_rate, output='sos')
        left_filtered = sosfilt(sos, left)
        right_filtered = sosfilt(sos, right)
        filtered = np.vstack([left_filtered, right_filtered]).T
    else:
        sos = butter(order, 3000, btype='low', fs=sample_rate, output='sos')
        filtered = sosfilt(sos, audio_data)

    filtered = np.clip(filtered, -32768, 32767).astype(np.int16)
    wav.write(output_path, sample_rate, filtered)
