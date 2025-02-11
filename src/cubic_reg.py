"""
This module implements cubic regularization of Newton's method, as described in Nesterov and Polyak (2006). This code solves the cubic subproblem
according to slight modifications of Algorithm 7.3.6 of Conn et. al (2000) or by finding a root of a monotone-like function using the Newton's method.
Cubic regularization solves unconstrained minimization problems by minimizing a cubic upper bound of the function at each iteration.

Original implementation by Corinne Jones, modified and the second method for the subproblem added by Ieva Petrulionyte

References:
- Nesterov, Y., & Polyak, B. T. (2006). Cubic regularization of Newton method and its global performance.
  Mathematical Programming, 108(1), 177-205.
- Cartis, C., Gould, N. I., & Toint, P. L. (2011). Adaptive cubic regularisation methods for unconstrained optimization.
  Part I: motivation, convergence and numerical results. Mathematical Programming, 127(2), 245-295.
- Conn, A. R., Gould, N. I., & Toint, P. L. (2000). Trust region methods (Vol. 1). Siam.
- Gould, N. I., Lucidi, S., Roma, M., & Toint, P. L. (1999). Solving the trust-region subproblem using the Lanczos
  method. SIAM Journal on Optimization, 9(2), 504-525.
"""

from cvxpy import lambda_min
from scipy.optimize import newton
import numpy as np
import scipy.linalg
import matplotlib.pyplot as plt


class Algorithm:
    def __init__(self, x0, f=None, gradient=None, hessian=None, L=None, L0=None, kappa_easy=0.0001, maxiter=10000,
                 submaxiter=100000, conv_tol=1e-5, conv_criterion='gradient', epsilon=2*np.sqrt(np.finfo(float).eps), aux_method="trust_region", verbose = 0):
        """
        Collect all the inputs to the cubic regularization algorithm.
        Required inputs: function to be solved.
        :param x0: Starting point for cubic regularization algorithm
        :param f: Function to be minimized
        :param gradient: Gradient of f (input as a function that returns a numpy array)
        :param hessian: Hessian of f (input as a function that returns a numpy array)
        :param L0: Starting point for line search for M
        :param kappa_easy: Convergence tolerance for the trust-region subproblem
        :param maxiter: Maximum number of cubic regularization iterations
        :param submaxiter: Maximum number of iterations for the cubic subproblem
        :param conv_tol: Convergence tolerance
        :param conv_criterion: Criterion for convergence: 'gradient' or 'decrement', 'gradient' uses norm of gradient
        :param epsilon: Value added/subtracted from x when approximating gradients and Hessians
        :param aux_method: Method for solving the auxiliary problem
        :param verbose: Display of additional solving information
        """
        self.f = f
        self.gradient = gradient
        self.hessian = hessian
        self.x0 = np.array(x0)*1.0
        self.maxiter = maxiter
        self.submaxiter = submaxiter
        self.conv_tol = conv_tol
        self.conv_criterion = conv_criterion.lower()
        self.epsilon = epsilon
        self.L0 = L0
        self.kappa_easy = kappa_easy
        self.n = len(x0)

        self.aux_method = aux_method
        self.verbose = verbose

        self._check_inputs()
        # Estimate the gradient, hessian, and find a lower bound L0 for L if necessary
        if gradient is None:
            self.gradient = self.approx_grad
        if hessian is None:
            self.hessian = self.approx_hess
        if L0 is None and L is None:
            self.L0 = np.linalg.norm(self.hessian(self.x0)-self.hessian(self.x0+np.ones_like(self.x0)), ord=2)/np.linalg.norm(np.ones_like(self.x0))+self.epsilon

        self.grad_x = self.gradient(self.x0)
        self.hess_x = self.hessian(self.x0)
        self.lambda_nplus = self._compute_lambda_nplus()[0]

    def _check_inputs(self):
        """
        Ensure that the inputs are of the right form and all necessary inputs have been supplied
        """
        if not isinstance(self.x0, (tuple, list, np.ndarray)):
            raise TypeError('Invalid input type for x0')
        if len(self.x0) < 1:
            raise ValueError('x0 must have length > 0')
        if not (self.f is not None or (self.gradient is not None and self.hessian is not None)):
            raise AttributeError('You must specify f and/or each of the following: gradient, hessian, and L')
        if not((not self.L0 or self.L0 > 0) and self.kappa_easy > 0 and self.maxiter > 0 and self.conv_tol > 0 and self.epsilon > 0):
            raise ValueError('All inputs that are constants must be larger than 0')
        if self.f is not None:
            try:
                self.f(self.x0)
            except TypeError:
                raise TypeError('x0 is not a valid input to function f')
        if self.gradient is not None:
            try:
                self.gradient(self.x0)
            except TypeError:
                raise TypeError('x0 is not a valid input to the gradient. Is the gradient a function with input '
                                'dimension length(x0)?')
        if self.hessian is not None:
            try:
                self.hessian(self.x0)
            except TypeError:
                raise TypeError('x0 is not a valid input to the hessian. Is the hessian a function with input dimension '
                                'length(x0)?')
        if not (self.conv_criterion == 'function' or self.conv_criterion == 'gradient' or self.conv_criterion == 'decrement'):
            raise ValueError('Invalid input for convergence criterion')
        if not (self.aux_method == "trust_region" or self.aux_method == "monotone_norm"):
            raise ValueError("No such method for solving the auxiliary problem")

    @staticmethod
    def _std_basis(size, idx):
        """
        Compute the idx'th standard basis vector
        :param size: Length of the vector
        :param idx: Index of value 1 in the vector
        :return: ei: Standard basis vector with 1 in the idx'th position
        """
        ei = np.zeros(size)
        ei[idx] = 1
        return ei

    def approx_grad(self, x):
        """
        Approximate the gradient of the function self.f at x
        :param x: Point at which the gradient will be approximated
        :return: Estimated gradient at x
        """
        return np.asarray([(self.f(x + self.epsilon * self._std_basis(self.n, i)) -
                            self.f(x - self.epsilon * self._std_basis(self.n, i))) / (2 * self.epsilon) for i in range(0, self.n)])

    def approx_hess(self, x):
        """
        Approximate the hessian of the function self.x at x
        :param x: Point at which the Hessian will be approximated
        :return: Estimated Hessian at x
        """
        grad_x0 = self.gradient(x)
        hessian = np.zeros((self.n, self.n))
        for j in range(0, self.n):
            grad_x_plus_eps = self.gradient(x + self.epsilon * self._std_basis(self.n, j))
            for i in range(0, self.n):
                hessian[i, j] = (grad_x_plus_eps[i]-grad_x0[i])/self.epsilon
        return hessian

    def _compute_lambda_nplus(self):
        """
        Compute max(-1*smallest eigenvalue of hessian of f at x, 0)
        :return: max(-1*smallest eigenvalue of hessian of f at x, 0)
        :return: lambda_n: Smallest eigenvaleu of hessian of f at x
        """
        lambda_n = scipy.linalg.eigh(self.hess_x, eigvals_only=True, eigvals=(0, 0))
        return max(-lambda_n[0], 0), lambda_n

    def _check_convergence(self, x_old, x_new):
        """
        Check whether the cubic regularization algorithm has converged
        :param lambda_min: Minimum eigenvalue at current point
        :param M: Current value used for M in cubic upper approximation to f at x_new
        :return: True/False depending on whether the convergence criterion has been satisfied
        """
        if self.conv_criterion == 'function':
            if self.f(x_new) > self.f(x_old):
                return True
            else:
                return False
        elif self.conv_criterion == 'gradient':
            if np.linalg.norm(self.grad_x) <= self.conv_tol:
                return True
            else:
                return False
        elif self.conv_criterion == 'decrement':
            lambda_sq = np.matmul(np.matmul(self.grad_x.T, np.linalg.pinv(self.hess_x)), self.grad_x)
            if lambda_sq * 1/2 <= self.conv_tol:
                return True
            else:
                return False


class CubicRegularization(Algorithm):
    def __init__(self, x0, f=None, gradient=None, hessian=None, L=None, L0=None, kappa_easy=0.0001, maxiter=10000,
                 submaxiter=10000, conv_tol=1e-5, conv_criterion='gradient', epsilon=2*np.sqrt(np.finfo(float).eps), aux_method="trust_region", verbose=0):
        Algorithm.__init__(self, x0, f=f, gradient=gradient, hessian=hessian, L=L, L0=L0, kappa_easy=kappa_easy,
                           maxiter=maxiter, submaxiter=submaxiter, conv_tol=conv_tol, conv_criterion=conv_criterion,
                           epsilon=epsilon, aux_method=aux_method, verbose=verbose)

        self.f_cubic = lambda x, y, mu: self.f(x) + np.matmul(self.grad_x.T,(y-x)) + 0.5*np.matmul((np.matmul(self.hess_x,(y-x))).T,(y-x)) + mu/6*(np.linalg.norm(y-x)**3)

    def _cubic_approx(self, f_x, s, mk):
        """
        Compute the value of the cubic approximation to f at the proposed next point
        :param f_x: Value of f(x) at current point x
        :param s: Proposed step to take
        :return: Value of the cubic approximation to f at the proposed next point
        """
        return f_x + np.matmul(self.grad_x.T,s) + 0.5*np.matmul((np.matmul(self.hess_x,s)).T,s) + mk/6*(np.linalg.norm(s)**3)

    def cubic_reg(self):
        """
        Run the cubic regularization algorithm
        :return: x_new: Final point
        :return: intermediate_points: All points visited by the cubic regularization algorithm on the way to x_new
        :return: iter: Number of iterations of cubic regularization
        """
        iter = flag = 0
        converged = False
        x_new = self.x0
        mk = self.L0
        intermediate_points = [x_new]
        intermediate_hess_cond = []
        MK = []
        while iter < self.maxiter and converged is False:
            x_old = x_new.copy()
            x_new, mk, flag, hess_cond = self._find_x_new(x_old, mk, iter)
            MK.append(np.linalg.norm(self.grad_x))#np.linalg.norm(x_old-x_new))
            self.grad_x = self.gradient(x_new)
            self.hess_x = self.hessian(x_new)
            intermediate_hess_cond.append(hess_cond)
            self.lambda_nplus, lambda_min = self._compute_lambda_nplus()
            self.f_x = self.f(x_new)
            converged = self._check_convergence(x_old, x_new)
            if flag != 0:
                print(RuntimeWarning('Convergence criteria not met, likely due to round-off error or ill-conditioned '
                                     'Hessian.'))
                return x_new, intermediate_points, iter, flag, intermediate_hess_cond
            intermediate_points.append(x_new)
            iter += 1
        eigvals, eigvecs = scipy.linalg.eigh(self.hess_x)
        if not (np.all(eigvals>=0)):
            print(RuntimeWarning('Did not converge to a local minimum, likely a saddle point or gradient very small.'))
        #print("avg(MK) =", "{:e}".format(np.average(MK)))
        #x_mk = np.arange(0, iter)
        #plt.plot(x_mk, MK)
        #plt.yscale("log")
        #plt.show()
        return x_new, intermediate_points, iter, flag, intermediate_hess_cond

    def _find_x_new(self, x_old, mk, iter):
        """
        Determine what M_k should be and compute the next point for the cubic regularization algorithm
        :param x_old: Previous point
        :param mk: Previous value of M_k (will start with this if L isn't specified)
        :return: x_new: New point
        :return: mk: New value of M_k
        """
        upper_approximation = False
        iter = 0
        mk = max(0.5 * mk, self.L0)
        while not upper_approximation and iter < self.submaxiter:
            # If mk is too small s.t. the cubic approximation is not upper, multiply by sqrt(2).
            if iter != 0:
                mk *= 2
            #print("mk: ", mk, ", iter: ", iter)
            aux_problem = _AuxiliaryProblem(x_old, self.grad_x, self.hess_x, mk, self.lambda_nplus, self.kappa_easy,
                                            self.submaxiter, self.aux_method, self.verbose)
            s, flag, hess_cond = aux_problem.solve()
            x_new = x_old + s
            cubic_approx = self._cubic_approx(self.f(x_old), s, mk)
            upper_approximation = (cubic_approx >= self.f(x_new))
            iter += 1
            if iter == self.submaxiter:
                raise RuntimeError('Could not find cubic upper approximation')
        return x_new, mk, flag, hess_cond


class _AuxiliaryProblem:
    """
    Solve the cubic subproblem as described in Conn et. al (2000) (see reference at top of file)
    The notation in this function follows that of the above reference.
    """
    def __init__(self, x, gradient, hessian, M, lambda_nplus, kappa_easy, submaxiter, aux_method, verbose):
        """
        :param x: Current location of cubic regularization algorithm
        :param gradient: Gradient at current point
        :param hessian: Hessian at current point
        :param M: Current value used for M in cubic upper approximation to f at x_new
        :param lambda_nplus: max(-1*smallest eigenvalue of hessian of f at x, 0)
        :param kappa_easy: Convergence tolerance
        :param aux_method: Method to be used to solve the auxiliary problem
        """
        self.x = x
        self.grad_x = gradient
        self.hess_x = hessian
        self.M = M
        self.lambda_nplus = lambda_nplus
        self.kappa_easy = kappa_easy
        self.maxiter = submaxiter
        self.method = aux_method
        self.verbose = verbose

    def _compute_s(self, lambduh):
        """
        Compute L in H_lambda = LL^T and then solve LL^Ts = -g
        :param lambduh: value for lambda in H_lambda
        :return: s, L
        """
        try:
            # Numpy's Cholesky seems more numerically stable than scipy's Cholesky
            L = np.linalg.cholesky(self.H_lambda(lambduh)).T
        except:
            # See p. 516 of Gould et al. (1999) (see reference at top of file)
            self.lambda_const *= 2
            try:
                s, L = self._compute_s(self.lambda_nplus + self.lambda_const)
            except:
                return np.zeros_like(self.grad_x), [], 1
        s = scipy.linalg.cho_solve((L, False), -self.grad_x)
        return s, L, 0

    def _update_lambda(self, lambduh, s, L):
        """
        Update lambda by taking a Newton step
        :param lambduh: Current value of lambda
        :param s: Current value of -(H+lambda I)^(-1)g
        :param L: Matrix L from Cholesky factorization of H_lambda
        :return: lambduh - phi/phi_prime: Next value of lambda
        """
        w = scipy.linalg.solve_triangular(L.T, s, lower=True)
        norm_s = np.linalg.norm(s)
        phi = 1/norm_s-self.M/(2*lambduh)
        phi_prime = np.linalg.norm(w)**2/(norm_s**3)+self.M/(2*lambduh**2)
        return lambduh - phi/phi_prime

    def _converged(self, s, lambduh):
        """
        Check whether the algorithm from the subproblem has converged
        :param s: Current estimate of -(H+ lambda I)^(-1)g
        :param lambduh: Current estimate of lambda := Mr/2
        :return: True/False based on whether the convergence criterion has been met
        """
        r = 2*lambduh/self.M
        if abs(np.linalg.norm(s)-r) <= self.kappa_easy:
            return True
        else:
            return False

    def solve(self):
        """
        Solve the cubic regularization subproblem.
        :return: s: Step for the cubic regularization algorithm
        """
        if self.method == "trust_region":
            """
            See algorithm 7.3.6 in Conn et al. (2000).
            """
            # Hessian condition number not calculated
            hess_cond = -1
            # Function to compute H(x)+lambda*I as function of lambda
            self.H_lambda = lambda lambduh: self.hess_x + lambduh*np.identity(np.size(self.hess_x, 0))
            # Constant to add to lambda_nplus so that you're not at the zero where the eigenvalue is
            self.lambda_const = (1+self.lambda_nplus)*np.sqrt(np.finfo(float).eps)
            if self.lambda_nplus == 0:
                lambduh = 0
            else:
                lambduh = self.lambda_nplus + self.lambda_const
            s, L, flag = self._compute_s(lambduh)
            if flag != 0:
                return s, flag, hess_cond
            r = 2*lambduh/self.M
            if np.linalg.norm(s) <= r:
                if lambduh == 0 or np.linalg.norm(s) == r:
                    return s, 0, hess_cond
                else:
                    Lambda, U = np.linalg.eigh(self.H_lambda(self.lambda_nplus))
                    s_cri = -U.dot(np.linalg.pinv(np.diag(Lambda))).dot(U.T).dot(self.grad_x)
                    alpha = max(np.roots([np.dot(U[:, 0], U[:, 0]),
                                        2*np.dot(U[:, 0], s_cri), np.dot(s_cri, s_cri)-4*self.lambda_nplus**2/self.M**2]))
                    s = s_cri + alpha*U[:, 0]
                    return s, 0, hess_cond
            if lambduh == 0:
                lambduh += self.lambda_const
            iter = 0
            while not self._converged(s, lambduh) and iter < self.maxiter:
                iter += 1
                lambduh = self._update_lambda(lambduh, s, L)
                s, L, flag = self._compute_s(lambduh)
                if flag != 0:
                    return s, flag, hess_cond
                #if iter == self.maxiter:
                #    print(RuntimeWarning('Warning: Could not compute s: maximum number of iterations reached'))
        elif self.method == "monotone_norm":
            """
            Newton on a monotone function.
            """
            # Compute the eigenvalues and the eigenvectors of the Hessian
            try:
                eigvals, eigvecs = scipy.linalg.eigh(self.hess_x)
                eigvals_min = eigvals[0]
                eigvals = np.where(eigvals<=0, 1.0e-08, eigvals)
                # Calculating hessian condition number for plotting
                hess_cond = eigvals[-1]/eigvals[0]
                #print("Eigenvalues :", eigvals)
            except:
                raise RuntimeError("Failed to compute the eigenvalues of the hessian")
            # Diagonalize the Hessian
            try:
                O = np.column_stack(eigvecs)
                I = np.matmul(O.T,O)
                I[np.isclose(I, 0)] = 0
            except:
                raise RuntimeError("Failed to diagonalize the hessian")
            # Diagonalization check
            assert (I.shape[0] == I.shape[1]) and np.allclose(I, np.eye(I.shape[0]))

            # Solve the auxiliary one-dimensional problem
            eta = np.matmul(O,self.grad_x)
            # If not at a stationary point, solve the auxiliary problem
            if not np.all(np.isclose(eta, 0)):
                # Monotone function to solve.
                #print("eigvals:", eigvals, ", M:", self.M)
                f = lambda x, et, l, mu: np.linalg.norm(et/(l+3*mu*x))-x
                #fder = lambda x, et, l, mu: np.sum((-3*mu*np.sqrt((et*et)/((l+3*mu*x)*(l+3*mu*x))))/(l+3*mu*x))-1
                # Initial guess for Newton's method.
                x0 = max((-1*np.min(eigvals))/(3*self.M)+1.0e-04,1.0e-04)
                (v, r) = newton(f, x0, args=(eta, eigvals, self.M), maxiter=self.maxiter, full_output=True, tol=1.48e-8)
                """
                print("Newton root :", r.root)
                print("Newton func value :", f(r.root, eta, eigvals, self.M))
                T = np.arange(0,0.2,0.001)
                f_T = [f(t, eta, eigvals, self.M) for t in T]
                plt.plot(T, f_T)
                plt.scatter(r.root, f(r.root, eta, eigvals, self.M))
                plt.show()
                """
                if self.verbose == 1:
                    print("Newton root :", r.root)
                    print("Newton iterations :", r.iterations)
                    print("Newton function calls :", r.function_calls)
                u = -eta/(eigvals+3*self.M*v)
                # Compute the step size.
                s = np.matmul(O.T, u)
            # Classify the stationary point w.r.t. second order optimality condition.
            else:
                # Maximum or saddle point, move to the descent direction
                if eigvals_min < 0:
                    s = eigvecs[0]
                # Undefined or local minimum, stay at the current point
                else:
                    s = eta
        return s, 0, hess_cond