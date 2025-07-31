import base64
import io
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Literal, TypeVar

import matplotlib.pyplot as plt
from IPython.display import HTML
from matplotlib.figure import Figure
from PIL import Image

__version__ = "0.2.0"
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
    loop: Literal["infinite", "once", "bounce"] = "infinite",
) -> HTML | None:
    """
    Generate a GIF from a sequence of frames.

    Based on the return type of the function, the following happens:
    - ``None``: assume that the currently active matplotlib figure has been
      contains the desired image. Use this figure for the next frame, and then
      close the figure.
    - ``str`` or ``Path``: assume that this points to an image file.
      This gets used as the next image in the gif.
    - ``plt.Figure``: use the current content of the matplotlib figure as the
      next image in the gif. The figure is **not** closed.

    The function is called for each frame, and the return values are used
    to generate images for the gif in order. In pseudocode:

    .. code-block:: python

        images = []
        for frame in frames:
            ret = function(frame)
            if isinstance(ret, str | Path):
                images.append(Image.open(ret))
            elif isinstance(ret, Figure):
                images.append(ret.savefig())
            elif ret is None:
                images.append(plt.savefig())

        return gif(images)


    Parameters
    ----------

    frames
        The frames to generate the gif from. These are passed in order,
        and one-by-one to the function, and can be arbitrary objects.
    function
        A function that takes an arbitrary frame object as input,
        and generates a single image for the gif. There are several behaviours
        here, depending on the return type:
        - ``None``: assume that a matplotlib plot has been generated.
            This is then used as the next image in the gif.
            The figure is cleared automatically after each frame.
        - ``plt.Figure``: uses the current content of the figure as the
            next image in the gif. The figure is **not** closed.
        - str or Path: assume that this points to an image file.
            This gets used as the next image in the gif.
    save_to
        The path to save the gif to. If not provided, the gif is not saved.
    fps
        The frames per second of the gif, by default 10
    css
        The CSS to apply to the HTML returned by the function.
    savefig_kwargs
        Keyword arguments to pass to ``[plt/figure].savefig()``
    loop
        The loop mode of the gif:
        - ``"infinite"``: loop the gif indefinitely
        - ``"once"``: play the gif once
        - ``"bounce"``: play the gif forwards and then backwards indefinitely

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

    save_kwargs = {
        **_DEFAULT_SAVEFIG_KWARGS,
        **(savefig_kwargs or {}),
    }

    css = {**__DEFAULT_CSS, **(css or {})}
    style = ";".join([f"{k}: {v}" for k, v in css.items()])

    # Collect all frames as PIL Images
    pil_frames = []
    for frame in frames:
        # call the function
        ret = function(frame)

        # get a file-like oject for the image,
        # and clean up as appropriate
        if isinstance(ret, str | Path):
            file = Path(ret)
            # no cleanup needed
        elif isinstance(ret, Figure):
            file = io.BytesIO()
            ret.savefig(file, **save_kwargs)
            # leave the figure open for the user
            # to keep working on : no cleanup needed
        elif ret is None:
            file = io.BytesIO()
            plt.savefig(file, **save_kwargs)
            # close the figure
            plt.close()
        else:
            raise ValueError(
                f"Unexpected return type from function: {type(ret)}. "
                "Expected one of None, str, Path, or Figure. Please see the "
                "docstring of `gif` for more information."
            )
        pil_frames.append(
            Image.open(file)
            .convert("P", palette=Image.Palette.ADAPTIVE)
            .convert("RGBA")
        )

    if loop == "bounce":
        pil_frames = pil_frames + pil_frames[1:-1][::-1]

    # Save as GIF
    if pil_frames:
        pil_frames[0].save(
            save_path,
            save_all=True,
            append_images=pil_frames[1:],
            loop=0 if loop in ("infinite", "bounce") else None,
            duration=int(1000 / fps),
            disposal=2,
        )

    with open(save_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    return HTML(
        f"""<img 
        src="data:image/gif;base64,{b64}" 
        style="{style}" 
        loop="infinite"/>"""
    )
