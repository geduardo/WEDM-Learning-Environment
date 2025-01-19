Wire EDM is a **extremely complex** physical process and there are many aspects to control. I think a simulation from a physics point of view is useless. It's just too complex. However, I think there's space for a simulation from a "probabilistic" point of view to test different control strategies and learning algorithms. This is, a simulation of the process aimed at testing different learning control strategies.

## Scope of the simulation

- Only straight cuts
- Only main cut 
- Focused on control: we only will simulate the parts of the process that are relevant for control.
    - Surface finish --> not relevant for control --> not simulated
    - Wire breakage --> relevant for control --> simulated

The goal of the simulation is not to be a faithful representation of the physical process, but to be a playground realistic enough so that we can test different control strategies and learning algorithms to accelerate development of control systems for Wire EDM.

### Trade-off between realism and speed/simplicity

There's always a trade-off between realism, computational complexity, speed, and ease of implementation. In this simulation, we will often lean towards speed and simplicity. For example:

- We could do detailed tensile and annealing simulations for wire breaking
- We could use SPH simulations for dielectric fluid flow within the cavity
- We could solve Maxwell's equations to calculate the electric field distribution for each wire/surface geometry

However, these approaches would be:
1. Computationally expensive
2. Of dubious accuracy given the complexity of the real process
3. Difficult to tune and validate

Instead, we will opt for easily tuneable methods that probabilistically approximate reality through testing. The focus is on capturing the key behaviours and relationships that matter for control, rather than exact physical modelling.

This doesn't mean we completely discard more advanced modelling techniques - they could potentially be used to develop fast surrogate models that maintain reasonable accuracy while being computationally efficient. For example, we might use tensile simulations to better understand wire breakage under different thermal and mechanical loads, but then approximate those results with simpler models. 
## Module based simulation

I want the simulation to be developed gradually, starting with simple models for each element of the process and then adding complexity. This way, we can test the effect of each element in the simulation update the simulation as new knowledge is acquired. 

To achieve this, I will use a modular approach to the simulation. Each module will be responsible for simulating a specific part of the process. Even though the modules are interconnected, they can be integrated mainly in a sequential way. 

There are 5 main modules in the simulation:

- [[Ignition module]]: This module is responsible for simulating the ignition of the spark. It will be based on a probabilistic model of the ignition process.
- [[Material removal module]]: This module is responsible for simulating the material removal process. It will be based on a probabilistic model of the material removal process.
- [[Dielectric module]]: This module is responsible for simulating the dielectric fluid. After a succesful ignition, the conditions of the dielectric fluid change and this affects the process.
- [[Wire status module]]: This module focuses on the wire's physical state:
    - Temperature distribution and thermal effects
    - Material properties and stress state
    - Breakage conditions and probability
- [[Mechanics module]]: This module handles the motion and dynamics:
    - Machine kinematics and servo control
    - Wire guide positions and movement
    - Wire vibrations and disturbances
    - System-level mechanical noise and disturbances
    
![[Pasted image 20241211232213.png]]

## Discrete time and state based simulation

## Temporal Discretization and State-Space Representation

The simulation adopts a discrete-time formalism, advancing in fixed increments of $\tau = 1 \mu s$. This temporal resolution is selected to satisfy two competing constraints:

1. **Dynamical Fidelity:** $\tau$ must be sufficiently small to capture the fastest dynamics that significantly influence the control performance.
2. **Computational Tractability:** Conversely, $\tau$ must be large enough to ensure that the computational cost associated with each time step remains within acceptable limits, permitting real-time or near-real-time simulation.

The system's evolution is modelled as a Markov Decision Process (MDP). This framework characterizes the system at any time $t$ by a state vector $\mathbf{s}_t \in S$, where $S$ denotes the complete [[state space (Wire EDM simulation)]]. The state vector encapsulates all variables necessary to fully specify the instantaneous condition of the Wire EDM process.

The system's dynamics are governed by probabilistic transitions between states. Given the current state $\mathbf{s}_t$, the probability of transitioning to state $\mathbf{s}_{t+1}$ at the next time step is given by the conditional probability distribution:

$$P(\mathbf{s}_{t+1}|\mathbf{s}_t)$$

Each module contributes to this overall transition probability by defining a subset of state variables and specifying the probabilistic laws governing their evolution. These modular contributions are then composed to yield the complete system dynamics- The temporal evolution of the system, therefore, emerges as a sequence of probabilistic transitions in the state space $S$, driven by the coupled dynamics of the individual modules.


