R = [ 1 0 0
      0 1 0
      0 0 1 ];
t = [0 0 1];
P = [0 0 0];
K= [2000.    0  2000.
       0. 2000. 2000.
       0.    0     1 ];

a = 0.25*pi;
RY = [ cos(a)  0 sin(a)
       0       1     0
       -sin(a) 0 cos(a) ]

pn = K * RY*(P - t)';
pn = round(pn/pn(3))


