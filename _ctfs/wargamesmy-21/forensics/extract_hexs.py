import re
from binascii import unhexlify
from base64 import b64decode

pattern = b'OtrpOlvrHtgdOt\("(\S+)"\)'
vba = open("olevba", "rb").read()

founds = re.findall(pattern, vba)
for found in founds:
    unhex = unhexlify(found)
    print(unhex.decode())