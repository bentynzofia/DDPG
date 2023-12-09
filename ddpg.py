from collections import deque
import random

import torch.nn as nn

from params import *


class ReplayBuffer:
    replay_buffer = None

    def __init__(self):
        self.replay_buffer = deque(maxlen=MAX_BUFFER_SIZE)

    def store_transition(self, state, action, reward, next_state, done):
        if len(self.replay_buffer) >= MAX_BUFFER_SIZE:
            self.replay_buffer.popleft()

        self.replay_buffer.append(
            transition(state, action, reward, next_state, done)
        )

    def sample_batch(self, batch_size=BATCH_SIZE):
        return transition(
            *[torch.cat(i) for i in
              [*zip(*random.sample(self.replay_buffer, min(len(self.replay_buffer), batch_size)))]]
        )


class DDPG:
    def __init__(self, env, actor, critic, target_actor, target_critic):
        self.__env = env
        self.__actor = actor
        self.__critic = critic
        self.__target_actor = target_actor
        self.__target_critic = target_critic

        self.__replay_buffer = ReplayBuffer()
        self.__train_rewards_list = None

    def train(self, actor_optimizer, critic_optimizer, max_episodes=MAX_EPISODES):
        self.__train_rewards_list = []

        print("Starting Training:\n")
        for episode in range(max_episodes):
            state = self.__env.reset()
            state = torch.tensor(state[0], device=device, dtype=dtype).unsqueeze(0)
            episode_reward = 0

            for time in range(MAX_TIME_STEPS):
                action = self.__actor.select_action(state, self.__env)
                next_state, reward, terminated, truncated, _ = self.__env.step(action[0])
                done = terminated or truncated
                episode_reward += reward

                next_state = torch.tensor(next_state, device=device, dtype=dtype).unsqueeze(0)
                reward = torch.tensor([reward], device=device, dtype=dtype).unsqueeze(0)
                done = torch.tensor([done], device=device, dtype=dtype).unsqueeze(0)

                self.__replay_buffer.store_transition(state, action, reward, next_state, done)
                state = next_state
                sample_batch = self.__replay_buffer.sample_batch(BATCH_SIZE)

                with torch.no_grad():
                    target = sample_batch.reward + \
                             (1 - sample_batch.done) * GAMMA * \
                             self.__target_critic.forward(sample_batch.next_state,
                                                          self.__target_actor(sample_batch.next_state))

                critic_loss = nn.MSELoss()(
                    target, self.__critic.forward(sample_batch.state, sample_batch.action)
                )

                critic_optimizer.zero_grad()
                critic_loss.backward()
                critic_optimizer.step()

                actor_loss = -1 * torch.mean(
                    self.__critic.forward(sample_batch.state, self.__actor(sample_batch.state))
                )

                actor_optimizer.zero_grad()
                actor_loss.backward()
                actor_optimizer.step()

                for actor_param, target_actor_param in zip(self.__actor.parameters(), self.__target_actor.parameters()):
                    target_actor_param.data = POLYAK * actor_param.data + (
                            1 - POLYAK) * target_actor_param.data

                for critic_param, target_critic_param in zip(self.__critic.parameters(),
                                                             self.__target_critic.parameters()):
                    target_critic_param.data = POLYAK * critic_param.data + (
                            1 - POLYAK) * target_critic_param.data

                if done:
                    print(
                        "Completed episode {}/{}".format(
                            episode + 1, MAX_EPISODES
                        )
                    )
                    break

            self.__train_rewards_list.append(episode_reward)

        self.__env.close()

    def get_reward_list(self):
        reward_list = self.__train_rewards_list
        return reward_list
