# signage
Display useful information on an LED Signboard

About This Project
==================
This project was developed as a part of an effort to make an LED sign made from Jumbotron panels a usable information board.  The idea behind it is that the adafruit framebuffer display is used to display the contents of the linux framebuffer for the lower 64x64 pixels of the display.  The adafruit code then happy sends this off for rendering to the display.  I have some photos of this in action which I will upload later.  On it's own this code probably isn't all that useful, except maybe to act as a tutorial/illustration of using python to interface with a CFFI library (SDL2)

While using it as a tutorial / illustration of SDL programming in python, a few areas may be interesting to you:

- Handling spritesheets and sprites

- Rendering objects to a scene without the use of PySDL-specific objects

I tried hard to get Emojis to display with only the use of a TTF font and SDL functions, but was not successful.  If anyone has any input on how to accomplish this, I'd appreciate the help.

Usage
=====
1.) Get an OpenWeatherMap.org API key, place it in the config.ini file.

2.) Get a NewsAPI.org API key, place it in the config.ini file.

3.) Initialize the repo for the PNG versions of the Emoji glyphs

4.) python sign.py

Dependencies
============
apt-get install libsdl2-ttf-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev

pip install pysdl2

pip install pysdl2-cffi
