# OptiTime

OptiTime is a Python-based timetable generation project. It produces feasible and optimized class timetables from enrollment and room data, validates the results for constraint satisfaction, and provides a Streamlit frontend for visualizing weekly schedules for students and professors.

## Features (high level)
- Data generation scripts to create rooms, enrollments, and other required inputs.
- A feasibility model (`new_model.py`) that finds timetables satisfying hard constraints (no conflicts, required number of slots, room capacities, etc.).
- An optimization (penalty) model (`penalty_model.py`) that adds an objective to reduce student fatigue (late time slots) and balance professor workload (e.g., avoid assigning 3 or more slots per day when possible).
- A validator (`validate.py`) to verify:
  - each course gets its required number of slots per week,
  - no student has overlapping classes,
  - professor workloads conform to rules (e.g., maximum classes per day),
  - other problem-specific checks.
- A Streamlit-based frontend to visualize the generated `timetable.json` so students and faculty can view weekly schedules.

## Repository layout
- data/  
  - Contains generated data for rooms, enrollments, etc. This folder is populated by the data generation scripts.
- gen_data_comp.py  
  - Script to generate comparison/complex dataset(s) (used to create larger/more detailed data).
- generate_data.py  
  - Script to create the basic dataset required by the models (rooms, enrollments, courses, etc.).
- new_model.py  
  - Feasibility-only model: finds a timetable that satisfies hard constraints (no objective function).
- penalty_model.py  
  - Optimization model: includes a penalty/objective function to reduce student fatigue (late slots) and limit professor workloads (e.g., avoid >2 classes/day).
- validate.py  
  - Checks the output timetable for constraint satisfaction and overall correctness.
- results/timetable_output.json  
  - The generated timetable produced by either model (feasibility or penalty) — used by the frontend for display.
- requirements.txt  
  - Python dependencies required to run the project.
- frontend/visualize.py  
  - Streamlit app that renders the timetable for easy viewing (the filename may vary; replace accordingly when running).


## Getting started

1. Clone the repository
   - git clone https://github.com/GOW444/OptiTime.git
   - cd OptiTime

2. Create and activate a Python virtual environment (recommended)
   - python3 -m venv venv
   - Linux / macOS: source venv/bin/activate
   - Windows (PowerShell): .\venv\Scripts\Activate.ps1

3. Install dependencies
   - pip install -r requirements.txt

## Typical usage / example workflow

1. Generate data
   - For a basic dataset:
     - python generate_data.py
   - For larger/complex datasets (or to regenerate with increased room capacities):
     - python gen_data_comp.py
   These scripts populate the `data/` folder with room definitions, enrollment lists, course requirements, etc. (Note: we increased room capacities in the generator to allow creating timetables for larger datasets.)

2. Run the feasibility model (no objective)
   - python new_model.py
   Output: `new_timetable_output.json` (feasible timetable satisfying the hard constraints).

3. Run the penalty/optimization model (improved schedules)
   - python penalty_model.py
   Output: `timetable_output.json` (timetable that minimizes penalties related to student fatigue and professor workload).  
   The penalty model was added to penalize late time slots for students and to limit professor workload per day (previously some professors were assigned 3 slots/day; with the objective the model prefers at most 2 classes/day where possible).

4. Validate the generated timetable
   - python validate.py
   The validator confirms that all courses received their required number of slots, there are no student conflicts, professor workloads are within acceptable limits, and other constraints are met.

5. Visualize with Streamlit
   - streamlit run visualize.py
   The frontend reads `timetable_output.json` and provides a visual weekly schedule so students and faculty can view their individual timetables.

## Notes and tips
- If you change room capacities or other data-generation parameters, re-run the appropriate generator script before running the models.
- The feasibility model (`new_model.py`) is useful to verify whether a timetable that satisfies the hard constraints exists. The penalty model (`penalty_model.py`) improves on that by optimizing soft constraints such as student fatigue and professor daily workload.
- The exact CLI options (if any) for each script may vary. Check the top of each Python file for usage examples or run them with `-h`/`--help` if argument parsing is implemented.

## Troubleshooting
- Missing dependencies: ensure the virtual environment is active and run `pip install -r requirements.txt`.
- No timetable produced: check model logs/prints for infeasibility messages (run the feasibility model first to confirm constraints are satisfiable).
- Frontend not loading timetable: ensure `timetable_output.json` exists in the expected location (project root or a path the frontend expects).

## Contributing
Contributions are welcome.


## Contact
For questions about the implementation or to report issues, please open an issue on the GitHub repository.

Happy scheduling!
