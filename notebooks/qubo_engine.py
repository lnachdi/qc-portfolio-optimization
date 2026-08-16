import numpy as np
import dimod
from itertools import product


def build_qubo_matrix(mean_returns,cov_matrix,lambda_risk,lambda_budget,lambda_sector,sector_map,sector_cap,n_assets,n_bits):
    mean_returns = np.asarray(mean_returns)
    cov_matrix= np.asarray(cov_matrix)

    N=n_assets*n_bits
    Q = np.zeros((N,N))

    #Returns term: maximize return= minimize negative return
    for i in range(n_assets):
        for k in range(n_bits):
            idx = i * n_bits + k
            weight_contribution = (2**k) /(2**n_bits -1)
            Q[idx,idx] -= mean_returns[i] * weight_contribution

    #Risk term: lambda_risk * w^T * sigma * w converted to binary
    for i in range(n_assets):
        for j in range(n_assets):
            for k in range(n_bits):
                for m in range(n_bits):
                    row = i * n_bits + k
                    col = j * n_bits + m
                    wi = (2**k) /(2**n_bits -1)
                    wj = (2**m)/(2**n_bits -1)
                    Q[row,col] += lambda_risk * cov_matrix[i,j] * wi * wj

    #Budget constraints: (sum_i w_i -1)^2 expanded into binary using binary idempotency so x_i^2=x_i
    for i in range(n_assets):
        for k in range(n_bits):
            idx= i *n_bits + k
            wi = (2**k)/ (2**n_bits-1)
            Q[idx,idx] += lambda_budget * wi * (wi-2) # diagonal terms

            for j in range(n_assets):
                for m in range(n_bits):
                    col = j*n_bits + m
                    if col> idx:
                        wj = (2**m)/(2**n_bits -1)
                        Q[idx,col] += 2 * lambda_budget * wi * wj

    # Sector cap constraint: upstream penalty
    # implemented as a quadratic penalty added to Q
    # for each sector s: (sum_{i in s} w_i - cap_s)^2 if sum > cap_s, else 0
    sectors = set(sector_map.values())
    for sector in sectors:
        sector_assets = [i for i, s in sector_map.items() if s == sector]
        for i in sector_assets:
            for k in range(n_bits):
                idx = i*n_bits +k
                wi = (2**k)/(2**n_bits -1)
                Q[idx,idx] += lambda_sector * wi * (wi -2 * sector_cap)
                for j in sector_assets:
                    for m in range(n_bits):
                        col= j*n_bits + m
                        if col>idx:
                            wj = (2**m)/(2**n_bits-1)
                            Q[idx,col]+= 2 * lambda_sector * wi * wj
    return Q
            

def brute_force_qubo(Q): #solves by searching over all 2^N binary strings
    N = Q.shape[0]
    best_energy = np.inf
    best_x = None

    for bits in product([0,1], repeat=N):
        x=np.array(bits)
        energy = x@Q@x
        if energy < best_energy:
            best_energy = energy
            best_x = x.copy()
    return best_x, best_energy

# x_brute,energy_brute = brute_force_qubo(Q)
# print(f"Brute force optimal energy: {energy_brute: .5f}")


def simulated_annealing_qubo(Q, num_reads=1000, num_sweeps=1000):
    N = Q.shape[0]
    Q_dict={}
    for i in range(N):
        for j in range(i,N):
            if i == j:
                val = Q[i,j]
            else:
                val = Q[i,j] + Q[j,i] # allows to fold the lower triange in and don't discard it
            if val != 0:
                Q_dict[(i,j)] = val
                
            # if Q[i,j]!=0:
            #     Q_dict[(i,j)] = Q[i,j]

    bqm = dimod.BinaryQuadraticModel.from_qubo(Q_dict)
    sampler = dimod.SimulatedAnnealingSampler()
    response = sampler.sample(bqm,num_reads=num_reads,num_sweeps=num_sweeps)

    best_sample=response.first.sample
    x_sa = np.array([best_sample[i] for i in range(N)])
    energy=x_sa@Q@x_sa
    return x_sa,energy

def decode_weights(x,n_assets,n_bits):
    return np.array([sum((2**k)* x[i*n_bits +k] for k in range(n_bits)) / (2**n_bits -1) for i in range(n_assets)])