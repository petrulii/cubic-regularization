import numpy as np
import src.cubic_reg as utils
import matplotlib.pyplot as plt
import time
from sklearn.metrics import mean_squared_error as mse

def f(x):
    n = len(x)
    result = 0
    for i in range(1,n):
        result += (x[i]-x[i-1]*x[0])**2
    for i in range(0,n):
        for j in range(0,n):
            result += (A[i,j]*x[i]*x[j]-c)**2
    return result

np.random.seed(0)

# Hyper-parameter of the polynomial
n = 5
a = np.random.uniform(-1,1,size=(n,n))
A = (a + a.T)/2
A[n-1, n-1] = 0
c = 20
x0 = np.random.uniform(-1,1,size=n)

nb_minima = 30
minima = np.zeros(nb_minima)

dom_range = 1.e2
for i in range(nb_minima):
    #x0 = np.ones(n)
    x0 = np.random.randint(-dom_range,dom_range,size=(n,))
    cr = utils.CubicRegularization(x0, f=f, conv_tol=1e-8, L0=0.00001, aux_method="monotone_norm", verbose=0, conv_criterion='gradient', maxiter=10000)
    x_opt, intermediate_points, n_iter, flag = cr.cubic_reg()
    f_x_opt = f(x_opt)
    print("Iterations:", n_iter, ", argmin of f:", x_opt, "i:", i)
    minima[i] = f(x_opt)

print("Local minima:", minima)
print("Number of local minima found:", len(np.unique(minima)))
print("Best local minimum:", np.min(minima))

"""
# Initialize multiple dimensions for experiments
nb_experiments = 10
N = np.arange(3, 11, 2)
nb_N = N.shape[0]

# For collecting experiment data and plotting
fig_name = "polynomial_tust_region"
time_tr = np.zeros((nb_experiments,nb_N))
time_mn = np.zeros((nb_experiments,nb_N))
estim_error_tr = np.zeros((nb_experiments,nb_N))
estim_error_mn = np.zeros((nb_experiments,nb_N))
iters_tr = np.zeros((nb_experiments,nb_N))
iters_mn = np.zeros((nb_experiments,nb_N))

for i in range(nb_experiments):
    for j in range(nb_N):
        n = N[j]
        print("Experiment: ",i, ", n: ",n)
        # Initial point for cubic regularization
        x0 = np.zeros(n)
        #x0 = np.random.randint(-10,10,size=(n,))
        # Hyper-parameter of the polynomial
        a = np.random.randint(-10,10,size=(n,n))
        A = (a + a.T)/2
        A[n-1, n-1] = 0
        print(A)
        c = 20

        start_time = time.time()
        cr = utils.CubicRegularization(x0, f=f, conv_tol=1e-4, L0=0.00001, aux_method="trust_region", verbose=1, conv_criterion='gradient')
        x_opt, intermediate_points, n_iter, flag = cr.cubic_reg()
        print("\nTrust region\n", "Iterations:", n_iter, ", time:", time.time() - start_time, ", f_opt:", f(x_opt))
        print("Argmin of f: ", x_opt) 
        x_pows = np.power(np.ones(n)*x_opt[0], np.arange(1,n+1))
        print("Power series: ", x_pows)
        time_tr[i,j] = time.time() - start_time
        estim_error_tr[i,j] = f(x_opt)
        iters_tr[i,j] = n_iter

        start_time = time.time()
        cr = utils.CubicRegularization(x0, f=f, conv_tol=1e-4, L0=0.00001, aux_method="monotone_norm", verbose=0, conv_criterion='gradient')
        x_opt, intermediate_points, n_iter, flag = cr.cubic_reg()
        print("\nMonotone norm\n", "Iterations:", n_iter, ", time:", time.time() - start_time, ", f_opt:", f(x_opt))
        print("Argmin of f: ", x_opt) 
        x_pows = np.power(np.ones(n)*x_opt[0], np.arange(1,n+1))
        print("Power series: ", x_pows)
        time_mn[i,j] = time.time() - start_time
        estim_error_mn[i,j] = f(x_opt)
        iters_mn[i,j] = n_iter


time_tr = np.average(time_tr, axis=0)
time_mn = np.average(time_mn, axis=0)
estim_error_tr = np.average(estim_error_tr, axis=0)
estim_error_mn = np.average(estim_error_mn, axis=0)
iters_tr = np.average(iters_tr, axis=0)
iters_mn = np.average(iters_mn, axis=0)

fig0, ax0 = plt.subplots()
ax0.plot(N, time_tr, label="Trust region")
#ax0.plot(N, time_mn, label="Monotone norm")
ax0.set_xlabel('k')
ax0.set_ylabel('Time')
ax0.legend(loc='best')
ax0.set_title("Time taken for different dimension k")
plt.savefig("figures/time_"+fig_name+".png", format="png")

fig1, ax1 = plt.subplots()
ax1.plot(N, estim_error_tr, label="Trust region")
#ax1.plot(N, estim_error_mn, label="Monotone norm")
ax1.set_xlabel('k')
ax1.set_ylabel('Estimation error')
ax1.legend(loc='best')
ax1.set_title("Power series estimation error for different dimension k")
plt.savefig("figures/error_"+fig_name+".png", format="png")

fig2, ax2 = plt.subplots()
ax2.plot(N, iters_tr, label="Trust region")
#ax2.plot(N, iters_mn, label="Monotone norm")
ax2.set_xlabel('k')
ax2.set_ylabel('Iterations')
ax2.legend(loc='best')
ax2.set_title("Iterations for different dimension k")
plt.savefig("figures/iterations_"+fig_name+".png", format="png")
"""

"""
f_first = lambda th, y: f(th) + np.dot(grad(th), y-th)
f_second = lambda th, y: f(th) + np.dot(grad(th), y-th) + 0.5*np.dot(hess(th), (y-th)**2)
f_cubic = lambda th, y, mu: f(th) + np.dot(grad(th), y-th) + 0.5*np.dot(hess(th), (y-th)**2) + mu/6*(np.linalg.norm(y-th)**3)

dumm = np.ones(theta.shape)

if m==1:
    dumm = np.ones((1, 1))

    T = np.arange(-10, 10, 0.1)
    f_t = np.array([f(t*dumm) for t in T])
    f_t_first = np.array([f_first(dumm, t*dumm) for t in T])
    f_t_first = f_t_first.reshape((f_t_first.shape[0], 1))
    f_t_second = np.array([f_second(dumm, t*dumm) for t in T])
    f_t_second = f_t_second.reshape((f_t_second.shape[0], 1))
    f_t_cubic_1 = np.array([f_cubic(dumm, t*dumm, 1) for t in T])
    f_t_cubic_1 = f_t_cubic_1.reshape((f_t_cubic_1.shape[0], 1))
    f_t_cubic_2 = np.array([f_cubic(dumm, t*dumm, 10) for t in T])
    f_t_cubic_2 = f_t_cubic_2.reshape((f_t_cubic_2.shape[0], 1))
    f_t_cubic_3 = np.array([f_cubic(dumm, t*dumm, 100) for t in T])
    f_t_cubic_3 = f_t_cubic_3.reshape((f_t_cubic_3.shape[0], 1))
    f_t_cubic_4 = np.array([f_cubic(dumm, t*dumm, 1000) for t in T])
    f_t_cubic_4 = f_t_cubic_4.reshape((f_t_cubic_4.shape[0], 1))

    plt.figure()
    plt.axis([-10, 10, 0, 1])
    plt.plot(T, f_t_cubic_1, 'g', T, f_t_cubic_2, 'r', T, f_t_cubic_3, 'y', T, f_t_cubic_4, 'm', T, f_t, 'b')#, T, f_t_first, 'y', T, f_t_second, 'g')
    plt.show()
"""