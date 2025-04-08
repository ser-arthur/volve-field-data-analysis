# Volve Field Production Data Analysis

## Overview

This project analyzes oil well production data from the Volve Field to understand production trends, water injection
impact, and well performance over time. The dataset consists of daily production data for multiple wells, and the
analysis is conducted using Python, Pandas, Matplotlib, and Seaborn.

## Objective
The goal of this analysis is to:
- Examine cumulative oil, gas, and water production trends. 
- Investigate well-level production performance. 
- Analyze the impact of water injection on production. 
- Identify signs of water breakthrough and production decline patterns. 
- Study Gas-Oil Ratio (GOR) trends to understand reservoir depletion. 
- Evaluate Water-Oil Ratio (WOR) trends to assess water breakthrough timing. 
- Explore pressure behavior in relation to production decline.

You can project in jupyter notebook here [Volve-Field Analysis](https://nbviewer.org/github/ser-arthur/volve-field-data-analysis/blob/main/volve-field-data-analysis.ipynb)

## Dataset

The dataset includes:
 - Daily production data for wells in the Volve Field.
 - Key parameters such as oil, gas, and water production rates, and pressure data.
 - Injection data for water injector wells.
 - GOR and WOR data for analyzing fluid behavior. 
 - Pressure measurements to study reservoir depletion.

## Key Analyses & Insights
**Field-Level Production Analysis:**
- Evaluates total oil, gas, and water production trends.
- Identifies key production phases (ramp-up, peak, decline).

**Well-Level Production Performance:**
- Compares oil, gas, and water output across different wells.
- Highlights high-performing and low-performing wells.

**Gas-Oil Ratio (GOR) & Water-Oil Ratio (WOR) Trends:**
- Tracks GOR changes over time to assess reservoir depletion. 
- Analyzes WOR trends to detect early signs of water breakthrough.

**Water Injection & Production Correlation:**
- Examines how water injection influenced production rates. 
- Identifies wells affected by water breakthrough.

**Pressure vs. Production Analysis:**
- Studies how downhole pressure trends correlate with oil and gas production decline.
- Evaluates pressure support from injection wells and its effect on production.

**Operational Time & Production Efficiency:**
- Assesses well uptime and how it relates to production performance.

## Technologies Used
 - Python
 - Pandas (for data manipulation)
 - Matplotlib & Seaborn (for data visualization)
 - Jupyter Notebook (for interactive analysis)

## How to Use This Notebook
 - Clone this repository or download the notebook.
 - Open the Jupyter Notebook and run the cells sequentially.
 - Ensure you have the necessary dependencies installed: `pip install pandas matplotlib seaborn` 
 - Load the dataset and explore the visualizations and insights.

## Future Work
- Expanding pressure analysis to explore pressure drawdown effects on well performance.
- Implementing production forecasting & decline curve analysis.
- Studying GOR behavior at different production stages for better reservoir management.
- Enhancing injection-efficiency analysis to improve secondary recovery insights.
