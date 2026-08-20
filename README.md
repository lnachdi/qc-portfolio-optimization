# Quantum-Classical Portfolio Optimization

A research extension of classical mean-variance portfolio optimization into a QUBO/quantum framework, benchmarking QAOA against classical and heuristic solvers with a focus on how portfolio constraints are coded into the optimization objective. Thisproject asks the question of if sector diversification constraints are encoded directly into QUBO's penalty structure (upstream rather than filtered downstream) how does it affect solution quality, constraint satisfaction, and discretization behaviour?

## Overview
This project reformulates the Markowitz portfolio optimization problem (see the 'classical portfolio optimization engine' repo) as a QUBO problem solved via QAOA. Continuous asset weights are discretized through a binary fixed-point encoding, and constraints, including a sector diversification cap, are encoded as penalty terms within the QUBO objective (designed as an 'upstream' penalty).
Three solution methods are implemented and benchmarked against each other on identical problem instances: brute-force serach, classical simulated annealing, and QAOA which is run on PennyLane's quantum simulator. A constrained continuous Markowitz solver is also included as a non-discretized point of reference.
Tested across 3 different qubit instances (N=6,9,10).

## Results
![Penalty Sensitivity Analysis](penalty_sensitivity_2bit.png)
*Sector cap constraint violation and resulting Sharpe ratio as sector penalty strength increases, at 2-bit vs 3-bit weight discretization.*

## Key Findings (Based on N=9)

**Simulated annealing (SA) methods matched exact brute force optimum exactly** on the 3-asset, 9 qubit isntance (energy=-6.5297 for both methods, identical portfolio weights: AAPL: 14.29% MSFT: 42.86% GS: 42.86%) despite brute force checking all 512 combinations in 0.002 sec vs SA's 20 secs across 1000 reads. This confirms that SA reliably finds the true optimum at this problem scale and provides a validated heuristic baseline for comparison against QAOA.

**Coarse binary discretization produces step-function constraint behaviour** and not a smooth tradeoff. With 2-bit weight encoding the sector-cap constraint violation was fixed at exactly 0.0667 across all lambda from 0.1-200, and since the discretization grid had no achievable point close to the 0.6 cap there were only 2 feasible allocation levels: one far under, and one that violates, and no value of lambda in that range was large enough to force the solver off the high-return violating option.

**Increasing to 3-bits eliminated the violation fully (0.00 across all lambdas tested) but revealed another effect** that the symmetric squared penalty term still reshapes the solution even at zero violation. Because lambda*(sum(w_i) - cap)^2 penalizesdistance from the cap in both directions instead of just upstream, higher lambda pulled the solver toward the discretized point closest to the cap even once the point was already compliant which shifted the Sharpe from 0.6435 to 0.6559 at lambda>=5 even with no change in violation. 

**QAOA's raw expectation value wasn't anything exceptional, but the sampled measuremnets concentrated near the true optimum.**



