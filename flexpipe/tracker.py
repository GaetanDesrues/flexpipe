import os
import shutil
import logging
from pathlib import PosixPath
from datetime import datetime
import gatools as ga
from flexpipe.transformation import Transformation as T


class Tracker:
    def __init__(self, parent):
        from flexpipe.pipeline import Pipeline

        parent: Pipeline
        # Initialize the tracker to monitor the pipeline steps
        self.out = parent.out
        self.out.mkdir(exist_ok=True)
        self.fname = self.out / "tracker.json"

        # Load previous tracker data if it exists, otherwise initialize empty steps and meta
        if self.fname.is_file():
            data = ga.load_json(self.fname)
            self.steps = data["steps"]
            self._meta = data["infos"]
        else:
            self.steps = {}
            self._meta = {}

    def clean_all(self):
        if not self._meta:
            return
        # Clean all tracked steps, removing specified files and directories
        for name, infos in self.steps.items():
            if self._meta.get(name).get("delete_step"):
                if os.path.exists(self.out / name):
                    shutil.rmtree(self.out / name)  # Remove the directory for the step
                    log.debug(f"Deleted {str(self.out/name)!r}")
            if self._meta.get(name).get("df_delete_cache"):
                if x := infos["end"].get("df_out_csv"):
                    ga.removeIfExists(x)  # Remove CSV file if it exists
                    log.debug(f"Deleted CSV {x}")

    def start_step(self, tr: T):
        # Begin tracking a step in the pipeline
        name = tr.name

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

    def get_filename(self, fname, _class: T = None):
        # Get the filename to save output of the step
        name = _class.name
        key, ext = os.path.splitext(fname)
        k = f"{key}_{ext[1:]}"
        out = self.out / name
        out.mkdir(exist_ok=True)  # Create directory for the step if it doesn't exist
        self.steps[name]["end"][k] = out / fname  # Save output file path in tracker
        return out / fname

    def get_outdir(self, _class: T = None):
        out = self.out / _class.name
        out.mkdir(exist_ok=True)
        return out

    def end_step(self, tr: T, df=None, meta=None, state="done"):
        # Finalize the step and save the outputs
        name = tr.name

        # Save dataframe output to CSV if provided
        if df is not None:
            df.to_csv(self.get_filename("df_out.csv", tr))
        # Save additional metadata if provided
        if meta:
            ga.dump_json(self.get_filename("meta_out.json", tr), meta, cls=JsonEncoder)

        # Mark the step as completed with the current date
        self.steps[name]["end"]["date"] = now()
        self.steps[name]["end"]["state"] = state

        # Save metadata about the step (e.g., cache and deletion preferences)
        self._meta[name] = {
            "df_delete_cache": tr.df_delete_cache,
            "delete_step": tr.delete_step,
            "lazy": tr.lazy,
        }

        self.save()  # Save tracker data to disk

    def save(self):
        # Save the tracker information to the JSON file
        ga.dump_json(
            self.fname, {"infos": self._meta, "steps": self.steps}, cls=JsonEncoder
        )

    def get_last_df(self) -> str:
        # Retrieve the filename of the last completed dataframe in the pipeline
        for name, infos in reversed(self.steps.items()):
            if infos["end"].get("state") == "done":
                if x := infos["end"].get("df_out_csv"):
                    return x  # last df of all
        #     if infos["end"].get("state") == "done":
        #         return infos["end"].get("df_out_csv")  # last step df

    def check_last_step_state(self, tr: T):
        for name, infos in reversed(self.steps.items()):
            if name != tr.name:
                return infos["end"].get("state") == "done", name
        return True, None


class JsonEncoder(ga.JsonEncoder):
    def default(self, obj):
        # Custom JSON encoder for datetime and PosixPath
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, PosixPath):
            return str(obj)
        return super().default(obj)


now = datetime.now
log = logging.getLogger(__name__)
