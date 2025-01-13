# State Space Representation

Our Wire EDM simulation operates within a state space $S \subset \mathbb{R}^N$, where each point $\mathbf{s}_t \in S$ represents the complete state of the simulated system at discrete time step $t$.

## Simulation Dynamics

The simulation advances through probabilistic state transitions governed by the transition probability function:

$$P(\mathbf{s}_{t+1}|\mathbf{s}_t, \boldsymbol{\theta}): S \times S \times \Theta \rightarrow [0,1]$$

where $\boldsymbol{\theta} \in \Theta$ represents the simulation parameters. The dimensionality $N$ of the state space depends on which simulation modules are active, with each component corresponding to a simulated physical quantity (see [[simulation variables]] for details).

## Computational Implementation

At each timestep, the simulation generates the next state by sampling from the transition probability distribution:

$$\mathbf{s}_{t+1} \sim P(\mathbf{s}_{t+1}|\mathbf{s}_t, \boldsymbol{\theta})$$

This sampling creates simulated trajectories that approximate the behavior of a real Wire EDM system.

## Modular Structure and Sequential Processing

The simulation is structured into five interconnected modules, each responsible for a specific aspect of the Wire EDM process:

1. Ignition Module: Models spark formation and short circuit events
2. Material Removal Module: Simulates the erosion process and workpiece geometry changes
3. Dielectric Module: Models fluid conditions, debris, and thermal effects
4. Wire Module: Tracks wire condition, thermal effects, and breakage probability
5. Mechanics Module: Handles machine kinematics, wire positioning, and mechanical dynamics

While these modules represent distinct physical aspects, their interactions are inherently coupled. The state vector reflects this structure and includes the servo action:

$$\mathbf{s}_t = [\mathbf{s}_{servo,t}, \mathbf{s}_{ignition,t}, \mathbf{s}_{removal,t}, \mathbf{s}_{dielectric,t}, \mathbf{s}_{wire,t}, \mathbf{s}_{mechanics,t}]$$

Due to the causal nature of the physical processes, the transition probability must be computed sequentially within each timestep, with each module depending on both the previous full state $\mathbf{s}_t$ and the partial updated state from preceding modules in timestep $t+1$:

1. Ignition Module:
   $$P(\mathbf{s}_{ignition,t+1}|\mathbf{s}_t, \boldsymbol{\theta}_{ignition})$$
   Determines spark events based on full previous state

2. Material Removal Module:
   $$P(\mathbf{s}_{removal,t+1}|\mathbf{s}_t, \mathbf{s}_{ignition,t+1}, \boldsymbol{\theta}_{removal})$$
   Updates workpiece geometry based on previous state and new ignition state

3. Dielectric Module:
   $$P(\mathbf{s}_{dielectric,t+1}|\mathbf{s}_t, \mathbf{s}_{ignition,t+1}, \mathbf{s}_{removal,t+1}, \boldsymbol{\theta}_{dielectric})$$
   Updates fluid properties based on previous state and new ignition/removal states

4. Wire Module:
   $$P(\mathbf{s}_{wire,t+1}|\mathbf{s}_t, \mathbf{s}_{ignition,t+1}, \mathbf{s}_{removal,t+1}, \mathbf{s}_{dielectric,t+1}, \boldsymbol{\theta}_{wire})$$
   Updates wire condition based on previous state and all new upstream states

5. Mechanics Module:
   $$P(\mathbf{s}_{mechanics,t+1}|\mathbf{s}_t, \mathbf{s}_{ignition,t+1}, \mathbf{s}_{removal,t+1}, \mathbf{s}_{dielectric,t+1}, \mathbf{s}_{wire,t+1}, \boldsymbol{\theta}_{mechanics})$$
   Updates machine state based on previous state and all new module states

The complete state transition probability can be expressed as the product of these conditional probabilities:

$$P(\mathbf{s}_{t+1}|\mathbf{s}_t, \boldsymbol{\theta}) = P(\mathbf{s}_{m,t+1}|\cdot) \cdot P(\mathbf{s}_{w,t+1}|\cdot) \cdot P(\mathbf{s}_{d,t+1}|\cdot) \cdot P(\mathbf{s}_{r,t+1}|\cdot) \cdot P(\mathbf{s}_{i,t+1}|\cdot)$$

where the conditioning arguments (denoted by $\cdot$) follow the dependencies outlined above. This sequential decomposition captures the physical causality of the Wire EDM process and allows for modular development and tuning of each simulation component.

Each module's transition probability combines deterministic and stochastic effects. For example, the Wire Module's probability distribution for wire breakage depends on the accumulated thermal stress, which is determined by the ignition outcomes.

## Parameters vs State Variables

The simulation framework uses two types of quantities:

1. State variables $\mathbf{s}_t \in S$ - The dynamic quantities updated each timestep based on our probabilistic models of Wire EDM physics

2. Simulation parameters $\boldsymbol{\theta} \in \Theta$ - The fixed configuration values that define how state transitions are calculated

The complete set of simulation parameters $\boldsymbol{\theta}$ is documented in [[simulation parameters]].