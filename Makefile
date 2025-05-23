.PHONY: bootstrap
bootstrap:
	which bootstrap.sh || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/adelynnmckay/bootstrap.sh/HEAD/bootstrap.sh)"
	chmod +x ./bin/*

.PHONY: install
install: bootstrap
	( ./src/linkbuild.sh && for f in "$HOME/bin/"*; do [ -f "$f" ] && mv "$f" "${f%.*}"; done )

.PHONY: test
test: bootstrap
	( ./src/anytest.sh )