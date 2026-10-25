'''
epipolar draws nothing itself: it computes where the match of a clicked point must lie in the other image.
A point seen by one camera is a ray in space; the ray seen by the other camera is a curve (a straight line
only without lens distortion), the epipolar curve. Display only: the distance calculation is in pyStereoComp.
calData is pyStereoComp.calData: left-camera coordinates XL map to right-camera coordinates XR = R*XL + T.
'''

import numpy as np
import cv2


def calParams(calData):
    #  camera matrices, distortion, R and T as plain float arrays (T may be (3,1), (1,3) or (3,))
    p = {}
    p['KL'] = np.asarray(calData['cameraMatrixL'], dtype=np.float64).reshape(3, 3)
    p['KR'] = np.asarray(calData['cameraMatrixR'], dtype=np.float64).reshape(3, 3)
    p['dL'] = np.asarray(calData['distCoeffsL'], dtype=np.float64).ravel()
    p['dR'] = np.asarray(calData['distCoeffsR'], dtype=np.float64).ravel()
    p['R'] = np.asarray(calData['R'], dtype=np.float64).reshape(3, 3)
    p['T'] = np.asarray(calData['T'], dtype=np.float64).reshape(3)
    return p


def project(points3D, K, dist):
    #  3D points in the camera frame to pixels, with lens distortion
    if len(points3D) == 0:
        return np.zeros((0, 2))
    xp, J = cv2.projectPoints(np.ascontiguousarray(points3D, dtype=np.float64).reshape(-1, 1, 3),
                              np.zeros(3), np.zeros(3), K, dist)
    return xp.reshape(-1, 2)


def epipolarCurve(calData, point, fromCam, imageSize=None, nPoints=200):
    '''
    Pixels of the other camera where the match of point (x, y) of the fromCam image ('L' or 'R') must lie,
    ordered from near to far and ending at the vanishing point when it is in front of the camera.
    imageSize = (width, height) drops the points outside the image (plus 10 %) and the ones where the
    lens distortion model folds the curve back. Returns an array (N, 2), empty when nothing is visible.
    '''
    if fromCam not in ('L', 'R'):
        raise ValueError("fromCam must be 'L' or 'R'")
    p = calParams(calData)
    if fromCam == 'L':
        Ks, ds, Kt, dt = p['KL'], p['dL'], p['KR'], p['dR']
        Rst, Tst = p['R'], p['T']
    else:
        Ks, ds, Kt, dt = p['KR'], p['dR'], p['KL'], p['dL']
        Rst, Tst = p['R'].T, -p['R'].T @ p['T']

    #  the clicked pixel is the ray (x, y, 1) of the source camera
    xy = cv2.undistortPoints(np.array([[[point[0], point[1]]]], dtype=np.float64), Ks, ds).reshape(2)
    if not np.all(np.isfinite(xy)):
        return np.zeros((0, 2))
    ray = np.array([xy[0], xy[1], 1.0])

    #  depths along the ray, log spaced from half to a thousand baselines
    baseline = np.linalg.norm(p['T'])
    depths = np.geomspace(0.5 * baseline, 1000 * baseline, nPoints)
    Xt = depths[:, None] * ray[None, :] @ Rst.T + Tst
    Xt = Xt[Xt[:, 2] > 0]

    #  the far end: the direction of the ray as seen by the other camera
    vanish = Rst @ ray
    if vanish[2] > 0:
        Xt = np.vstack((Xt, vanish[None, :]))
    curve = project(Xt, Kt, dt)
    curve = curve[np.all(np.isfinite(curve), axis=1)]

    if imageSize is not None and len(curve) > 0:
        w, h = float(imageSize[0]), float(imageSize[1])
        inside = ((curve[:, 0] >= -0.1 * w) & (curve[:, 0] <= 1.1 * w) &
                  (curve[:, 1] >= -0.1 * h) & (curve[:, 1] <= 1.1 * h))
        maxJump = 0.5 * max(w, h)
        kept = []
        for c in curve[inside]:
            if len(kept) > 0 and np.hypot(c[0] - kept[-1][0], c[1] - kept[-1][1]) > maxJump:
                continue
            kept.append(c)
        curve = np.array(kept).reshape(-1, 2)
    return curve


def distToPolyline(point, curve):
    #  shortest distance from point to the segments joining the (N, 2) points of curve
    a = curve[:-1]
    ab = curve[1:] - a
    ap = np.asarray(point, dtype=np.float64)[None, :] - a
    len2 = np.sum(ab * ab, axis=1)
    t = np.zeros(len(a))
    ok = len2 > 0
    t[ok] = np.clip(np.sum(ap[ok] * ab[ok], axis=1) / len2[ok], 0.0, 1.0)
    nearest = a + t[:, None] * ab
    return float(np.min(np.hypot(*(np.asarray(point, dtype=np.float64)[None, :] - nearest).T)))


def epipolarDistance(calData, pointL, pointR, imageSize=None):
    '''
    How far, in pixels, the pair pointL, pointR is from being a valid stereo match: the mean of the distance
    of pointR from the curve of pointL and of pointL from the curve of pointR. None when a curve is too short.
    '''
    curveR = epipolarCurve(calData, pointL, 'L', imageSize)
    curveL = epipolarCurve(calData, pointR, 'R', imageSize)
    if len(curveR) < 2 or len(curveL) < 2:
        return None
    return (distToPolyline(pointR, curveR) + distToPolyline(pointL, curveL)) / 2
