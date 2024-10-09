import os
import shutil
import logging
import json
from pathlib import Path, PosixPath
from functools import partial
from datetime import datetime
import pandas as pd
import traceback

__ALL__ = ["Pipeline", "Tracker", "Transformation"]


class Pipeline:
    def __init__(self, out: Path, steps: list["Transformation"] = None):
        # Initialize the pipeline with output directory and steps (list of transformations)
        log.info(f"Initializing pipeline at {out}")
        self.out = out
        self.steps = steps
        self.tracker = Tracker(self)

    def start(self, *steps: "Transformation"):
        # Start the pipeline by running all transformation steps
        if len(steps) > 0:
            self.steps = steps
        for x in self.steps:
            x._run(self)

    def clean(self):
        # Clean the pipeline by removing cached files and directories
        self.tracker.clean_all()

    def __enter__(self) -> "Pipeline":
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.clean()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False
        return True


class Tracker:
    def __init__(self, parent: Pipeline):
        # Initialize the tracker to monitor the pipeline steps
        self.out = parent.out
        self.out.mkdir(exist_ok=True)
        self.fname = self.out / "tracker.json"

        # Load previous tracker data if it exists, otherwise initialize empty steps and meta
        if self.fname.is_file():
            data = load_json(self.fname)
            self.steps = data["steps"]
            self._meta = data["infos"]
        else:
            self.steps = {}
            self._meta = {}

    def clean_all(self):
        # Clean all tracked steps, removing specified files and directories
        for name, infos in self.steps.items():
            if self._meta[name].get("delete_step"):
                shutil.rmtree(self.out / name)  # Remove the directory for the step
                log.debug(f"Deleted {str(self.out/name)!r}")
            if self._meta[name].get("df_delete_cache"):
                if x := infos["end"].get("df_out_csv"):
                    removeIfExists(x)  # Remove CSV file if it exists
                    log.debug(f"Deleted CSV {x}")

    def start_step(self, tr):
        # Begin tracking a step in the pipeline
        name = tr.__class__.__name__

        # Skip step if it's already completed and the transformation is lazy
        if (
            name in self.steps
            and self.steps[name]["end"].get("state") == "done"
            and tr.lazy
        ):
            log.info(f"Lazy transform {name!r}, skipping step")
            return True
        else:
            # Start tracking the step with initial information
            self.steps[name] = {
                "start": {
                    "name": name,
                    "date": now(),
                },
                "end": {},
            }

    def get_filename(self, fname, _class=None):
        # Get the filename to save output of the step
        name = _class.__class__.__name__
        key, ext = os.path.splitext(fname)
        k = f"{key}_{ext[1:]}"
        out = self.out / name
        out.mkdir(exist_ok=True)  # Create directory for the step if it doesn't exist
        self.steps[name]["end"][k] = out / fname  # Save output file path in tracker
        return out / fname

    def end_step(self, tr, df=None, meta=None):
        # Finalize the step and save the outputs
        name = tr.__class__.__name__

        # Save dataframe output to CSV if provided
        if df is not None:
            df.to_csv(self.get_filename("df_out.csv", tr))
        # Save additional metadata if provided
        if meta:
            dump_json(self.get_filename("meta_out.json", tr), meta)

        # Mark the step as completed with the current date
        self.steps[name]["end"]["date"] = now()
        self.steps[name]["end"]["state"] = "done"

        # Save metadata about the step (e.g., cache and deletion preferences)
        self._meta[name] = {
            "df_delete_cache": tr.df_delete_cache,
            "delete_step": tr.delete_step,
            "lazy": tr.lazy,
        }

        self.save()  # Save tracker data to disk

    def save(self):
        # Save the tracker information to the JSON file
        dump_json(self.fname, {"infos": self._meta, "steps": self.steps})

    def get_last_df(self) -> str:
        # Retrieve the filename of the last completed dataframe in the pipeline
        for name, infos in reversed(self.steps.items()):
            if infos["end"].get("state") == "done":
                if x := infos["end"].get("df_out_csv"):
                    return x  # last df of all
        #     if infos["end"].get("state") == "done":
        #         return infos["end"].get("df_out_csv")  # last step df

    def check_last_step_state(self, tr):
        for name, infos in reversed(self.steps.items()):
            if name != tr.__class__.__name__:
                return infos["end"].get("state") == "done", name
        return True, None


class Transformation:
    def __init__(self, *args, lazy=False, **kwargs):
        # Initialize transformation with arguments and parameters
        self.args = args
        self.kwargs = kwargs
        self.lazy = lazy
        self.df = None  # Dataframe produced by the transformation
        self.meta = None  # Metadata produced by the transformation

        self.prev_df_fname = None  # Filename of the previous step's dataframe
        self.prev_df = None  # Dataframe from the previous step

        # Parameters for step deletion and caching
        self.delete_step = False
        self.df_delete_cache = False

    def _run(self, ctx: Pipeline):
        # Execute the transformation within the pipeline context
        skip = ctx.tracker.start_step(self)
        if skip:
            return  # Skip step if it is lazy and already done

        # Check last step
        val, last_step = ctx.tracker.check_last_step_state(self)
        if not val:
            raise RuntimeError(f"Last step {last_step!r} failed")

        # Load the previous dataframe if available
        self.prev_df_fname = ctx.tracker.get_last_df()
        if self.prev_df_fname and os.path.exists(self.prev_df_fname):
            self.prev_df = pd.read_csv(self.prev_df_fname, index_col=0)

        # Get the filename function for this step
        self.get_fname = partial(ctx.tracker.get_filename, _class=self)

        # Run the actual transformation process
        ret = self.process(*self.args, **self.kwargs)
        meta = ret or self.meta  # Use returned metadata or default to self.meta

        # End the step, saving the dataframe and metadata
        ctx.tracker.end_step(self, df=self.df, meta=meta)


def removeIfExists(fname: str):
    # Remove a file if it exists
    if os.path.exists(fname):
        os.remove(fname)


def load_json(filename: str, munch: bool = False, **kwargs):
    """Loads a json file with `json.load`

    :return: dict
    """
    filename = str(filename)
    with open(filename, "r") as f:
        if munch:
            from munch import munchify

            return munchify(json.load(f, **kwargs))
        else:
            return json.load(f, **kwargs)


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        # Custom JSON encoder for datetime and PosixPath
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, PosixPath):
            return str(obj)
        return super().default(obj)


def dump_json(filename: str, data, **kwargs):
    """Dumps a dict to a json file with `json.dump`

    :param data: dict
    """
    filename = str(filename)
    kwargs.setdefault("indent", 4)  # Pretty-print JSON with indentation
    kwargs.setdefault("cls", JsonEncoder)  # Use custom encoder
    with open(filename, "w") as f:
        json.dump(data, f, **kwargs)


now = datetime.now
log = logging.getLogger(__name__)
