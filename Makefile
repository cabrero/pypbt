.PHONY: build docs documentation

build:
	python3 -m build

upload-testpypy:
	python3 -m twine upload --repository testpypi dist/*

upload-pypy:
	python3 -m twine upload dist/*

# User doccumentation (readthedocs.io)
documentation:
	. ./venv/mkdocs/bin/activate; \
	mkdocs serve; \
	deactivate

# Developers documentation (github pages)
docs:
	cd docs; bundle exec jekyll serve
