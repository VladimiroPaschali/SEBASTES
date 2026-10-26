# SEBASTES

Software for underwater stereo camera analysis.

SEBASTES is a Python application for viewing and annotating images from a calibrated underwater stereo camera. You step through left/right image pairs, mark and measure fish, assign species and frame metadata, and get 3D range and length from stereo triangulation. It was developed by NOAA Fisheries employees Kresimir Williams and Rick Towler, but is not an official government product. The original manual is NOAA report PR2016-03; it is not included in this repository.

This version adds:

- **Video input**: two synchronized videos, one per camera, can be used instead of folders of still images.
- **Linux support**: image loading no longer depends on Windows paths.
- **First-run setup**: SEBASTES creates its configuration database when it is missing, so it starts from a fresh clone.

It has been tested on Ubuntu 24.04 with Python 3.12. The original NOAA version targets Windows, but the Windows steps below have not yet been tested with this version.

## Installation on Linux

You need Python 3 with `venv` (on Ubuntu/Debian: `sudo apt install python3-venv`).

```bash
git clone <repository URL>
cd SEBASTES
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` installs `opencv-python-headless`, not `opencv-python`. On Linux, the regular `opencv-python` package bundles its own Qt, which can stop PySide6 from opening its window. If you already have it in the environment, remove it with `pip uninstall opencv-python`.

## Installation on Windows

1. **Install Python.** Download the 64-bit Python 3.12 installer from [python.org](https://www.python.org/downloads/windows/). In the first screen of the installer, tick **Add python.exe to PATH**.
2. **Get SEBASTES.** Either:
   - install [Git for Windows](https://git-scm.com/download/win) and clone the repository (below), or
   - on the GitHub page, use **Code > Download ZIP** and extract it. Then skip the `git clone` line, and `cd` into the extracted folder. GitHub adds the branch to its name, as in `SEBASTES-main`.
3. **Create the environment.** Open **PowerShell** in the folder where you want SEBASTES and run:

   ```powershell
   git clone <repository URL>
   cd SEBASTES
   py -3.12 -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

If PowerShell says that running scripts is disabled on this system, use one of these:
- Allow scripts for your user once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Then run `.venv\Scripts\Activate.ps1` again.
- Use **Command Prompt** (`cmd.exe`) instead of PowerShell, and activate with `.venv\Scripts\activate.bat`.

## Running

Activate the environment in every new terminal, then start `application/MainWindow.py`.

Linux:

```bash
cd SEBASTES
source .venv/bin/activate
python application/MainWindow.py
```

Windows (PowerShell):

```powershell
cd SEBASTES
.venv\Scripts\Activate.ps1
python application\MainWindow.py
```

`MainWindow.py` finds its own files, so it also works from another folder if you give its full path.

On Windows, after completing installation, double-click `Launch_SEBASTES.bat` in the repository folder. It uses `.venv\Scripts\pythonw.exe` to open the application without keeping a terminal window open. The batch file works even when launched from another folder; a console may appear briefly while it starts.

On Windows there are two other ways to start it:
- **With an error log.** From inside `application\`, run `python SEBASTES.py`. It starts SEBASTES and writes its console output to `logs\`.
- **From a desktop shortcut, without a terminal.** Create a shortcut whose target is the environment's `pythonw.exe` followed by `MainWindow.py`, for example:

  ```
  C:\Users\you\SEBASTES\.venv\Scripts\pythonw.exe C:\Users\you\SEBASTES\application\MainWindow.py
  ```

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

Open **Settings > Profiles...** and go to the **Species Collections** tab.

1. Click **Create new Species Collection** and type a name and a description.
2. Click **Insert** once per species. Give each one a name, a description, a button color and an optional order.

A species collection holds up to 30 species. Each one becomes a button that you use while annotating: only the buttons that have a species are shown, and the second tab of the species panel (species 16 to 30) appears only when there are more than 15. The collection is saved when you insert its first species.

SEBASTES remembers the size and position of its window and of its panels (Species, Measurements) from one session to the next.

### 2. Profile

A profile tells SEBASTES how a deployment folder is organized. In the same dialog, go to the **Profiles** tab.

When opening a deployment, you can also click **Create Profile** in the **Select Profile** dialog. It opens the same profile form. After **Save changes**, the new profile is selected in the list; click **Select** to continue loading the deployment. **Cancel** discards the unsaved profile.

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

Open **Settings > Create New Project...**, or click **Create Project** in the project list that appears when you load a deployment. Give the project a name and pick its species collection and metadata group.

In the **Create a new project** dialog, click **Create Species Collection** to create a collection without leaving project setup. Enter a collection name and description, use **Insert**, **Edit** and **Delete** to set up its species (up to 30), then click **Save changes**. Each species has a name, description, button color and optional sort order, using the same species editor as **Settings > Profiles...**. The saved collection is selected automatically in the project. **Cancel** discards the unsaved collection and its species.

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

SEBASTES divides 3D coordinates, ranges and lengths by 10 after triangulation. With a calibration in millimetres (the usual case, with `T` in mm), results are therefore in **centimetres**.

If `CalibrationFileName` is empty, SEBASTES works without 3D measurements: you can still mark and count fish, but not measure them.

## Annotating

1. **File > Open Deployment...** (Ctrl+O, or **Open** in the toolbar, or the button on the welcome page) and select the deployment folder. Until a deployment is open, the window shows a welcome page with a photo, the first steps and the last 8 deployments you opened: double-click one, or select it and press Enter, to open it again without choosing its folder.
2. Select the project.
3. The first time you open a deployment, select its profile. SEBASTES remembers the profile for that deployment.
4. Move through the frames with the bar under the images. The timeline is its top row: the ticks on it mark the frames that have a measurement (tall ticks) and the frames that have targets only (short ticks). The second row has the buttons, which do the same as the keys, the frame number (with the time in the video, `hours:minutes:seconds.hundredths`, for videos) and the sample interval and speed (**Every ... frames, offset ...**, **Speed**). In a narrow window the bar gives up the speed slider (the speed stays in its box), the time, the offset and then the sample interval; while recording, when there is no room for both, the speed goes before the sample interval:
   - **Right / Left arrow**, or the `<<` and `>>` buttons: go to the next or the previous frame of the sample, the frames that are a multiple of **Every ... frames** plus the offset. From a frame that is not in the sample, Right goes to the first sample frame after it and Left to the last one before it.
   - **Ctrl + Right / Left**, or the `|<` and `>|` buttons next to Play: move one frame.
   - The buttons at the ends of the row go to the first frame (frame 0 of a video, the first image of a folder) and to the last frame; the last button goes to the last frame that has data (Record only). The arrow keys stop at the same first and last frames.
   - You can also use the slider, or type a frame number in the frame box.
   - **Play** runs through the frames and turns into a **Pause** button; **Space** plays and pauses too. The speed is set in frames per second with the **Speed** slider, or by typing a value in the fps box next to it. For videos it starts at the video's own frame rate. When the computer can't draw every frame at the chosen speed, frames are skipped so the video still plays at that speed. Playback stops at the last frame, and Play is disabled while recording.
5. Press **Record** (toolbar, **Annotate > Record**, or the **R** key) and enter your initials. The button turns red while recording, and the status bar shows the annotator. The species buttons and the measuring tools are enabled while recording; **Measure Target** is shown only while recording in stereo mode, and **Link Target**, **Edit Species** and **Delete Link** only while recording. A selected species button is filled with its color.
6. **File > Copy Images To...** saves the current pair. Image files are copied; in video mode the two frames are saved as PNG, for example `GX010123_frame000250.png`.

### Marking and measuring fish

While recording in stereo mode with a calibration, SEBASTES guides the clicks: the image that is not waiting for a click is dimmed and clicks in it are ignored, the one that is waiting gets a border in the accent color, and the status bar says what to click next. Click a species button, then:

1. **Shift + click** the head in the left image (or tick **Stereo Targets Only** and click). The left image dims.
2. Click the same point of the head in the right image. This creates a **stereo target**: SEBASTES computes its 3D position and range (`r`, cm) and the reprojection error (`e`, px, should be a few pixels at most).
3. Click the tail in the left image, then the same point of the tail in the right image.

When the first point of a pair is clicked, SEBASTES draws a dashed line in the other image, the epipolar curve: the same point of the fish must lie on it, so click where the line crosses the fish. It is drawn for the head, for the tail, and for the two ends of a line drawn in one image with **Measure Target**. It goes when the pair is complete, with **Esc**, and when you change frame. **View > Epipolar Hints** turns it off; the choice is remembered.

SEBASTES then saves the length as the target's line (the measurement chosen in the list next to **Measure Target**, `length` by default), asks a name for it and is ready for the next fish. The name offered is the species followed by the next free number (`Sargus 1`, `Sargus 2`, ...), or the name the fish already has when it is measured again or for another measurement; **Enter** accepts it and **Cancel** keeps it. Shift is needed only for the first click. With **Auto Match** ticked, the right-image points are found for you: one click on the head and one on the tail. **Esc** cancels the fish being marked; after the head, it keeps the target without a length.

After each measurement the status bar shows a short chip with how good it is, for example `Fish A · 31.2 cm · e 0.4 px`: the name and length and the reprojection error `e`. A point target shows its range and `e`. When `epi`, how far the clicks are from the epipolar line of their match (the worse end of a line), is 2 px or more, it is added to the chip; the tooltip always gives the range from the left camera (for a fish, of the middle of its line) and `epi`. The chip is green when `e` is below 2 px, amber below 5 px and red above that. A large `e` on every fish means the calibration does not match the videos (see Stereo calibration); a large `epi` on one fish means its two clicks are not the same point. Hover over the chip for this explanation. It appears with the first measurement of a deployment.

**Help > Keyboard Shortcuts** (**F1**) lists all the keys and mouse gestures. While recording, the keys **1** to **9** select the species buttons of the tab on screen (the tooltip of a button says its key), **R** starts and stops recording, **M** starts Measure Target and **L** shows and hides the labels.

While recording, **Ctrl+Z** undoes the last marking click in the current frame, for both plain clicks and Shift+clicks. In guided stereo marking it goes back one head or tail click, so you can correct that point and continue. With Auto Match, the automatically matched point is undone together with the click. Up to 100 marking clicks can be undone; changing frames or leaving Record clears this history. Text fields retain their normal text undo. **Z** also undoes the last marking click when Auto Match is enabled.

The target label is drawn beyond the head and the length label beyond the tail (or above/below them when there is no room), so they don't overlap. They appear when **Show Labels** is ticked. Lengths and names are saved in the `lines` table (`NAME` column, also in `*_lines.csv`); for the units, see Stereo calibration.

The species buttons are next to the left image. The **Measurements** panel, next to the right image, lists every measurement of the deployment: name, species, length (cm), frame, target, measurement, distance from the left camera (cm) and error. The first five columns fit the panel at its default width; scroll to see the others. Drag its edge to resize it. Double-click a name to change it; click a row to go to that frame and select the fish; click a column header to sort.

Outside Record the marks and measurements of each frame are still shown, read only, with the measurement names in the length labels. Clicking a row of the Measurements panel shows that fish as usual and fades the other fish of the same frame, until you move to another frame.

- **Plain click** in the left image: marks the fish in that image only. Use it to count fish. These marks cannot be measured.
- **Right-click** a mark to select its target. **Delete** removes the selected target.
- To measure an existing stereo target again, or another measurement such as `width`, select it, choose the measurement and press **Measure Target**, then drag the line in the left image and in the right image. With **Auto Match** ticked, SEBASTES draws the second line for you. The old line is replaced only when the new one is saved: **Esc** keeps it. The frame can't be changed (arrow keys, buttons, the frame box or the Measurements panel) while a line is being drawn.

In mono mode clicks are not guided. Without a calibration they are not guided either, and only plain clicks can be used.

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

- **The window does not open on Linux** (`Could not load the Qt platform plugin "xcb"`). Check that `opencv-python` is not installed (see Installation on Linux) and install `libxcb-cursor0` (`sudo apt install libxcb-cursor0`).
- **Windows: `python` or `py` is not recognized, or `python` opens the Microsoft Store.** Python is not installed or not on the PATH. Run the Python installer again, choose **Modify**, and enable **Add Python to environment variables**. Then open a new terminal.
- **Windows: `DLL load failed while importing ...`.** Install the latest Microsoft Visual C++ Redistributable (x64) from Microsoft's website, then try again.
- **SEBASTES closes after an error while loading a deployment.** This is how SEBASTES handles every loading error. Read the message: usually a camera subfolder is missing, or it holds no video or more than one.
- **"Timestamp could not be extracted from file name"**. Image profiles without a timestamp type show this warning on every load. You can ignore it.

## Building the Windows executable

On Windows, `application/build_exe.bat` builds the executable with PyInstaller using `SEBASTES.spec`. Edit the `pathex` in the spec file first: it points to the original developer's WinPython install.
