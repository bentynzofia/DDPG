import gymnasium as gym
import torch
import json
import sys

from torch.optim import Adam
import matplotlib.pyplot as plt

from GymnasiumDDPGTrainer import Actor, Critic

from GymnasiumDDPGTrainer.DDPG.DDPG import DDPG
from GymnasiumDDPGTrainer.OUNoise import OUNoise


def main(args):
    settingsFile = open("settings.json")
    settings = json.load(settingsFile)
    settingsFile.close()
    assert isinstance(settings, dict)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    environment = gym.make("Ant-v4")

    dtype = torch.float32

    noise = OUNoise(environment.action_space.shape[0], dtype="float32")

    actor_net = Actor.ActorNet(
        environment.observation_space.shape[0], environment.action_space.shape[0], device, dtype, noise=noise
    )
    critic_net = Critic.CriticNet(
        environment.observation_space.shape[0], environment.action_space.shape[0], device, dtype
    )

    actor_optimizer = Adam(actor_net.parameters(), lr=settings["HYPERPARAMS"]["ACTOR_LR"])
    critic_optimizer = Adam(
        critic_net.parameters(), lr=settings["HYPERPARAMS"]["CRITIC_LR"],
        weight_decay=settings["HYPERPARAMS"]["WEIGHT_DECAY"]
    )

    target_actor_net = Actor.ActorNet(
        environment.observation_space.shape[0], environment.action_space.shape[0], device, dtype, noise=noise
    )
    target_critic_net = Critic.CriticNet(
        environment.observation_space.shape[0], environment.action_space.shape[0], device, dtype
    )

    target_actor_net.load_state_dict(actor_net.state_dict())
    target_critic_net.load_state_dict(critic_net.state_dict())

    agent = DDPG(
        environment, actor_net, critic_net, target_actor_net, target_critic_net, settings["HYPERPARAMS"], device
    )
    agent.train(actor_optimizer, critic_optimizer, max_episodes=settings["HYPERPARAMS"]["MAX_EPISODES"])

    rew_list = agent.get_reward_list()
    plt.plot(rew_list)

    actor_error_hist, critic_error_hist = agent.get_losses()
    fig, ax = plt.subplots()
    ax.plot(actor_error_hist, label="Actor error")
    ax.plot(critic_error_hist, label="Critic error")

    ax.set_xlabel("Iteration")
    ax.set_ylabel("Error value")
    ax.legend()

    fig.savefig("400_layer_both.png")
    plt.show()


if __name__ == "__main__":
    main(sys.argv)
