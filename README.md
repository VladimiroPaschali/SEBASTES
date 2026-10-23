# SEBASTES

Software for underwater stereo camera analysis.

SEBASTES is a Python application for viewing and annotating images from a calibrated underwater stereo camera. You step through left/right image pairs, mark and measure fish, assign species and frame metadata, and get 3D range and length from stereo triangulation. It was developed by NOAA Fisheries employees Kresimir Williams and Rick Towler, but is not an official government product. The original manual is NOAA report PR2016-03; it is not included in this repository.

This version adds:

- **Video input**: two synchronized videos, one per camera, can be used instead of folders of still images.
- **Linux support**: image loading no longer depends on Windows paths.
- **First-run setup**: SEBASTES creates its configuration database when it is missing, so it starts from a fresh clone.

It has been tested on Ubuntu 24.04 with Python 3.12. The original NOAA version targets Windows.

## Installation

You need Python 3 with `venv` (on Ubuntu/Debian: `sudo apt install python3-venv`).

```bash
git clone <repository URL>
cd SEBASTES
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` installs `opencv-python-headless`, not `opencv-python`. On Linux, the regular `opencv-python` package bundles its own Qt, which can stop PySide6 from opening its window. If you already have it in the environment, remove it with `pip uninstall opencv-python`.

## Running

```bash
source .venv/bin/activate
python application/MainWindow.py
```

You can start it from any folder. On Windows, `python SEBASTES.py` from inside `application/` also works: it writes the console output to `logs/`.

## Folder layout

SEBASTES keeps its configuration next to the `application` folder:

```
SEBASTES/
├── application/      the program
├── db/               created on the first start
│   ├── Application.db      projects, profiles, species, metadata groups
│   └── Project.db.sql      template for the per-deployment data database
└── calibrations/     stereo calibration files (create it yourself)
```

`db/` and `calibrations/` are not tracked by git. If you have the `db` folder from the original NOAA distribution, copy it to `SEBASTES/db` and SEBASTES uses it as is. It never overwrites existing files.

The empty `Application.db` is built from `application/schema/Application.db.sql`. That schema was reconstructed from the queries in the code, so it may differ in small ways from the NOAA original.

## First-time setup

On the first start SEBASTES tells you it created an empty `Application.db`. Before you can load any data you need a species collection, a profile and a project.

### 1. Species collection

Open **File > Setup Profiles, Species, Etc** and go to the **Species Collections** tab.

1. Click **Create new Species Collection** and type a name and a description.
2. Click **Insert** once per species. Give each one a name, a description, a button color and an optional order.

A species collection holds up to 30 species. Each one becomes a button that you use while annotating. The collection is saved when you insert its first species.

### 2. Profile

A profile tells SEBASTES how a deployment folder is organized. In the same dialog, go to the **Profiles** tab.

1. Click **Create New Profile**.
2. Fill in the settings (see the table below).
3. Click **Save changes**.

**Save changes** also closes the dialog. To create another profile, open the dialog again.

| Setting | Video deployments | Image deployments |
|---|---|---|
| LeftCameraImagePath | Subfolder with the left camera video | Subfolder with the left camera images |
| RightCameraImagePath | Subfolder with the right camera video | Subfolder with the right camera images |
| ImageFileType | Video extension: `mp4`, `mov`, `m4v`, `avi`, `mkv` or `mts` | Image extension, e.g. `jpg` |
| FrameNumberIndices | Leave empty | Character positions of the frame number in the file name (1-based, from–to) |
| ImageTimestampType, ImageTimestampFormat, ImageTimestampStart | Leave empty | Where the image time comes from: `in_file_name` (with format and start position), `EXIF` or `none` |
| CalibrationFileName | Calibration file name in `calibrations/`, or empty for no 3D | Same |
| RotateLeftImage, RotateRightImage | Rotation in degrees | Same |
| SubsampleMask | Optional `x,y,width,height` area to analyse; empty for the whole image | Same |
| CollectMetadata | Show the frame metadata panel while recording | Same |

The extension is matched case-insensitively, so `mp4` also finds `.MP4` files. Hover over a field in the dialog to see its description.

### 3. Metadata group (optional)

Frame metadata are extra fields recorded per frame, such as habitat type. Groups are set up in the **Metadata Groups** tab. Every project needs a group, so the new database already contains an empty one called `NoMetadata`. Use it if you don't collect frame metadata.

### 4. Project

Open **File > Create New Project**, or click **Create Project** in the project list that appears when you load a deployment. Give the project a name and pick its species collection and metadata group.

## Preparing a deployment

A deployment is one folder per recording, with one subfolder per camera. The subfolder names must match the profile.

For a video deployment, each camera subfolder must contain **exactly one** video:

```
dive_2026_05_01/
├── left/
│   └── GX010123.MP4
└── right/
    └── GX010456.MP4
```

For an image deployment, each subfolder contains the still images. The frame number must be part of every file name.

SEBASTES creates a `data/` subfolder inside the deployment for its results.

### Videos

- **Synchronization.** The two videos must be synchronized: frame *n* of the left video and frame *n* of the right video must show the same instant. SEBASTES does not apply any offset, so cut the videos to a common start before using them.
- **Frame numbers.** Frames are numbered from 0, as in OpenCV.
- **Timestamps.** Each frame's time is the recording start time stored in the file (MP4/MOV `creation_time`) plus *frame / fps*. This is the camera clock as stored by the camera, not necessarily UTC. Videos without a start time, such as many edited or exported files, get no timestamp.
- **Calibration.** Use a calibration made with the same cameras, in the same video mode and resolution as the videos, with image stabilization turned off.
- **Speed.** Stepping forward and playback are fast. Jumping to a distant frame is slower, because the video has to be decoded from the previous keyframe: about 0.1 s per jump for 1080p H.264 in our tests.

## Stereo calibration

SEBASTES does not compute calibrations. Make one with another tool and put the file in `SEBASTES/calibrations/`. Then set `CalibrationFileName` in the profile to the file name. Supported formats:

- `.mat`: MATLAB Camera Calibration Toolbox stereo results (`Calib_Results_stereo.mat`).
- `.npz`: OpenCV parameters saved with NumPy, with the arrays `cameraMatrixL`, `distCoeffsL`, `cameraMatrixR`, `distCoeffsR`, `R`, `T` and optionally `F`.
- `.yml`: a YAML export with `Camera1`/`Camera2` intrinsic and extrinsic parameters, including SeaGIS calibrations.

3D coordinates, ranges and lengths are expressed in the units of the calibration's translation vector `T`. If `CalibrationFileName` is empty, SEBASTES works without 3D measurements.

## Annotating

1. **File > Load Deployment...** and select the deployment folder.
2. Select the project.
3. The first time you open a deployment, select its profile. SEBASTES remembers the profile for that deployment.
4. Move through the frames:
   - **Right / Left arrow**: move by the number of frames set in **Sample Interval**.
   - **Ctrl + Right / Left**: move one frame.
   - The slider, the frame number box and **Play** also work.
5. Press **Record** and enter your initials. The species buttons and the measuring tools are enabled while recording.
6. **Copy Images to...** saves the current pair. Image files are copied; in video mode the two frames are saved as PNG, for example `GX010123_frame000250.png`.

The marking and measuring tools are described in the NOAA manual.

While a deployment is open, SEBASTES keeps a `<user>.lck` file in its `data/` folder and deletes it on exit. The file does not currently stop a second user from opening the same deployment, so avoid annotating it from two computers at once.

## Results

Results are written to `<deployment>/data/<project>_<deployment>.db`, a SQLite database. When you close SEBASTES or load another deployment, every table is also exported to CSV in the same folder:

| File | Content |
|---|---|
| `*_frames.csv` | Recorded frames: `FRAME_TIME` is the image or video time, `TIME_STAMP` is when the frame was annotated |
| `*_targets.csv` | Targets with species, comments and links |
| `*_points.csv` | Marked points, with 3D position and range in stereo mode |
| `*_lines.csv` | Measured lines, with length in stereo mode |
| `*_bounding_boxes.csv` | Bounding boxes from **Create training set** |
| `*_frame_metadata.csv` | Frame metadata |

The image adjustments (brightness, contrast…) are saved to `<deployment>_image_adjustments.npy`.

## Troubleshooting

- **The window does not open on Linux** (`Could not load the Qt platform plugin "xcb"`). Check that `opencv-python` is not installed (see Installation) and install `libxcb-cursor0` (`sudo apt install libxcb-cursor0`).
- **SEBASTES closes after an error while loading a deployment.** This is how SEBASTES handles every loading error. Read the message: usually a camera subfolder is missing, or it holds no video or more than one.
- **"Timestamp could not be extracted from file name"**. Image profiles without a timestamp type show this warning on every load. You can ignore it.

## Building the Windows executable

On Windows, `application/build_exe.bat` builds the executable with PyInstaller using `SEBASTES.spec`. Edit the `pathex` in the spec file first: it points to the original developer's WinPython install.
