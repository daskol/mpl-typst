import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from mpl_typst.testing import IssueRegression


class TestIssue32(IssueRegression):

    DATA = [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6], [3, 4, 5, 6, 7]]

    @staticmethod
    def figure() -> Figure:
        fig, ax = plt.subplots(figsize=(6, 4), layout='constrained')
        labels = ['Data 1', 'Data 2', 'Data 3']
        colors = ['black', '#CC79A7', '#56B4E9']
        _counts, _bins, patches = ax.hist(
            TestIssue32.DATA,
            bins=5, color=colors, edgecolor='black')  # type: ignore

        for patch in patches[-1]:  # type: ignore[index]
            patch.set_hatch('//')

        ax.set_xlabel('Value')
        ax.set_ylabel('Count')
        ax.set_title('Histogram with Hatch Patterns')
        ax.legend(labels)
        return fig
