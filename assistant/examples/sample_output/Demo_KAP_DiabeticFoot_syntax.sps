* AsaadStat — SPSS syntax generated to mirror the automated analysis.
* Open your .sav file first, then run all.

RELIABILITY /VARIABLES=K1 K2 K3 K4 K5 K6 K7 K8 K9 K10 /SCALE('Knowledge') ALL
  /MODEL=ALPHA /STATISTICS=DESCRIPTIVE SCALE /SUMMARY=TOTAL.
COMPUTE Knowledge_score = SUM.10(K1, K2, K3, K4, K5, K6, K7, K8, K9, K10).
COMPUTE Knowledge_pct = (Knowledge_score - 0) / (10 - 0) * 100.
RECODE Knowledge_pct (LOWEST THRU 59.999=1) (60 THRU 79.999=2) (80 THRU HIGHEST=3) INTO Knowledge_level.
VALUE LABELS Knowledge_level 1 'Poor' 2 'Moderate' 3 'Good'.
EXECUTE.

* Reverse-code A8 (example for a 1–5 scale; adjust to your item range).
RECODE A8 (1=5)(2=4)(3=3)(4=2)(5=1) INTO A8_r.
RELIABILITY /VARIABLES=A1 A2 A3 A4 A5 A6 A7 A8_r /SCALE('Attitude') ALL
  /MODEL=ALPHA /STATISTICS=DESCRIPTIVE SCALE /SUMMARY=TOTAL.
COMPUTE Attitude_score = SUM.8(A1, A2, A3, A4, A5, A6, A7, A8_r).
COMPUTE Attitude_pct = (Attitude_score - 8) / (40 - 8) * 100.
RECODE Attitude_pct (LOWEST THRU 59.999=1) (60 THRU 79.999=2) (80 THRU HIGHEST=3) INTO Attitude_level.
VALUE LABELS Attitude_level 1 'Negative' 2 'Neutral' 3 'Positive'.
EXECUTE.

RELIABILITY /VARIABLES=P1 P2 P3 P4 P5 P6 P7 /SCALE('Practice') ALL
  /MODEL=ALPHA /STATISTICS=DESCRIPTIVE SCALE /SUMMARY=TOTAL.
COMPUTE Practice_score = SUM.7(P1, P2, P3, P4, P5, P6, P7).
COMPUTE Practice_pct = (Practice_score - 0) / (7 - 0) * 100.
RECODE Practice_pct (LOWEST THRU 59.999=1) (60 THRU 79.999=2) (80 THRU HIGHEST=3) INTO Practice_level.
VALUE LABELS Practice_level 1 'Poor' 2 'Fair' 3 'Good'.
EXECUTE.

FREQUENCIES VARIABLES=age_group gender nationality education experience facility training /ORDER=ANALYSIS.

EXAMINE VARIABLES=Knowledge_score Attitude_score Practice_score /PLOT NPPLOT /STATISTICS DESCRIPTIVES.

* age_group: use T-TEST (2 groups) or ONEWAY (>2) if normal; else NPAR TESTS.
NPAR TESTS /M-W= Knowledge_score Attitude_score Practice_score BY age_group(1 2).
NPAR TESTS /K-W= Knowledge_score Attitude_score Practice_score BY age_group(1 9).

* gender: use T-TEST (2 groups) or ONEWAY (>2) if normal; else NPAR TESTS.
NPAR TESTS /M-W= Knowledge_score Attitude_score Practice_score BY gender(1 2).
NPAR TESTS /K-W= Knowledge_score Attitude_score Practice_score BY gender(1 9).

* nationality: use T-TEST (2 groups) or ONEWAY (>2) if normal; else NPAR TESTS.
NPAR TESTS /M-W= Knowledge_score Attitude_score Practice_score BY nationality(1 2).
NPAR TESTS /K-W= Knowledge_score Attitude_score Practice_score BY nationality(1 9).

* education: use T-TEST (2 groups) or ONEWAY (>2) if normal; else NPAR TESTS.
NPAR TESTS /M-W= Knowledge_score Attitude_score Practice_score BY education(1 2).
NPAR TESTS /K-W= Knowledge_score Attitude_score Practice_score BY education(1 9).

* experience: use T-TEST (2 groups) or ONEWAY (>2) if normal; else NPAR TESTS.
NPAR TESTS /M-W= Knowledge_score Attitude_score Practice_score BY experience(1 2).
NPAR TESTS /K-W= Knowledge_score Attitude_score Practice_score BY experience(1 9).

* facility: use T-TEST (2 groups) or ONEWAY (>2) if normal; else NPAR TESTS.
NPAR TESTS /M-W= Knowledge_score Attitude_score Practice_score BY facility(1 2).
NPAR TESTS /K-W= Knowledge_score Attitude_score Practice_score BY facility(1 9).

* training: use T-TEST (2 groups) or ONEWAY (>2) if normal; else NPAR TESTS.
NPAR TESTS /M-W= Knowledge_score Attitude_score Practice_score BY training(1 2).
NPAR TESTS /K-W= Knowledge_score Attitude_score Practice_score BY training(1 9).

CROSSTABS /TABLES=gender education experience training BY Knowledge_level
  /STATISTICS=CHISQ PHI /CELLS=COUNT ROW EXPECTED.

NONPAR CORR /VARIABLES=Knowledge_score Attitude_score Practice_score /PRINT=SPEARMAN TWOTAIL NOSIG.

LOGISTIC REGRESSION VARIABLES Practice_adequate
  /METHOD=ENTER gender education experience training Knowledge_score
  /CONTRAST (gender)=Indicator(1)
  /PRINT=GOODFIT CI(95) /CRITERIA=PIN(.05) POUT(.10) ITERATE(20) CUT(.5).
