## Collecting facts

### Wire EDM in general

- The main limiting factor limiting cutting speed in rough cut Wire EDM is the power that can be delivered through the wire electrode without causing it to break. Therefore, modelling wire breaking is essential for a simulation focused on control of wire EDM main cut
- The wire can break for several reasons. In order of importance (Schaat thesis)
	- The wire gets too hot, the mechanical properties of the wire change at some local point that causes it to break. This can happen through several mechanisms:
		- Ductile fracture with a strong reduction of wire diameter due to elevated wire temperature
		- Complete melting of the wire
	- Brittle fracture of the wire without reduction of the diameter, likely due to initiation and propagation of cracks during the spark explosion. This kind of rupture can also happen after the wire has left the working area (e.g. bending in the evacuation system)
- Most wire breakages are not preceded by a concentration of sparks (kunieda)
- Some wire breakages are preceded by a concentration of sparks (kunieda)

### Thermal aspects
- There are two main sources of heating in the wire: (Schaat thesis)
	- Thermal energy from the plasma during the discharge (main source in thicker wires)
	- Joule effect in the wire (relevant in thinner wires)

- The heat is extracted from the wire by several mechanisms with different relevance:
	- Convective cooling to dielectric fluid (combined conduction and advection):
		- Conduction through boundary layer: Direct heat transfer to adjacent fluid molecules at wire surface
		- Advective removal: Flushing flow carries away heated fluid (forced convection) and buoyancy effects create natural circulation (natural convection)
		- Convective heat transfer coefficient $h$ depends on:
			- Dielectric temperature $T_{dielectric}$
			- Flow conditions (better flow = better convection)
			- Wire diameter/surface area (larger contact area = better convection)
			- Material properties (relative thermal conductivity of wire and dielectric)
			
	- The convective heat transfer can be modeled using Newton's law of cooling:
		$$q_{conv} = h A_{wire} (T_{wire} - T_{dielectric})$$
		where:
		- $q_{conv}$ is the convective heat transfer rate [W]
		- $h$ is the convective heat transfer coefficient [W/m²K]
		- $A_{wire}$ is the surface area of the wire [m²]
		- $T_{wire}$ is the wire temperature [K]
		- $T_{dielectric}$ is the dielectric fluid temperature [K]
	
	- Heat conduction along the wire length: Temperature gradients along the wire drive heat transfer, spreading heat and reducing hotspots. Heat flows from hotter regions to colder regions along the wire, effectively removing thermal energy from the working zone. The heat conduction rate is governed by Fourier's Law:
		$$q_{cond} = -k S_{wire} \frac{dT}{dy}$$
		where:
		- $q_{cond}$ is the conductive heat transfer rate [W]
		- $k$ is the thermal conductivity of the wire material [W/mK]
		- $S_{wire}$ is the cross-sectional area of the wire [m²]
		- $\frac{dT}{dy}$ is the temperature gradient along the wire length [K/m]

	- Partial evaporation when craters form:
		- Phase change energy: $\Delta H_{vap} \approx 5-10\%$ of discharge energy
		- Creates transient temperature drops up to 200K at discharge sites
		
	- Electron emission cooling:
		- Thermionic emission carries away ~0.1-1% of discharge energy
		- More significant for high melting point materials (W, Mo)

	- Heat removal by wire movement:
		- Wire unwinding speed (VD) removes stored heat via advection: $q_{transport} = \rho c_p v_D \Delta T$
		- High VD (>10m/min) reduces average temperature by 15-20% per 5m/min increase
		- Enables higher $\Delta T_{safety}$ margins through forced convection enhancement

















## Drafting

## 1D Thermal Model for Wire EDM Breakage Prediction

### Fundamental Assumptions

1. Wire Geometry: Model wire as 1D rod along y-axis (wire length direction)

2. Heat Transfer Mechanisms:

    - Conduction along wire (y-direction)
    - Convection to dielectric fluid
    - Adiabatic boundary at wire ends
    - Joule heating from discharge current

3. Discharge Characteristics:

    - Stochastic spark distribution (Poisson process)
    - Energy deposition per spark follows Kunieda's concentrated discharge observations
    - Spark locations follow observed discharge concentration patterns

### 2. Governing Equation

Modified Heat Equation with Moving Wire:

$$\frac{\partial T}{\partial t} = \underbrace{\alpha\frac{\partial^2 T}{\partial y^2}}_{\text{Conduction}} - \underbrace{v_w\frac{\partial T}{\partial y}}_{\text{Advection}} + \underbrace{\frac{Q_{\text{joule}} + Q_{\text{process}}}{\rho c_p}}_{\text{Sources}} - \underbrace{h(T-T_0)}_{\text{Cooling}}$$

Where:

- $T(y,t)$: Temperature distribution
- $v_w$: Wire feed velocity
- $\alpha$: Thermal diffusivity
- $h$: Convective cooling coefficient
- $Q_{\text{joule}} = I^2R/L$: Joule heating per unit length
- $Q_{\text{process}}$: Discharge energy input

### 3. Discharge Energy Model

From Kunieda's observations:

$$Q_{\text{process}} = \sum_{i} \frac{E_{\text{spark}}}{\tau\sqrt{2\pi}}e^{-\frac{(y-y_i)^2}{2\sigma^2}}$$

- $E_{\text{spark}} = \int_0^{\tau} V(t)I(t)dt$ (Single spark energy)
- $y_i$: Spark locations (Poisson distributed)
- $\sigma$: Discharge concentration parameter (from paper Table 2)

### 4. Breakage Criterion

From Schacht's wire model:

$$\exists y \ s.t.\ T(y,t) \geq T_{\text{crit}} = T_{\text{melt}} - \Delta T_{\text{safety}}$$

Where:

- $T_{\text{melt}}$: Wire material melting point
- $\Delta T_{\text{safety}}$: Empirical safety margin (from Kunieda's Table 5)

### 5. Stochastic Elements

- Spark Ignition:
    - Probability $P_{\text{ignition}} \propto \frac{V^2}{d^2}\cdot f(\text{debris})$
    - Follows hazard function from ignition module

- Discharge Location:
    - Clustering tendency modeled with Markov process:
    $$P(y_{i+1}|y_i) \sim \mathcal{N}(y_i, \sigma_c)$$
    - $\sigma_c$: Concentration parameter from Kunieda's Fig 2-4

### 6. Numerical Implementation Strategy

| Aspect | Approach | Reference |
|---|---|---|
| Spatial Discretization | Finite Difference (0.1mm segments) | Schacht's diameter analysis |
| Temporal Integration | Explicit Euler (1μs steps) | Ignition module timing |
| Advection Handling | Upwind scheme | Wire velocity ~10m/s |
| Breakage Detection | Real-time max temp monitoring | Kunieda's observation window |

### 7. Key Parameters

From Experimental Data:

\begin{array}{l|l|l}
\text{Parameter} & \text{Value} & \text{Source} \\
\hline
\alpha_{\text{brass}} & 3.5\times10^{-5} m^2/s & \text{Schacht Ch.III} \\
h_{\text{dielectric}} & 5\times10^4 W/m^2K & \text{Kunieda Table 2} \\
T_{\text{melt}} & 1180K & \text{Wire specs} \\
\sigma_c & 0.2-1.0mm & \text{Kunieda Fig 2-4} \\
E_{\text{spark}} & 0.1-1mJ & \text{Schacht Eq.III.7} \\
\end{array}

### 8. Model Validation Approach

1. Static Validation:
    - Compare steady-state temp profile with Schacht's analytical solutions
    - Verify breakage thresholds against Table 5 (Kunieda)

2. Dynamic Validation:
    - Match discharge concentration patterns from Fig 2-4
    - Reproduce temperature oscillation frequencies from dirty.ipynb

### 9. Simulation Process Flow

Initialize $T(y,0) = T_{\text{ambient}}$

↓

While $t < t_{\text{max}}$ and not broken:

    ↓

    [Stochastic Spark Generation]

    ↓

    [Solve Heat Equation]

    ↓

    [Update Wire Position]

    ↓

    Check $\max(T) > T_{\text{crit}} \rightarrow$ Break

    ↓

    $t += \Delta t$

This model captures the essential thermal dynamics while maintaining computational efficiency for real-time simulation. Would you like me to elaborate on any particular aspect or propose specific numerical implementation details?