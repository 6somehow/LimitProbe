# Offline demo

From the repository root, run `conda run -n findlimit bash examples/offline_demo.sh`. It runs the offline test suite, unions two copies of a synthetic prediction, scores it with the deterministic fake judge, prints coverage JSON, and prints the comparison table. The fixture is invented and is not an experimental result. No key, PDF, or network is needed. Temporary outputs are removed on exit.
