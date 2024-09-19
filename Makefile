# holy shit fuck this makefile ong

FUSE3DS = $(cd finalize && $(MAKE))
finalize: 
	cd finalize && $(MAKE)
app:
	python3 setup-cxfreeze.py build_exe

all: finalize app