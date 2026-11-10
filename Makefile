PYTHON ?= python3
.PHONY: test demo live-demo
test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m py_compile scripts/*.py writing_ftm/*.py
demo:
	$(PYTHON) -m writing_ftm.demo
live-demo:
	$(PYTHON) -m writing_ftm.demo --live
