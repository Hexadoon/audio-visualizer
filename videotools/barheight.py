import numpy as np

magnitude = np.vectorize(np.absolute, signature='(m,n)->(m,n)')
vfft = np.vectorize(np.fft.rfft, signature='(m,n)->(m,k)')

# for a given frame, returns the heights of each bar
def bar_height(frame, blocks, points_per_bar):
    """ breaks up the result of an FFT into 'blocks' amount of sections, isolates the max in the section
        and that maximum is used as the height of a bar in the video """
    heights = [] 
    for i in range(blocks):
        curr_h = 0
        for j in range(points_per_bar):
            if frame[i*points_per_bar+j] > curr_h:
                curr_h = frame[i*points_per_bar + j]

        heights.append(curr_h)

    return np.array(heights)


class VideoProcessor:
    def __init__(self, vwidth, vheight, framerate, blocks, audiofile):
        """ vheight/width are the dimensions of the video
            framerate is the framerate
            blocks is the amount of bars to be displayed in each frame
            audiofile is the scipy.io.wavfile (after conversion) that's being used """
        
        self.vheight = vheight
        self.vwidth = vwidth
        self.framerate = framerate
        self.blocks = blocks

        self.samples_per_frame = audiofile[0]//framerate
        self.audio = audiofile[1]


    def decompose(self):
        """ given an audio file and samples_per_frame (which is the sample rate divided by
            the frame rate), decomposes the audio and returns a 2D numpy array where 
            along axis 0 are the frames and along axis 1 are the heights of the bars in that frame """

        print("converting to mono")
        if len(self.audio.shape) > 1 and self.audio.shape[1] > 1:
            # convert stereo to mono via simply adding the channels
            self.audio = np.sum(self.audio, axis=1)
        
        # now 'audio' represents an array of audio frames, where each array
        # corresponds to a frame in the video
        print(f"converted. resizing {self.audio.shape[0]}")
        self.audio.resize(self.audio.shape[0]//self.samples_per_frame-1, self.samples_per_frame)
        
        # transformed applies a real-valued fast fourier transform on each frame
        # a frame is a section of samples in the wav file, as framerate goes up
        # the accuracy decreases, while the framerate of the video increases
        # 60 fps is probably a good compromise
        print(f"resized. transforming {self.audio.shape}->{self.audio.shape[0]*self.audio.shape[1]}")
        transformed = vfft(self.audio)

        # the output of the rfft is complex, we want the magnitudes of these numbers
        # to get the actual magnitude of that frequency (which will be the height of the bar)
        print(f"transformed, taking magnitudes {transformed.shape}")
        transformed = magnitude(transformed)
        print(f"magnitudes taken, calculating bar heights {np.amax(transformed)}")    
        
        points_per_bar = (transformed.shape[1]//self.blocks) 
        #                 ^samples per frame    ^ per bar
        
        for i in range(4):
            if points_per_bar >> 1 > 0:
                points_per_bar >>= 1
        # this loop cuts off high ends while trying to keep as much information as is necessary


        get_heights = np.vectorize(bar_height, signature='(m),(),()->(k)')
        
        video_bar_heights = get_heights(transformed, self.blocks, points_per_bar)
        
        print(f"bar heights calculated {video_bar_heights.shape}")

        return video_bar_heights 

