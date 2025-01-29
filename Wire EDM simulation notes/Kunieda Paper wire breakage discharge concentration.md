# Research

## Wire-break Prevention on Wire Electrical Discharge Machining

**Tatsushi SATO*, Seiji SATO*, Hidetaka MIYAKE*, Koichiro HATTORI*, and Hitoshi TOKURA**

* Electric Processing Society of Japan

### Abstract

Wire-break, which greatly harms machining performance, can be prevented by reducing the machining energy. However, too much reducing the energy also harms machining speed. Thus a control algorithm which brings minimum requirement for wire-break prevention is needed. In this paper, we clarify there exists energy limit that brings wire-break, and the limit changes according to two factors: the workpiece thickness and the flow of dielectric fluid. In addition, we propose the control algorithm for wire-break prevention, which detect these two factors automatically. It is also shown that this control algorithm brings much higher performance when these two factor change during machining.

**Key words:** WEDM, Wire-break Prevention, Thickness Detection, Off-time Control

---

### 1. Introduction

Wire electrode breakage in wire electrical discharge machining (WEDM) causes a decrease in machining efficiency due to re-threading operations, as well as damage to the machined surface in the areas where machining is restarted. Thus, it should be avoided as much as possible. In order to avoid wire breaks, it is necessary to reduce the machining energy; however, this leads to a decrease in machining speed. Therefore, the reduction should be kept to the minimum required. Until now, machining condition tables provided by machine tool manufacturers were the basis for experienced operators to adjust the machining conditions by taking into account the influence of the machined shape. Except for the initial stage of machining, where the flow of machining fluid is unstable, the general practice has been to process all parts with a single set of machining conditions. It is expected that machining efficiency can be improved by switching to appropriate machining conditions for each part, but it is difficult to actually apply this because it requires the creation of a complex machining program with multiple appropriate machining conditions. However, with a single set of machining conditions, the overall processing is carried out using the "safest" machining conditions to prevent wire breaks even at the most likely locations. As a result, excessive safety conditions are applied to most locations, and there is a problem that machining efficiency is significantly reduced depending on the shape of the machining process. In addition, even an experienced operator cannot take all effects into account, and so it is necessary to set conditions with margins for unforeseen disturbances, which also tends to result in overly safe machining conditions.

To address these issues, some attempts have been made to clarify the wire breakage mechanism and to detect the occurrence of wire breakage in advance. If wire breakage can be predicted, high energy and high-speed machining can be carried out when the probability of breakage is low, and machining energy can be automatically reduced only when the probability of breakage is high. This control can realize more efficient machining. In this control, machining energy is automatically reduced when necessary according to the machining conditions that change moment by moment depending on the shape of the machining path and the machining fluid flow conditions. It is expected to provide more efficient machining than switching machining conditions according to the machining site, as well as eliminating the need for machining condition adjustment by skilled operators, which is a significant advantage in practice.

+ *Presented in part at the 1994 National Conference of the Japan Society for Electrical Machining and at the 173rd Electrical Machining Research Meeting.*
*  *Mitsubishi Electric Corporation (2-7-3 Marunouchi, Chiyoda-ku, Tokyo)*
** *Tokyo Institute of Technology (2-12-1 Oookayama, Meguro-ku, Tokyo)*

---

### 2. Discharge Concentration and Wire Breakage

There is a theory that wire breakage occurs when discharge is concentrated on a narrow region of the wire electrode for a short time, and the energy input exceeds the cooling capacity of the machining fluid on the wire electrode. Therefore, the relationship between the location of discharge and the occurrence of wire breakage was investigated.

#### 2.1 Discharge Location Detection Method

The location of discharge was estimated based on the distribution of discharge currents flowing through the upper and lower power lines, as proposed by Ohara et al. Specifically, when the current flowing through the upper power line is Iᵤ, the current flowing through the lower power line is Iₗ, and the proportionality constants are K₁ and K₂, the discharge location Pa is estimated using:
```

content_copydownload

Use code [with caution](https://support.google.com/legal/answer/13505487).Markdown

Pa = K₁ * (Iᵤ - Iₗ) / (Iᵤ + Iₗ) + K₂

```
The proportionality constants K₁ and K₂ were determined from measurements of the currents in the upper and lower power lines when processing thin plates placed at various heights, and when discharge was limited to a narrow range. The experiment was carried out under the conditions shown in Table 1. After confirming that machining was stable, a wire break was intentionally induced by one of the following: lowering the servo voltage, shortening the pause time, or reducing the flow of the machining fluid. The relationship between the location of discharge and the presence or absence of discharge concentration immediately before the wire break was examined. The experimental setup is shown in Fig. 1. The configuration also records the current waveform and the ON-OFF signals of the machining power supply from the oscillator to the memory at the same time.

|          |                               |
|:---------|:------------------------------|
| **Table 1**   | **Machining Conditions**       |
| **WEDM**  | MITSUBISHI DWC110SA     |
| **Wire**   | Brass ø0.3          |
| **Workpiece**  | Steel (t 80)     |
| **Nozzle**     | Both are close to the workpiece  |
| **Peak Current**  | 700A                 |
| **Off-time**    | 8 µs                 |
| **Servo Voltage**    | 45V                 |
| **Wire Speed**    | 13 m/min           |
| **Wire Tension** | 22N      |
---
#### 2.2 Discharge Location Before Wire Breakage

Fig. 2 shows an example of discharge concentration before wire breakage. Fig. 3 shows an example where discharge concentration was observed, but not immediately before breakage. Fig. 4 shows an example where discharge concentration was not observed before wire breakage. In these figures, the wire breakage occurs at the right edge, and the position of 500 discharge pulses before the wire break is shown.

During the experiment, the machining was progressing stably, so the discharge frequency was around 60 kHz. Therefore, these figures show the discharge position from about 8 ms before the breakage. Because the concentration period in the figures is less than 100 discharge pulses, the duration of discharge concentration is 1.6 ms or less, and the travel distance of the wire is estimated to be 0.36 mm or less from the wire speed.

|     |                               |   |   |
|:----|:------------------------------|:--|:--|
|  **Fig. 1**  |  **Layout of discharge position detection** |   |   |

|      |  |   |  |
|:-----|:------------------------------|:--|:--|
|   **Fig. 2**  | **Discharge concentration was observed just before wire break**   |  |  |
|   **Fig. 3** |  **Discharge concentration was observed, but not before wire break**   | | |
|   **Fig. 4** |  **Discharge concentration was not observed**   |  |  |

| **Table 2** | **Result of wire break examination** |   | |
| :------------- | :---------------------- |:---|:----|
| **Parameter (initial value)**   | **Value when break**  | **Discharge concentration** | |
| Servo voltage (45V)   | 40V   | X   |  |
|  | 43V | Δ  |  |
|  | 42V | X  |  |
| Fluid rate (Upper: 6 l/min Lower:6 l/min)   | Lower 5 l/min  | Δ  |   |
|  | Lower 5 l/min | Δ |  |
| | Lower 5.5 l/min | O |   |
|  | Both 11 l/min | O |  |
| Off time (8µs)  | 6µs | X  |   |
|  | 6µs | Δ  |   |
|  | 6µs | X  |   |
|  | 6µs | X  |   |

Table 2 shows the results of 11 wire breakage experiments. In the table, the left column shows the parameters changed to cause breakage, the center column shows the parameter values at the time of breakage, and the right column shows the presence or absence of discharge concentration. O indicates that discharge concentration occurred immediately before wire breakage, Δ indicates that discharge concentration was observed during the measurement time but not immediately before wire breakage, and X indicates that discharge concentration was not observed during the measurement time. From these results, the following was clarified:

*   Discharge concentration does not always occur immediately before wire breakage. Rather, wire breakage often occurs without discharge concentration.
*   When the flow rate of the machining fluid is reduced, discharge concentration tends to occur more easily, but it is less likely to occur in other cases.

---

### 3. Machining Energy and Wire Breakage

Since discharge concentration was not always observed at the time of wire breakage, the relationship between machining energy based on the number of discharge pulses and wire breakage was examined.

#### 3.1 Method for Measuring the Number of Discharge Pulses

The outline of the experimental apparatus used is shown in Fig. 5. The machining power supply used in the experiment is equipped with a control device that generates pulses with smaller machining current than usual when the distance between the wire and the workpiece becomes shorter. In this experiment, a short-circuit detector was also installed to detect the presence or absence of short-circuits based on the voltage level between the electrodes. The pulses were classified into three types: normal machining current pulses (OK pulses), pulses with a smaller machining current but no short-circuit (NG pulses), and pulses with short-circuits (SH pulses). Each type was counted every 10 ms.

The experiment was conducted for 67 different machining conditions within the range shown in Table 3. The peak current value was gradually increased every few tens of seconds, and the number of pulses until the peak current value reached its maximum value or the wire broke was measured.  Note that the wire diameter and other machining conditions not listed in Table 3 are the same as in Table 1.

|          |                 |
|:---------|:----------------|
| **Table 3**   | **Machining Conditions** |
| **WEDM** |  MITSUBISHI DWC110SZ+AE11 |
| **Workpiece** | Steel (t 20, 60, 100)      |
| **Servo Voltage** |  45~75V           |
| **Peak Current (OK pulse)**  | 600~940A           |
| **Peak Current (NG and SH pulse)** | 368~384A           |
| **Nozzle Position** | Close or 2mm distant       |

#### 3.2 Machining Energy Before and After Wire Breakage

Fig. 6 shows an example of the number of pulses measured. As the peak current value changes every 20 seconds, the number of pulses of each type also changes. In this example, wire breakage occurred immediately after the fourth change of conditions. Using the measured number of pulses, the machining energy before and after wire breakage was evaluated as follows. First, it was assumed that discharge contributing to machining does not occur at the time of SH pulses, but only short-circuit current flows. Therefore, SH pulses were not included in the machining energy. Also, it was assumed that the discharge voltage of OK pulses and NG pulses were constant (approximately 20 V). Although strictly speaking the discharge voltage of each pulse varies according to the impedance between the electrodes, it was assumed that the overall voltage converges to a value that depends on the material of the electrodes and the average discharge gap length. Based on the above assumptions, the machining energy was assumed to be proportional to the average current excluding the SH pulses. This value was designated as Ī, which was used as an index for evaluating average machining energy. The current I is:
```

I = (N_OK * I_pOK * T_OK + N_NG * I_pNG * T_NG) / T_m

```
Where N_OK is the number of OK pulses, I_pOK is the peak current value, T_OK is the ONTIME (1.4 µs or less), N_NG is the number of NG pulses, I_pNG is the peak current value, and T_NG is the ONTIME (0.6 µs or less). If the current waveform is approximated as a triangular wave, the average current I in the measurement time Tm becomes:

Fig. 7 shows the average current I for the example shown in Fig. 6. As shown in this figure, the average current at which wire breakage occurred is defined as I_BK, and the maximum average current at which wire breakage did not occur is defined as I_MAX.

The average current of each of these two types was evaluated for all 67 types of machining conditions experimented with. The results are organized by servo voltage (SV) and shown in Fig. 8 (when the upper and lower machining fluid nozzles are in close contact with the workpiece) and Fig. 9 (when the upper machining fluid nozzle is 2 mm away from the workpiece). In these figures, the thickness of the workpiece is indicated by the shape of the marker, and the filled markers indicate the average current I_BK at which breakage occurred, and the unfilled markers indicate the maximum average current I_MAX at which breakage did not occur. From these figures, the following points were clarified.

*   The presence or absence of breakage corresponds well to the magnitude of the average current, which is an index of machining energy, and a threshold value exists for the occurrence of breakage (dashed lines in Fig. 8 and Fig. 9). Therefore, it can be considered that there is an average machining energy (hereinafter referred to as the breakage limit energy) at which wire breakage occurs, and that excessive input of machining energy is the main cause of wire breakage.
*   The breakage limit energy tends to increase as the workpiece becomes thicker, but it is not proportional to the thickness. When the workpiece is thick, the part where discharge occurs becomes longer, and the machining energy per unit length of the wire electrode decreases, so the total amount of the breakage limit energy increases. However, because the flow of the machining fluid deteriorates and the wire is less likely to be cooled, it is thought that the breakage limit energy per unit length of the wire electrode decreases.
*   The breakage limit energy decreases when the machining fluid nozzle is moved away from the workpiece. It is thought that this occurs because the flow of the machining fluid deteriorates when the machining fluid nozzle is moved away from the workpiece, and the wire is less likely to be cooled.
*   The influence of the machining fluid nozzle installation position on the breakage limit energy is greater as the workpiece becomes thicker. It is thought that this is because, if the workpiece is thin, the machining fluid can flow even if the nozzle is separated, so the influence of the nozzle installation position becomes smaller.

---

### 4. Analysis of Discharge Pulse Patterns Near Wire Breakage Limits

While discharge concentration isn't always present before wire breakage occurs, the existence of a breakage limit energy suggests that wire failure is caused by excessive overall machining energy rather than localized wire overheating. This breakage limit energy varies significantly based on workpiece thickness and coolant flow conditions. Therefore, machining parameters need to be adjusted to prevent wire breakage when these conditions change, such as:

- During machining of chamfered or stepped parts (varying workpiece thickness)
- At workpiece end faces or corners (changing coolant flow)
- When coolant nozzle positions are adjusted

To address this, we investigated methods to detect when the wire approaches its breakage limit by analyzing discharge pulse patterns.

#### 4.1 Methodology for Discharge Pulse Analysis

To investigate how discharge pulses arise, experiments were conducted under conditions where plate thickness ranged from 10 mm to 150 mm, and wire diameter ranged from 0.2 mm to 0.3 mm. The machining-fluid nozzles were set in one of four configurations—both upper and lower nozzles in close contact with the workpiece (“close contact”), only the lower nozzle in contact (“upper separated”), neither nozzle in contact (“both separated”), or only the upper nozzle in contact (“lower separated”), as shown in Table 4—and the discharge frequency was varied.

As for the discharge frequency, we took the standard conditions for each wire diameter provided by the manufacturer and used the condition for 60 mm plate thickness (which has the highest machining energy) for all plate thicknesses. We then varied the frequency by inserting an additional pause after each discharge pulse. Concretely, we made it possible to set the additional pause from an external computer. The output from the machining power supply’s oscillator was input to a counter board in the computer so that it could count the discharge pulses. Starting from an additional pause of 40 μs, we gradually shortened this pause by 2 μs increments every 30 s to increase the machining energy, and recorded the number of normal discharge pulses that occurred within a 100 ms interval under those conditions

#### 4.2 Impact of Coolant Nozzle Configuration on Discharge Patterns

Figure 10 shows discharge pulse patterns for a 60mm workpiece under different nozzle configurations. Key findings include:

- At longer pause times, pulse counts were similar across all nozzle configurations
- As pause times shortened, pulse counts decreased in order: close > upper open > lower open > both open
- Near breakage limits, pulse counts plateaued despite shorter pause times

This suggests that while shorter pause times increase total discharges, most additional pulses are defective or short-circuit pulses rather than normal discharges.

Figure 11 demonstrates similar patterns for a 20mm workpiece, comparing "close" versus "both open" configurations. The relationships observed with the 60mm workpiece held true qualitatively for the thinner workpiece as well.

|  **Table 4** | **Test conditions** | | |
| :------------ |:----------------------|:---|:----|
| **WEDM** | MITSUBISHI FA20 (submerged)   |  |  |
| **Wire**  | Brass ø0.2, 0.25, 0.3 |  |  |
| **Workpiece**  | Steel (t 10, 20, 60, 100, 150) |  |  |
| **Nozzle**  | Both close, Upper open, Lower open, Both open |   |  |

---

### 5. Adaptive Control Experiment

#### 5.1 Off-Time Control Algorithm

Analysis of discharge patterns revealed that as the wire approaches its breakage limit, increasing the pulse frequency (by reducing pause time) does not significantly increase the number of normal discharges. This observation led to the development of a control algorithm that maintains safe operation by comparing the actual number of normal discharges to the expected number under optimal conditions (nozzles in close contact).

Figure 12 illustrates the relationship between pause time and normal discharge count for different nozzle configurations (close contact, upper separated, lower separated, and both separated). These characteristic curves share a common property - their slopes become more gradual near the breakage limit. This allows us to define a threshold curve (shown as a dashed line) that intersects each characteristic curve at its respective breakage limit point.

Using this threshold curve, the control system can dynamically adjust the pause time based on the measured number of normal discharges, as shown in Figure 13:
- If discharge count exceeds the threshold: decrease pause time
- If discharge count falls below threshold: increase pause time

This creates a self-regulating system where the operating point (defined by pause time and discharge count) naturally moves toward the intersection of:
1. The characteristic curve for current nozzle conditions
2. The threshold curve

This approach ensures machining occurs at maximum safe energy levels while automatically adapting to changing conditions. When coolant flow conditions change during machining, the operating point shifts to the new characteristic curve but maintains safe operation by finding the new intersection with the threshold curve.

Since workpiece thickness affects the characteristic curves, real-time thickness detection is necessary. We implemented the method proposed by Yafuku et al., which calculates thickness by:
1. Assuming constant kerf width
2. Recognizing that machining energy (average current) is proportional to machining volume (thickness × speed)
3. Computing thickness as the ratio of average current to machining speed

#### 5.2 Control Results

Initial testing used the cross-sectional workpiece shown in Figure 14, machined with a 0.25mm brass wire on steel. The machining direction was set from thick to thin sections, which typically presents higher risk of wire breakage. Figure 15 shows how the system automatically adjusted pause time to accommodate different conditions including:
- Approach sections
- Nozzle contact regions
- Step changes in thickness
- Sections with separated nozzles

The algorithm was then implemented in the machine's NC controller for comprehensive testing under varying conditions. Table 5 shows the test parameters used to compare machining speeds between conventional and new control methods.

Two scenarios were tested:
1. Submerged machining: Using the workpiece geometry in Figure 16, which includes both nozzle-contact and thin-plate sections
2. Non-submerged machining: Using the geometry in Figure 17, featuring two vertical holes where coolant flow is severely restricted

Results showed significant improvements:
- Submerged machining: 24% faster overall, mainly due to higher speeds in nozzle-contact regions (Table 6)
- Non-submerged machining: Nearly 3x faster, particularly in difficult-to-machine areas where conventional control required extremely conservative settings (Table 7)

---

### 6. Conclusion

The causes of wire breakage in wire electrical discharge machining were investigated, and a wire breakage prevention control device that adapts to changes in workpiece thickness and machining fluid flow conditions was developed. The following findings were obtained:

(1) The temporal and spatial concentration of discharge is not the main cause of breakage.
(2) Excessive input of machining energy is one of the main causes of breakage.
(3) The amount of machining energy that causes breakage varies depending on the workpiece thickness and the machining fluid flow conditions.
(4) The number of normal discharge pulses reflects the flow conditions of the machining fluid.
(5) An adaptive control algorithm based on the number of normal discharge pulses was proposed, and improvements in machining speed of 24% for submerged machining and 190% for blowing-off machining were achieved. The effectiveness of the algorithm was confirmed.

### References

1)  Masahiko Fukui, Natsuo Kinoshita, Kotaro Gamou, and Yoshiyuki Nomura: Study on Wire-cut Electrical Discharge Machining (Part 1) - On the Breakage of Wire Electrode -, Electrical Machining Society Journal, Vol. 11, No. 22, 1977, pp. 89-99.
2)  Masahiko Fukui, Natsuo Kinoshita, and Kanezane Okuda: Study on Wire-cut Electrical Discharge Machining (Part 2) - Method for Observation of Precursor Phenomena of Wire Breakage -, Electrical Machining Society Journal, Vol. 12, No. 24, 1978, pp. 24-36.
3)  Haruki Ohara, Yuji Okuyama, Yasunobu Tokiwa, and Hidenori Suzuki: A Study on Discharge Position Detection in Electrical Discharge Machining - Part 1 On the Cause of Breakage in Wire EDM -, Electrical Machining Society Journal, Vol. 23, No. 45, 1989, pp. 22-28.
4)  Haruki Ohara, Yuji Okuyama, Masatomo Yoneya, and Tadaaki Ioka: A Study on Discharge Position Detection in Electrical Discharge Machining - Part 2 Detection of Discharge Position in Wire EDM and Detection Characteristics-, Electrical Machining Society Journal, Vol. 24, No. 47, 1990, pp. 12-22.
5)  Haruki Ohara, Shunji Ishibashi, and Tadaaki Ioka: A Study on Discharge Position Detection in Electrical Discharge Machining - Part 3 Analysis of Discharge Position Detection Characteristics in Die Sinking and Wire EDM -, Electrical Machining Society Journal, Vol. 26, No. 51, 1992, pp. 13-27.
6)  Haruki Ohara, Mitsuru Abe, and Tsuyoshi Ohsumi: A Study of Wire Breakage Prevention Control in Wire EDM - Part 2 Classification Detection Method of Gap Signals according to Discharge Position -, Electrical Machining Society Journal, Vol. 32, No. 70, 1998, pp. 8-15.
7)  Hiroyuki Kojima and Masanori Kunieda: Observation of Discharge Point Distribution in Die Sinking EDM, Journal of the Japan Society of Precision Engineering, Vol. 57, No. 9, 1991, pp. 1603-1608.
8)  Tetsuya Yoshida, Hiroyuki Kojima, and Masanori Kunieda: Detection of Discharge Points in Die Sinking EDM by Multi-Point Power Supply Method, 1989 Autumn Meeting of the Japan Society of Precision Engineering, pp. 499-500.
9)  Tatsushi Sato, Seiji Sato, Hisashi Yamada, Takashi Magara, Yoshito Imai, and Kazuhiko Kobayashi: Machining Energy and Wire Breakage in Wire EDM, 1995 Spring Meeting of the Japan Society of Precision Engineering, pp. 983-984.
10) Haruki Ohara, Masashi Yamada, Tsuyoshi Ohsumi, and Masatoshi Hatano: A Study of Wire Breakage Prevention Control in Wire EDM (Part 3) - Discharge Position and Discharge Voltage in the Case of Large Current Discharge -, Electrical Machining Society Journal, Vol. 36, No. 81, 2002, pp. 24-30.
11) Haruki Ohara, Yasushi Iwata, Tsuyoshi Ohsumi, and Osamu Yasuda: Trial of Wire Temperature Distribution Measurement in Wire EDM, Electrical Machining Society Journal, Vol. 28, No. 57, 1994, pp. 21-31.
12) Haruki Ohara, Seiji Adachi, and Tsuyoshi Ohsumi: Trial of Wire Temperature Distribution Measurement in Wire EDM (Part 2) Wire Average Temperature During Machining -, Electrical Machining Society Journal, Vol. 31, No. 68, 1997, pp. 18-25.
13) Satoru Takeshita and Masanori Kunieda: Wire Temperature Measurement of Wire EDM Using Changes of Sensitivity of Discharge Point Detection, Journal of the Japan Society of Precision Engineering, Vol. 63, No. 9, 1997, pp. 1275-1279.
14) Satoru Takeshita, Kouji Yamiya, and Masanori Kunieda: Wire Temperature Distribution Simulation in Wire EDM, Journal of the Japan Society of Precision Engineering, Vol. 63, No. 10, 1997, pp. 1464-1468.
15) Yasuhito Shioda: Radiated Radio Waves in Wire Cut EDM, Electrical Machining Society Journal, Vol. 15, No. 29, 1981, pp. 11-19.
16) Haruki Ohara, Mitsuru Abe, and Tsuyoshi Ohsumi: A Study of Wire Breakage Prevention Control in Wire EDM Part 1: Comparison of Machining State Detection Methods of Wire EDM -, Electrical Machining Society Journal, Vol. 31, No. 68, 1997, pp. 11-17.
17) Takeshi Yafuku, Kazuhiko Kobayashi, Yutaka Tanaka, and Yoshio Ozaki: Optimal Control of Wire Cut EDM (Part 1), Electrical Machining Society Journal, Vol. 12, No. 24, 1978, pp. 37-51.
18) Takeshi Yafuku, Kazuhiko Kobayashi, Yutaka Tanaka, and Yoshio Ozaki: Optimal Control of Wire Cut EDM (Part 2), Electrical Machining Society Journal, Vol. 14, No. 28, 1980, pp. 1-9.
19) Haruki Ohara: Analysis of Wire Breakage Limit in Wire EDM - Part 1 Analysis of Machining Fluid Flow -, Electrical Machining Society Journal, Vol. 22, No. 44, 1988, pp. 10-22.

(Received November 14, 2013)