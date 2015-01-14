# Gierzwaluw

A very specific kind of migrating Swallow that carries files and maybe coconuts across the LAN.

You are with a bunch of friends in some random place.
There might or might not be WiFi.
The presence of a USB drive is unlikely.
There are a multitude of operating systems.
You want to transfer a file.

I have been in this situation way too often.
The only thing that kind of works is `nc -l 9090`.
No more!

This tool aims to easily and reliably transfer a file to the person sitting next to you.

There are 2 modes of operation:

The ideal case, a swallow-to-swallow transfer, initiated via Bonjour.

1. One user selects a file to share.
2. The file is broadcast via Bonjour.
3. It appears in the menu for other users.
4. Other users download the file.

![example transfer](https://raw.githubusercontent.com/pepijndevos/gierzwaluw/master/images/transfer.gif)

A swallow-to-browser or browser-to-swallow transfer with optional internet based discovery.

1. Gierzwaluw announces its private IP on a public website.
2. Other users see nodes with the same public IP.
3. Click through to Gierzwaluw web interface.
4. Download file shared by the host.
5. Offer files to the host.


![example transfer](https://raw.githubusercontent.com/pepijndevos/gierzwaluw/master/images/browser_transfer.gif)

## Installation

For now just install the requirements and run `python gui.py` or  `python cli.py`.

Application bundles are desirable at some point, but a pain to generate.

## Status

Very much work in progress.

Thanks to @Sidnicious and @myf for talking me into this.
