## Dielectric Module

The dielectric module is responsible for simulating the state and behavior of the dielectric fluid in the inter-electrode gap. The dielectric fluid plays a crucial role in the Wire EDM process by providing electrical insulation, cooling, and debris removal. The fluid's properties and dynamics significantly influence the ignition, material removal, and overall process stability.

### Key aspects of the dielectric fluid in Wire EDM

1. **Electrical properties:** The dielectric fluid's electrical resistivity and dielectric strength determine the breakdown voltage required for ignition. These properties are affected by factors such as fluid composition, temperature, and contamination levels. The module will model the spatial and temporal variation of these properties based on the process conditions.

2. **Thermal properties:** The fluid's thermal conductivity, specific heat capacity, and convective heat transfer coefficients govern the cooling of the wire electrode, workpiece, and debris particles. Efficient heat removal is critical for maintaining process stability and limiting wire breakage. The module will simulate the temperature distribution and heat transfer in the fluid based on the discharge energy and fluid flow.

3. **Fluid dynamics:** The flow of the dielectric fluid in the inter-electrode gap is driven by various forces, including the flushing pressure, wire motion, and plasma channel dynamics. The fluid velocity field affects the removal of debris particles and the distribution of heat and contaminants. The module will use simplified fluid dynamics models to capture the essential flow behavior while maintaining computational efficiency.

4. **Debris distribution:** The dielectric fluid carries the debris particles generated during the material removal process. The concentration and spatial distribution of these particles influence the gap conductivity and the probability of secondary discharges or short circuits. The module will track the generation, transport, and removal of debris particles based on the material removal rate and fluid flow.

### Modeling approach

The dielectric module implements a simplified model focusing on three key state variables:

1. **Debris Concentration** ($C_d$):  This variable represents the concentration of debris particles in the dielectric fluid within the inter-electrode gap. It starts at 0 at the beginning of the simulation or after a complete flushing cycle.  Instead of using a differential equation based on spark events per time unit, we directly increment the debris concentration with each spark, where the increment is now dependent on the material removed by the spark (crater volume), and decrement it based on the flow rate at each microsecond timestep.

   - **Debris Accumulation:** For each spark event, the debris concentration $C_d$ is increased proportionally to the crater volume $V_c$ of that spark.  This is represented as $C_d \leftarrow C_d + \beta V_c$, where $\beta$ is a factor that scales the crater volume to the increase in debris concentration.  A larger crater volume (more material removed) will result in a greater increase in debris concentration.
   - **Debris Decay:**  Simultaneously, the debris concentration decays at a rate proportional to the flow rate $f$.  This decay is modeled by reducing $C_d$ by a fraction $\gamma f$ of its current value at each timestep.

   This can be conceptually represented as:

   - Initialize $C_d = 0$
   - At each timestep:
     - If a spark occurred in this timestep with crater volume $V_c$: $C_d \leftarrow C_d + \beta V_c$
     - Debris Decay: $C_d \leftarrow C_d \times (1 - \gamma f)$


2. **Flow Rate** ($f$): This is a normalized parameter representing the dielectric fluid flow rate. It is non-dimensional and ranges from 0 to 1, where:
   - $f = 0$ indicates no dielectric fluid flow.
   - $f = 1$ represents the maximum or nominal dielectric fluid flow rate.
   - Values between 0 and 1 represent proportional levels of flow rate between these extremes.
   This normalized representation simplifies the model and allows for easy adjustment and interpretation of flow rate effects without needing to specify physical units.

3. **Ionized Channel State**:  Models the condition where the inter-electrode gap becomes temporarily conductive after a spark, effectively acting as a short circuit for a brief period $\tau_{deionization}$.  This state signifies that the dielectric in the spark region remains ionized and highly conductive, facilitating current flow.  The location of the ionized channel is also recorded.
   The dynamics are:

   - \textbf{Initiation:} A spark event at location $y_{discharge}$ triggers the ionized channel state.
   - \textbf{Duration:} The "conductive" condition persists for $\tau_{deionization}$ timesteps, during which the gap is conductive at $y_{discharge}$.
   - \textbf{Deactivation:} After $\tau_{deionization}$, the ionization dissipates, the gap returns to its insulating state, and the Ionized Channel State becomes inactive.


### Integration with other modules

The dielectric state interacts with other simulation modules through the following mechanisms:

1. **Ignition Module:**
   - Debris concentration ($C_d$) directly affects short-circuit probability through contaminated dielectric
   - Ionized channel state prevents new spark formation in recently discharged regions
   - Dielectric conductivity influences breakdown voltage calculation
   - Flow rate ($f$) modifies spark distribution by affecting debris accumulation patterns

2. **Wire Status Module:**
   - Dielectric flow rate ($f$) determines convective cooling efficiency:
     ```python
     wire_temperature -= k_flow * f * (wire_temperature - dielectric_temperature)
     ```
3. **Mechanics Module:**
    - Viscosity (dependent on temperature) determines drag forces on wire. This affects wire vibration and wire deflection dynamics. (Not implemented yet)
    - Flow rate ($f$) determines the drag force on the wire, which affects wire deflection dynamics.
    - Turbulence (not implemented yet) is a random force on the wire, which affects wire deflection dynamics.