# Purpose

This is a tentative rewriting of the `omf6 load` and other similar commands in python.

# How to use

## Invoking

The python entry point is named `imaging-main.py` but it should be called through one of the symlinks like `imaging-load`.

So in short:

    $ imaging-load [-i filename] 1 4 5
    
The arguments, known as a *node_spec*`* would be similar to what `nodes` accepts as input, i.e.

    $ load-image 1-12 fit15-reboot18 ~4-6

Would essentially work on nodes 1 to 3, 7 to 12, and 15 to 18

Run `imaging-load --help` as usual for a list of options.

## env. variables    

If no node argument is provided on the command line, the value of the `NODES` environment variable is used. So 

    $ all-nodes
    $ focus-nodes-on
    $ echo this way you can check : NODES=$NODES
    $ imaging-load

Would effectively address all nodes currently turned on

In addition, the `-a` option allows you to use the **ALL_NODES** variables

## Logging

TBD
 
# Install and Configure

## Inventory

In short: see `/etc/imaging-inventory.json`

Unfortunately the tools need a mapping between hostnames and MAC addresses - essentially for messing with pxelinux symlinks. At this point at least; it occurred to me only later that maybe an IP address would have done. In any case for now the tool needs to find an inventory in a file named	`/etc/imaging-inventory.json`. This is taken care of by  `inventory/configure.py` and its `Makefile`. Note that like for the OMF JSON inventory file, `configure.py` creates 2 different files for faraday and bemol - to account for any replacement node on farady, like when e.g. node 41 actually sits in slot 15.

FYI an inventory files just looks like below; the `data` field is not needed

#
    # less /etc/imaging-inventory.json
     [
      {
        "cmc": {
          "hostname": "reboot01",
          "ip": "192.168.1.1",
          "mac": "02:00:00:00:00:01"
        },
        "control": {
          "hostname": "fit01",
          "ip": "192.168.3.1",
          "mac": "00:03:1d:0e:03:19"
        },
        "data": {
          "hostname": "data01",
          "ip": "192.168.2.1",
          "mac": "00:03:1d:0e:03:18"
        }
      },
      ... etc
      ]

## Configuration

Configuration is done through a collection of files, which are loaded in this order if they exist:

 * `/etc/imaging.conf`
 * `~/.imaging.conf`
 * `./imaging.conf`

 So in essence, there is a system-wide config (mandatory), and possibly overridden values at a user level, or even more specific at a directory level.
 
 Format is like aim	 `.ini` file, should be straightforward. Just beware to **not mention quotes** around strings, as such quotes end up in the python string verbatim.



# Dependencies

## python-3.4 *vs* python-3.5
We use python 3.4's `asyncio` library. python3.4 can be taken as granted on the ubuntus we use on both `faraday` and `bemol`. 

It would have been nice to assume `python3.5` instead, as the syntax has changed rather drastically between the 2 versions. However as of this writing (Nov. 2015), python3.5 is not yet available on ubuntu-LTS-14.04 that we use, and I'd rather not install that from sources.

In practical terms this means that whenever we use 

    @asyncio.coroutine
    def foo():
    
we would have written instead in pure python-3.5 this

    async def foo():
    
and also each we have written this

    yield from bar()
    
it would have been this instead

    await bar()


## other libs

* `telnetlib3` for invoking `frisbee` on the nodes
* `aiohttp` for talking to the CMC cards

There's also `asyncssh` that might come in handy at some point; this would let us create ssh connections, and then sessions inside that (sharing a connection for several purposes), all this in a asynchroneous way; sounds real great e.g. for nepi. But another story entirely..

# TODO

* get the timeout to work
* return some decent retcod
* more decent monitor (at least knowns how many nodes, does averages..)
* imagesaver
* rename CMC into just plain node ?
* nicer imaging-list