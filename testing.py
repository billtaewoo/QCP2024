from simulator import *

#testing
a = np.array([[3, 2, 1], 
      [0, 0, 0], 
      [0, 3, 4]])
b = np.array([[5, 1, 2], 
      [7, 4, 7],
      [1, 2, 3]])
a = Matrix(a)
b = Matrix(b)
#print(a+b)

"""
We can use something similar to this code, to test the performance of the sparse matrix class against the dense matrix class. 
Could be useful to include in the report and something to talk about during the presentation. For 16x16 matrices, the performance of the sparse matrix class is around 26x faster than the dense matrix class. We would have to test this on different size matrices and see how much the performance difference is. Also have to test the kronecker product.

c = scipy.sparse.random(16,16,density=0.1).toarray()
d = scipy.sparse.random(16,16,density=0.1).toarray()
csparse = Sparse(c)
dsparse = Sparse(d)
t1 = time.time()
test = csparse*dsparse
t2 = time.time()
t3 = t2-t1
print("sparse", t3)

cdense = Matrix(c)
ddense = Matrix(d)
t4 = time.time()
test = cdense*ddense
t5 = time.time()
t6 = t5-t4
print("dense", t6)

print("Sparse is", t6/t3, "times faster")

"""