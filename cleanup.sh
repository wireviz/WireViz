#!/bin/zsh

uv run autoflake -i --remove-all-unused-imports src/wireviz/*.py
uv run isort src/wireviz/*.py
uv run black src/wireviz/*.py
