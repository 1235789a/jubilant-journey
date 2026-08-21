.PHONY: init demo serve tick test check

init:
	PYTHONPATH=src python -m distribution_os.cli init

demo:
	PYTHONPATH=src python -m distribution_os.cli demo

serve:
	PYTHONPATH=src python -m distribution_os.cli serve

tick:
	PYTHONPATH=src python -m distribution_os.cli tick

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

check:
	python -m json.tool config/platforms.json >/dev/null
	python -m json.tool config/verticals.json >/dev/null
	python -m compileall -q src tests
	PYTHONPATH=src python -m unittest discover -s tests -v
	node --check src/distribution_os/dashboard/app.js
