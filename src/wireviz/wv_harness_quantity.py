from pathlib import Path

import click
import json
import logging


class HarnessQuantity:
    def __init__(
        self, harnesses, multiplier_file="quantity_multipliers.txt", output_dir=None
    ):
        self.harness_names = [harness.stem for harness in harnesses]
        self.multipliers = {}
        self.folder = output_dir if output_dir is not None else harnesses[0].parent
        self.qty_multipliers = self.folder / multiplier_file

    def __getitem__(self, harness):
        return self.multipliers[harness]

    def fetch_qty_multipliers_from_file(self):
        if self.qty_multipliers.is_file():
            with open(self.qty_multipliers, "r") as f:
                try:
                    self.multipliers = json.load(f)
                except json.decoder.JSONDecodeError as err:
                    raise ValueError(
                        f"Invalid format for file {self.qty_multipliers}, error: {err}"
                    )
        else:
            self.get_qty_multipliers_from_user()
            self.save_qty_multipliers_to_file()
        self.check_all_multipliers_defined()

    def check_all_multipliers_defined(self):
        for name in self.harness_names:
            assert (
                name in self.multipliers
            ), f"No multiplier defined for harness {name}, maybe delete the multiplier_file {self.qty_multipliers}"

    def get_qty_multipliers_from_user(self):
        for name in self.harness_names:
            try:
                self.multipliers[name] = int(
                    input("Quantity multiplier for {}? ".format(name))
                )
            except ValueError:
                logging.warning("Quantity multiplier must be an integer!")
                break

    def save_qty_multipliers_to_file(self):
        with open(self.qty_multipliers, "w") as f:
            json.dump(self.multipliers, f)

    def retrieve_harness_qty_multiplier(self, bom_file):
        return int(self[Path(Path(bom_file).stem).stem])


@click.command(no_args_is_help=True)
@click.argument(
    "files",
    type=click.Path(
        exists=True,
        readable=True,
        dir_okay=False,
        path_type=Path,
    ),
    nargs=-1,
    required=True,
)
@click.option(
    "-m",
    "--multiplier-file-name",
    default="quantity_multipliers.txt",
    type=str,
    help="name of file used to fetch or save the qty_multipliers",
)
@click.option(
    "-f",
    "--force-new",
    is_flag=True,
    type=bool,
    help="if set, will always ask for new multipliers",
)
def qty_multipliers(files, multiplier_file_name, force_new):
    harnesses = HarnessQuantity(files, multiplier_file_name)
    if force_new:
        harnesses.qty_multipliers.unlink(missing_ok=True)

    harnesses.fetch_qty_multipliers_from_file()
    qty_multipliers = harnesses.multipliers
    return
