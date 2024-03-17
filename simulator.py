#use simulator to implement classes of matrices etc. -> simulator interface should be completely separate

# MATRIX abstract base class with DENSE and SPARSE child classes, SPARSEREP is a helper class 

from abc import ABC, abstractmethod
import numpy as np
import math
import time # to check performance, no point using sparse if its slower than normal matrix
import scipy # for generating random sparse matrices, testing purposes

class Matrix(ABC):
    @abstractmethod
    def __add__(self, other):
        pass
    
    @abstractmethod
    def __sub__(self, other):
        pass
    
    @abstractmethod
    def __mul__(self, other):
        pass
    
    @abstractmethod
    def __mod__(self, other):
        pass
    
    @abstractmethod
    def __str__(self):
        pass
    
    @abstractmethod
    def transpose(self):
        pass
    
    @abstractmethod
    def scalar(self, scale):
        pass

    @abstractmethod
    def adjoint(self, other):
        pass

class Dense(Matrix):
    """
    Class for initial testing of the quantum computer simulator. 
    Also used for testing the performance of the sparse matrix class
    """

    def __init__(self, array, id = ""):
        """
        Converts a 2D np.ndarray into a matrix object.
        """
        self.matrix = array
        self.rows, self.cols = array.shape
        self.id = id

    def __mul__(self, other, id = ""):
        """
        Matrix multiplication of 2 matrices.
        """
        assert (self.cols == other.rows), "Can only multiply 2 matrices of dimensions (m,n) and (n,p)"
        multiply = np.zeros((self.rows, other.cols), dtype=complex)
        for i in range(self.rows):
            for j in range(other.cols):
                for k in range(other.rows):
                    multiply[i, j] += self.matrix[i, k] * other.matrix[k, j]

        return Dense(multiply)

    def __mod__(self, other):
        """
        Kronecker product of two matrices.
        """
        tensor = np.zeros((self.rows * other.rows, self.cols * other.cols),
                          dtype=complex)

        for i in range(self.rows):
            for j in range(self.cols):
                for k in range(other.rows):
                    for l in range(other.cols):
                        tensor[i * other.rows + k, j * other.cols +
                               l] = self.matrix[i, j] * other.matrix[k, l]

        return Dense(tensor)

    def __add__(self, other):
        """
        Add two matrices. This is needed to ensure that matrices added together are of the same dimension.
        """
        assert (self.rows == other.rows
                and self.cols == other.cols), "Matrix dimensions do not match"
        return Dense(self.matrix + other.matrix)

    def __sub__(self, other):
        """
        Subtract two matrices. This is needed to ensure that matrices added together are of the same dimension.
        """
        assert (self.rows == other.rows
                and self.cols == other.cols), "Matrix dimensions do not match"
        return Dense(self.matrix - other.matrix)

    def transpose(self):
        """
        Transpose a matrix.
        """
        zero = np.zeros((self.cols, self.rows), dtype=complex)
        for i in range(self.cols):
            for j in range(self.rows):
                zero[i, j] = self.matrix[j, i]
        id = "" if self.id == "" else self.id + "\u1D40"
        return Dense(zero, id)

    def adjoint(self):
        """
        Returns adjoint of the matrix
        """
        zero = np.zeros((self.cols, self.rows), dtype=complex)
        for i in range(self.cols):
            for j in range(self.rows):
                zero[i, j] = self.matrix[j, i].conjugate()
        id = "" if self.id == "" else self.id + "\u2020"
        return Dense(zero, id)
        
    def scalar(self, scale):
        """
        Multiply a matrix by a scalar
        """
        return Dense(self.matrix * scale)

    def __str__(self):
        return str(self.matrix)


class SparseRep(object):
    """
    This class exists to distinguish between an array or a sparse matrix when running the constructor for the Sparse matrix class. Also used to return a sparse matrix when multiplying or using the kronecker product for 2 sparse matrices.
    """

    def __init__(self, elements, indices, rows, cols):

        self.elements = elements
        self.indices = indices
        self.rows = rows
        self.cols = cols


class Sparse(Matrix):
    """
    2D sparse matrix class with entries of type complex
    """

    def __init__(self, array, id=""):
        """
        Sparse(np.ndarray) -> Converts the array into a sparse matrix. 
        Elements of the matrix are stored in an array whose elements are in the following format [Matrix element] [row, column]. 
        Row and column are zero indexed.

        Sparse(SparseRep) -> Converts the sparse representation into a sparse matrix. 
        This is used to distinguish between converting an array containing a matrix and an array containing a sparse representation of a matrix [Matrix element, row, column).

        Sparse(Matrix) -> Converts a dense matrix into a sparse matrix.
        The rows and columns attributes refer to the maximum rows and columns of the matrix. 

        "id" argument is the string identifier of the matrix. Can be of any length
        """
        assert isinstance(array, (np.ndarray, SparseRep, Dense)), "Can only convert an array, SparseRep or Matrix classes"

        # converts array to sparse matrix
        if isinstance(array, np.ndarray):
            self.rows, self.cols = array.shape
            elements = []
            indices = []
            for i in range(self.rows):
                for j in range(self.cols):
                    if array[i, j] != 0:
                        elements.append(array[i, j])
                        indices.append([i, j])
            self.elements = np.array(elements, dtype = complex)
            self.indices = np.array(indices, dtype = int)

        # converts Dense to sparse matrix
        elif isinstance(array, Dense):
            self.rows, self.cols = array.rows, array.cols
            elements = []
            indices = []
            for i in range(self.rows):
                for j in range(self.cols):
                    if array.matrix[i, j] != 0:
                        elements.append(array.matrix[i, j])
                        indices.append([i, j])
            self.elements = np.array(elements, dtype = complex)
            self.indices = np.array(indices, dtype = int)

        # stores sparse representation as sparse matrix
        else:
            self.elements = array.elements
            self.indices = array.indices
            self.rows = array.rows
            self.cols = array.cols
        self.shape = np.array((self.rows, self.cols))
        self.id = id
    def scalar(self, scale):
        """
        Multiplies the matrix by a scalar
        """
        elements = self.elements * scale
        return Sparse(SparseRep(elements, self.indices, self.rows, self.cols))

    def __mul__(self, other):
        # add multiplication with scalar
        """
        Matrix multiplication of two sparse matrices
        """

        assert (self.cols == other.rows), "Can only multiply 2 matrices of dimensions (m,n) and (n,p)"
        multiply = []
        m_indices = []
        # loop through all the elements and mutiply the ones that are in the same row and column
        for i in range(len(self.elements)):
            for j in range(len(other.elements)):
                if self.indices[i,1] == other.indices[j,0]:
                    multiply.append(self.elements[i] * other.elements[j])
                    m_indices.append([self.indices[i,0],other.indices[j,1]])
        # this will give an array that has repeated entries of the same row and column
        # so we need to remove the duplicates and sum the elements
        # lists to store unique sets of indices
        elements = []
        unique = []
        for k in range(len(multiply)):

            if m_indices[k] not in unique:
                unique.append(m_indices[k])
                elements.append(multiply[k])
            else:
                ind = unique.index(m_indices[k])
                elements[ind] += multiply[k]
        elements = np.array(elements)
        unique = np.array(unique)
        return Sparse(SparseRep(elements, unique, self.rows, other.cols))

    def __add__(self, other):
        """
        Add two sparse matrices
        """
        assert (self.rows == other.rows and self.cols == other.cols), "Matrix dimensions do not match"
        add = []
        add.extend(self.elements.tolist())
        add.extend(other.elements.tolist())
        a_indices = []
        a_indices.extend(self.indices.tolist())
        a_indices.extend(other.indices.tolist())
        elements = []
        unique = []
        for k in range(len(add)):
            if a_indices[k] not in unique:
                unique.append(a_indices[k])
                elements.append(add[k])
            else:
                ind = unique.index(a_indices[k])
                elements[ind] += add[k]
        elements = np.array(elements)
        unique = np.array(unique)
        return Sparse(SparseRep(elements, unique, self.rows, self.cols))

    def __sub__(self, other):
        """
        Subtract two sparse matrices
        """
        assert (self.rows == other.rows and self.cols == other.cols), "Matrix dimensions do not match"
        elements = self.elements.tolist()
        unique = self.indices.tolist()
        other_indices = other.indices.tolist()
        
        for i in range(len(other.elements)):
            if other_indices[i] in unique:
                ind = unique.index(other_indices[i])
                elements[ind] -= other.elements[i]
            else:
                elements.append(-other.elements[i])
                unique.append(other_indices[i])
        elements = np.array(elements)
        unique = np.array(unique)
        return Sparse(SparseRep(elements, unique, self.rows, self.cols))

    def __mod__(self, other):
        """
        Kronecker product of two sparse matrices
        """
        kronecker = []
        indices = []

        for i in range(len(self.elements)):
            for j in range(len(other.elements)):
                kronecker.append(self.elements[i]*other.elements[j])
                indices.append([self.indices[i,0]*other.rows+other.indices[j,0],
                                self.indices[i,1]*other.cols+other.indices[j,1]])
                
        kronecker = np.array(kronecker)
        indices = np.array(indices)
        return Sparse(SparseRep(kronecker, indices, self.rows * other.rows, self.cols * other.cols))

    def transpose(self):
        """
        Transpose of a sparse matrix
        """
        indices = []
        
        for i in self.indices:
            indices.append([i[1],i[0]])
        indices = np.array(indices)
        id = "" if self.id == "" else self.id + "\u1D40"
        return Sparse(SparseRep(self.elements, indices, self.cols, self.rows), id)

    def adjoint(self):
        """
        Transpose of a sparse matrix
        """
        indices = []

        for i in self.indices:
            indices.append([i[1],i[0]])
        indices = np.array(indices)
        for ele in self.elements:
            ele = ele.conjugate()
        id = "" if self.id == "" else self.id + "\u2020"
        return Sparse(SparseRep(self.elements, indices, self.cols, self.rows),id)
            
    def __str__(self):
        matrix = np.zeros((self.rows, self.cols), dtype = complex)
        for i in range(len(self.elements)):
            matrix[self.indices[i,0],self.indices[i,1]] = self.elements[i]
        return str(matrix)


def state(n, m):
    # fixed so it properly initializes the register and uses Sparse
    """
        Nx1 Matrix state of the quantum register initialised to state corresponding to qubit m
    """
    assert isinstance(m,int), "The number of qubits n inputted must be an integer"
    assert isinstance(n,int), "The qubit to which quantum register is intialised m must be an integer"
    assert (m >= 0 and m < 2**n), "m must be between 0 and 2^n"

    # initialise register to all zeros
    state = np.zeros((2**n, 1), dtype=complex)

    # initialize to state |m>
    state[m] = 1

    return Sparse(state)

# global gates
I = Sparse(np.array([[1, 0], [0, 1]]),id = "I")  #Identity
H = Sparse((1/np.sqrt(2)) * np.array([[1, 1], [1, -1]]), id = "H")  #Hadamard
X = Sparse(np.array([[0, 1], [1, 0]]), id = "X")  #Pauli X 
Y = Sparse(np.array([[0, -1j], [1j, 0]]), id = "Y") #Pauli Y
Z = Sparse(np.array([[1, 0], [0, -1]]), id = "Z") #Pauli Z 

def phaseshift(theta, id = ""):
    return Sparse(np.array([[1, 0], [0, np.exp(1j*theta)]]))

T = phaseshift(np.pi/4, id = "T")
S = phaseshift(np.pi/2, id = "S")

def CNOT(qubit_count, control_list, target_list, id = ""):
    """
    Returns an appropriate CNOT-Type gate for the given qubit count, control and target qubits as a Sparse matrix.
    This gate flips all the target qubits, if all the control qubits are |1>
    Control and Target qubits are zero-indexed and are to be inputted as lists of integers.
    Can also include the "id" argument to give the gate a name.
    
    Example:
    To construct a Toffoli gate for a 3 qubit register, we require 2 control qubits and 1 target qubit.
    Toffoli = CNOT(3, [0,1], [2], id = "Toffoli")
    """
    assert qubit_count >= (len(control_list) + len(target_list)), "Number of qubits must be greater than or equal to the number of control and target qubits"
    assert isinstance(qubit_count, int), "Qubit count must be an integer"
    assert isinstance(control_list, list), "Control qubits must be provided as a list"
    assert isinstance(target_list, list), "Target qubits must be provided as a list"
    for control in control_list:
        assert isinstance(control, int), "One or more control qubits is not an integer"
    for target in target_list:
        assert isinstance(target, int), "One or more target qubits is not an integer"
    assert len(control_list) == len(set(control_list)), "Control qubits must be unique"
    assert len(target_list) == len(set(target_list)), "Target qubits must be unique"

    # initializes a zero array
    gate = np.zeros((2**qubit_count, 2**qubit_count), dtype=complex)

    # initializes a list to store the indices of the rows
    rows = np.arange(0,2**qubit_count,1)
    
    # converts the indices to binary
    bin_rows = []
    for row in rows:
        bin_rows.append(bin(row)[2:].zfill(qubit_count))

    # initializes a list to store the swapped binary indices
    bin_swapped_rows = []

    # flips bits in the binary representation of the row indices according to the required CNOT-Type Gate
    for binary in bin_rows:
        counter = 0
        for i in range(len(control_list)):
            if binary[qubit_count - control_list[i] - 1] == "1":
                counter += 1
        if counter == len(control_list):
            for j in range(len(target_list)):
                if binary[qubit_count - target_list[j] - 1] == "1":    
                    buffer = list(binary)
                    buffer[qubit_count - target_list[j] - 1] = "0"
                    binary = "".join(buffer)
                else:
                    buffer = list(binary)
                    buffer[qubit_count - target_list[j] - 1] = "1"
                    binary = "".join(buffer)  
        bin_swapped_rows.append(binary)

    # initializes a list to store the swapped integer indices
    swapped_rows = []
    
    # converts the binary representation of the row indices back to decima
    for binary in bin_swapped_rows:
        swapped_rows.append(int(binary,2))

    # sets the appropriate ones in the gate
    for i in range(len(swapped_rows)):
        gate[rows[i], swapped_rows[i]] = 1
        
    return Sparse(gate,id)


class programmer(object):
    """
    Class used to program a quantum circuit. Quantum circut can also be named using the optional argument "name" when initializing the programmer.
    Can visualize the circuit by running print() on the object. Supports visualization of 1 qubit gates only. n-qubit gates can only be visualized by the user assigned id given to the gate.
    It is up to the user to appropriate name their gates.
    To run a circuit, it must be first compiled and then run.
    """
    def __init__(self, register, name = ""):
        """
        The first argument gives the register of the state the circuit is to be applied to. 
        
        The second argument is optional and can be used to name the circuit.
        """
        self.register = register
        # finds number of qubits based on rows of the register
        rows = register.rows
        self.qubit_count = 0
        while True:
            rows = rows/2
            self.qubit_count += 1
            # stops if it reaches 1
            if rows == 1:
                break
            # raises exception to invalid register
            if rows < 1:
                raise Exception("Invalid register size, must have 2^n rows")
        self.steps = []
        self.name = name

        # stores if circuit is compiled or run
        self.compiled = False
        
    def add_step(self, gates, step_number = -1):
        """
        Adds a step to the quantum circuit. If no step_number is provided, the step is added to the end of the circuit. 
        Otherwise, it is added to the circuit at the given step_number index.
        step_number is zero indexed.
        """
        if step_number == -1:
            step_number = len(self.steps)
        assert step_number >= 0 and step_number <= len(self.steps), "Step number must be within the already defined steps"
        assert isinstance(step_number, int), "Step number must be an integer"
        assert isinstance(gates, list), "Gates must be provided as a list of single qubits or a list with a single n-qubit gate"
        assert len(gates) == 1 or len(gates) == self.qubit_count, "Number of gates must be equal to the number of qubits in the register, unless it is an n-qubit gate"
        # insert gates into the list at the right index
        self.steps.insert(step_number, gates)
        # if new step is added, circuit needs to be compiled again
        self.compiled = False
    
    def remove_step(self, step_number):
        """
        Removes a step from the quantum circuit.
        """
        assert step_number >= 0 and step_number < len(self.steps), "Step number must be within the already defined steps"
        assert isinstance(step_number, int), "Step number must be an integer"
        del self.steps[step_number]

        # if new step is removed, circuit needs to be compiled again
        self.compiled = False

    def compile(self):
        """
        Compiles the circuit into a single matrix. Circuit has to be compiled before it can be run.
        Can be used to create custom matrices.
        """

        # first does the appropriate tensor products
        compiled_steps = []
        for step in self.steps:
            if len(step) == 1:
                compiled_steps.append(step[0])
            else:
                gate = step[0]
                for i in range(len(step) - 1):
                    gate = gate % step[i + 1]
                compiled_steps.append(gate)

        # then combines each step into a single matrix 
        circuit = compiled_steps[-1]
        for i in range(len(compiled_steps) - 1):
            circuit = circuit * compiled_steps[len(compiled_steps) - i - 2]
        self.circuit = circuit
        self.compiled = True

    def run(self):
        """
        Runs the circuit on the provided input register. Can only be run after the circuit has been compiled.
        """
        if self.compiled:
            self.output = self.circuit * self.register
            return self.output
        else:
            raise Exception("Circuit has not been compiled. Please compile the circuit before running it. \n If you are trying to run after modifying the circuit, you must compile the circuit again")
    
    def get_matrix(self):
        """
        Returns matrix representation of the circuit. Can only be used after the circuit has been compiled.
        """
        if self.compiled:
            return self.circuit
        else:
            raise Exception("Circuit has not been compiled. Please compile the circuit before getting the matrix representation.")

        
    def __str__(self):
        """
        Prints a representation of the circuit. Utilizes the id attributes of the gates to print a representation of the circuit.
        """
        # calculates appropriate width each step needs to be
        rows = []
        for i in range(len(self.steps)):
            ids = []
            for j in range(len(self.steps[i])):
                if len(self.steps[i]) == 1:
                    for _ in range(self.qubit_count-1):
                        ids.append(self.steps[i][j].id)
                ids.append(self.steps[i][j].id)
            rows.append(ids)
        widths = [max(len(gate) for gate in row) for row in rows]

        # Prepares the string to be printed
        buffer = "Quantum Circuit " + self.name + ":\n"
        for i in range(self.qubit_count):
            buffer += "q" + str(i) + " -> "
            for j in range(len(self.steps)):
                if len(self.steps[j]) == 1:
                    buffer += "[" + self.steps[j][0].id.center(widths[j]) + "]" + "---"
                elif self.steps[j][i].id == "I":
                    for _ in range(widths[j]+5):
                        buffer += "-" 
                else:
                    buffer += "[" + self.steps[j][i].id.center(widths[j]) + "]" + "---"
            buffer += "\n"
                
        return buffer

# SIIICK IT WORKS I THINK
wikipedia_toff = CNOT(4,[0,2],[1], id = "Toffoli")
#print(wikipedia_toff)
q = programmer(state(3,0), name = "Grovers")
q.add_step([H,H,H])
# searching for qubit 2
Oracle = I%I%I - (state(3,2) * (state(3,2).transpose()).scalar(2))
Oracle.id = "Oracle"
q.add_step([Oracle])
print(q)
q.compile()
q.run()
print(q.get_matrix())
print(q.output)