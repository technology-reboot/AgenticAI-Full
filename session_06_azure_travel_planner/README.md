# Azure Travel Planner Training Labs

This folder contains a simple, readable training version of the Azure AI Studio travel-planner labs from the session guide.

## What is included?

- Lab 1: Speech Agent + Vision Agent
- Lab 2: Trip Planner Agent + Weather Agent
- Lab 3: Orchestrator flow and simple deployment-style demo

## Project structure

```text
labs/session_06_azure_travel_planner/
├── README.md
├── requirements.txt
├── .env.example
├── common.py
├── lab1_speech_vision_agents.py
├── lab2_trip_planner_weather.py
├── lab3_orchestrator_deploy.py
└── data/
    └── README.md
```

## Setup

1. Open a terminal in this folder.
2. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install the Python packages:

```bash
pip install -r requirements.txt
```

4. Create your environment file:

```bash
copy .env.example .env
```

5. Update .env with your Azure OpenAI values.

## Run the labs

### Lab 1

```bash
python lab1_speech_vision_agents.py
```

### Lab 2

```bash
python lab2_trip_planner_weather.py
```

### Lab 3

```bash
python lab3_orchestrator_deploy.py
```

## Notes

- The scripts work in demo mode even if Azure credentials are not available.
- For live Azure execution, place your real files in the data folder:
  - data/travel_query.wav
  - data/hotel_photo.jpg
- The code is written for training clarity and uses simple comments so participants can follow the flow easily.
