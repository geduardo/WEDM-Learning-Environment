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






# 1D Wire Thermal Model Proposal

## Model Components

### 1. Geometry Discretization
The wire is divided into N discrete segments along its length (y-axis) to enable numerical simulation. Each segment represents a small portion of the wire and tracks:
- Position yᵢ: Location along wire length [m]
- Length Δy: Size of segment [m] 
- Cross-sectional area S = πr²: Area perpendicular to wire axis [m²]
- Surface area A = 2πrΔy: Area exposed to dielectric [m²]
- Temperature Tᵢ: Local temperature of segment [K]

### 2. Heat Generation Terms

#### a) Plasma Heating (Q_plasma)
When a spark occurs at position yₛ, it transfers thermal energy to the wire:
$$Q_{plasma} = \eta_{plasma}E_{discharge}/\Delta t$$
Where:
- η_plasma (0.3-0.5): Efficiency of energy transfer from plasma to wire
- E_discharge = V⋅I⋅Δt: Total energy of a single spark [J]
- Δt: Simulation timestep [s]

#### b) Joule Heating (Q_joule) 
Resistive heating occurs as current flows through wire:
$$Q_{joule} = I^2R_{segment}$$
$$R_{segment} = \rho_{elect}(T)\cdot\Delta y/S$$
Where:
- ρ_elect(T): Temperature-dependent electrical resistivity [Ω·m]
- I: Current flowing through wire [A]

### 3. Heat Loss Terms

#### a) Convective Cooling (Q_conv)
Heat transfer to surrounding dielectric fluid:
$$Q_{conv} = h\cdot A\cdot(T_i - T_{dielectric})$$

#### b) Conductive Cooling (Q_cond)
Heat spreading along wire length between segments:
$$Q_{cond} = \frac{k(T)\cdot S}{\Delta y}(T_{i-1} - 2T_i + T_{i+1})$$

#### c) Wire Transport Cooling (Q_transport)
Heat removed by physical movement of wire:
$$Q_{transport} = \rho c_pv_D(T_{i-1} - T_i)\cdot S/\Delta y$$

### 4. Temperature Evolution Equation
The rate of temperature change for each segment is determined by the sum of heat terms:
$$\rho c_p\frac{\partial T_i}{\partial t} = \frac{Q_{plasma} + Q_{joule} - Q_{conv} + Q_{cond} + Q_{transport}}{S\Delta y}$$

### 5. Numerical Implementation

#### Finite Difference Scheme (Explicit)
The temperature is updated each timestep using forward Euler integration:
$$T_i^{n+1} = T_i^n + \frac{\Delta t}{\rho c_p}[ \frac{Q_{plasma} + Q_{joule}}{S\Delta y} - \frac{hA}{S\Delta y}(T_i^n - T_{dielectric}) + \frac{k}{(\Delta y)^2}(T_{i-1}^n - 2T_i^n + T_{i+1}^n) + \frac{v_D}{\Delta y}(T_{i-1}^n - T_i^n) ]$$

### 6. Boundary Conditions
The wire temperature is constrained at its ends:
- Entry point (y=0): Fixed at ambient temperature as new wire enters (we neglect the heating of the wire due to conduction outside of the contacts
- Exit point (y=L): Fixed at ambient temperature (we assume wire outside contacts cools fast )

### 7. Wire Break Criteria
Wire failure is checked at each segment using three mechanisms:
1. **Melting Threshold**: Immediate break if temperature exceeds melting point
2. **Ductile Failure**: Break occurs after sustained exposure to critical temperature
3. **Thermal Stress**: Break due to excessive temperature gradient causing material stress

### 8. Required Parameters

| Parameter | Symbol | Typical Value |
|-----------|--------|---------------|
| Density | ρ | 8900 kg/m³ (Cu) |
| Specific heat | c_p | 385 J/kg·K |
| Thermal conductivity | k | 400 W/m·K |
| Convection coeff | h | 500-5000 W/m²K |
| Wire velocity | v_D | 0.1-10 m/s |
| Wire radius | r | 0.05-0.25 mm |

### 9. Implementation Strategy

1. Create wire temperature array in EDMState
2. Add thermal properties to material database
3. Create ThermalModule class with:
   - Heat source calculations
   - Finite difference solver
   - Break detection
4. Connect to existing spark tracking








