"""The cost catalogue: what the project costs in time, memory and disk.

This file is what makes the folder win the name: without it `perf` is a namespace package, and a
namespace package loses to any regular module on the path. Ubuntu's linux-tools ships one —
`/usr/lib/linux-tools/<kernel>/lib/perf.cpython-312-*.so` — so on gorilla every `import perf.…`
died with «'perf' is not a package» (📓 2026-10-11): `pipeline.stages.gates`, `pipeline.cleanup`
and the window's data catalogue.
"""
