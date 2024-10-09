import logging
from pathlib import Path
import seaborn as sns

from flexpipe import Pipeline, Transformation


class TSnsLoad(Transformation):
    def process(self, dataset):
        # Load current dataframe
        self.df = sns.load_dataset(dataset)
        # self.df will be saved to file as 'df_out_csv' entry in tracker


class TRenameCols(Transformation):
    def process(self):
        self.df_delete_cache = False
        self.delete_step = False
        self.lazy  # overwrite laziness

        # Save a new file
        self.get_fname("my_file.txt")  # will create a my_file_txt entry in tracker

        # Access previous step dataframe and path
        df_fname = self.prev_df_fname
        df = self.prev_df

        # Return metadata (written as json file)
        # or save it to 'self.meta'
        return {"shape": df.shape}


def main():
    out = Path(__file__).parent / "out"

    # Test steps
    steps = [
        TSnsLoad("iris", lazy=True),
        TRenameCols(),
    ]

    x = Pipeline(out, steps)
    x.start()
    x.clean()


log = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    main()
