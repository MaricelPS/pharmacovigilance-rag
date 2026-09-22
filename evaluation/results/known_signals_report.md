# Known Signals Validation Report

Validates that our disproportionality analysis on FAERS 2024 detects safety signals published in peer-reviewed literature or reported by regulatory agencies (FDA, EMA).

## Overall detection metrics

| Metric | Value |
|--------|-------|
| Known signals evaluated | 11 |
| Present in FAERS 2024   | 11 (100%) |
| Detected (EMA criteria) | 11 (100%) |
| Detected (BCPNN)        | 11 (100%) |
| Detected (either)       | 11 (100%) |

## Per-signal breakdown

| ID | Drug | Best-match PT | n | ROR (95% CI) | IC | EMA | BCPNN | Year |
|----|------|---------------|---|--------------|----|-----|-------|------|
| k01 | semaglutide | Optic ischaemic neuropathy | 90 | 67.34 (51.46-88.12) | 5.03 | yes | yes | 2024 |
| k02 | semaglutide | Impaired gastric emptying | 818 | 73.37 (66.96-80.39) | 5.32 | yes | yes | 2023 |
| k03 | liraglutide | Impaired gastric emptying | 30 | 18.94 (13.19-27.20) | 3.82 | yes | yes | 2023 |
| k04 | tirzepatide | Impaired gastric emptying | 421 | 11.55 (10.36-12.87) | 3.18 | yes | yes | 2023 |
| k05 | semaglutide | Pancreatitis | 345 | 10.64 (9.51-11.90) | 3.23 | yes | yes | 2023 |
| k06 | liraglutide | Pancreatitis acute | 21 | 16.01 (10.42-24.58) | 3.52 | yes | yes | 2023 |
| k07 | semaglutide | Cholecystitis | 69 | 8.32 (6.51-10.64) | 2.87 | yes | yes | 2022 |
| k08 | liraglutide | Cholelithiasis | 27 | 14.25 (9.75-20.83) | 3.47 | yes | yes | 2022 |
| k09 | semaglutide | Suicidal ideation | 247 | 4.02 (3.54-4.57) | 1.94 | yes | yes | 2023 |
| k10 | tirzepatide | Injection site erythema | 1753 | 10.48 (9.94-11.05) | 3.05 | yes | yes | 2021 |
| k11 | semaglutide | Ileus | 252 | 35.83 (30.99-41.43) | 4.63 | yes | yes | 2023 |

## Detailed references

### k01 — semaglutide × ['Optic ischaemic neuropathy']
**Source**: Hathaway JT et al. Risk of Nonarteritic Anterior Ischemic Optic
Neuropathy in Patients Prescribed Semaglutide. JAMA Ophthalmol. 2024.
**Notes**: NAION cases reported in patients on semaglutide. First large-scale
cohort analysis prompting FDA post-marketing surveillance.

- Best match: **Optic ischaemic neuropathy**, n=90, ROR=67.34, IC=5.03
- Signal EMA: True, BCPNN: True

### k02 — semaglutide × ['Impaired gastric emptying', 'Gastroparesis']
**Source**: Sodhi M et al. Risk of Gastrointestinal Adverse Events Associated
With Glucagon-Like Peptide-1 Receptor Agonists for Weight Loss.
JAMA. 2023;330(18):1795-1797.
**Notes**: Gastroparesis signal in weight-loss cohort. Well-established
pharmacological effect via delayed gastric emptying.

- Best match: **Impaired gastric emptying**, n=818, ROR=73.37, IC=5.32
- Signal EMA: True, BCPNN: True

### k03 — liraglutide × ['Impaired gastric emptying', 'Gastroparesis']
**Source**: Sodhi M et al. JAMA. 2023;330(18):1795-1797.
**Notes**: Same signal class in liraglutide, first-in-class subcutaneous GLP-1.

- Best match: **Impaired gastric emptying**, n=30, ROR=18.94, IC=3.82
- Signal EMA: True, BCPNN: True

### k04 — tirzepatide × ['Impaired gastric emptying']
**Source**: FDA prescribing information for Mounjaro/Zepbound. Common adverse
reactions include delayed gastric emptying.
**Notes**: Class effect extended to the dual GIP/GLP-1 agonist.

- Best match: **Impaired gastric emptying**, n=421, ROR=11.55, IC=3.18
- Signal EMA: True, BCPNN: True

### k05 — semaglutide × ['Pancreatitis', 'Pancreatitis acute']
**Source**: FDA prescribing information for Ozempic/Wegovy. Warnings and
precautions section includes pancreatitis.
**Notes**: Long-standing GLP-1 class warning going back to exenatide.

- Best match: **Pancreatitis**, n=345, ROR=10.64, IC=3.23
- Signal EMA: True, BCPNN: True

### k06 — liraglutide × ['Pancreatitis', 'Pancreatitis acute']
**Source**: FDA prescribing information for Victoza/Saxenda.
**Notes**: Class warning applied to liraglutide.

- Best match: **Pancreatitis acute**, n=21, ROR=16.01, IC=3.52
- Signal EMA: True, BCPNN: True

### k07 — semaglutide × ['Cholelithiasis', 'Cholecystitis']
**Source**: He L et al. Association of Glucagon-Like Peptide-1 Receptor Agonist
Use With Risk of Gallbladder and Biliary Diseases. JAMA Intern Med.
2022;182(5):513-519.
**Notes**: Gallbladder disease signal replicated in FAERS-based analyses.

- Best match: **Cholecystitis**, n=69, ROR=8.32, IC=2.87
- Signal EMA: True, BCPNN: True

### k08 — liraglutide × ['Cholelithiasis', 'Cholecystitis']
**Source**: He L et al. JAMA Intern Med. 2022;182(5):513-519.
**Notes**: Same gallbladder/biliary signal in liraglutide.

- Best match: **Cholelithiasis**, n=27, ROR=14.25, IC=3.47
- Signal EMA: True, BCPNN: True

### k09 — semaglutide × ['Suicidal ideation']
**Source**: EMA. Signal review of semaglutide and suicidal ideation, 2023.
FDA statement on suicidality, January 2024 (no clear causal link
confirmed but signal under active monitoring).
**Notes**: Controversial signal detected in EudraVigilance. FDA's post-marketing
review did not confirm causality but signal remains under surveillance.

- Best match: **Suicidal ideation**, n=247, ROR=4.02, IC=1.94
- Signal EMA: True, BCPNN: True

### k10 — tirzepatide × ['Injection site pain', 'Injection site erythema']
**Source**: Frias JP et al. Tirzepatide versus Semaglutide Once Weekly in Patients
with Type 2 Diabetes. N Engl J Med. 2021;385:503-515. (SURPASS-2 trial)
**Notes**: Injection-site reactions well documented in SURPASS registration
trials. Not a "signal" in the disproportionality sense; used here as
a positive control (should appear massively).

- Best match: **Injection site erythema**, n=1753, ROR=10.48, IC=3.05
- Signal EMA: True, BCPNN: True

### k11 — semaglutide × ['Ileus']
**Source**: FDA label update for Ozempic, September 2023: warning added for
ileus based on post-marketing FAERS reports.
**Notes**: Label update triggered by post-marketing signal.

- Best match: **Ileus**, n=252, ROR=35.83, IC=4.63
- Signal EMA: True, BCPNN: True
