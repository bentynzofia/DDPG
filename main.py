import gymnasium as gym

from torch.optim import Adam
import matplotlib.pyplot as plt

from params import MAX_EPISODES, LR
import ddpg as ddpg
import actor as actor
import critic as critic

environment = gym.make("MountainCarContinuous-v0")

actor_net = actor.ActorNet(environment.observation_space.shape[0], 64)
critic_net = critic.CriticNet(environment.observation_space.shape[0], environment.action_space.shape[0], 64)

actor_optimizer = Adam(actor_net.parameters(), lr=LR)
critic_optimizer = Adam(critic_net.parameters(), lr=LR)

target_actor_net = actor.ActorNet(environment.observation_space.shape[0], 64)
target_critic_net = critic.CriticNet(environment.observation_space.shape[0], environment.action_space.shape[0], 64)

target_actor_net.load_state_dict(actor_net.state_dict())
target_critic_net.load_state_dict(critic_net.state_dict())

agent = ddpg.DDPG(environment, actor_net, critic_net, target_actor_net, target_critic_net)
agent.train(actor_optimizer, critic_optimizer, max_episodes=MAX_EPISODES)

rew_list = agent.get_reward_list()
plt.plot(rew_list)
plt.show()
