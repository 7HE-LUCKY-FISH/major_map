Web App for SJSU to plan their 4 years before classes even start.

[![CI](https://github.com/7HE-LUCKY-FISH/major_map/actions/workflows/ci.yml/badge.svg)](https://github.com/7HE-LUCKY-FISH/major_map/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/7HE-LUCKY-FISH/major_map/branch/main/graph/badge.svg)](https://codecov.io/gh/7HE-LUCKY-FISH/major_map)

https://main.dy0gxxub1du5m.amplifyapp.com

An update link instead of the auto-generated AWS Amplify will be made after a fully working deployment 

> **For CMPE 195B:** Please read **[README_195.md](README_195.md)** first.

## Overview

Major Map is a comprehensive web application designed for San Jose State University (SJSU) students to streamline the complex process of long-term academic planning and semester scheduling. By consolidating fragmented information into a single platform, the application helps students stay on track for timely graduation.

## Features

- **Personalized Roadmaps**: Generates custom academic plans based on a student's specific major requirements and already completed coursework.
- **Predictive Scheduling**: Utilizes machine learning models trained on historical data to predict professor assignments and class timings for future semesters.
- **Historical Data Search**: Allows users to search through past course schedule data for reference.
- **Professor Insights**: Integrates professor ratings and historical offering patterns directly into the scheduling interface.

## Getting Started

### Prerequisites

- **Python**: 3.10.X+
- **Node.js**: v20.X+
- **MySQL Server**: Required for the backend database.

### Installation

#### Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "JWT_SECRET=your-secret-here" > .env

# Generate required ML artifacts
python3 -m ml.train_hoang  # or ml.train_anthony
```

#### Frontend Setup

```bash
cd frontend
npm install
npm build
```


#### Database Setup

```bash
cd backend/database

# Start up MySQL8
# Run
python3 load_schdule_data.py

```
All data should now be loaded
