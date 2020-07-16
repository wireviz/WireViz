import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

examples_path = os.path.join('..','..','examples')

generated_extensions = ['.gv', '.png', '.svg', '.html', '.bom.tsv']

files = os.listdir(examples_path)

for file in files:
    if list(filter(file.endswith, generated_extensions)):
        os.remove(os.path.join(examples_path, file))
os.remove(os.path.join(examples_path,'readme.md'))