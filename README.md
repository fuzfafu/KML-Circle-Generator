# Circle KML Generator

Draws a circle of a chosen radius around each coordinate in a CSV file,
and saves it as a KML map file.

## What you need

Python installed. Check by opening a terminal and typing:

```
python
```

If that doesn't show a version number, install Python from
[python.org/downloads](https://www.python.org/downloads/) (on Windows,
tick **"Add Python to PATH"** during setup, and use `python` instead of
`python3` below).

## How to run it

1. Put `circle_kml.py` and your CSV file in the same folder.
2. Open a terminal in that folder.
3. Run:

```
python3 circle_kml.py
```

4. Answer the two questions it asks:
   - the path to your CSV file (try `sample_coordinates.csv` to test it)
   - the circle radius in meters

That's it. It saves two `.kml` files in the same folder, named after your
CSV (e.g. `sample_coordinates_circles.kml` and
`sample_coordinates_centers.kml`) and tells you exactly where:

- **`..._circles.kml`** — just the circle outlines
- **`..._centers.kml`** — just a marker at each circle's center point

Keeping them separate makes it easy to turn one off (e.g. hide the center
pins but keep the circles) in Google Earth or My Maps.

Open either file in [Google Earth](https://earth.google.com/) or
[Google My Maps](https://www.google.com/maps/d/) to see your circles.

## Your CSV file

You can get a CSV file by using Open Street Maps, asking any AI or creating it in Excel (not recommended)
Needs a header row with `latitude` and `longitude` columns. A `name`
column is optional but will label your points:

```
name,latitude,longitude
Warehouse A,40.7128,-74.0060
Warehouse B,34.0522,-118.2437
```

## Troubleshooting

- **"command not found: python3"** — try `python` instead, or reinstall
  Python and check "Add to PATH" was ticked during setup.
- If you don't have Python installed, when you run `python` it may pronpt
  you to download it from the MS store as an easy option, otherwise you
  can download from [wwww.python.org/downloads](https://www.python.org/downloads/)
- **"Couldn't find [file]"** — make sure you typed the correct file name
  and that the CSV is in the same folder you're running the command from.
- **"CSV must contain 'latitude' and 'longitude' columns"** — check your
  CSV's header row has those exact column names.
- **Typed something that's not a number for the radius** — it just falls
  back to the default (250m) and tells you so; rerun if you wanted a
  different value.

## Sharing this with others

Just send the whole folder (or `circle_kml.py` + your CSV together).
Anyone with Python installed can run it — no other setup needed.
