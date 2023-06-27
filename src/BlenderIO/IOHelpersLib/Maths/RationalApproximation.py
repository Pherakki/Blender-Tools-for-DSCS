import numpy as np


def rational_approx_brute_force(numbers, max_denominator):
    best_denominator = 1
    best_residual = float('inf')
    fast_exit_threshold = 1/max_denominator
    
    # Offload input list to numpy immediately so we don't
    # make loads of useless copies
    nums = np.array(numbers)
    
    for denominator in range(1, max_denominator + 1):
        # Compute worst-approximated number using this denominator
        approximants = nums*denominator
        int_approximations = np.rint(approximants)
        residual = np.max(np.abs(approximants-int_approximations))
        
        # Update results if it's better than the previous worst
        if residual < best_residual:
            best_denominator = denominator
            best_residual = residual
        
        # Check if the residuals will all be indistinguishable from a "better"
        # approximation at the requested level of precision
        if residual < fast_exit_threshold:
            break
    
    # Return list of numerators + shared denominator
    return [int(round(n*best_denominator, 0)) for n in numbers], best_denominator
