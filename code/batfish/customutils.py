from prettytable import PrettyTable
import pandas as pd


def process_stats(result):
    """Stas processing"""

    for h, res in result.items():
        # print(f"TYPE OF RES -> {type(res)}")
        print(f"TYPE OF RES -> {type(res.result.statistics)}")

        res.result.statistics.insert(0, "Device", [f"{h}"], True)

    tmp_list_df = []
    for h, res in result.items():
        tmp_list_df.append(res.result.statistics)

    tmp_df = pd.concat(tmp_list_df, axis=0)
    tmp = tmp_df.reset_index(drop=True)

    return tmp


def dataframe_to_prettytable(
    df: pd.DataFrame, title: str = "Error Elements"
) -> PrettyTable:
    """Creates a Pretty Table from a Dataframe"""
    # Create PrettyTable object
    table = PrettyTable()

    if df is not None:
        # Add columns
        table.field_names = ["#"] + df.columns.tolist()
        # Add rows
        for row in df.itertuples():
            table.add_row(row)

    return table.get_string(title=title)
