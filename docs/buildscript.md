# (Re-)Building the example projects

<!--
The following text is taken from #118
https://github.com/formatc1702/WireViz/pull/118

TODO: write a better explaination -->

## Commands

- `python build_examples.py` to build generated files in all groups.
- `python build_examples.py compare` to compare generated files in all groups against the last commit.
- `python build_examples.py clean` to delete generated files in all groups.
- `python build_examples.py restore` to restore generated files in all groups from the last commit.
- `python build_examples.py -V` or `--version` to display the WireViz version.
- `python build_examples.py -h` or `--help` to see a summary of the usage help text.


## Options

- Append `-b` or `--branch` followed by a specified branch or commit to compare with or restore from (default: The last commit in the current branch).
- Append `-c` or `--compare-graphviz-output` to the `compare` command above to also compare the Graphviz output (default: False).
- Append `-g` or `--groups` followed by space separated group names to any command above, and the set of generated files affected by the command will be limited to the selected groups.
Possible group names:
  - `examples` to process `examples/{readme.md,ex*.*}`
  - `tutorial` to process`tutorial/{readme.md,tutorial*.*}`
  - `demos` to process`examples/demo*.*`

  Affected filetypes: `.gv`, `.tsv`, `.png`, `.svg`, `.html`


## Usage hints

- Run `python build_examples.py` after any code changes to verify that it still is possible to process YAML-input from all groups without errors.
- Run `python build_examples.py compare` after the rebuilding above to verify that the output differences are as expected after a code change.
- Run `python build_examples.py restore` before adding and committing to avoid including changes to generated files after the rebuilding above.
