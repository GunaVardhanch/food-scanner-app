# 🍱 NutriScanner — Trained Barcodes for Manual Testing

All **20 barcodes** below are pre-seeded into the local SQLite database.
Scan them at **http://localhost:3000** — no internet needed.

---

## 🟢 GREEN — NutriScore A & B &nbsp;*(Score ≥ 7.0)*

| # | Barcode | Product | Brand | NutriScore | Score |
|---|---------|---------|-------|:----------:|------:|
| 1 | `8906042711014` | Patanjali Aloe Vera Juice | Patanjali | **A** | 9.2 |
| 2 | `8901262173034` | MTR Ready to Eat Palak Paneer | MTR Foods | **A** | 8.1 |
| 3 | `8904109601200` | Too Yumm! Multigrain Chips | RP-SG Group | **B** | 7.8 |
| 4 | `8800025000290` | Nescafé Classic Instant Coffee | Nestlé | **B** | 7.5 |
| 5 | `8901826100016` | Dabur Pure Honey | Dabur | **B** | 7.0 |

---

## 🟡 YELLOW — NutriScore C & D &nbsp;*(Score 4.0 – 6.9)*

| # | Barcode | Product | Brand | NutriScore | Score |
|---|---------|---------|-------|:----------:|------:|
| 6  | `5000159484695` | McVitie's Digestive Biscuits | McVitie's | **C** | 6.2 |
| 7  | `8901058002085` | Nestlé Milo Energy Drink | Nestlé | **C** | 5.8 |
| 8  | `8901826400043` | Dabur Real Mango Juice | Dabur | **C** | 5.5 |
| 9  | `8901491100108` | 7UP Nimbooz Masala Soda | PepsiCo | **C** | 5.1 |
| 10 | `8901030706615` | Parle-G Original Gluco Biscuits | Parle | **D** | 4.8 |
| 11 | `8901063151849` | Britannia Good Day Butter Cookies | Britannia | **D** | 4.3 |
| 12 | `8906001200014` | Amul Pure Butter | Amul | **D** | 4.0 |

---

## 🔴 RED — NutriScore E &nbsp;*(Score < 4.0)*

| # | Barcode | Product | Brand | NutriScore | Score | Flagged Additives |
|---|---------|---------|-------|:----------:|------:|-------------------|
| 13 | `8901058852424` | Maggi 2-Minute Noodles Masala | Nestlé | **E** | 3.8 | INS 627, INS 631 |
| 14 | `8901491502230` | Lay's Classic Salted Chips | PepsiCo | **E** | 3.5 | — |
| 15 | `8901764004404` | Parle Monaco Smart Chips | Parle | **E** | 3.2 | INS 627, INS 631 |
| 16 | `8902102901013` | Kurkure Masala Munch | PepsiCo | **E** | 3.0 | INS 627, INS 631, INS 330 |
| 17 | `8901058501898` | KitKat 4 Finger Milk Chocolate | Nestlé | **E** | 2.8 | INS 322 |
| 18 | `7622201169091` | Cadbury Dairy Milk Chocolate | Mondelēz | **E** | 2.5 | INS 442, INS 476 |
| 19 | `8901058505476` | Nestlé Munch Chocolate Wafer Bar | Nestlé | **E** | 2.2 | INS 322 |
| 20 | `8901764001052` | Parle Hide & Seek Choc Chip Biscuits | Parle | **E** | 2.0 | INS 322, INS 503 |

---

## 📋 All 20 Barcodes — Quick Reference

```
#   BARCODE           PRODUCT                              GRADE   SCORE
─────────────────────────────────────────────────────────────────────────
1   8906042711014     Patanjali Aloe Vera Juice            GREEN    9.2
2   8901262173034     MTR Ready to Eat Palak Paneer        GREEN    8.1
3   8904109601200     Too Yumm! Multigrain Chips           GREEN    7.8
4   8800025000290     Nescafé Classic Instant Coffee       GREEN    7.5
5   8901826100016     Dabur Pure Honey                     GREEN    7.0
6   5000159484695     McVitie's Digestive Biscuits         YELLOW   6.2
7   8901058002085     Nestlé Milo Energy Drink             YELLOW   5.8
8   8901826400043     Dabur Real Mango Juice               YELLOW   5.5
9   8901491100108     7UP Nimbooz Masala Soda              YELLOW   5.1
10  8901030706615     Parle-G Original Gluco Biscuits      YELLOW   4.8
11  8901063151849     Britannia Good Day Butter Cookies    YELLOW   4.3
12  8906001200014     Amul Pure Butter                     YELLOW   4.0
13  8901058852424     Maggi 2-Minute Noodles Masala        RED      3.8
14  8901491502230     Lay's Classic Salted Chips           RED      3.5
15  8901764004404     Parle Monaco Smart Chips             RED      3.2
16  8902102901013     Kurkure Masala Munch                 RED      3.0
17  8901058501898     KitKat 4 Finger Milk Chocolate       RED      2.8
18  7622201169091     Cadbury Dairy Milk Chocolate         RED      2.5
19  8901058505476     Nestlé Munch Chocolate Wafer Bar     RED      2.2
20  8901764001052     Parle Hide & Seek Choc Chip          RED      2.0
```

---

## 🧪 How to Test

### Option A — Physical Barcode
Scan the actual product barcode with your camera in the app.

### Option B — Generate a Barcode Image
1. Go to [barcode.tec-it.com/en/EAN13](https://barcode.tec-it.com/en/EAN13)
2. Enter any 13-digit barcode number from the list above
3. Download the EAN-13 image
4. Upload or scan it in the app at **http://localhost:3000**

---

## ✅ What to Verify Per Scan

| Aspect | Expected Behaviour |
|--------|--------------------|
| **Score** | Matches the table value (±0.1) |
| **Grade Badge** | 🟢 GREEN / 🟡 YELLOW / 🔴 RED matches the table |
| **Additives Section** | INS codes listed in *Flagged Additives* column appear |
| **Scan History** | Entry appears in the History tab after each scan |
| **Analytics Chart** | Score bar added to the Trends chart |

---

## 🏗️ Re-seed / Retrain

If the database is reset, re-run:

```bash
cd backend
.\venv\Scripts\python.exe train_and_seed.py
```

This re-seeds all 20 products **and** retrains the XGBoost model in one step.
