""" Convert datalogger output to a standard csv file.
"""
import sys
import zlib

CHECK_AMT = 10

filename = sys.argv[1]
output = sys.argv[2]

print(f"Reading file {filename} ...")

with open(filename, "rb") as f:
    data = f.read()

decompressor = zlib.decompressobj()
data = decompressor.decompress(data)

print(f"Writing to {output} ...")
with open(output, "w") as f:
    try:
        f.write(data.decode())
    except UnicodeDecodeError:
        f.write(data[:-1].decode())
