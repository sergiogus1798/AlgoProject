"""Portable SQX custom-block engine: bootstrap (discover) + emit (build) + validate.

grammar.py  — build-stable operators / arithmetic / make_block (shipped, proven)
bootstrap.py — parse a user's config.xml (+ export) -> catalog.json / catalog.md
emit.py     — Catalog.atom(): catalog entry -> block-ready <Item> XML
validate.py — 7-check linter (stdlib only)
"""
