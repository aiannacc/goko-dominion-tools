import math
import scipy.optimize
import trueskill
from trueskill import Rating
from gdt.ratings.result import Result


# A distance metric between two ratings
def distance(r1, r2):
    return math.sqrt((r1.mu-r2.mu)**2 + (r1.sigma-r2.sigma)**2)

# Distance between predicted and actual updated rating,
# as a function of rating system parameters (beta, tau, dp)
def update_error(x, rA1, rA2, rB1, rB2, scoreA):
    (beta, tau, dp) = x
    goko_env = trueskill.TrueSkill(beta=beta, tau=tau,
                                   draw_probability=dp,
                                   backend='mpmath')
    draw_m = trueskill.calc_draw_margin(goko_env.draw_probability,
                                        2, goko_env)
    (rAx, rBx) = Result(rA1, rB1, goko_env, scoreA, draw_m).post_game_ratings()
    error = distance(rAx, rA2)**2 + distance(rBx, rB2)**2
    return math.sqrt(error)


# Distance between predicted and actual updated rating,
# as a function of new player rating (mu_0, sigma_0)
def init_error(args, beta, tau, dp, rA2, rB1, rB2, scoreA):
    (mu_0, sigma_0) = args
    rA1 = Rating(mu_0, sigma_0)
    return update_error((beta, tau, dp), rA1, rA2, rB1, rB2, scoreA)


if __name__ == '__main__':
    # Game data for two experienced players with disparate ratings
    # Initial ratings
    rA1 = Rating(6809.432229001433, 261.9561557935375)
    rB1 = Rating(3846.1388816353556, 1061.7646611437733)
    scoreA = 1
    # Post-game ratings
    rA2 = Rating(6815.568466240228, 262.8624518211366)
    rB2 = Rating(3746.361372235074, 1026.5999719019248)

    print()
    print('Estimating update parameters: beta, tau, draw_prob')
    # Determine beta, tau, and draw_probability
    starting_guesses = (1400, 30, .07)
    opt = scipy.optimize.minimize(update_error, x0=starting_guesses,
                                  args=(rA1, rA2, rB1, rB2, scoreA),
                                  tol=0.000001)
    print('Residual Error: %6.4f ' % (opt.fun))
    (beta, tau, dp) = opt.x


    # Game data for one experienced players and one newbie
    # Initial ratings
    rA1 = None  # Unknown values
    rA2 = Rating(7417.093503590504, 1722.2897943089736)
    scoreA = 1
    # Post-game ratings
    rB1 = Rating(6827.465878433451, 262.4592609358525)
    rB2 = Rating(6801.097762744435, 263.14332861731685)

    print()
    print('Estimating initialization paramters: mu0, sigma0')
    starting_guesses = (8250, 2750)
    args = (beta, tau, dp, rA2, rB1, rB2, scoreA)
    opt = scipy.optimize.minimize(init_error, x0=starting_guesses,
                                  args=args, tol=.000000001)
    print('Residual Error: %6.4f ' % (opt.fun))
    (mu0, sigma0) = opt.x

    print()
    print('Error-minimizing Parameters:')
    print('mu0:       %7.2f' % mu0)
    print('sigma0:    %7.2f' % sigma0)
    print('beta:      %7.2f' % beta)
    print('tau:       %7.2f' % tau)
    print('draw_prob: %7.2f' % dp)

    # Test it on a third game
    goko_env = trueskill.TrueSkill(mu=mu0, sigma=sigma0,
                                   beta=beta, tau=tau,
                                   draw_probability=dp,
                                   backend='mpmath')
 
    # Game data for two experienced players with similar ratings
    # Initial ratings
    print()
    print('Testing Parameters on a different game:')
    rA1 = Rating(6789.036432492558, 262.8329415491707)
    rB1 = Rating(7108.43720451577, 266.9581590879031)
    scoreA = 1
    # Post-game ratings
    rA2 = Rating(6822.354187108161, 262.6577478580567)
    rB2 = Rating(7074.076798465825, 266.6845904766116)

    res = Result(rA1, rB1, goko_env, scoreA,
                 trueskill.calc_draw_margin(goko_env.draw_probability,
                                            2, goko_env))
    (rAx, rBx) = res.post_game_ratings()
    error = distance(rA2, rAx)**2 + distance(rB2, rBx)**2
    print('Initial ratings:')
    print(' A: %7.2f +/- %5.2f' % (rA1.mu, rA1.sigma))
    print(' B: %7.2f +/- %5.2f' % (rB1.mu, rB1.sigma))
    print('Expected post-game ratings:')
    print(' A: %7.2f +/- %5.2f' % (rAx.mu, rAx.sigma))
    print(' B: %7.2f +/- %5.2f' % (rBx.mu, rBx.sigma))
    print('Observed post-game ratings:')
    print(' A: %7.2f +/- %5.2f' % (rA2.mu, rA2.sigma))
    print(' B: %7.2f +/- %5.2f' % (rB2.mu, rB2.sigma))
    print('Rating prediction error: %6.4f' % error)
