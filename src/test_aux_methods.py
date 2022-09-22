import numpy as np
import src.cubic_reg as cubic_reg
import matplotlib.pyplot as plt
from src.quadratic_obj import quadratic_obj
import time

def test_aux_methods(nb_experiments=10, high_dim=9):
    """
    Compare Trust region and Monotone norm methods for solving the auxiliary problem.
    :param nb_experiments: number of times both methods will be executed
    :param high_dim: highest dimension of the problem (will run all odd dimensions starting at 3)
    """
    # Specify number of experiments
    nb_experiments = nb_experiments
    # Initialize multiple dimensions for experiments
    N = np.arange(3, high_dim, 2)
    nb_N = N.shape[0]
    # For collecting experiment data and plotting
    fig_name = "aux_methods"
    time_tr = np.zeros((nb_N, nb_experiments))
    time_mn = np.zeros((nb_N, nb_experiments))
    estim_error_tr = np.zeros((nb_N, nb_experiments))
    estim_error_mn = np.zeros((nb_N, nb_experiments))
    iters_tr = np.zeros((nb_N, nb_experiments))
    iters_mn = np.zeros((nb_N, nb_experiments))

    # Solve for multiple increasing dimensions
    for i in range(nb_N):
        # Dimension of the problem
        n = N[i]
        # Parameters for the quadratic objective
        a = np.random.randint(-1,1,size=(n,n))
        A = (a + a.T)/2
        A[n-1, n-1] = 0
        c = np.random.uniform(-10,10)
        # Generate the objective function
        f = quadratic_obj(n, A, c, lambd=1)
        # Number of experiments per dimension
        for j in range(nb_experiments):
            start_time = time.time()
            # Initial point for cubic regularization
            x0 = np.random.randint(-10,10,size=(n,))
            cr = cubic_reg.CubicRegularization(x0, f=f, conv_tol=1e-8, L0=1.e-05, aux_method="trust_region", verbose=0, conv_criterion='gradient')
            x_opt, intermediate_points, n_iter, flag, intermediate_hess_cond = cr.cubic_reg()
            #print("\nTrust region\n", "Iterations:", n_iter, ", time:", time.time() - start_time, ", f_opt:", f(x_opt))
            #print("Argmin of f: ", x_opt)
            time_tr[i,j] = time.time() - start_time
            estim_error_tr[i,j] = 1 if np.isclose(f(x_opt),0) else 0
            iters_tr[i,j] = n_iter

            start_time = time.time()
            cr = cubic_reg.CubicRegularization(x0, f=f, conv_tol=1e-8, L0=1.e-05, aux_method="monotone_norm", verbose=0, conv_criterion='gradient')
            x_opt, intermediate_points, n_iter, flag, intermediate_hess_cond = cr.cubic_reg()
            #print("\nMonotone norm\n", "Iterations:", n_iter, ", time:", time.time() - start_time, ", f_opt:", f(x_opt))
            #print("Argmin of f: ", x_opt)
            time_mn[i,j] = time.time() - start_time
            estim_error_mn[i,j] = 1 if np.isclose(f(x_opt),0) else 0
            iters_mn[i,j] = n_iter

    time_tr = np.average(time_tr, axis=1)
    time_mn = np.average(time_mn, axis=1)
    estim_error_tr = np.average(estim_error_tr, axis=1)
    estim_error_mn = np.average(estim_error_mn, axis=1)
    iters_tr = np.average(iters_tr, axis=1)
    iters_mn = np.average(iters_mn, axis=1)

    fig0, ax0 = plt.subplots()
    ax0.plot(N, time_tr, label="Trust region")
    ax0.plot(N, time_mn, label="Monotone norm")
    ax0.set_xlabel('dimension $k$')
    ax0.set_ylabel('time (s)')
    ax0.legend(loc='best')
    ax0.set_title("Time taken with increasing $k$")
    plt.savefig("figures/time_"+fig_name+".png", format="png")
    plt.show()

    fig1, ax1 = plt.subplots()
    ax1.plot(N, estim_error_tr, label="Trust region")
    ax1.plot(N, estim_error_mn, label="Monotone norm")
    ax0.set_xlabel('dimension $k$')
    ax1.set_ylabel('success score')
    ax1.legend(loc='best')
    ax1.set_title("How often the global minimum is found")
    plt.savefig("figures/value_"+fig_name+".png", format="png")
    plt.show()

    fig2, ax2 = plt.subplots()
    ax2.plot(N, iters_tr, label="Trust region")
    ax2.plot(N, iters_mn, label="Monotone norm")
    ax0.set_xlabel('dimension $k$')
    ax2.set_ylabel('iterations')
    ax2.legend(loc='best')
    ax0.set_title("Iterations with increasing $k$")
    plt.savefig("figures/iterations_"+fig_name+".png", format="png")
    plt.show()