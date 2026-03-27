from aiortc import AudioStreamTrack
from pyrnnoise import RNNoise
import numpy as np


class FrameSplitterTrack(AudioStreamTrack):

    def __init__(self, track, frame_size=960):
        super().__init__()
        self.track = track
        self.frame_size = frame_size
        self.rnnoise = RNNoise(sample_rate=48000)
        self.initialized = False

    async def recv(self):
        frame = await self.track.recv()
        audio_data = frame.to_ndarray()

        if audio_data.ndim == 1:
            audio_data = np.expand_dims(audio_data, axis=0)

        if not self.initialized:
            self.rnnoise.channels = audio_data.shape[0]
            self.rnnoise.dtype = audio_data.dtype
            self.initialized = True

        _, denoised_audio = self.rnnoise.denoise_frame(audio_data)

        frame.from_ndarray(denoised_audio, layout=frame.layout.name)
        return frame
