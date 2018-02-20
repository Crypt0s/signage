#/usr/bin/python

######### EARLY TRY WITH CTYPES ON GIFLIB - WOULD BE FUN TO FINISH ################
#import ctypes
#from ctypes import CDLL
#lib = CDLL("/usr/local/Cellar/giflib/5.1.4/lib/libgif.dylib")
#int_ptr = ctypes.POINTER(ctypes.c_int)
## create an integer pointer in python to hold the errorcode result.
#errcode = int_ptr()
##GifFileType *DGifOpenFileName(char *GifFileName, int *ErrorCode)
#lib.DGifOpenFileName("resources/test.gif")
###################################################################################

## Utilize Pillow to parse the GIF in python, turn it into some compatible c type for SDL ##
from PIL import Image
import io
import sdl2

def get_frames(filename):
    # create in-mem datastream as python filepointer to get save to write to memory
    gif = Image.open(filename)
    gif_frames = []

    frames = 0
    while gif:
        try:
            gif_data = io.BytesIO()
            gif.seek(frames)
            gif.save(gif_data, "gif")

            # each element in the gif_frames actually should be a file pointer?
            gif_data.seek(0)
            buffer = gif_data.read()

            image = sdl2.SDL_RWFromMem(buffer, len(buffer))

            # deref python longpointer type
            image = image.contents

            # load the image from the buffer and then add the resulting surface to the array
            gif_frames.append(sdl2.sdlimage.IMG_Load_RW(image, 0).contents)

        except EOFError:
            break
        frames += 1
    print "done processing %d frames" % (frames)
    return gif_frames