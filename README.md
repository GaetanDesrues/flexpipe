# Pipeline Processing Framework

This module implements a flexible pipeline processing framework, designed for tracking, executing, and managing data transformations. It supports step-by-step execution, lazy execution, caching, and easy output management.

**Install**
`pip install flexpipe`

**Table of Contents**

1. Pipeline Class
2. Tracker Class
3. Transformation Class
4. Logging

## Pipeline Class

The Pipeline class coordinates a series of transformation steps, tracking the progress and managing the results of each step.

**Attributes**:

- out (Path): Directory where pipeline outputs will be stored.
- steps (list[Transformation]): List of Transformation objects representing the pipeline steps.
- tracker (Tracker): A Tracker instance that manages tracking of pipeline steps.

**Methods**:

- __init__(self, out: Path, steps: list["Transformation"]):
Initializes the pipeline, creating an output directory and associating a list of transformation steps.
- out: Path where the pipeline outputs will be saved.
- steps: List of transformations to be executed.
- start(self):
Starts the pipeline, running each transformation step sequentially.
- clean(self):
Cleans up files created by the pipeline, depending on the tracker settings (e.g., cached files or step outputs).

## Tracker Class

The Tracker class manages the state and progress of each step in the pipeline. It handles saving intermediate results, managing cache, and storing metadata.

**Attributes**:

- out (Path): Directory where pipeline outputs will be stored.
- fname (Path): Path to the tracker JSON file that stores the progress of each step.
- steps (dict): Dictionary of steps with metadata tracking their start and end.
- _meta (dict): Metadata about each step, including caching and deletion options.

**Methods**:

- __init__(self, parent: Pipeline):
Initializes the tracker, loading previous progress if available from tracker.json.
- parent: The parent Pipeline instance.
- clean_all(self):
Cleans up all tracked outputs based on step metadata, such as deleting step outputs or cached CSV files.
- start_step(self, tr):
Starts tracking a step. If the step has already been completed and the lazy flag is set, the step is skipped.
- tr: The transformation step to be started.
- Returns: True if the step should be skipped (due to laziness and completion), otherwise None.
- get_filename(self, fname, _class=None):
Generates and returns the output file path for a specific step and filename. Tracks the output file in the step’s metadata.
- fname: Name of the file to track.
- _class: The transformation class instance associated with the step.
- end_step(self, tr, df=None, meta=None):
Marks the step as complete, optionally saving a DataFrame and metadata.
- tr: The transformation step that just finished.
- df: DataFrame to be saved (optional).
- meta: Metadata to be saved (optional).
- save(self):
Saves the current progress and step information into the tracker.json file.
- get_last_df(self) -> str:
Retrieves the filename of the last output DataFrame from the most recent completed step.
- Returns: Filename (string) of the most recent DataFrame output.

## Transformation Class

The Transformation class defines individual steps in the pipeline. Each transformation can process data and optionally read from the output of the previous step.

**Attributes**:

- args: Arguments passed to the transformation during initialization.
- kwargs: Keyword arguments passed to the transformation during initialization.
- lazy (bool): If True, the transformation is skipped if it has already been completed.
- df (pd.DataFrame): The result DataFrame after processing the transformation.
- meta (dict): Metadata associated with the transformation.
- prev_df_fname (str): Filename of the previous step’s output DataFrame.
- prev_df (pd.DataFrame): DataFrame from the previous step.
- delete_step (bool): If True, the step’s output will be deleted during cleanup.
- df_delete_cache (bool): If True, cached DataFrame files will be deleted during cleanup.

**Methods**:

    __init__(self, *args, lazy=False, **kwargs):
Initializes the transformation with optional arguments and keyword arguments. The lazy flag can be used to skip already completed transformations.
- args: Positional arguments for the transformation.
- lazy: Whether to skip this step if it has already been completed.
- kwargs: Additional keyword arguments.
- _run(self, ctx: Pipeline):
Runs the transformation step, retrieving the output from the previous step (if applicable), calling the transformation’s process method, and saving the output.
- ctx: The parent Pipeline instance.

## Logging

The module uses Python’s standard logging library for debugging and tracking events during the pipeline execution.

The logger is instantiated as log and is used to record information such as when steps are skipped, when files are deleted, and general debugging information.

## Conclusion

This concludes the documentation for the pipeline processing framework. Each class and function works together to provide a flexible, lazy-execution pipeline with automatic tracking and caching capabilities.

**Docker**

```bash
docker build -t flexpipe . --no-cache
docker run -it --rm flexpipe bash  # debug

docker run -d --name flexpipe_ct flexpipe:latest
docker stop flexpipe_ct
docker rm flexpipe_ct
docker rmi flexpipe
```

**PYPI**

```bash
rm -rf build dist
python setup.py sdist bdist_wheel
python -m twine upload dist/*
```
