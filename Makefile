run.v0.example-%:
	NANOPDB_VERSION=0 python -m nanopdb examples/example-$*.py 10

run.v1.example-%:
	NANOPDB_VERSION=1 python -m nanopdb examples/example-$*.py 10

run.v2.example-%:
	NANOPDB_VERSION=2 python -m nanopdb examples/example-$*.py 10

run.v3.example-%:
	NANOPDB_VERSION=3 python -m nanopdb examples/example-$*.py 10

# run.v4.example-%:
# 	NANOPDB_VERSION=4 python -m nanopdb examples/example-$*.py 10