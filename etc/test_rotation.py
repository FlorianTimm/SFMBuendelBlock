import numpy as np

from etc import eulerAnglesToRotationMatrix


x1 = np.array([4, 5, 1])
R1 = eulerAnglesToRotationMatrix(0.5*np.pi, 0, 0)
print(R1)

t = np.array([0, 0, 1])
R1z2 = eulerAnglesToRotationMatrix(0, 0.5*np.pi, 0)


x2 = x1 + R1@t
R2 = R1z2@R1

print(x2)

x1n = x2-np.linalg.inv(R1z2)@R2@t
R1n = np.linalg.inv(R1z2)@R2

print(x1n)
print(R1n)
