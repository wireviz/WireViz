# Contribution Guidelines

When contributing to this repository, please [submit a new issue](https://github.com/wireviz/WireViz/issues) first to discuss the proposed change, before submitting a pull request.

## Submitting a new Issue

- First, search existing (open and closed) issues for any related issues.
  - You might then find an existing answer or suggested solution to your issue, possibly also an existing PR you can test.
  - When finding existing issues that seem related to your issue, please include references (# followed by issue number) to related issues in your new issue description, or if a very similar issue is still open, consider adding a comment in that issue instead of creating a new one.
- When appropriate, please prefix your issue title with one of these category prefixes followed by a space:
  - **[bug]** When the issue seems to be caused by a bug.
  - **[feature]** When requesting a feature change or new feature.
  - **[internal]** When suggesting code improvements that doesn't change any output.
  - **[doc]** For documentation issues.
  - **[meta]** For issues about the development or contribution process.
- Please include enough information in the description to enable another user to reproduce any error state described in your issue:
  - The versions of your WireViz, Graphviz (`dot -V`), Python (`python -V`), and operating system.
  - The relevant input files unless (preferably) you can demonstrate the same issue using one of the example files. If your input file is large or complex, please try to find a smaller/simplified input that still can reproduce the same issue.
  - Any warnings or error messages you get.
- See also [How We Write Github Issues](https://wiredcraft.com/blog/how-we-write-our-github-issues/) in general.

## Submitting a new Pull Request

1. Fork this repository and clone it on your local machine.
1. Create a new feature branch on top of the `dev` branch.
1. Commit your code changes to this feature branch.
1. Push the changes to your fork.
1. Please format your code using [`isort`](https://pycqa.github.io/isort/) and [`black`](https://black.readthedocs.io) before submitting.
1. Submit a new pull request, using `dev` as the base branch.
  - If your code changes or extends the WireViz YAML syntax, be sure to update the [syntax description document](https://github.com/wireviz/WireViz/blob/dev/docs/syntax.md) in your PR.
1. Please include in the PR description (and optionally also in the commit message body) a reference (# followed by issue number) to the issue where the suggested changes are discussed.

### Hints

- Make sure to [write good commit messages](https://chris.beams.io/posts/git-commit/).
- Always consider `git rebase` before `git merge` when joining commits from different branches, to keep the commit history simple and easier to read.
- If the `dev` branch has advanced since your fork, consider rebasing onto the current state to avoid merge conflicts.
- Avoid committing changes to generated files in PRs (examples, tutorials, etc.) to reduce merging conflicts. The owner will rebuild them.
- For complex PRs, consider [interactively rebasing](https://thoughtbot.com/blog/git-interactive-rebase-squash-amend-rewriting-history) your contribution to remove intermediate commits and clean up the commit history.
- Feel free to submit a [draft PR](https://github.blog/2019-02-14-introducing-draft-pull-requests/) for your work-in-progress. This lets other contributors comment on and review your code, while clearly marking it as not ready for merging.


## Documentation Strings

Documentation strings are to follow the Google Style ([examples](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)).
