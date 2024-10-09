import logging
from pathlib import Path
import seaborn as sns

from flexpipe import Pipeline, Transformation as Tr


class TSnsLoad(Tr):
    def process(self, dataset):
        self.df = sns.load_dataset(dataset)


class TRenameCols(Tr):
    def process(self):
        self.delete_step = True

        self.df = self.prev_df
        self.df.rename(columns={"species": "sp"}, inplace=True)


class TSave(Tr):
    def process(self, fname):
        self.prev_df.to_csv(self.get_fname(fname))


log = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    out = Path(__file__).parent / "out"

    with Pipeline(out) as x:
        x.start(
            TSnsLoad("iris", lazy=True),
            TRenameCols(),
            TSave("last_df.csv"),
        )
