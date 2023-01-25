autoflake -i -r --remove-all-unused-imports src/wireviz/
isort src/wireviz/*.py src/wireviz/tools/*.py
black src/wireviz/*.py src/wireviz/tools/*.py
