# Gierzwaluw

A very specific kind of migrating Swallow that carries files and maybe coconuts across the LAN.

You are with a bunch of friends in some random place.
There might or might not be WiFi.
The presence of a USB drive is unlikely.
There are a multitude of opperating systems.
You want to transfer a file.

I have been in this situation way too often.
The only thing that kind of works is `nc -l 9090`.
No more!

This tool aims to easily and reliably transfer a file to the person sitting next to you.

There are 3 modes of opperation:

1. The ideal case, a swallow-to-swallow transfer, initiated via Bonjour.
2. A swallow-to-browser or browser-to-swallow transfer with internet based discovery.
3. Swallow-to-browser or browser-to-swallow without autodiscovery.

Very much work in progress.

Thanks to @Sidnicious and @myf for talking me into this.
