import os
import struct
import marshal
import zlib
import sys
import imp
import types

class CTOCEntry:
    def __init__(self, position, cmprsdDataSize, uncmprsdDataSize, cmprsFlag, typeCmprsData, name):
        self.position = position
        self.cmprsdDataSize = cmprsdDataSize
        self.uncmprsdDataSize = uncmprsdDataSize
        self.cmprsFlag = cmprsFlag
        self.typeCmprsData = typeCmprsData
        self.name = name

class PyInstArchive:
    def _extractPyz(self, name, mainfile):
        dirName =  name + '_extracted'
        # Create a directory for the contents of the pyz
        if not os.path.exists(dirName):
            os.mkdir(dirName)

        with open(name, 'rb') as f:
            pyzMagic = f.read(4)
            assert pyzMagic == b'PYZ\0' # Sanity Check

            pycHeader = f.read(4) # Python magic value

            # if imp.get_magic() != pycHeader:
            #     print('[!] WARNING: The script is running in a different python version than the one used to build the executable')
            #     print('    Run this script in Python{} to prevent extraction errors(if any) during unmarshalling'.format(self.pyver))

            (tocPosition, ) = struct.unpack('>I', f.read(4))
            f.seek(tocPosition, os.SEEK_SET)

            try:
                toc = marshal.load(f)
            except:
                print('[!] Unmarshalling FAILED. Cannot extract {}. Extracting remaining files.'.format(name))
                return

            print('[*] Found {} files in PYZ archive'.format(len(toc)))
            
            # load pyc from pyz
            if type(toc) == list:
                toc = dict(toc)            

            for key in toc.keys():
                (ispkg, pos, length) = toc[key]
                f.seek(pos, os.SEEK_SET)
                data = zlib.decompress(f.read(length))
                fileName = key
                try:
                    # for Python > 3.3 some keys are bytes object some are str object
                    fileName = key.decode('utf-8')
                except:
                    pass

                with open(os.path.join(dirName, fileName + '.pyc'), 'wb') as pycFile:
                    pycFile.write(pycHeader)    # Write pyc magic
                    pycFile.write(b'\0' * 4)     # Write timestamp
                    pycFile.write(b'\0' * 4)  # Size parameter added in Python 3.3
                    pycFile.write(data)

            # save dga as dga.pyc
            mainpyc = open(mainfile, "rb").read()
            with open(os.path.join(dirName, mainfile + '.pyc'), 'wb') as pycFile:
                pycFile.write(pycHeader)    # Write pyc magic
                pycFile.write(b'\0' * 4)     # Write timestamp
                pycFile.write(b'\0' * 4)  # Size parameter added in Python 3.3
                pycFile.write(mainpyc)


arch = PyInstArchive()
arch._extractPyz(sys.argv[1], sys.argv[2])
