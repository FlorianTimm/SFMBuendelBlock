import numpy as np


def rotationMatrixToEulerAngles(R):
    # source: https://learnopencv.com/rotation-matrix-to-euler-angles/
    # assert (isRotationMatrix(R))

    sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

    singular = sy < 1e-6

    if not singular:
        x = np.arctan2(R[2, 1], R[2, 2])
        y = np.arctan2(-R[2, 0], sy)
        z = np.arctan2(R[1, 0], R[0, 0])
    else:
        x = np.arctan2(-R[1, 2], R[1, 1])
        y = np.arctan2(-R[2, 0], sy)
        z = 0

    return np.array([x, y, z])

# Calculates Rotation Matrix given euler angles.


def eulerAnglesToRotationMatrix(rx, ry, rz):
    # source: https://learnopencv.com/rotation-matrix-to-euler-angles/

    R_x = np.array([[1,         0,                  0],
                    [0,         np.cos(rx), -np.sin(rx)],
                    [0,         np.sin(rx), np.cos(rx)]
                    ])

    R_y = np.array([[np.cos(ry),    0,      np.sin(ry)],
                    [0,                     1,      0],
                    [-np.sin(ry),   0,      np.cos(ry)]
                    ])

    R_z = np.array([[np.cos(rz),    -np.sin(rz),    0],
                    [np.sin(rz),    np.cos(rz),     0],
                    [0,                     0,                      1]
                    ])
    R = np.dot(R_z, np.dot(R_y, R_x))
    return R
