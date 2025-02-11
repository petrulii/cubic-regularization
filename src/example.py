import src.cubic_reg as cubic_reg
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import rosen as banana_f
from scipy.optimize import rosen_der as banana_grad
from scipy.optimize import rosen_hess as banana_hess

def Ackley(x):
    """
    Ackley function, description can be found here: https://en.wikipedia.org/wiki/Test_functions_for_optimization.
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
    A class that describes a function and its parameters for cubic regularization.
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
            self.plot_x_lim = 1.2
            self.plot_y_lim = 1.2
            self.plot_nb_contours = 80
        elif function == 'simple':
            self.f = lambda x: x[0]**2*x[1]**2 + x[0]**2 + x[1]**2
            self.grad = lambda x: np.asarray([2*x[0]*x[1]**2 + 2*x[0], 2*x[0]**2*x[1] + 2*x[1]])
            self.hess = lambda x: np.asarray([[2*x[1]**2 + 2, 4*x[0]*x[1]], [4*x[0]*x[1], 2*x[0]**2 + 2]])
            self.x0 = np.array([1, 2])
            self.plot_x_lim = 5
            self.plot_y_lim = 5
            self.plot_nb_contours = 80
        elif function == 'quadratic':
            self.f = lambda x: x[0]**2+x[1]**2
            self.grad = lambda x: np.asarray([2*x[0], 2*x[1]])
            self.hess = lambda x: np.asarray([[2, 0], [0, 2]])*1.0
            self.x0 = np.array([2, 2])
            self.plot_x_lim = 4
            self.plot_y_lim = 4
            self.plot_nb_contours = 80
        elif function == 'banana':
            self.f = lambda x: banana_f(x)
            self.grad = lambda x: banana_grad(x)
            self.hess = lambda x: banana_hess(x)
            self.x0 = np.array([3, -3])
            self.plot_x_lim = 3.5
            self.plot_y_lim = 9
            self.plot_nb_contours = 280
        elif function == 'ackley':
            self.f = lambda x: Ackley(x)
            self.grad = None
            self.hess = None
            self.x0 = np.array([0.5, -0.5])
            self.plot_x_lim = 1.5
            self.plot_y_lim = 1.5
            self.plot_nb_contours = 80
        elif function == 'polynomial':
            n = 2
            a = np.random.uniform(-1,1,size=(n,n))
            A = (a + a.T)/2
            c = np.random.uniform(-10,10)
            self.f = lambda x: (x[1]-x[0]*x[0])**2+(A[0,0]*x[0]*x[0]-c)**2+(A[0,1]*x[0]*x[1]-c)**2+(A[1,0]*x[1]*x[0]-c)**2+(A[1,1]*x[1]*x[1]-c)**2
            self.grad = None
            self.hess = None
            self.x0 = np.random.uniform(-10,10,(n,))
            self.plot_x_lim = 8
            self.plot_y_lim = 8
            self.plot_nb_contours = 80
        else:
            raise TypeError('Invalid input type for function initialization')
        self.cr = cubic_reg.CubicRegularization(self.x0, f=self.f, gradient=self.grad, hessian=self.hess, maxiter=10000, conv_tol=1e-8,
                                                    L0=1.e-05, aux_method=aux_method, verbose=0, conv_criterion='gradient')

    def run(self):
        """
        Solve the cubic regularization problem.
        """
        x_opt, intermediate_points, n_iter, flag, intermediate_hess_cond = self.cr.cubic_reg()
        print('Value of function at argmin:', self.f(x_opt))
        return x_opt, intermediate_points, n_iter

    def plot_points(self, intermediate_points):
        """
        Plot the intermediate steps of cubic regularization.
        :param intermediate_points: Intermediate points of cubic regularization minimization
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
        cs = plt.contour(X, Y, Z, self.plot_nb_contours, cmap=plt.cm.magma, alpha=0.8, extend='both')
        # Show contour values.
        #plt.clabel(cs, cs.levels, inline=True, fontsize=10)
        plt.scatter(points[0, 0], points[0, 1], marker='.', color='#495CD5')
        plt.scatter(points[1:, 0], points[1:, 1], marker='.', color='#5466DE')
        plt.scatter(points[-1, 0], points[-1, 1], marker='*', color='r')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.xlim(-self.plot_x_lim, self.plot_x_lim)
        plt.ylim(-self.plot_y_lim, self.plot_y_lim)
        plt.savefig("figures/cubic_regularization_"+self.plot_name+".png", format="png")
        plt.show()

def main(function='simple', aux_method='monotone_norm'):
    """
    Choose a function to run it on, and a method to solve the auxiliary one-dimensional problem
    :param function: Example functions - 'bimodal', 'simple', 'quadratic', 'banana', 'ackley', 'polynomial'
    :param aux_method: Method for the auxiliary problem - 'trust_region', 'monotone_norm'
    """
    bm = Function(function=function, aux_method=aux_method)
    # Run the algorithm on the function
    x_opt, intermediate_points, n_iter = bm.run()
    print('Argmin of function:', x_opt)
    print('Number of iterations:', n_iter)
    # Plot the path of the algorithm and save it in 'figures' folder
    bm.plot_points(intermediate_points)