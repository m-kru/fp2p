Installation and usage
----------------------

Installation
============

fp2p is not available on the `PyPI <https://pypi.org/>`_ website.
Why?
fp2p is pure program, contained within single file, there is no library part, it can't be imported.
This will *never* change.
What is more, I didn't want to litter PyPI with a program that is relatively rarely used (although being very useful).
It is not like new boards are designed or manufactured once per week or month.

User has full freedom in terms of installation.
For example, you can do one of the followings:

- Copy :code:`fp2p.py` file to the repository with the FPGA project design.
- Add fp2p repository as a submodule to the repository with the FPGA project design.
- Clone the repository *somewhere* in the filesystem and call the program providing path :code:`python ~/your/path/fp2p/fp2p.py ...`.
- Copy :code:`fp2p.py` file to some directory included in the :code:`PATH`. You may want to add shebang to the file, for example :code:`#!/bin/python` and :code:`chmod +x fp2p.py`.

Usage
=====

fp2p supports 3 subcommands:

1. :code:`assign` - assings ports to pins,
2. :code:`graph` - resolves a mapping tree and prints graph,
3. :code:`resolve` - resolves a mapping tree and prints the result.

After preparing proper mapping tree files or assignment files user only needs to call fp2p with one of the subcommands and proper order of arguments.
This is further explained in the section ...
You can also always run :code:`python fp2p.py -h` or :code:`python fp2p.py {subcommand} -h`.

Windows
=======

The program has not been tested on Windows OS, and no one has so far reported that it works corretly.
However, it *should* work, as no OS specific mechanisms or system calls are used.
