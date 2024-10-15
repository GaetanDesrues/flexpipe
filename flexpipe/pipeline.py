import logging
import traceback
from pathlib import Path
import gatools as ga
from logging.handlers import RotatingFileHandler

from flexpipe.tracker import Tracker
from flexpipe.transformation import Transformation


class Pipeline:
    def __init__(self, out: Path, steps: list["Transformation"] = None, logger=None):
        out.mkdir(exist_ok=True)
        self.out = out
        self.steps = steps
        self.state = "init"

        if logger:
            self.log_to_file(logger)

        # Initialize the pipeline with output directory and steps (list of transformations)
        log.info(f"Initializing pipeline at {out}")
        self.tracker = Tracker(self)

    def start(self, *steps: "Transformation", ignore_failed=False):
        self.state = "starting"

        # Start the pipeline by running all transformation steps
        if len(steps) > 0:
            self.steps = steps
        if self.steps is not None:
            valid = True
            for x in self.steps:
                self.state = f"step-{x.name}"
                if valid:
                    valid = x._run(self, ignore_failed) == "done"
                    valid = valid or ignore_failed
                else:
                    log.error("Stopping pipeline: last step failed.")
                    self.state = "failed"
                    return
        self.state = "finished"

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

    def log_to_file(self, logger, level=logging.DEBUG):
        x = RotatingFileHandler(
            self.out / "logs.txt",
            maxBytes=int(1e6),  # 5 Mo max
            backupCount=3,
        )
        x.setFormatter(ga.CSVFormatter())
        if level == "default":
            level = logger.level
        x.setLevel(level)
        logger.addHandler(x)

    def get_fname(self, step, key):
        if step in self.tracker.steps:
            return self.tracker.steps[step]["end"].get(key)
        log.error(f"({step}, {key}) could not be found")


log = logging.getLogger(__name__)
