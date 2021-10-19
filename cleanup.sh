#!/bin/zsh

autoflake -i --remove-all-unused-imports src/wireviz/*.py
isort src/wireviz/*py
black src/wireviz/*.py
