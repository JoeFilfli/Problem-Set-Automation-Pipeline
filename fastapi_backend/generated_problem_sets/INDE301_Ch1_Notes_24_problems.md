# Problem Set: INDE301_Ch1_Notes_24.pdf

Generated using AI-powered agent orchestration system.

---

## Chapter Analysis

**Topics Covered:**
- Interest Examples
- Simple and Compound Interest
- Equivalence
- Cash Flows
- Interest
- Engineering Economy and Economic Feasibility Analysis
- Time Value of Money
- Operations Research (OR) and Data Analytics
- Rule of 72
- What is Engineering Economy?
- Minimum Attractive Rate of Return (MARR)

**Key Formulas:**
- Interest earned = Final amount - Initial amount
- ROR = (Interest earned / Initial amount) × 100
- F = P + niP (Simple Interest)
- F = P(1 + i)^n (Compound Interest)
- Interest rate = (Interest accrued per time unit) / (Original amount)
- Interest rate = (Final loan amount - Original amount borrowed) / Original amount × 100
- n ≈ 72 / i (Rule of 72)

---

## Problem 1

**Difficulty:** EASY

**Topic:** Simple and Compound Interest

### Problem Statement

You deposit $1,000 in a savings account that earns a simple interest rate of 5% per year. How much interest will you earn after 3 years?

**Given:**
- Initial amount (P) = $1,000
- Interest rate (i) = 5%
- Time (n) = 3 years

**Find:**
- Total interest earned after 3 years

### Solution

To solve the problem of calculating the total interest earned on a deposit of $1,000 at a simple interest rate of 5% per year over a period of 3 years, we will follow a systematic approach.

### 1. Approach/Strategy
We will use the formula for calculating simple interest, which is given by:

$$
I = P \cdot i \cdot n
$$

where:
- \( I \) is the total interest earned,
- \( P \) is the principal amount (initial deposit),
- \( i \) is the interest rate (expressed as a decimal),
- \( n \) is the time in years.

### 2. Step-by-step Calculations

#### Step 1: Identify the given values
From the problem statement, we have:
- Initial amount (principal), \( P = 1000 \) dollars
- Interest rate, \( i = 5\% = 0.05 \) (as a decimal)
- Time, \( n = 3 \) years

#### Step 2: Substitute the values into the formula
Now, we substitute the values into the simple interest formula:

$$
I = P \cdot i \cdot n
$$

Substituting the values:

$$
I = 1000 \cdot 0.05 \cdot 3
$$

#### Step 3: Perform the calculations
Now we will calculate the interest:

1. Calculate \( 1000 \cdot 0.05 \):

   $$
   1000 \cdot 0.05 = 50
   $$

2. Now multiply this result by \( n \) (which is 3):

   $$
   I = 50 \cdot 3 = 150
   $$

### 3. Final Answer
The total interest earned after 3 years is:

$$
\boxed{150} \text{ dollars}
$$

### Summary
After depositing $1,000 in a savings account with a simple interest rate of 5% per year, the total interest earned after 3 years is $150. This calculation was performed using the simple interest formula, demonstrating the straightforward nature of simple interest calculations.

**Quality Assessment:** excellent

---

## Problem 2

**Difficulty:** MEDIUM

**Topic:** Rule of 72

### Problem Statement

You have invested $5,000 in a mutual fund that has an annual return of 9%. Using the Rule of 72, approximately how many years will it take for your investment to double?

**Given:**
- Investment amount = $5,000
- Annual return (i) = 9%

**Find:**
- Number of years to double the investment

### Solution

To solve the problem of determining how many years it will take for an investment of $5,000 to double at an annual return of 9% using the Rule of 72, we can follow a structured approach.

### 1. Approach/Strategy
The Rule of 72 is a simple formula used to estimate the number of years required to double an investment at a fixed annual rate of return. The formula is given by:

$$
n \approx \frac{72}{i}
$$

where:
- \( n \) is the number of years to double the investment,
- \( i \) is the annual interest rate expressed as a percentage.

In this case, we will substitute \( i = 9\% \) into the formula to find \( n \).

### 2. Step-by-step calculations

**Step 1: Identify the annual return rate.**
- Given: \( i = 9\% \)

**Step 2: Substitute the value into the Rule of 72 formula.**
Using the Rule of 72:

$$
n \approx \frac{72}{i}
$$

Substituting \( i = 9 \):

$$
n \approx \frac{72}{9}
$$

**Step 3: Perform the division.**

Calculating \( \frac{72}{9} \):

$$
n \approx 8
$$

### 3. Final answer(s)
Using the Rule of 72, it will take approximately **8 years** for the investment of $5,000 to double at an annual return of 9%.

### Summary
Thus, the final answer is:

**It will take approximately 8 years for the investment to double.**

**Quality Assessment:** excellent

---

## Problem 3

**Difficulty:** HARD

**Topic:** Minimum Attractive Rate of Return (MARR)

### Problem Statement

A company is considering a new project that requires an initial investment of $200,000. The project is expected to generate cash flows of $50,000 per year for 5 years. If the company's MARR is set at 10%, should the company undertake the project? Calculate the Net Present Value (NPV) to support your answer.

**Given:**
- Initial investment = $200,000
- Annual cash flow = $50,000
- MARR = 10%
- Number of years = 5

**Find:**
- NPV of the project
- Decision to undertake the project (Yes/No)

### Solution

To determine whether the company should undertake the project based on the Net Present Value (NPV) calculation, we will follow a systematic approach. Here’s how we will solve the problem:

### 1. Approach/Strategy
We will calculate the NPV of the project using the formula:

$$
\text{NPV} = \sum_{t=1}^{n} \frac{C_t}{(1 + r)^t} - C_0
$$

Where:
- \( C_t \) = cash flow at time \( t \)
- \( r \) = discount rate (MARR in this case)
- \( n \) = total number of periods (years)
- \( C_0 \) = initial investment

After calculating the NPV, we will compare it to zero:
- If \( \text{NPV} > 0 \), the project is financially viable and should be undertaken.
- If \( \text{NPV} < 0 \), the project should not be undertaken.

### 2. Step-by-step calculations

#### Given Data
- Initial investment \( C_0 = 200,000 \)
- Annual cash flow \( C_t = 50,000 \) for \( t = 1, 2, 3, 4, 5 \)
- MARR (discount rate) \( r = 10\% = 0.10 \)
- Number of years \( n = 5 \)

#### Step 1: Calculate Present Value of Cash Flows

We will calculate the present value of each annual cash flow over the 5 years.

For each year \( t \):
$$
PV_t = \frac{C_t}{(1 + r)^t}
$$

Calculating for each year:

- For \( t = 1 \):
$$
PV_1 = \frac{50,000}{(1 + 0.10)^1} = \frac{50,000}{1.10} \approx 45,454.55
$$

- For \( t = 2 \):
$$
PV_2 = \frac{50,000}{(1 + 0.10)^2} = \frac{50,000}{1.21} \approx 41,322.31
$$

- For \( t = 3 \):
$$
PV_3 = \frac{50,000}{(1 + 0.10)^3} = \frac{50,000}{1.331} \approx 37,688.45
$$

- For \( t = 4 \):
$$
PV_4 = \frac{50,000}{(1 + 0.10)^4} = \frac{50,000}{1.4641} \approx 34,257.28
$$

- For \( t = 5 \):
$$
PV_5 = \frac{50,000}{(1 + 0.10)^5} = \frac{50,000}{1.61051} \approx 31,081.08
$$

#### Step 2: Sum the Present Values

Now, we will sum all the present values calculated above:

$$
\text{Total PV} = PV_1 + PV_2 + PV_3 + PV_4 + PV_5
$$

Calculating the total:

$$
\text{Total PV} \approx 45,454.55 + 41,322.31 + 37,688.45 + 34,257.28 + 31,081.08 \approx 189,803.67
$$

#### Step 3: Calculate NPV

Now we can calculate the NPV using the total present value of cash flows:

$$
\text{NPV} = \text{Total PV} - C_0
$$

Substituting the values:

$$
\text{NPV} = 189,803.67 - 200,000 \approx -10,196.33
$$

### 3. Final answer(s)

- **NPV of the project**: \(\text{NPV} \approx -10,196.33\)
- **Decision**: Since the NPV is less than zero, the company **should not undertake the project**.

### Conclusion
The project does not meet the company's Minimum Attractive Rate of Return (MARR) of 10%, as indicated by the negative NPV. Therefore, the financial analysis suggests that the project is not a viable investment.

**Quality Assessment:** excellent

---

