# holy shit fuck this makefile ong

FUSE3DS = $(cd finalize && $(MAKE))
fuse3ds: 
	cd finalize && $(MAKE)
app:
	python3 setup-cxfreeze.py build_exe

all: fuse3ds app