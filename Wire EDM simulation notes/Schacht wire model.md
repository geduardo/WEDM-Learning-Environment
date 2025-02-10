Chapter III

Design of a wire electrode by
functional decomposition

III.1 Introduction

This chapter will use a different and new approach to the development of wire
electrodes for EDM. In stead of using an exhaustive design of experiments, like in
the previous chapter II, physical insights and phenomenological descriptions are
supplied. They will clarify the conclusions of the factorial design and allow the
design of wire electrodes for various purposes. The stress will however lie on the
development of high tensile strength steel core wire electrodes.

First of all subsection III.1.1 will discuss the importance of the wire diameter to the
performance and the design of the wire. In Chapter II the wire diameter was omitted
from the design of experiments. Instead two separate designs were started for 100
µm and 250 µm wires, since the identification of the diameter as a significant factor
was superfluous. In this chapter the physical mechanisms that define the influence of
the wire diameter will be explained. The gained insights will allow an outlook to
future wire EDM developments, since together with wire electrical discharge
machines the appearance of the wire is changing.

Following sections offer a functional decomposition from which the design phase is
started. The functional decomposition is destilled from experiments done during this
doctoral research and served as a comprehensive framework for the authors wire
electrode research. Previously unreported layers, like the insulating and superficial
layer are introduced. Other layers, like the conductive layer and the coating are now
for the first time extensively described. Their functions and needed properties are
given based on extensive experimental proove, new theorethical insights, and
models drawn up further on in this dissertation (Chapter IV and Chapter V). The
function of the features varies according to the wire diameter and its envisaged goal.

47

Chapter III: Functional decomposition of the wire electrode

48

Another important outcome of this chapter is the definition of a performance index
for uncoated wire electrodes and for wire coatings. Up to now no performance index
for EDM wires was reported.

III.1.1 Wires without coating: influence of the diameter

As in Chapter II, the wire diameter is considered as the major factor influencing the
cutting rate (CR) of the wire. What diameter is picked depends on the envisaged
application. The development of wire electrodes for EDM goes in two directions,
both towards thicker diameters for higher cutting speeds or higher parts and towards
smaller diameters, for high precision applications. At one end of the market, the
trend to produce ever smaller or more detailed products with subsequent narrower
tolerances, which is especially the case in the electronics industry, necessitates
machining with higher accuracy at economic speed. Wire EDM must keep up with
these demands, while keeping the production economic. At the other outer end of the
market, there is a trend of building machines able to cut higher parts. In both market
segments, economic machining speed is a main issue. Economic, as ever, means as
fast as possible. As illustrated in section I.6 the development of faster machines goes
hand in hand with the development of new and thicker wires.

200
150
100
Cutting rate (mm²/min)

V.H

50
0
50
100
250
300 350
150 200
Wire diameter (µm)

Robofil 2000-Robofil 2030si

Robofil 240cc

Figure III.1: Cutting rate for brass wires versus diameter on different machines
workpiece: DINX210CrW12, height: 32.7 mm, VD: 10 m/min

This paragraph discusses the influence of the wire diameter $d$ on the maximum
attainable cutting rate in wire EDM. The CR is expressed in mm²/min and is the
product of the wire feed velocity $v_f$ and the height of the workpiece H. If also the
width of the cut slot is taken into account the material removal rate (MRR),
expressed in mm³/min is meant. On figure III.1 a rise in maximum cutting rate with
increasing diameter is witnessed in the small diameter range (up to 200 µm). For
diameters over 350 µm no gain in cutting speed can be reached. The experiments
were performed on Charmilles wire EDM machines of different generations. For the
Robofil 2030SI the plateau in the removal rate starts from about 250 µm diameter.
For newer machines (Charmilles' Robofil 240cc), the start tends to shift to thicker
diameters (330 μm).

Composite wire electrodes and alternative dielectrics for wire EDM
49
Förster [37] reported on a linear rise in cutting rate as a result of the larger
applicable discharge currents on the larger cross section. He attributed this to a
higher cooling of the wire by conduction through the wire core. He could however
not explain that this rise attenuated for the largest diameters.

This dissertation uses the assumption of wire cooling by convective heat transfer in
the dielectric to enable the explanation of the authors (figure III.1) and Försters [37]
results. The next sections will elaborately deduce an expression for the maximum
cutting rate as a function of wire diameter. Only uncoated wires are addressed here
to allow simple reasoning. The deduction is split up in two. One deduction is made
for thick wires (>250 µm) in which Joule heating is neglected. It will prove that their
cutting rate is independent of wire diameter. Another deduction is made for thin
wires in which Joule heating is considered the most important heating mechanism. It
leads to a rising cutting rate proportional to the square root of the wire diameter. For
intermediate diameters both Joule heating as well as heating by the discharge itself
should be incorporated in the definition of the wire's total heating. This will only
shortly be addressed.

The introduction of several proportionality constants ($\zeta$, $\phi$, $\psi$) in the following
sections enables understanding how future machines can enhance cutting rate by
altering these constants. As shown on figure III.1 the most recent machine
(Charmilles' Robofil 240cc) has best cutting rate. It will explain why the attaining of
higher cutting rates with larger wires goes hand in hand with the use of higher
discharge energy and dielectric inlet pressure. The one is not possible without the
other.

Moreover the theory will lead to a performance index for uncoated wires, which will
state the importance of electrical conductivity, temperature resistance and sparking
ability.

III.1.1.1 Thick wires

As far as thick wires are concerned, it will be shown below that there is a
technological maximum in the maximum attainable cutting rate for cutting a given
material (e.g. steel) with a fixed height H and with a given type of wire (e.g. plain
brass wire). This maximum can be calculated by assuming a maximum allowable
temperature raise $\Delta T$ in the wire and that the material removal rate ($v_f$.$d$.$H^1$) is
proportional to the average working current $\bar{i}$. The assumption of a maximum
allowable temperature raise is based on the hypothesis that wire rupture is
temperature related and that the maximum temperature at which the wire will break
is known. This is stated by many authors, e.g. Dekeyser [21]. No other assumptions
or further deductions are made. The maximum allowable temperature raise in the
wire is a material constant. It can have different interpretations. Heating up to the
melting temperature $T_m$ can be used, but it is better to consider the temperature that
halves the tensile strength of the wire $T_g$. $\Delta T$ then equals $T_g - 20^\circ$C.
Feed rate $v_f$ multiplied by diameter of the wire $d$ and height of the part $H$. The working gap is neglected in this approximate calculation.

Chapter III: Functional decomposition of the wire electrode
50
Heating of the wire
For a needle impulse generator (section 1.3.2) the average working current can be
approximated as in equation III.1. The ignition current $i_{ei}$ is neglectable compared to
the peak working current and an isosceles triangular current pulse shape is assumed.
The average working current is then approximately proportional to the peak working
current $\hat{i}_e$. The proportionality is expressed by$\zeta$, which is dimensionless. It can
change if other wires are used or different workpiece materials and heights are
machined. It is also a function of servo-regulated factors and generator settings,
because $t_p=t_a+t_e+t_o$ (see table 1.3). $t_a$ is regulated by the servo. $t_o$ and $t_e=t_{ei}+t_r+t_f$ are
kept constant during machining. As the servo regulates the machine to an average
working voltage, hence an average $t_d$, an average working current will be
maintained.

It is important to realise that the peak working current in equation III.1, is the current
that is applied to the wire when the maximum cutting rate is reached. It is hence
assumed that the generator of the wire EDM machine is able to deliver this current.
This is not trivial and depends on the machine in use and the electrical load on the
generator. It could e.g. be well possible that this current can be reached with a well
conducting electrode, like copper, but not with a worse conducting electrode, like
brass. Section III.4.1 will make extensive comments on this issue.
$$
\frac{\hat{i_e} t_r}{t_p} + \frac{i_{ei} t_{ei}}{t_p} =  \frac{\hat{i_e}t_r + i_{ei} t_{ei} + i_r t_f}{t_p}  =  \frac{\hat{i_e} t_r}{t_p} = \bar{i_e}
$$
(eq. III.1)

The heating of a thick wire is mostly generated by the discharge itself, the plasma.
Joule heating is small with thick wires. Since the discharge voltage $u_e$ is
approximately constant, the machining power is proportional to the average working
current $\bar{i}$. A small amount of the machining power is used for heating and
consuming the wire (cathode). This is further on called the process heat. In equation
III.2 $\phi$ is the process heat flow created in the wire by one Ampere of working
current. It is expressed in W/A. $\phi$ depends on how the total energy is distributed
between cathode, anode and spark plasma. Many attempts have already been made
to define the energy balance [9, 35, 123, 124, 158]. All reported models yield
remarkably different results, leaving the energy distribution in electrical discharge
machining as one of the main unknown factors of the process. It is however
generally accepted that the energy distribution depends on the wire and workpiece
material, as well as on the dielectric.

The efficiency factor $\psi$ in equation III.2, given in C/mm³, expresses the
proportionality between average current and material removal rate. It can be
interpreted as the amount of charge needed to machine 1 mm³ of the workpiece, or
not yet set in for the pulse durations used in wire EDM of steel, the efficiency is
constant. Siegel [142] and Nöthe [116], amongst others, proved experimentally that
the size of anode as well as cathode craters changed linearly with working current
Composite wire electrodes and alternative dielectrics for wire EDM
51
for commonly used wire EDM energies. $\psi$ is hence constant for one machine (pulse
type), if the wire and the workpiece are kept constant. For modern machines this
factor is smaller because of the steeper current slopes that new generators can apply.
For badly sparking wire materials, such as plain steel, or difficult to machine
workpiece materials, $\psi$ will be large.
$$Q_{process} = \phi \cdot \bar{i} = \phi \cdot \zeta \cdot \hat{i}_e = \phi \cdot \psi \cdot v_f \cdot d \cdot H$$
(eq. III.2)
Cooling of the wire
As in known models [21] for the calculation of the overall wire temperature, it is
assumed here that the cooling of the wire is by convective heat transfer to the
dielectric. This is in contradiction to the earlier description of Förster [37] who
presumed that heat conduction in the wire core (proportional to $d^2$) was the prevalent
cooling mechanism. Further on in this work (Chapter V) heat conduction in the wire
will also be included for the calculation of local temperatures close to the crater, but
this is neglected here. Three other cooling mechanisms are neglected here. The wire
is also cooled by partial evaporation when a crater is formed, by emission of
electrons, as will be discussed in section III.5.1.3 and by its unwinding speed the
wire is also removing heat stored in its heat capacitance. Dekeyser [21] clearly
shows how the average wire temperature drops when the wire unwinding speed $V_D$ is
raised.

In convective heat transfer the heat consumption is proportional to the wire's surface
(π.$d$. H) and temperature. In equation III.3 the convective heat transfer coefficient
$h$ makes the equation hold. As discussed in section VIII.4.5 $h$ is largely dependent
on the amount and quality of flushing. With modern machines higher dielectric inlet
pressure $p_{in}$ is applied aiming at higher cooling rates. With higher workpieces the
flushing will be less effective, lowering the heat transfer coefficient.
$$Q_{cooling} = h(H, p_{in}, ...)\cdot \pi \cdot d \cdot H \cdot \Delta T$$
(eq. III.3)

Equilibrium

In steady state, cooling and heating of the wire are in equilibrium. By setting
equation III.2 equal to equation III.3, it is found that $v_f$, which is the maximum
attainable feed rate, is independent of the wire's diameter, but proportional to the
maximum allowable temperature rise in the wire:

$$v_f = \frac{h(H, p_{in},……) \cdot \pi \cdot \Delta T}{\phi \cdot \psi}$$
(eq. III.4)
Performance index for thick uncoated wires

Therefore equation III.4 shows that the maximum attainable speed can be higher
when temperature resistant wire materials are chosen. $\frac{\Delta T}{\psi}$ is a performance index

Chapter III: Functional decomposition of the wire electrode
52
for thick wires, showing that good EDM efficiency (low $\psi$) and a high allowable
$\frac{h}{\phi \cdot \psi}$ indicates that it is also possible
temperature rise must be combined. The ratio
to reach higher removal rates by enhancing the cooling of the wire, i.e. raising the
convective heat transfer to the dielectric or by lowering the heat dissipation in the
wire ($\phi$) and the needed working current per unit of removed workpiece material
($\psi$). Lowering $\phi$ can e.g. be done by raising the current impulse slope. Since
raising the wire unwinding speed $v_D$ introduces an extra cooling effect in the
process, it will also improve the maximum attainable cutting rate.

In the equation the electrical resistivity $\rho$ of the wire does not show up. This is due
to assuming that the generator is able to supply a peak working current $\hat{i}_e$ that rises
the wire temperature by $\Delta T$. Chapter IV will however show that the electrical
resistivity of the wire restricts the working current. In this case pulses deviate from
the triangular form (figure I.18) and the efficiency of energy transfer to the
workpiece drops, in other words $\phi$ and $\psi$ rise.

Figure III.1 showed that for diameters over 250 µm no gain in cutting speed could
be reached on the Charmilles' Robofil 2000 and 2030SI. The above deduction
proved that this is a consequence of the equilibrium between heating (proportional to
d) and cooling (also proportional to d) of the wire at maximum cutting energy. The
intuitive fact that a larger wire can withstand a higher energy is correct, but this
extra energy does not result in a higher cutting rate, but only in a higher material
removal rate, because the machined slot will be thicker (see appendix B).

For newer machines (Charmilles' Robofil 240cc), the start of the cutting rate plateau
tends to shift to thicker diameters (330 µm). This is due to the use of higher flushing
pressures (improved cooling), shorter pulses (less process heat) and larger wire
unwinding speeds. In the future the introduction of even faster cutting machines will
go hand in hand with the use of thicker wires and higher flushing rates (section I.6).
As a conclusion equation III.4 reveals that a wire electrode for high speed wire EDM
should withstand high temperatures and show good EDM efficiency (small $\psi$). In
the functional decomposition that will be introduced in this chapter these properties
will be attributed to different parts of the wire.

III.1.1.2 Thin wires

Heating of the wire
For thin wires, there is a gain in maximum attainable cutting rate with larger
diameters. This is to be related to the extra Joule heating in the wire by conduction
of the working current. If the heating of the wire by the sparking process (sparks) is
neglected as compared to the Joule heating, equation III.2 can be rewritten as III.5.
These conditions are met in thin wires only if the maximum cutting rate is
considered, and hence the maximum peak discharge current $\hat{i}_e$ (see calculations in
section V.2.2). Nöthe [116] neglected Joule heating and only shortly addresses it in
Composite wire electrodes and alternative dielectrics for wire EDM
53
his work on micro wire EDM. The current he applied was far beneath the maximum
possible. Again the ignition current $i_{ei}$ is neglected and isosceles triangular current
pulses are assumed. Only one fourth of the total wire resistance $R_w$ is taken into
account, since in wire EDM the current is fed to the wire via two current contacts,
one above the workpiece and one below the workpiece. In average the discharge
occurs in the middle of the workpiece so that the total current sees a total resistance
equal to two halves of the wire in parallel. In equation III.5 $\rho$ is the resistivity of the
wire material.
$$Q_{Joule} = \frac{1}{4} \frac{R_w}{t_p} \int_0^{t_p} \hat{i_e}^2(t) dt = \frac{2}{4} \cdot \frac{\zeta^2 R_w}{3} \hat{i_e}^2 = \frac{2 \cdot \zeta \rho H}{3 \pi d^2} \cdot \frac{\hat{i_e}^2}{4}  = \frac{2 \cdot \zeta^2  \rho \cdot H}{3 \cdot \pi \cdot d^2}  \cdot \frac{\psi^2 \cdot v_f^2 \cdot d^2 \cdot H^2}{4} = \frac{2 \cdot \rho \cdot \psi^2 \cdot v_f^2 H^3}{3 \cdot \pi \cdot \zeta}$$
(eq. III.5)

Equilibrium

Setting equation III.5 equal to equation III.3 now yields:

$$v_f = \frac{1}{\psi H} \sqrt{\frac{3 \cdot \pi \cdot \zeta \cdot h(H, p_{in}, ...)\cdot d \cdot \Delta T}{2 \cdot \rho}}$$

(eq. III.6)
Performance index for thin uncoated wires

The maximum attainable cutting rate hence raises with the square root of the
diameter in the lower diameter range. This raise is higher if the resistivity of the wire
is lower. Figure III.1 shows this quadratic raise clearly. For newer machines higher
cutting rates can be reached because of better flushing (higher h) and the use of
sharper current impulses (lower ψ).

It is important to notice that, for thin wires the ratio $\sqrt{\frac{d}{\rho}} \frac{ \Delta T}{\psi}$ is a performance
index. The perfect thin wire should withstand high temperatures, have low electrical
resistivity and good EDM efficiency (low $\psi$). These properties will be undertaken
by different parts of the wire in the functional decomposition, following this section.

In comparison to thick wires, the performance index shows a loss of importance of
$\Delta T$, but now $\rho$ comes in. It also shows that the electrical conductivity is less
important than the EDM efficiency. This explains why a brass wire can give better
results than a more conductive copper wire. The good sparking properties of the zinc
in brass overcomes the loss of conductivity.
Chapter III: Functional decomposition of the wire electrode
54
III.1.1.3 Intermediate diameters

Heating of the wire
In an intermediate diameter range the heating of the wire at maximum cutting rate is
both due to Joule heating and process heat (equation III.7). The cooling of the wire
is still mainly due to convective heat transfer to the dielectric (equation III.3).

$$Q_{total} = Q_{Joule} + Q_{process}$$
(eq. III.7)
Starting from which diameter the Joule heating can be neglected compared to the
process heat or vice versa depends on the envisaged wire material. For materials
with high resistivity the influence of Joule heat can be expected to extend to larger
diameters. This means that a thicker wire will be needed before the plateau in cutting
rate is reached. For the use of other dielectrics the point where Joule heating can be
neglected will also shift. In the case of a dielectric with less cooling capacity than
water, e.g. oil based dielectrics, this diameter will be smaller.

Performance index for uncoated wires

For all diameters the ratio $\frac{\Delta T}{\rho}$ must be maximised and $\psi$ must be minimised. A
low electrical resistivity is also requested for thick wires in order to lower the load
on the generator. As will be shown in section III.4 a large load restricts the attainable
peak discharge current and hence limits the maximum attainable cutting rate.

This Ph.D. aims the design of wire electrodes targeted for a high tensile strength in a
way that their bending can be minimised by applying high wire pretensioning force
(Chapter VI). Wires in the small diameter range and in the thick diameter range will
be designed. The small diameter is intended to be used in high precision
applications. The thick diameter is intended for the machining of very high parts or
for fast cutting. From the previous section it is clear that both wires will have to be
designed differently. The described design phase is based on phenomenological
understanding and can be extended to other smaller, larger or intermediate
diameters.

III.1.1.4 Conclusion

The elaborated deduction above uncovers several important facts with respect to the
use of uncoated wires. Since the drawn up model shows good accordance with
experiments, the following conclusions can be stated.

*   Wire rupture and hence maximum cutting rate is related to the temperature in
    the wire.
*   There is a technological maximum in the attainable cutting rate using thick
    wires. For a given machine it makes no sense using larger wires. The extra
    applied energy will not lead to a higher cutting rate.

Composite wire electrodes and alternative dielectrics for wire EDM
55
*   The place where this plateau in the maximum attainable cutting rate sets in
    depends on the importance of Joule heating. Highly resistive electrodes can
    profit from larger diameters.
*   For wires in the small diameter range the cutting rate rises with the square root
    of the diameter.
*   The important heating factor for thick wires is the process heat input. For thin
    wires it is Joule heating.
*   The cooling of the wire electrode is by convective heat transfer to the dielectric.
    Dielectrics with less cooling capacity, like e.g. oil based dielectrics (section
    VIII.4.5), lead to lower performance. The technological maximum will be
    reached for smaller diameters.
*   The performance of the wire is influenced by the following wire related
    parameters: $\Delta T$, $\rho$ and $\psi$. The first should be as high as possible the latter
    two, as small as possible.

III.1.2 Functional decomposition of coated wires

In this text a general EDM wire electrode is supposed to maximally consist of five
components (figure III.2):

*   the core of the wire, mostly responsible for tensile strength.
*   a thermally insulating layer on the core that protects the core from the heat input
    by the discharge. It safeguards the unique mechanical properties of the core, i.e.
    its tensile strength.
*   a conductive layer can supply extra electrical conductivity. It is in between the
    core (and possibly its insulation) and the coating (and possibly its enhancing
    superficial layer).
*   the coating which is intended to provide the wire with a high (economic) cutting
    speed.
*   on top of a wire a very thin superficial layer may be applied with variant
    purposes.

    1. Core
2. Insulating layer
    
 3. Conductive layer
    
    4. Coating
    
    5. Superficial layer
    
Figure III.2: Functional decomposition of an EDM wire electrode

The presence of all five or just some of these components depends on the intended
use of the wire. This paragraph discusses the functions of each of the layers in detail,
and proposes suited materials for performing the layer's function. Though this text
will assume the design of a high strength wire electrode, the proposed functional
decomposition is valid for all EDM wires. If e.g. the tensile strength of the wire is
not considered important, but only its electrical conductivity, the core and its