-- Schema of the SEBASTES application database (db/Application.db).
-- SEBASTES runs this script to create an empty Application.db when none exists.
-- Reconstructed from the queries in the SEBASTES code: the original NOAA file may differ.

CREATE TABLE PROJECTS (
    PROJECT TEXT,
    DESCRIPTION TEXT,
    DATABASE_PATH TEXT,
    SPECIES_COLLECTION TEXT,
    METADATA_GROUP TEXT,
    ACTIVE TEXT DEFAULT 'Yes'
);

CREATE TABLE PROFILES (
    PROFILE TEXT,
    ACTIVE TEXT DEFAULT 'Yes',
    DESCRIPTION TEXT
);

CREATE TABLE PROFILE_SETTINGS (
    PROFILE TEXT,
    SETTING TEXT,
    VALUE TEXT
);

CREATE TABLE SETTING_DESCRIPTIONS (
    SETTING TEXT,
    DESCRIPTION TEXT
);

CREATE TABLE SPECIES_COLLECTIONS (
    SPECIES_COLLECTION TEXT,
    ACTIVE TEXT DEFAULT 'Yes',
    DESCRIPTION TEXT
);

CREATE TABLE SPECIES_SETUP (
    SPECIES_COLLECTION TEXT,
    SPECIES_GROUP TEXT,
    DESCRIPTION TEXT,
    BUTTON_COLOR TEXT,
    SORT_ORDER INTEGER
);

CREATE TABLE METADATA_GROUPS (
    METADATA_GROUP TEXT,
    ACTIVE TEXT DEFAULT 'Yes',
    DESCRIPTION TEXT
);

CREATE TABLE FRAME_METADATA_SETUP (
    METADATA_GROUP TEXT,
    METADATA_TAG TEXT,
    METADATA_TYPE TEXT,
    DESCRIPTION TEXT,
    METADATA_GUI_ELEMENT TEXT,
    SORT_ORDER INTEGER
);

-- The profile setup dialog saves exactly the settings listed here and shows the
-- descriptions as tooltips.
INSERT INTO SETTING_DESCRIPTIONS (SETTING, DESCRIPTION) VALUES
    ('LeftCameraImagePath', 'Subfolder of the deployment folder that holds the left camera images, or the left camera video in video mode.'),
    ('RightCameraImagePath', 'Subfolder of the deployment folder that holds the right camera images, or the right camera video in video mode.'),
    ('CalibrationFileName', 'Stereo calibration file in the SEBASTES/calibrations folder (.mat, .npz or .yml). Leave empty to work without 3D measurements.'),
    ('FrameNumberIndices', 'Character positions (1-based, from-to) of the frame number in the image file names. Ignored in video mode.'),
    ('ImageTimestampType', 'Where each image time comes from: in_file_name, EXIF or none. Ignored in video mode, where the time comes from the video start time.'),
    ('ImageTimestampFormat', 'Format of the time in the file name, as a Python strftime format (or DyyyyMMdd-Thhmmss.zzz). Used with in_file_name.'),
    ('ImageTimestampStart', 'Character position (1-based) where the time starts in the file name. Used with in_file_name.'),
    ('ImageFileType', 'Image file extension, such as jpg. A video extension (mp4, mov, m4v, avi, mkv, mts) switches to video mode: one video per camera folder.'),
    ('CollectMetadata', 'Show the frame metadata panel while recording.'),
    ('RotateLeftImage', 'Rotation applied to the left image, in degrees.'),
    ('RotateRightImage', 'Rotation applied to the right image, in degrees.'),
    ('SubsampleMask', 'Optional x,y,width,height rectangle that limits the analysed part of the image. Leave empty to use the whole image.');

-- A project needs a metadata group; this one lets a project start without frame metadata.
INSERT INTO METADATA_GROUPS (METADATA_GROUP, ACTIVE, DESCRIPTION) VALUES
    ('NoMetadata', 'Yes', 'Empty group for projects that do not collect frame metadata.');
