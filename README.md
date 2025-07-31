<div align="center">

# `make-a-gif`

A (very) simple package for generating gifs using `matplotlib`.

<img src="https://github.com/jla-gardner/make-a-gif/raw/main/examples/outputs/noise.gif" width="80%" style="border-radius: 10px;">

</div>

## Installation

```bash
pip install make-a-gif
```

or just copy across the `make_a_gif.py` file to your project.

## Usage

For a full suite of examples, see the [examples](examples) directory - note that 
`make-a-gif` works well with Jupyter notebooks.

```python
import matplotlib.pyplot as plt
from make_a_gif import gif


# define a function that generates a plot for a given frame
def plotting_func(i: int) -> None:
    xs = range(i + 1)
    ys = [x**2 for x in xs]
    plt.plot(xs, ys, "-o", clip_on=False, zorder=10)
    # make sure the limits are always the same
    plt.xlim(0, 10)
    plt.ylim(0, 100)


# create the gif
gif(plotting_func, frames=range(11), fps=2, save_to="squared.gif")
```
<img src="examples/outputs/squared.gif" width="360px">


## Documentation

The only object exported by `make-a-gif` is the `gif` function.

```python
gif(
    frames: Iterable[Frame],
    function: Callable[[Frame], None | str | Path | Figure],
    save_to: str | Path | None = None,
    fps: float = 10,
    css: dict[str, str] | None = None,
    savefig_kwargs: dict[str, Any] | None = None,
) -> HTML | None:
    ...
```

**Description:**

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

```python
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
```

**Parameters:**

- `frames` is an iterable of arbitrary objects. These are passed in order,
  and one-by-one to the `function`.
- `function` takes an arbitrary frame object as input, and generates a single
  image for the gif. There are several behaviours here, depending on the return
  type of `function`:
    - `None`: assume that a matplotlib plot has been generated.
      This is then used as the next image in the gif.
      The figure is closed automatically after each frame.
    - `plt.Figure`: uses the current content of the figure as the
      next image in the gif. The figure is **not** closed.
    - `str` or `Path`: assume that this points to an image file.
      This gets used as the next image in the gif.
- `save_to` is the path to save the gif to. If not provided, the gif is not saved.
- `fps` is the frames per second of the gif, by default 10
- `css` is the CSS to apply to the HTML returned by the function.
- `savefig_kwargs` are the keyword arguments to pass to `plt.savefig` when
  saving the figure to a file. The default is `{"bbox_inches": "tight", "transparent": True}`.
- `loop` is the loop mode of the gif:
  - `"infinite"`: loop the gif indefinitely
  - `"once"`: play the gif once
  - `"bounce"`: play the gif forwards and then backwards indefinitely

**Returns:**

`gif` returns an `IPython.display.HTML` object. This contains a base64 encoded
version of the gif, and so is independent of the file system - you can e.g. share
notebooks that display this object as a standalone file and the gif will still
work.