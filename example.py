import matplotlib.pyplot as plt
import numpy as np

from scipy.optimize import rosen as banana_f
from scipy.optimize import rosen_der as banana_grad
from scipy.optimize import rosen_hess as banana_hess

import src.cubic_reg

n = 2
a = np.random.uniform(-1,1,size=(n,n))
A = (a + a.T)/2
#A = np.array([[1.,-3.],[-3., 0.]])
c = 10

def n_polynomial(x):
    n = len(x)
    result = 0
    for i in range(1,n):
        result += (x[i]-x[i-1]*x[0])**2
    for i in range(0,n):
        for j in range(0,n):
            result += (A[i,j]*x[i]*x[j]-c)**2
    return result

def Ackley(x):
    """
    Ackley function, description can be found here: https://en.wikipedia.org/wiki/Test_functions_for_optimization
    """
    a = 20
    b = 0.2
    c = 2*np.pi
    dim = len(x)
    term1 = -1. * a * np.exp(-1. * b * np.sqrt((1./dim) * sum(map(lambda i: i**2, x))))
    term2 = -1. * np.exp((1./dim) * (sum(map(lambda j: np.cos(c * j), x))))
    return term1 + term2 + a + np.exp(1)

class Function:
    """
    A class that describes a function and its parameters for cubic regularization
    """
    def __init__(self, function='bimodal', aux_method="trust_region"):
        self.plot_name = function
        if function == 'bimodal':
            self.f_sub = lambda x, i: x[i]**2*np.exp(1-np.linalg.norm(x)**2) 
            self.f = lambda x: -(self.f_sub(x,0)+3*self.f_sub(x,1))
            self.basis = lambda i: (np.arange(2) == i).astype(int)
            self.grad_sub = lambda x, i: 2*np.exp(1-np.linalg.norm(x)**2)*(x[i]*self.basis(i)-x[i]**2*x)
            self.grad = lambda x : -(self.grad_sub(x,0)+3*self.grad_sub(x,1))
            self.hess = None
            self.x0 = np.array([1, 0])  # Start at saddle point!
            self.plot_x_lim = 3
            self.plot_y_lim = 3
            self.plot_nb_contours = 24
        elif function == 'simple':
            self.f = lambda x: x[0]**2*x[1]**2 + x[0]**2 + x[1]**2
            self.grad = lambda x: np.asarray([2*x[0]*x[1]**2 + 2*x[0], 2*x[0]**2*x[1] + 2*x[1]])
            self.hess = lambda x: np.asarray([[2*x[1]**2 + 2, 4*x[0]*x[1]], [4*x[0]*x[1], 2*x[0]**2 + 2]])
            self.x0 = np.array([1, 2])
            self.plot_x_lim = 5
            self.plot_y_lim = 5
            self.plot_nb_contours = 15
        elif function == 'quadratic':
            self.f = lambda x: x[0]**2+x[1]**2
            self.grad = lambda x: np.asarray([2*x[0], 2*x[1]])
            self.hess = lambda x: np.asarray([[2, 0], [0, 2]])*1.0
            self.x0 = np.array([2, 2])
            self.plot_x_lim = 4
            self.plot_y_lim = 4
            self.plot_nb_contours = 20
        elif function == 'banana':
            self.f = lambda x: banana_f(x)
            self.grad = lambda x: banana_grad(x)
            self.hess = lambda x: banana_hess(x)
            self.x0 = np.array([3, -3])
            self.plot_x_lim = 3.5
            self.plot_y_lim = 15
            self.plot_nb_contours = 80
        elif function == 'ackley':
            self.f = lambda x: Ackley(x)
            self.grad = None
            self.hess = None
            self.x0 = np.array([1.5, 1])
            self.plot_x_lim = 2
            self.plot_y_lim = 2
            self.plot_nb_contours = 40
        elif function == 'polynomial':
            self.f = lambda x: n_polynomial(x)
            self.grad = None
            self.hess = None
            self.x0 = np.array([1.5, 1])
            self.plot_x_lim = 2.5
            self.plot_y_lim = 2.5
            self.plot_nb_contours = 70
            print('A:', A)
        else:
            raise TypeError('Invalid input type for function initialization')
        self.cr = src.cubic_reg.CubicRegularization(self.x0, f=self.f, gradient=self.grad, hessian=self.hess, maxiter=10000, conv_tol=1e-8,
                                                    L0=1.e-05, aux_method=aux_method, verbose=0, conv_criterion='gradient')

    def run(self):
        """
        Solve the cubic regularization problem
        """
        x_opt, intermediate_points, n_iter, flag = self.cr.cubic_reg()
        print('Value of function:', self.f(x_opt))
        return x_opt, intermediate_points, n_iter

    def plot_points(self, intermediate_points):
        """
        Plot the intermediate steps of cubic regularization
        """
        points = np.asarray(intermediate_points)
        xlist = np.linspace(-1*self.plot_x_lim, self.plot_x_lim, self.plot_nb_contours)
        ylist = np.linspace(-1*self.plot_y_lim, self.plot_y_lim, self.plot_nb_contours)
        X, Y = np.meshgrid(xlist, ylist)
        Z = np.zeros_like(X)
        for i in range(0, len(X)):
            for j in range(0, len(X)):
                Z[i, j] = self.f((X[i, j], Y[i, j]))
        plt.clf()
        cs = plt.contour(X, Y, Z, self.plot_nb_contours, cmap=plt.cm.magma, alpha=1, extend='both')
        plt.clabel(cs, cs.levels, inline=True, fontsize=10)
        plt.scatter(points[0, 0], points[0, 1], marker='.', color='#495CD5')
        plt.scatter(points[1:, 0], points[1:, 1], marker='.', color='#5466DE')
        plt.scatter(points[-1, 0], points[-1, 1], marker='*', color='#C4CCFF')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.xlim(-self.plot_x_lim, self.plot_x_lim)
        plt.ylim(-self.plot_y_lim, self.plot_y_lim)
        plt.savefig("figures/cubic_regularization_"+self.plot_name+".png", format="png")


if __name__ == '__main__':
    """
    Choose a function to run it on, and a method to use for the auxiliary one-dimensional problem
    Function choices: 'bimodal', 'simple', 'quadratic', 'banana', 'ackley', 'polynomial'
    Method choices for the auxiliary problem: 'trust_region', 'monotone_norm'
    """
    bm = Function(function='polynomial', aux_method='monotone_norm')
    # Run the algorithm on the function
    x_opt, intermediate_points, n_iter = bm.run()
    print('Argmin of function:', x_opt)
    print('Number of iterations:', n_iter)
    # Plot the path of the algorithm and save it in 'figures' folder
    bm.plot_points(intermediate_points)
