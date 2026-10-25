'''
videoSource reads frames from a video file with OpenCV so SEBASTES can use one
video per camera in place of a folder of still images. Frames are numbered from 0.
'''

import os
import struct
from datetime import datetime, timedelta
import cv2

#  ImageFileType values that put SEBASTES in video mode
VIDEO_TYPES = ['mp4', 'mov', 'm4v', 'avi', 'mkv', 'mts']

#  forward jumps up to this many frames are decoded in sequence instead of seeking
MAX_GRAB = 60


class videoSource(object):

    def __init__(self, filename):
        self.filename = filename
        self.cap = cv2.VideoCapture(filename)
        if not self.cap.isOpened():
            raise IOError('Unable to open video file: ' + filename)
        self.frameCount = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.startTime = getCreationTime(filename)
        #  index of the frame the next read() will return
        self.nextFrame = 0

    def getFrame(self, frame):
        '''
        getFrame returns the requested frame as a BGR numpy array, or None if it
        can't be read.
        '''
        if self.nextFrame >= 0 and 0 < frame - self.nextFrame <= MAX_GRAB:
            #  short jump forward (playback, stepping by the sample rate)
            while self.nextFrame < frame and self.cap.grab():
                self.nextFrame += 1
        elif frame != self.nextFrame:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        ok, image = self.cap.read()
        if not ok:
            #  position unknown - seek on the next request
            self.nextFrame = -1
            return None
        self.nextFrame = frame + 1
        return image

    def frameTime(self, frame):
        '''
        frameTime returns the datetime of the given frame, or None if the video
        has no start time.
        '''
        if self.startTime is None or not self.fps:
            return None
        return self.startTime + timedelta(seconds=frame / self.fps)

    def release(self):
        self.cap.release()


def getCreationTime(filename):
    '''
    getCreationTime returns the start time stored in the "mvhd" box of an MP4/MOV
    file, or None if there is none. The time is returned as stored: most cameras
    write their own clock time there, not UTC.
    '''
    try:
        with open(filename, 'rb') as f:
            moov = findBox(f, b'moov', 0, os.path.getsize(filename))
            if moov is None:
                return None
            mvhd = findBox(f, b'mvhd', moov[0], moov[1])
            if mvhd is None:
                return None
            f.seek(mvhd[0])
            #  full box: 1 byte version and 3 bytes flags, then creation_time
            version = f.read(4)[0]
            if version == 1:
                seconds = struct.unpack('>Q', f.read(8))[0]
            else:
                seconds = struct.unpack('>I', f.read(4))[0]
    except (OSError, struct.error, IndexError):
        return None
    if seconds == 0:
        return None
    return datetime(1904, 1, 1) + timedelta(seconds=seconds)


def findBox(f, boxType, start, end):
    '''
    findBox returns the (data start, box end) offsets of the first MP4 box of the
    given type between the start and end offsets, or None.
    '''
    pos = start
    while pos + 8 <= end:
        f.seek(pos)
        size, kind = struct.unpack('>I4s', f.read(8))
        header = 8
        if size == 1:
            size = struct.unpack('>Q', f.read(8))[0]
            header = 16
        elif size == 0:
            size = end - pos
        if size < header:
            return None
        if kind == boxType:
            return pos + header, pos + size
        pos += size
    return None
