import base64
import io
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, TypeVar

import imageio.v2 as imageio
import matplotlib.pyplot as plt
from IPython.display import HTML
from matplotlib.figure import Figure

__version__ = "0.1.0"
__all__ = ["gif"]

__DEFAULT_CSS = {"width": "360px", "height": "auto"}
_DEFAULT_SAVEFIG_KWARGS = {"bbox_inches": "tight"}

Frame = TypeVar("Frame")


def gif(
    frames: Iterable[Frame],
    function: Callable[[Frame], None | str | Path | Figure],
    save_to: str | Path | None = None,
    fps: float = 10,
    css: dict[str, str] | None = None,
    savefig_kwargs: dict[str, Any] | None = None,
) -> HTML | None:
    """
    Generate a GIF from a sequence of frames.

    Parameters
    ----------
    frames
        The frames to generate the gif from. These are passed in order,
        and one-by-one to the function, and can be arbitrary objects.
    function
        A function that takes an arbitrary frame object as input,
        and generates a single image for the gif. There are several behaviours
        here, depending on the return type:
            - None: assume that a matplotlib plot has been generated.
              This is then used as the next image in the gif.
              The figure is cleared automatically after each frame.
            - plt.Figure: uses the current content of the figure as the
              next image in the gif. The figure is then closed.
            - str or Path: assume that this points to an image file.
              This gets used as the next image in the gif.
    save_to
        The path to save the gif to. If not provided, the gif is not saved.
    fps
        The frames per second of the gif, by default 10
    css
        The CSS to apply to the HTML returned by the function.

    Returns
    -------
    HTML
        The HTML to display the gif in a Jupyter notebook. This contains
        a base64 encoded version of the gif, and so is independent of the
        file system - you can share this notebook as a standalone file and
        the gif will still display.
    """

    if save_to is None:
        save_path = Path(tempfile.mktemp(suffix=".gif"))
    else:
        save_path = Path(save_to).with_suffix(".gif")

    css = {**__DEFAULT_CSS, **(css or {})}
    style = ";".join([f"{k}: {v}" for k, v in css.items()])

    with imageio.get_writer(save_path, mode="I", fps=fps, loop=0) as writer:
        for frame in frames:
            returned_image = function(frame)
            file = get_file_for(returned_image, savefig_kwargs or {})
            image = imageio.imread(file)
            writer.append_data(image)  # type: ignore
            clean_up_based_on(returned_image)

    with open(save_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    return HTML(
        f"""<img 
        src="data:image/gif;base64,{b64}" 
        style="{style}" 
        loop="infinite"/>"""
    )


def get_file_for(
    returned_image: None | str | Path | Figure,
    savefig_kwargs: dict[str, Any],
) -> Path | io.BytesIO:
    if isinstance(returned_image, str | Path):
        return Path(returned_image)

    tmp_file = io.BytesIO()
    save_kwargs = {**_DEFAULT_SAVEFIG_KWARGS, **savefig_kwargs}
    if returned_image is None:
        plt.savefig(tmp_file, **save_kwargs)
    elif isinstance(returned_image, Figure):
        returned_image.savefig(tmp_file, **save_kwargs)

    tmp_file.seek(0)
    return tmp_file


def clean_up_based_on(returned_image: None | str | Path | Figure):
    if returned_image is None:
        plt.close()
    elif isinstance(returned_image, Figure | str | Path):
        pass
    else:
        raise ValueError(
            f"Unexpected return type from function: {type(returned_image)}. "
            "Expected one of None, str, Path, or Figure. Please see the "
            "docstring of `gif` for more information."
        )
