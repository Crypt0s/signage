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
from PIL import Image, ImageSequence
import io
import sdl2
import sdl2.sdlimage

# cribbed from https://gist.github.com/skywodd/8b68bd9c7af048afcedcea3fb1807966
def resize(filename, out=None):
    gif = Image.open(filename) #.convert('RGBA')

    size = (64,64)

    if gif.size == (64,64):
        return True

    frames = [frame.copy() for frame in ImageSequence.Iterator(gif)]

    print "processed %s frames" % (str(len(frames)))
    def thumbnails(frames):
        for frame in frames:
            thumbnail = frame.copy()
            thumbnail.thumbnail(size, Image.ANTIALIAS)
            yield thumbnail

    frames = thumbnails(frames)
    outframes = []
    try:
        while 1:
            outframes.append(next(frames).convert("RGBA"))
    except StopIteration:
        pass

    output = outframes[0]
    output.info = gif.info

    # Debug 
    if out != None:
        filename = out

    output.save(filename, save_all=True, append_images=outframes)


def get_frames(filename):
    try:
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
                img = sdl2.sdlimage.IMG_Load_RW(image, 1).contents
                gif_frames.append(img)
                import pdb;pdb.set_trace()
                #print len(gif_frames)
                #SDL_FreeSurface(img)

            except EOFError:
                break
            #SDL_FreeSurface(image)
            frames += 1
        print "done processing %d frames" % (frames)
        return gif_frames

    except IOError:
        print "read err - retrying..."
        return get_frames(filename)
    except:
        return []

if __name__ == "__main__":
    resize("/tmp/current2.gif","/opt/signage/resources/web/current.gif")
