 
## Simple 1D model for ignition

The breakdown of a dielectric medium between two conductors begins at the atomic scale. Under an applied electric field, free electrons in the medium are accelerated, gaining kinetic energy. When these electrons collide with atoms or molecules, they can ionize them if they have sufficient energy, releasing additional electrons. The probability of an electron gaining enough energy to cause ionization depends on the local electric field strength and the electron's mean free path between collisions.

What makes this process inherently stochas  tic is the random nature of these initial electron-atom collisions and the subsequent ionization events. The presence of impurities, local field variations, and thermal fluctuations all influence where and when the initial breakdown occurs. This microscopic randomness manifests as macroscopic uncertainty in the breakdown timing and location.

### First Basic Model: 1D uniform breakdown

For our first implementation, we'll create a simplified 1D model that captures this fundamental stochasticity. The model makes the following assumptions:

1. The ignition process is a stochastic process that is influenced by three main factors:
   - The voltage $V$ between the wire and workpiece
   - The distance $d$ between them, which determines the electric field strength
   - The dielectric gap properties (e.g., dielectric constant, conductivity, impurities...)

2. After a voltage is applied between the electrodes, an electric field is established in the gap. After a certain time (normally ignition delay time 
 $\tau_{\text{D}}$), the dielectric breaks down and a spark is formed and a conductive path is established between the wire and the workpiece at a certain location sampled from a uniform probability distribution.

3. The spark lasts until the generator stops the current.

4. If there is contact between the wire and the workpiece, a short circuit is formed immediately after the voltage is applied at the contact point.

### Implementation

Our simulation occurs in discrete time steps of $\tau = 1 \mu s$. At each time step, we will update the ignition variables based on the probability of ignition. 

First, we will check for short circuits. If the wire is in contact with the workpiece, we set the ignition state to short circuit -- in more advanced models, we will also include stochastic short circuit events due to debris in the cavity.

If there is no short circuit, we will sample from a probability distribution to determine if ignition occurs in this time step. If ignition occurs, we will set the ignition state to spark formation and sample the location of the spark along the y-axis.

What probability distribution should we use to model the ignition process? 

While it's possible to sample the total ignition delay time $\tau_D$ based on the wire-workpiece distance [cite paulo paper], we need to calculate the probability of ignition occurring in the next timestep given that it hasn't occurred yet.

> [!note]
> We make the following approximation:
> $$d(t) \approx d(t_0) \quad \forall t \in [t_0, t_0 + \tau_D]$$
> where $d(t)$ is the gap distance at time $t$, $t_0$ is the time when the voltage was raised, and $\tau_D$ is the ignition delay time.
> 
> This approximation is justified by the significant difference in timescales:
> - Servo movements: $\mathcal{O}(10^{-3})$ seconds
> - Ignition delay time: $\mathcal{O}(10^{-5})$ seconds


 This is:

$$P(\text{ignition at } \tau = \tau_D \mid \text{no ignition for } \tau < \tau_D)$$ 

where $\tau = 0$ corresponds to the time when the voltage was raised

This gives us the instantaneous probability of spark formation at the current time-step, conditioned on the fact that no spark has formed in previous time-steps.

> [!note]
> This is known in survival analysis as the hazard function or hazard rate - the probability of failure (in our case, ignition) occurring at time $t$, given that it has not occurred before $t$. The dielectric breakdown can be understood as a type of failure - the failure of the dielectric medium to maintain its insulating properties.

### Bayesian Calculation of Ignition Probability

Let's derive the hazard function - the probability of ignition occurring at the current simulation timestep given that it hasn't occurred yet. We start with a probability mass function (PMF) for the ignition delay time $\tau_D$:

$$P(\tau_D = t) = p(t)$$

where $p(t)$ is the PMF of the ignition delay time occurring at time $t$.

Using Bayes' theorem:
$$P(A|B) = \frac{P(B|A)P(A)}{P(B)}$$

Let's define:
- Event $A$: "ignition occurs at current time $\tau$"
- Event $B$: "no ignition has occurred before time $\tau$"

The hazard function $h(\tau)$ is then:

$$h(\tau) = P(A|B) = \frac{P(B|A)P(A)}{P(B)}$$

We can determine each term:
1. $P(A) = p(\tau)$ - probability of ignition occurring exactly at current time $\tau$
2. $P(B|A) = 1$ since if ignition occurs at current time $\tau$, there must be no ignition before $\tau$
3. $P(B) = 1 - F(\tau)$ where $F(\tau)$ is the cumulative distribution function (CDF) representing the probability of ignition occurring at any time before $\tau$

Therefore, our discrete hazard function is:

$$h(\tau) = \frac{p(\tau)}{1 - F(\tau)}$$

This gives us the probability of ignition occurring at the current simulation timestep $\tau$, given that no ignition has occurred in previous timesteps. We can use this expression directly in our discrete-time simulation to determine if ignition occurs at each timestep.


### Example: Exponential Ignition Delay Time

A common assumption is that the ignition delay time follows an exponential distribution. This is justified by the memoryless property of the exponential distribution, which aligns with the physical understanding that the probability of breakdown depends primarily on the current conditions rather than the history.

For an exponential distribution with rate parameter $\lambda$, we have:

- PMF: $p(\tau) = \lambda e^{-\lambda \tau}$
- CDF: $F(\tau) = 1 - e^{-\lambda \tau}$

Substituting into our hazard function:

$$h(\tau) = \frac{p(\tau)}{1 - F(\tau)} = \frac{\lambda e^{-\lambda \tau}}{e^{-\lambda \tau}} = \lambda$$

This gives us a constant hazard rate $\lambda$, meaning the probability of ignition in the next timestep (given no previous ignition) remains constant. This is a useful simplification for initial modeling, though real systems may show more complex time dependencies.

The rate parameter $\lambda$ typically depends on various factors:
- Gap distance between wire and workpiece: $\lambda(d)$
- Dielectric fluid properties (temperature, contamination, ionization)
- Applied voltage
- Previous discharge history

In practice, $\lambda$ can be determined experimentally from experimental data.

### Fitting lambda to experimental data

We have performed experiments to measure the breakdown delay time CDF for a set of different gap distances $\{d_1, d_2, ..., d_n\}$. Then we can use a simple interpolation method (e.g. polynomial interpolation) to fit the rate parameter $\lambda(d)$ as a function of the gap distance and use this in our simulation.

### Non-Markovian ignition models

If the distribution is not exponential (e.g., Weibull), the hazard function becomes time-dependent, indicating that the breakdown process has memory. For example, with a Weibull distribution with shape parameter $k$ and scale parameter $\lambda$, we have:

- PMF: $p(\tau) = \frac{k}{\lambda} (\frac{\tau}{\lambda})^{k-1} e^{-(\tau/\lambda)^k}$
- CDF: $F(\tau) = 1 - e^{-(\tau/\lambda)^k}$

This gives us a time-dependent hazard function:

$$h(\tau) = \frac{k}{\lambda} (\frac{\tau}{\lambda})^{k-1}$$

When $k > 1$, the hazard rate increases with $\tau$, suggesting that the probability of breakdown increases the longer the voltage has been applied. This could model effects like progressive ionization of the dielectric fluid or charge accumulation. When $k < 1$, the hazard rate decreases with $\tau$, which might represent scenarios where initial conditions are more favorable for breakdown.

This non-Markovian behavior means that the state space must be augmented with time information ($\tau_D$ in our state vector) to maintain the Markov property in the simulation.



