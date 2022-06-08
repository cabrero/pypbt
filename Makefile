.PHONY: build docs

build:
	python3 -m build

upload-testpypy:
	python3 -m twine upload --repository testpypi dist/*

upload-pypy:
	python3 -m twine upload dist/*

olddocs:
	sphinx-apidoc \
	    --force \
	    --implicit-namespaces \
	    --module-first \
	    --separate \
	    -o docs/reference/ \
	    src/pypbt/
	sphinx-build -n -W --keep-going -b html docs/source/ docs/build/

watchdocs:
	sphinx-autobuild -n -W -b html docs/source/ docs/build/


docs:
	. ./venv-mkdocs/bin/activate; \
	mkdocs serve; \
	deactivate
