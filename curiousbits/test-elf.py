#!/usr/bin/env python

from curiousbits.misc.output import get_hex_dump
from curiousbits.elf.oop import *

if __name__ == "__main__":
	if len(sys.argv) == 1:
		print("provide argument")
		sys.exit(-1)

	elif sys.argv[1] == 'info':
		ef = ElfFile(sys.argv[2])
		print(ef)

	elif sys.argv[1] == 'section':
		section_name = sys.argv[2]
		ef = ElfFile(sys.argv[3])
		header = ef.getSectionHeader(section_name)
		print(header)
		contents = ef.getSectionContents(section_name)
		print(get_hex_dump(contents, header.sh_offset))

	elif sys.argv[1] == 'verifyhash':
		ef = ElfFile(sys.argv[2])
		ef.hashtable.verify()
		print(ef.hashtable)

	elif sys.argv[1] == 'rehash':
		print("%s -> %s" % (sys.argv[2], sys.argv[3]))
		shutil.copy(sys.argv[2], sys.argv[3])
		ef = ElfFile(sys.argv[3])
		ef.hashtable.recompute()
		ef.hashtable.write()
		print(ef.hashtable)
		
	elif sys.argv[1] == 'scrub':
		print("%s -> %s" % (sys.argv[2], sys.argv[3]))
		shutil.copy(sys.argv[2], sys.argv[3])
		ef = ElfFile(sys.argv[3])

		# replace the string in the string tables
		ef.stringTables['dynstr'].table = \
			ef.stringTables['dynstr'].table.replace('before', 'afterr')
		ef.stringTables['dynstr'].write()

		# recompute the hash table
		ef.hashtable.recompute()
		ef.hashtable.write()
		print(ef.hashtable)

	# eg: ./elf.py zerosect before.so after.so .debug_line
	# eg: ./elf.py zerosect before.so after.so .debug_line
	elif sys.argv[1] == 'zerosect':
		(fileA, fileB, secName) = sys.argv[2:]
		print("%s -> %s" % (fileA, fileB))
		#shutil.copy(fileA, fileB)

		(offs, size) = (0, 0)

		ef = ElfFile(fileA)
		hdr = ef.getSectionHeader(secName)
		if not hdr:
			raise Exception("ERROR: couldn't find section \"%s\"\n" % secName)
		offs = hdr.sh_offset
		size = hdr.sh_size
		ef = None

		fobj = open(fileA, 'rb+')
		fobj.seek(offs, os.SEEK_SET)
		fobj.write('\x00'*size)
		fobj.close()

	elif sys.argv[1] == 'wherestring':
		(fname, string) = sys.argv[2:]

		# first, find the offset:
		fobj = open(fname, 'rb')
		stuff = fobj.read()
		fobj.close()

		# collect all file offsets where string appears
		offsets = []
		curr = -1
		while 1:
			curr = stuff.find(string, curr+1)
			if curr == -1:
				break

			offsets.append(curr)

		# get section headers
		ef = ElfFile(fname)

		for o in offsets:
			# in which section?
			scnName = '<unknown>'
			for hdr in ef.Shdrs:
				if o >= hdr.sh_offset and o < (hdr.sh_offset + hdr.sh_size):
					scnName = hdr.getName()
					break

			print("found at offset %08X (%d) in section \"%s\"" % (o, o, scnName))
