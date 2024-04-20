from time import sleep
from os import stat
import argparse
import serial
from tqdm import tqdm


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Loads a bitstream created using Xilinx ISE onto the Mojo dev board.')
    parser.add_argument('port', type=str, help='Serial port Mojo is attached on.')
    parser.add_argument('bin_file', type=str,
                        help='Location of .bin file to load into Mojo flash memory.')
    args = parser.parse_args()

    bin_file = open(args.bin_file, 'rb')
    bin_file_size = stat(args.bin_file).st_size

    ser = serial.Serial(
        port=args.port,
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_ONE,
        parity=serial.PARITY_NONE,
        exclusive=True,
        timeout=10.0,
    )

    try:
        # Restart the Mojo
        ser.dtr = False
        for _ in range(5):
            ser.dtr = False
            sleep(0.005)
            ser.dtr = True
            sleep(0.005)

        ser.flush()
        ser.read_all()

        print('Erasing flash...')
        ser.write(b'E')
        if ser.read(size=1) != b'D':
            raise RuntimeError('Mojo did not acknowledge flash erase!')

        print('Writing to flash...')
        ser.write(b'V')  # Write with verification
        if ser.read(size=1) != b'R':
            raise RuntimeError('Mojo did not respond to writing request!')

        # Tell the Mojo how many bytes of data we will write
        buff = bytearray([bin_file_size >> (i * 8) & 0xFF for i in range(4)])
        if bin_file_size >> (4 * 8) > 0:
            raise RuntimeError(f'Binary file size of {bin_file_size} is too large.')
        ser.write(buff)
        ser.flush()
        if ser.read(size=1) != b'O':
            raise RuntimeError('Mojo did not acknowledge the transfer size!')

        # Split the data into chunks and write
        chunk_size = 256
        num_chunks = (bin_file_size - 1)//chunk_size + 1
        for chunk in tqdm(range(num_chunks)):
            n_read = min(chunk_size, bin_file_size - chunk_size*chunk)
            data_to_transfer = bin_file.read(n_read)
            assert len(data_to_transfer) == n_read
            ser.write(data_to_transfer)
            ser.flush()

        bin_file.close()
        bin_file = None

        if ser.read(size=1) != b'D':
            raise RuntimeError('Mojo did not acknowledge the data transfer!')

        print('Verifying the write...')
        bin_file = open(args.bin_file, 'rb')
        ser.write(b'S')
        start_byte = ser.read(size=1)
        if start_byte != b'\xAA':
            raise RuntimeError(f'Did not get valid start byte, got: {start_byte}')

        # First byte should indicate how many bytes were written.
        flash_size = int.from_bytes(ser.read(size=4), byteorder='little')
        if flash_size != bin_file_size + 5:
            raise RuntimeError(f'Expected size of {bin_file_size + 5} but got {flash_size}.')

        num_chunks = (bin_file_size - 1)//chunk_size + 1
        for chunk in tqdm(range(num_chunks)):
            n_read = min(chunk_size, bin_file_size - chunk_size*chunk)
            data_to_verify = bin_file.read(n_read)
            data_from_flash = ser.read(size=chunk_size)
            for i in range(n_read):
                if data_to_verify[i] != data_from_flash[i]:
                    raise RuntimeError(f'Verification failed at byte {chunk*chunk_size+i} out of {bin_file_size}'
                                       f'Expected {data_to_verify[i]}, got {data_from_flash[i]}')

        # FIXME - I'm not sure what purpose this part serves!
        ser.write(b'L')
        if ser.read(size=1) != b'D':
            raise RuntimeError('Could not load from flash!')

    finally:
        if ser.is_open:
            ser.close()
        if bin_file is not None:
            bin_file.close()

