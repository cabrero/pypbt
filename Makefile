.PHONY: build

build:
	python3 -m build

upload-testpypy:
	python3 -m twine upload --repository testpypi dist/*

upload-pypy:
	python3 -m twine upload dist/*
