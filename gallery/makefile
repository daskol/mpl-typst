export PYTHONPATH := $(abspath $(PWD)/..):$(PYTHONPATH)

all: main.pdf main.png

main.pdf: line-plot-simple.typ hist-hatched.typ main.typ
	typst compile main.typ $@

main.png: line-plot-simple.typ hist-hatched.typ main.typ
	typst compile --pages 1 --ppi 288 main.typ $@

line-plot-simple.typ: line-plot-simple.py
	python $^

hist-hatched.typ: hist-hatched.py
	python $^

.PHONY:
clean:
	rm -rfv main.pdf main.png line-plot-simple.typ hist-hatched.typ
