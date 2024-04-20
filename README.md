Py Mojo Loader
==============

This loader for the Mojo v3 is a simpler replacement for the Embedded Micro version available [here](https://github.com/embmicro/mojo-loader).

You will need to install the following modules:
* `pyserial`
* `tqdm`

To us this loader you should first create your `.bin` file using the Xilinx ISE, and connect your Mojo to your machine and identify the port. On a Linux box this is likely to be `/dev/ttyACM0`. The following command will then erase the Mojo's flash memory, upload your bitstream, and verify that it has been written correctly:
```
python3 ./mojo-loader.py [port name] [bin filename]
```

Note that the Embedded Micro repo linked to above has an additional capability: writing to the RAM.
I don't fully understand this yet, and hence cannot test it, so I have not implemented it here.

