#!/usr/bin/python
# -*- coding: utf-8 -*-

# We'll use sys to properly exit with an error code.
import os
import sys
import sdl2
import sdl2.ext
import sdl2.sdlttf
import sdl2.sdlimage
import ctypes
from sdl2 import *
import os
import ConfigParser
import time
import requests
import math
import resources.giflib
import multiprocessing
import resources.webserver

# Create a resource container, so that we can easily access all
# resource, we bundle with our application. We are using the current
# file's location and define the "resources" subdirectory as the
# location, in which we keep all data.
RESOURCES = sdl2.ext.Resources(__file__, "resources")

class FileNotFound(Exception):
    def __init__(self, message):
        print message


class BadFile(Exception):
    def __init__(self, filename):
        print "Bad File Format For File %s" % filename

# Process and display each frame of a GIF onto the SDL Surface
class Gif:
    def __init__(self, config, window, x, y):
        self.x = x
        self.y = y
        self.window = window
        self.frames = None
        self.frame_index = 0
        self.get_frames()
        self.config = config
        self.framerate = 1.0 / config.getfloat("GIF", "fps")
        self.lasttime = 0

    def get_frames(self):
        if self.frames is not None:
            for i in self.frames:
                SDL_FreeSurface(i)
        frames = resources.giflib.get_frames("resources/web/current.gif")
        print "got :: " + str(len(frames))
        self.frames = frames
        self.frame_index = 0

    def draw(self):
        # get this draw()s frame
        frame = self.frames[self.frame_index]

        # boilerplate drawing stuff
        window = self.window
        window_pointer = ctypes.POINTER(sdl2.SDL_Window)
        lp_window = ctypes.cast(id(window), window_pointer)
        screen = window.get_surface()

        # blit the frame onto the window surface
        SDL_BlitSurface(frame, None, screen, None)
        SDL_UpdateWindowSurface(lp_window)

        # cleanup
        SDL_FreeSurface(screen)

        del window_pointer
        del lp_window
        del window

    def tick(self):
        self.draw()

        # we draw the frame every tick, but we dont draw a new frame every tick.
        now = time.time()
        if now > (self.lasttime + self.framerate):
            self.lasttime = now
            self.frame_index += 1

        # get the next frame but if we've completed the gif, get a new one.
        if self.frame_index >= len(self.frames):
            self.get_frames()

# display a user-defined message in the surface.
class Message:
    def __init__(self, config, window, s_val, x, y):
        self.x = x
        self.y = y
        self.window = window
        self.s_val = s_val

    def draw(self):
        draw_text(self.window, None, text=self.s_val.value, x=self.x, y=self.y, size=7)

    def tick(self):
        self.draw()

# Tell the time.
class Clock:
    def __init__(self, config, window, x, y):
        self.x = x
        self.y = y
        self.window = window
        self.date_format = config.get("CLOCK","date_format")
        self.time_format = config.get("CLOCK","time_format")

    def draw(self):
        date = time.strftime(self.date_format)
        timenow = "    " + time.strftime(self.time_format)

        draw_text(self.window, None, text=date, x=self.x, y=self.y, size=10)
        draw_text(self.window, None, text=timenow, x=self.x, y=self.y+9)

    def tick(self):
        self.draw()


class Emoji:
    """
    Allows for the loading of Emojis as sprites of different sizes via spritesheets, allows templates via config file.
    """
    def __init__(self, size, x, y, emoji):
        """
        :param size: font size (in px) of the emoji
        :param x: x position of the emoji on screen
        :param y: y position of emoji on screen
        :param emoji: int emoji number in the spritesheet
        """
        self.size = size
        self.x = x
        self.y = y
        self.sprite = None

        sprite_template = config.get("SPRITES", "emoji_spritesheet")
        sprite_template = sprite_template % self.size

        if not os.path.exists(sprite_template):
            raise FileNotFound("Emoji Spritefile not found: %s" % sprite_template)
        self.spritesheet = sprite_template

        #sprite = Sprite(location, number, size, x, y)
        self.sprite = Sprite(sprite_template, emoji, self.size, 0, 0)


class EmojiTime:
    """
    A class which is loaded into the eventloop which can display emoji's at specific intervals.  Think Big Ben?
    """
    def __init__(self, spriteManager):
        # How often will we display the emoji?  In seconds.
        self.interval = config.getint("EMOJITIME", "interval")
        self.emoji = config.getint("EMOJITIME", "emoji")
        self.size = config.getint("EMOJITIME", "size")

        self.current_emoji = Emoji(self.size, 0, 0, self.emoji).sprite
        self.spriteManager = spriteManager

        self.duration = config.getint("EMOJITIME", "duration")
        self.active = 0

    def draw(self):
        return

    def tick(self):

        if int(time.time()) % self.interval == 0:
            self.active = int(time.time())
            print "EMOJITIME!"
            # remove our current sprite from the manager - we're going to display something else.
            self.spriteManager.remove_sprite(self.current_emoji)

            # load the new sprite
            self.current_emoji = Emoji(self.size, 0, 0, self.emoji).sprite
            self.spriteManager.add_sprite(self.current_emoji)
            self.draw()

        elif self.active > 0 and (time.time() - self.active) > self.duration:
            self.spriteManager.remove_sprite(self.current_emoji)



class Sprite:
    """
    Sprite class manages loading a sheet of square sprites
    The spacing variable lets us know how spaced they are from each other, and the sheet will be cut up

    Sprites are assigned like this:

    1,2,3,4
    5,6,7,8
    9......

    """
    def __init__(self, spritesheet_location, number, size, x, y):
        self.x = x
        self.y = y
        self.size = size
        self.location = spritesheet_location
        self.sheet = sdl2.sdlimage.IMG_Load(self.location).contents

        row_size = self.sheet.w / self.size
        num_rows = self.sheet.h / self.size

        x_position = number % row_size

        y_position = math.ceil(number / row_size)
        x_position = (self.size * x_position) % self.sheet.w
        y_position = self.size * y_position

        x_position -= size
        if x_position < 0:
            x_position = 0

        print "Getting Sprite at : %d,%d" % (x_position, y_position)
        self.sprite = sdl2.rect.SDL_Rect(int(x_position), int(y_position), self.size, self.size)


class SpriteManager:
    """
    SpriteManager holds a buncha sprites.
    Sprites hold the data on their cutouts from their spritesheets as well as their x/y positions on-screen
    """
    def __init__(self, config, window):
        """
        :param window: pySDL2 window
        """
        self.config = config
        self.sprites = []
        self.window = window

    def add_sprite(self, sprite):
        self.sprites.append(sprite)

    def remove_sprite(self, sprite):
        """
        :param sprite: int | Sprite
        """
        if isinstance(sprite, Sprite):
            for i in self.sprites:
                if sprite == i:
                    self.sprites.remove(sprite)
        elif isinstance(sprite, int):
            self.sprites.pop(sprite)

    def draw(self):
        for i in self.sprites:
            self.drawsprite(i)

    def drawsprite(self, sprite):
        # make a rect which will be used to put the sprite at a specific position at the screen
        position = sdl2.rect.SDL_Rect(sprite.x, sprite.y)

        # draw the sprite onto the surface of the window with Blit.
        window = self.window
        window_pointer = ctypes.POINTER(sdl2.SDL_Window)
        lp_window = ctypes.cast(id(window), window_pointer)
        screen = window.get_surface()

        SDL_BlitSurface(sprite.sheet, sprite.sprite, screen, position)
        SDL_UpdateWindowSurface(lp_window)

        #del sprite
        del position
        SDL_FreeSurface(screen)
        del window_pointer
        del lp_window
        del window

    # draw sprites every tick
    def tick(self):
        self.draw()


# convenience class to hold some Icon PNG Surfaces for drawing, only used by weather for now.
class Icon:
    def __init__(self, location):
        if not os.path.exists(location):
            raise FileNotFound("icon file at location %s was not found" % location)
        self.location = location
        self.surface = self.__get_surface()

    # load the surface from the icon.
    def __get_surface(self):
        surface = sdl2.sdlimage.IMG_Load(self.location)
        if surface is None:
            raise BadFile(self.location)
        return surface


class News:
    def __init__(self, config, window, x, y):
        self.config = config
        self.window = window
        self.x = x
        self.y = y
        self.apikey = config.get("NEWS","apikey")
        self.url = config.get("NEWS", "url")
        self.source = config.get("NEWS", "source")
        self.update_interval = config.getint("NEWS", "update")
        self.last_update = time.time()
        self.news = ""
        self.current_text = ""
        self.text_index = 0
        self.display_chars = 12

        self.get_news()

    def get_news(self):
        self.last_update = time.time()
        self.news = "" #""SAMPLE TEXT FOR THIS PROJECT>>>END"
        parameters = "?sources=%s&apiKey=%s" % (self.source, self.apikey)
        request_url = self.url+parameters
        print request_url

        try:
            news_request = requests.get(request_url)
        except:
            print "exception in news request"
            return 1

        if news_request.status_code != 200:
            oops = "Invalid response %d" % news_request.status_code
            print oops
            self.news = oops
            return

        news_articles = news_request.json()['articles']
        for item in news_articles:
            self.news += " <<< " + item['title'].encode("ascii", "ignore")
        return

    def tick(self):
        # every time we tick we should draw.
        self.draw()
        self.text_index = (self.text_index + 1) % len(self.news)
        if (time.time() - self.last_update) >= self.update_interval:
            print "GETTING NEW NEWS"
            self.get_news()
        return

    def draw(self):
        text = self.news[self.text_index:self.text_index+self.display_chars]
        draw_text(self.window, None, text=text, x=self.x, y=self.y)
        return 0


class Weather:
    def __init__(self, config, window, x, y):
        #self.scene = scene
        self.key = config.get("WEATHER", "apikey")
        if self.key is None:
            raise Exception

        self.window = window
        self.zip = config.get("WEATHER", "zip")
        self.update_interval = config.getint("WEATHER", "update")
        self.units = config.get("WEATHER", "units")
        self.url = "http://api.openweathermap.org/data/2.5/weather?zip=%s&units=%s&appid=%s" % (self.zip, self.units, self.key)
        self.last_update = 0

        # place all our filenames into the dict here.
        self.icons = {}
        for atuple in config.items("WEATHER_ICONS"):
            self.icons.update({atuple[0]: Icon(atuple[1])})

        self.current_icon = None
        self.current_weather = None
        self.text = ""

        # get the weather, the current_icon and current_weather variables will be updated.
        self.get_weather()

        # make a call to draw thyself - this is the first run so we need to prepare something.
        self.draw()

    def __map_status(self, weatherId):
        """
        https://openweathermap.org/weather-conditions
        :param weatherId: int
        :return: str which will map to an icon
        """
        if weatherId >= 200 and weatherId < 300:
            return self.icons["stormy"]
        elif weatherId >= 300 and weatherId < 600:
            return self.icons["rainy"]
        elif weatherId >= 600 and weatherId < 700:
            return self.icons["snowy"]
        elif weatherId >= 700 and weatherId < 800:
            return self.icons["foggy"]
        elif weatherId >= 800 and weatherId <= 802:
            return self.icons["sunny"]
        elif weatherId > 802 and weatherId < 900:
            return self.icons["cloudy"]
        elif weatherId >= 900 and weatherId < 1000:
            # Todo: this is EXTREME weather -- probably want to display something else other than "lightning"
            return self.icons["stormy"]
        else:
            # todo: handle this case gracefully
            return None
        # todo: use partly-cloudy...

    def get_weather(self):
        try:
            weather = requests.get(self.url)
            if weather.status_code != 200:
                raise Exception
        except:
            print "Could not get weather code: %d" % weather.status_code
            raise Exception
        weather = weather.json()
        self.current_icon = self.__map_status(weather['weather'][0]['id'])

        # todo: display this description string somewhere.
        status_string = weather['weather'][0]['description'].encode("ascii",'ignore')
        print status_string

        # todo: maybe also display high and low?
        temp = weather['main']['temp']
        print "temp: %d" % temp

        self.text = "%d %s" % (temp, status_string)

    def draw(self):
        # icon is 16x16, the info is going to be somwhat smaller.
        icon_surface = self.current_icon.surface
        # todo: return the temp and the icon together on a surface
        # self.scene.append(icon_surface)
        print "trying to draw..."
        screen = self.window.get_surface()
        SDL_BlitSurface(icon_surface, None, screen, None)
        window_pointer = ctypes.POINTER(sdl2.SDL_Window)
        lp_window = ctypes.cast(id(self.window), window_pointer)
        SDL_UpdateWindowSurface(lp_window)

        draw_text(self.window, None, self.text, x=17, y=0)

    def tick(self):
        # don't do anything if it's not past the update_interval
        if (time.time() - self.last_update) <= self.update_interval:
            self.draw()
            return
        print "UPDATE WEATHER!"
        self.last_update = time.time()
        self.get_weather()
        self.draw()
        # todo:  will it be easier to just push a callback into here and use the callback to handle the
        # todo: drawing of the surface since only one widget will be able to call in and the callback would be able to
        # todo: manage the draws?

# organize the fonts into a permanent dict so that we avoid the memory leak of grabbing it over and over.
fonts = {}
global fonts


def get_font(font, size):
    global fonts
    if fonts.get(font) is None:
        fonts[font] = {size : sdl2.sdlttf.TTF_OpenFont("resources/fonts/%s.ttf" % font, size)}
    elif fonts.get(font).get(size) is None:
        fonts[font][size] = sdl2.sdlttf.TTF_OpenFont("resources/fonts/%s.ttf" % font, size)
    return fonts[font][size]

def draw_text(window, scene, text, x=0, y=0, font="slkscr", size=7, unicode=False):

    """
    Draw something on the surface screen
    :param window: sdl2.window
    :param text: str
    :param x: int
    :param y: int
    :param font: str
    :param size: int
    :return: exit code
    """


    screen = window.get_surface()
    # screen = SDL_CreateRGBSurface(0, 64, 64, 32, 0, 0, 0, 0).contents
    #font_original = sdl2.sdlttf.TTF_OpenFont("resources/fonts/%s.ttf" % font, size)

    # if font is not none but evals to false, there was an error and font will contain a NULL pointer
    #if not font:
    #    print "Failed to load font!"
    #    exit(1)
    #font = font_original.contents
    font = get_font(font, size)

    color = sdl2.SDL_Color(r=255, g=255, b=255)

    line_num = 0
    for line in text.split('\n'):
        if type(text) == unicode or unicode == True:
            print "Handling UNICODE"
            surface_out_og = sdl2.sdlttf.TTF_RenderGlyph_Solid(font, ctypes.c_uint16(0x1f600), color)
            #short = ctypes.POINTER(ctypes.c_ushort)
            #derp = [ctypes.c_ushort(0x1f600), ctypes.c_ushort(0x00)]

            #nums = [ctypes.c_uint16(0x1f600)]
            #fuck = (ctypes.c_uint16 * len(nums))(*nums)
            #surface_out_og = sdl2.sdlttf.TTF_RenderUNICODE_Solid(font, fuck, color)
        else:
            surface_out_og = sdl2.sdlttf.TTF_RenderText_Solid(font, line, color)
        #surface_out_og = sdl2.sdlttf.TTF_RenderText_Solid(font, text, color)

        if not surface_out_og:
            print "There was a problem"
            del surface_out_og
            return
        surface_out = surface_out_og.contents

        # create a rect at x, y with zero height and width to act as an arg for BlitSurface to use for a transform
        line_y_offset = (line_num*size)
        position = sdl2.rect.SDL_Rect(x, y+line_y_offset)

        window_pointer = ctypes.POINTER(sdl2.SDL_Window)
        lp_window = ctypes.cast(id(window), window_pointer)

        #SDL_FillRect(screen, None, SDL_MapRGB(screen.format, 0, 0, 0))
        SDL_BlitSurface(surface_out, None, screen, position)

        #increment the number of lines processed so we can increment the y position of new text segment
        line_num += 1

    SDL_UpdateWindowSurface(lp_window)
    # scene.append(surface_out)

    SDL_FreeSurface(surface_out)
    del surface_out_og
    SDL_FreeSurface(screen)
    del window_pointer
    del lp_window
    del window
    return 0


# main routine
def run(config):
    """
    Main()

    :param config: ConfigParser object
    :return: int exit code - nonzero indicates error.  Will be propagated to exit()
    """
    if config is None:
        return 1

    #web_thread = multiprocessing.Process(target=resources.webserver.run, args=()) #config.getint('WEBSERVER','port')))
    #web_thread.start()

    # we hold a reference to a shared memory object for our "user-defined message here"
    s_val = multiprocessing.Array(ctypes.c_char, 8192)
    s_val.value = "Initializing"

    # use a factory method to get a reference to a runnable webserver
    server = resources.webserver.get_webserver(s_val)

    # start that reference in another process
    web_thread = multiprocessing.Process(target=server.run, args=())
    web_thread.start()

    sdl2.ext.init()

    mode = sdl2.SDL_DisplayMode()
    sdl2.SDL_GetDesktopDisplayMode(0, mode)

    w = mode.w
    h = mode.h-(64+30)

    print w,h

    window = sdl2.ext.Window("SignPi", position=(-2,h), size=(64, 64))
    #window.DEFAULTPOS = (0,0)
    window.show()

    # this is key.
    tfi = sdl2.sdlttf.TTF_Init()
    if tfi != 0:
        print("TTF_Init FAIL")
        exit(1)

    flags = sdl2.sdlimage.IMG_INIT_JPG | sdl2.sdlimage.IMG_INIT_PNG;
    sdl2.sdlimage.IMG_Init(flags)

    # now we can read from the errors var to see if we biffed an SDL call.
    SDL_ClearError()
    event = SDL_Event()

    # a list to hold our surfaces for the next frame update
    surface_list = []

    spriteManager = SpriteManager(config, window)

    emojitime = EmojiTime(spriteManager)

    # a list to hold all the elements which manage the things on the screen
    tracked_objects = [
        #Weather(config, window, 0, 0),
        #News(config, window, 0, 56),
        #Clock(config, window, 0, 24),
        #emojitime,
        #spriteManager
        Gif(config, window, 0, 0),
        Message(config, window, s_val, 0, 24)
    ]

    running = 1

    # create a pointer type, then grab the address of the window object and create a python longpointer to it (LP_)
    window_pointer = ctypes.POINTER(sdl2.SDL_Window)
    lp_window = ctypes.cast(id(window), window_pointer)
    screen = window.get_surface()

    lasttick = 0

    while running:
        if sdl2.SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
                print "HANDLING EXIT"
                break

        # once a second
        if (sdl2.SDL_GetTicks() % 125 == 0) or (lasttick - sdl2.SDL_GetTicks()) > 125:
            lasttick = sdl2.SDL_GetTicks()

            window.refresh()
            #SDL_UpdateWindowSurface(lp_window)

            # ...blank the screen
            SDL_FillRect(screen, None, SDL_MapRGB(screen.format, 0, 0, 0))
            #print "<<UPDATE>>"

            # fire a signal to our objects that they could consider updating themselves -- they may not though.
            for i in tracked_objects:
                i.tick()

            #print len(tracked_objects)
            #draw_text(window, surface_list, u'\U0001F600', x=0, y=41, size=12, unicode=True, font='emojione-apple')

            # update the surface of the window (using the pointer to the window generated earlier)
            SDL_UpdateWindowSurface(lp_window)

        # refresh the window.
        SDL_UpdateWindowSurface(lp_window)

    sdl2.ext.quit()
    return 0


if __name__ == "__main__":
    # todo: optparse here
    if len(sys.argv) < 2:
        path = "resources/config.ini"
    else:
        path = sys.argv[1]

    if not os.path.exists(path):
        print "Configuration file %s not found" % (path)
        raise Exception

    config = ConfigParser.ConfigParser()
    config.read(path)

    sys.exit(run(config))
