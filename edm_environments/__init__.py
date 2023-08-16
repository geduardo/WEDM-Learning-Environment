from gymnasium.envs.registration import register

register(
     id="edm_environments/WireEDM-v0",
     entry_point="edm_environments.envs:WireEDMEnv"
)