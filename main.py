from typing import List
import json

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def main():
    filename_colors = "resources/colors.json"
    filename_ejcs = "resources/list_of_ejcs.csv"
    width_px = 1000
    height_px = 800

    colors = _read_colors(filename=filename_colors)
    df_ejcs = prepare_ejcs(filename=filename_ejcs, colors=colors)
    fig = create_map(df_ejcs=df_ejcs)
    create_output(
        fig=fig,
        width=width_px,
        height=height_px,
        output_folder="output",
        show_figure=True,
        save_figure=True,
    )


def create_output(
    fig: go.Figure,
    width: int,
    height: int,
    output_folder: str,
    show_figure: bool,
    save_figure: bool,
) -> None:
    config = {"displayModeBar": False}

    fig.update_layout(width=width, height=height)

    if show_figure:
        fig.show(config=config)

    if save_figure:
        filename = "ejc_map"
        fig.write_html(
            f"{output_folder}/{filename}.html",
            include_plotlyjs="cdn",
            config=config,
        )
        fig.write_html(
            f"index.html",
            include_plotlyjs="cdn",
            config=config,
        )
        fig.write_image(
            f"{output_folder}/{filename}.webp",
            width=width,
            height=height,
            scale=1.0,
        )


def create_map(df_ejcs: pd.DataFrame) -> go.Figure:
    fig = px.line_map(
        df_ejcs,
        lat="latitude",
        lon="longitude",
        map_style="carto-voyager-nolabels",  # For possible map styles see https://plotly.com/python/tile-map-layers/
        center=dict(lat=51, lon=2),
        zoom=3.6,
    )

    fig.add_traces(
        px.scatter_map(
            df_ejcs,
            lat="latitude",
            lon="longitude",
            color="color",
            custom_data=[
                df_ejcs["issue"],
                df_ejcs["year"],
                df_ejcs["city"],
                df_ejcs["country"],
            ],
        )["data"]
    )

    fig.update_traces(
        marker=dict(size=16),  # line=dict(color="black", width=2)),
        line=dict(width=0.6, color="darkgray"),
        hovertemplate="<b>EJC %{customdata[1]}</b><br>"
        + "Issue: %{customdata[0]}<br>"
        + "Location: %{customdata[2]}, %{customdata[3]}"
        + "<extra></extra>",
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        hoverlabel=dict(font=dict(size=20)),
    )

    return fig


def prepare_ejcs(filename: str, colors: List[str]) -> pd.DataFrame:
    df_ejcs_raw = pd.read_csv(filename, sep=";")
    df_ejcs_grouped = _group_same_hosts(df_ejcs=df_ejcs_raw)
    df_ejcs = _join_ejcs_grouped(df_ejcs=df_ejcs_raw, df_ejcs_grouped=df_ejcs_grouped)

    extended_colors = _extend_colors(colors=colors, n_entries=len(df_ejcs_raw))
    return df_ejcs.assign(color=extended_colors)


def _join_ejcs_grouped(
    df_ejcs: pd.DataFrame, df_ejcs_grouped: pd.DataFrame
) -> pd.DataFrame:
    df_ejcs_joined = df_ejcs.filter(["city", "country", "latitude", "longitude"]).merge(
        right=df_ejcs_grouped,
        on=["city", "country", "latitude", "longitude"],
        how="left",
    )
    return df_ejcs_joined


def _group_same_hosts(df_ejcs: pd.DataFrame) -> pd.DataFrame:
    df_ejcs_grouped = (
        df_ejcs.groupby(["city", "country", "latitude", "longitude"])
        .agg(
            {
                "issue": lambda x: " | ".join(map(str, x)),
                "year": lambda x: " | ".join(map(str, x)),
            }
        )
        .reset_index()
    )
    return df_ejcs_grouped


def _read_colors(filename: str) -> List[str]:
    with open(filename) as f:
        colors = json.load(f)
    return [color["color"] for color in colors]


def _extend_colors(colors: List[str], n_entries: int) -> List[str]:
    q, r = divmod(n_entries, len(colors))
    extended_colors = q * colors + colors[:r]
    return extended_colors


if __name__ == "__main__":
    main()
