from rllab_maml.envs.mujoco.hopper_env import HopperEnv
from rllab_maml.core.serializable import Serializable
from sandbox.jonas.envs.mujoco.base_env_rand_param import BaseEnvRandParams
from rllab_maml.misc import logger
from rllab_maml.misc.overrides import overrides
from sandbox.jonas.envs.helpers import get_all_function_arguments
from rllab_maml.envs.base import Step

import numpy as np


class HopperEnvMAMLRandParams(BaseEnvRandParams, HopperEnv, Serializable):

    FILE = 'hopper.xml'

    def __init__(self, *args, log_scale_limit=2.0, fix_params=False, rand_params=BaseEnvRandParams.RAND_PARAMS, random_seed=None, **kwargs):
        """
        Half-Cheetah environment with randomized mujoco parameters
        :param log_scale_limit: lower / upper limit for uniform sampling in logspace of base 2
        :param random_seed: random seed for sampling the mujoco model params
        :param fix_params: boolean indicating whether the mujoco parameters shall be fixed
        :param rand_params: mujoco model parameters to sample
        """

        args_all, kwargs_all = get_all_function_arguments(self.__init__, locals())
        BaseEnvRandParams.__init__(*args_all, **kwargs_all)
        HopperEnv.__init__(self, *args, **kwargs)
        Serializable.__init__(*args_all, **kwargs_all)

    @overrides
    def step(self, action):
        self.forward_dynamics(action)
        next_obs = self.get_current_obs()
        lb, ub = self.action_bounds
        scaling = (ub - lb) * 0.5
        vel = self.get_body_comvel("torso")[0]
        reward = vel + self.alive_coeff - \
            0.5 * self.ctrl_cost_coeff * np.sum(np.square(action / scaling))
        state = self._state
        notdone = np.isfinite(state).all() and \
            (np.abs(state[3:]) < 100).all() and (state[0] > .7) and \
            (abs(state[2]) < .2)
        done = not notdone
        return Step(next_obs, reward, done)

    @overrides
    def log_diagnostics(self, paths, prefix=''):
        progs = [
            path["observations"][-1][-4] - path["observations"][0][-4]
            for path in paths
        ]
        logger.record_tabular(prefix+'AverageForwardProgress', np.mean(progs))
        logger.record_tabular(prefix+'MaxForwardProgress', np.max(progs))
        logger.record_tabular(prefix+'MinForwardProgress', np.min(progs))
        logger.record_tabular(prefix+'StdForwardProgress', np.std(progs))

if __name__ == "__main__":
    env = HopperEnv()
    env.reset()
    print(env.model.body_mass)
    for _ in range(1000):
        env.render()
        env.step(env.action_space.sample())  # take a random action