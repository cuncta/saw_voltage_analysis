# all angles here are in degrees!

import math
# change to numpy!

pi=2*math.acos(0)


V3_x=(1,0,0)
V3_y=(0,1,0)
V3_z=(0,0,1)

# vector is a touple of 3 values...

def V3_length(a):
    return math.sqrt(a[0]*a[0]+a[1]*a[1]+a[2]*a[2])

def V3_norm(a):
    return (a[0]/V3_length(a),a[1]/V3_length(a),a[2]/V3_length(a))
    
def V3_invert(a):
    return (-1*a[0],-1*a[1],-1*a[2])

def V3_angle(a,b):
    return math.acos((a[0]*b[0]+a[1]*b[1]+a[2]*b[2])/(V3_length(a)*V3_length(b)))*180/pi

def V3_distance(a,b):
    return V3_length((a[0]-b[0],a[1]-b[1],a[2]-b[2]))

def V3_xprod(a,b):
    return (a[1]*b[2]+a[2]*b[1],a[2]*b[0]+a[0]*b[2],a[0]*b[1]+a[2]*b[0])

# calculates the projection of the vector b on the plane
# normal to vector a
def V3_add(a,b):
    return ((a[0]+b[0],a[1]+b[1],a[2]+b[2]))

def V3_substract(a,b):
    return ((a[0]-b[0],a[1]-b[1],a[2]-b[2]))
    
def V3_projekt(a,b):
    n = V3_norm(a)
    c = V3_xprod(n,b)
    return(V3_xprod(V3_invert(n),c))
    
# Quaternions:
def Q3_from_V3(A):
    return (A[0],A[1],A[2],0)

def V3_from_Q3(Q):
    return (Q[0],Q[1],Q[2])

# this returns a rotation quaternion around A, angle in degrees
def Q3_make_rot(alpha,A):
    di=V3_norm(A)
    a=alpha*pi/180
    q0=di[0]*math.sin(a/2)
    q1=di[1]*math.sin(a/2)
    q2=di[2]*math.sin(a/2)
    q3=math.cos(a/2)
    return (q0,q1,q2,q3)

def Q3_invert(q):
    return (-1*q[0],-1*q[1],-1*q[2],q[3])

def Q3_mult(rot, q):
    t3 = rot[3]*q[3] - rot[0]*q[0] - rot[1]*q[1] - rot[2]*q[2]
    t0 = rot[3]*q[0] + rot[0]*q[3] + rot[1]*q[2] - rot[2]*q[1]
    t1 = rot[3]*q[1] + rot[1]*q[3] + rot[2]*q[0] - rot[0]*q[2]
    t2 = rot[3]*q[2] + rot[2]*q[3] + rot[0]*q[1] - rot[1]*q[0]

    return (t0,t1,t2,t3)


# rotate takes a quaternion and vector!
def V3_rotate(Q, A):
    Qi=Q3_invert(Q)
    QA=Q3_from_V3(A)
    # b = Q a Q^
    V=Q3_mult(Q3_mult(Q,QA),Qi)
    return (V[0], V[1], V[2])
    
# rotations:
def V3_rot_x(alpha, A):
    Q=Q3_make_rot(alpha,V3_x)
    res=V3_rotate(Q,A)
    return res

def V3_rot_y(alpha, A):
    Q=Q3_make_rot(alpha,V3_y)
    res=V3_rotate(Q,A)
    return res

def V3_rot_z(alpha, A):
    Q=Q3_make_rot(alpha,V3_z)
    res=V3_rotate(Q,A)
    return res


def Q3_test():
    print "distance between (0,0,0) and (1,1,1)"
    print V3_distance((0,0,0),(1,1,1))
    print "divided by sqrt(3)"
    print V3_distance((0,0,0),(1,1,1))/math.sqrt(3)
    print "distance between (0,0,0) and (2,2,0)"
    print V3_distance((0,0,0),(2,2,0))
    print "divided by sqrt(2)"
    print V3_distance((0,0,0),(2,2,0))/math.sqrt(2)
    print " "
    print "cross product (1,0,0) x (0,2,0)"
    print V3_xprod((1,0,0),(0,2,0))
    print " "
    print "rotation tests"
    print "z = ", V3_z
    print "x = ", V3_x
    print "rotating x around z 45 deg"
    print " c = ", V3_rot_z(45,V3_x)
    print "rotating x around z 45 deg and back"
    print " c = ", V3_rot_z(-45,V3_rot_z(45,V3_x))

