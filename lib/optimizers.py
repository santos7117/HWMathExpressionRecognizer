import theano
import theano.tensor as tensor

import numpy

profile = False

def itemlist(tparams):
    return [vv for kk, vv in tparams.items()]

def itemlist_name(tparams):
    return [kk for kk, vv in tparams.items()]

"""
General Optimizer Structure: (adadelta, adam, rmsprop, sgd)
Parameters
----------
    lr : theano shared variable
        learning rate, currently only necessaary for sgd
    tparams : OrderedDict()
        dictionary of shared variables {name: variable}
    grads : 
        dictionary of gradients
    inputs :
        inputs required to compute gradients
    cost : 
        objective of optimization
    hard_attn_up :
        additional updates required for hard attention mechanism learning 
Returns
-------
    f_grad_shared : compute cost, update optimizer shared variables
    f_update : update parameters
"""
# optimizers
# name(hyperp, tparams, grads, inputs (list), cost) = f_grad_shared, f_update
def adam(lr, tparams, grads, inp, cost):
    gshared = [theano.shared(p.get_value() * 0.,
                             name='%s_grad' % k)
               for k, p in tparams.items()]
    gsup = [(gs, g) for gs, g in zip(gshared, grads)]

    f_grad_shared = theano.function(inp, cost, updates=gsup, profile=profile)

    lr0 = 0.0002
    b1 = 0.1
    b2 = 0.001
    e = 1e-8

    updates = []

    i = theano.shared(numpy.float32(0.))
    i_t = i + 1.
    fix1 = 1. - b1**(i_t)
    fix2 = 1. - b2**(i_t)
    lr_t = lr0 * (tensor.sqrt(fix2) / fix1)

    for p, g in zip(list(tparams.values()), gshared):
        m = theano.shared(p.get_value() * 0.)
        v = theano.shared(p.get_value() * 0.)
        m_t = (b1 * g) + ((1. - b1) * m)
        v_t = (b2 * tensor.sqr(g)) + ((1. - b2) * v)
        g_t = m_t / (tensor.sqrt(v_t) + e)
        p_t = p - (lr_t * g_t)
        updates.append((m, m_t))
        updates.append((v, v_t))
        updates.append((p, p_t))
    updates.append((i, i_t))

    f_update = theano.function([lr], [], updates=updates,
                               on_unused_input='ignore', profile=profile)

    return f_grad_shared, f_update


def adadelta(lr, tparams, grads, inp, cost):
    zipped_grads = [theano.shared(p.get_value() * numpy.float32(0.),
                                  name='%s_grad' % k)
                    for k, p in tparams.items()]
    running_up2 = [theano.shared(p.get_value() * numpy.float32(0.),
                                 name='%s_rup2' % k)
                   for k, p in tparams.items()]
    running_grads2 = [theano.shared(p.get_value() * numpy.float32(0.),
                                    name='%s_rgrad2' % k)
                      for k, p in tparams.items()]

    zgup = [(zg, g) for zg, g in zip(zipped_grads, grads)]
    rg2up = [(rg2, 0.95 * rg2 + 0.05 * (g ** 2))
             for rg2, g in zip(running_grads2, grads)]

    f_grad_shared = theano.function(inp, cost, updates=zgup+rg2up,
                                    profile=profile)

    updir = [-tensor.sqrt(ru2 + lr) / tensor.sqrt(rg2 + lr) * zg
             for zg, ru2, rg2 in zip(zipped_grads, running_up2,
                                     running_grads2)]
    ru2up = [(ru2, 0.95 * ru2 + 0.05 * (ud ** 2))
             for ru2, ud in zip(running_up2, updir)]
    param_up = [(p, p + ud) for p, ud in zip(itemlist(tparams), updir)]

    f_update = theano.function([lr], [], updates=ru2up+param_up,
                               on_unused_input='ignore', profile=profile)

    return f_grad_shared, f_update


def rmsprop(lr, tparams, grads, inp, cost):
    zipped_grads = [theano.shared(p.get_value() * numpy.float32(0.),
                                  name='%s_grad' % k)
                    for k, p in tparams.items()]
    running_grads = [theano.shared(p.get_value() * numpy.float32(0.),
                                   name='%s_rgrad' % k)
                     for k, p in tparams.items()]
    running_grads2 = [theano.shared(p.get_value() * numpy.float32(0.),
                                    name='%s_rgrad2' % k)
                      for k, p in tparams.items()]

    zgup = [(zg, g) for zg, g in zip(zipped_grads, grads)]
    rgup = [(rg, 0.95 * rg + 0.05 * g) for rg, g in zip(running_grads, grads)]
    rg2up = [(rg2, 0.95 * rg2 + 0.05 * (g ** 2))
             for rg2, g in zip(running_grads2, grads)]

    f_grad_shared = theano.function(inp, cost, updates=zgup+rgup+rg2up,
                                    profile=profile)

    updir = [theano.shared(p.get_value() * numpy.float32(0.),
                           name='%s_updir' % k)
             for k, p in tparams.items()]
    updir_new = [(ud, 0.9 * ud - 1e-4 * zg / tensor.sqrt(rg2 - rg ** 2 + 1e-4))
                 for ud, zg, rg, rg2 in zip(updir, zipped_grads, running_grads,
                                            running_grads2)]
    param_up = [(p, p + udn[1])
                for p, udn in zip(itemlist(tparams), updir_new)]
    f_update = theano.function([lr], [], updates=updir_new+param_up,
                               on_unused_input='ignore', profile=profile)

    return f_grad_shared, f_update


def sgd(lr, tparams, grads, x, mask, y, cost):
    gshared = [theano.shared(p.get_value() * 0.,
                             name='%s_grad' % k)
               for k, p in tparams.items()]
    gsup = [(gs, g) for gs, g in zip(gshared, grads)]

    f_grad_shared = theano.function([x, mask, y], cost, updates=gsup,
                                    profile=profile)

    pup = [(p, p - lr * g) for p, g in zip(itemlist(tparams), gshared)]
    f_update = theano.function([lr], [], updates=pup, profile=profile)

    return f_grad_shared, f_update


def adadelta_weightnoise(lr, tparams_miu, tparams_sigma, grads_miu, grads_sigma, inp, cost):
    zipped_grads_miu = [theano.shared(p.get_value() * numpy.float32(0.),
                                  name='%s_grad' % k)
                    for k, p in tparams_miu.items()]
    running_up2_miu = [theano.shared(p.get_value() * numpy.float32(0.),
                                 name='%s_rup2' % k)
                   for k, p in tparams_miu.items()]
    running_grads2_miu = [theano.shared(p.get_value() * numpy.float32(0.),
                                    name='%s_rgrad2' % k)
                      for k, p in tparams_miu.items()]
    zipped_grads_sigma = [theano.shared(p.get_value() * numpy.float32(0.),
                                  name='%s_grad' % k)
                    for k, p in tparams_sigma.items()]
    running_up2_sigma = [theano.shared(p.get_value() * numpy.float32(0.),
                                 name='%s_rup2' % k)
                   for k, p in tparams_sigma.items()]
    running_grads2_sigma = [theano.shared(p.get_value() * numpy.float32(0.),
                                    name='%s_rgrad2' % k)
                      for k, p in tparams_sigma.items()]
    zgup_miu = [(zg, g) for zg, g in zip(zipped_grads_miu, grads_miu)]
    rg2up_miu = [(rg2, 0.95 * rg2 + 0.05 * (g ** 2))
             for rg2, g in zip(running_grads2_miu, grads_miu)]
    zgup_sigma = [(zg, g) for zg, g in zip(zipped_grads_sigma, grads_sigma)]
    rg2up_sigma = [(rg2, 0.95 * rg2 + 0.05 * (g ** 2))
             for rg2, g in zip(running_grads2_sigma, grads_sigma)]
    f_grad_shared = theano.function(inp, cost, updates=zgup_miu+rg2up_miu+zgup_sigma+rg2up_sigma,
                                    profile=profile)

    updir_miu = [-tensor.sqrt(ru2 + lr) / tensor.sqrt(rg2 + lr) * zg
             for zg, ru2, rg2 in zip(zipped_grads_miu, running_up2_miu,
                                     running_grads2_miu)]
    ru2up_miu = [(ru2, 0.95 * ru2 + 0.05 * (ud ** 2))
             for ru2, ud in zip(running_up2_miu, updir_miu)]
    param_up_miu = [(p, p + ud) for p, ud in zip(itemlist(tparams_miu), updir_miu)]

    f_update_miu = theano.function([lr], [], updates=ru2up_miu+param_up_miu,
                               on_unused_input='ignore', profile=profile)

    updir_sigma = [-tensor.sqrt(ru2 + lr) / tensor.sqrt(rg2 + lr) * zg
             for zg, ru2, rg2 in zip(zipped_grads_sigma, running_up2_sigma,
                                     running_grads2_sigma)]
    ru2up_sigma = [(ru2, 0.95 * ru2 + 0.05 * (ud ** 2))
             for ru2, ud in zip(running_up2_sigma, updir_sigma)]
    param_up_sigma = [(p, p + ud) for p, ud in zip(itemlist(tparams_sigma), updir_sigma)]

    f_update_sigma = theano.function([lr], [], updates=ru2up_sigma+param_up_sigma,
                               on_unused_input='ignore', profile=profile)
    return f_grad_shared, f_update_miu, f_update_sigma

