# Artificial Intelligence

## Prompt 16 — AI Digitizer

```
Role: Act as a senior AI engineer specializing in the integration of vision models and structured
data extraction.

Context: The store tracks sales history and daily transactions in physical notebooks. The user
(admin or salesperson) needs to take or upload a photo of the notebook page, and the system
must automatically extract: date, product, code, quantity, and price. The backend endpoint
POST /ia/digitalizar (Prompt 4) already exists as a defined contract.

Task: Implement the digitization workflow: (1) photo upload/capture on the frontend, (2) sending
to the backend, (3) backend calls the vision model to extract data, (4) backend returns the
EXTRACTED (not yet saved) data to the frontend, (5) frontend displays a pre-filled, editable
form for user review and correction, (6) only upon confirmation is the data sent to POST /ventas
to record the sale.

Format: Backend endpoint code that calls the vision model and structures the response (JSON
containing detected fields and a confidence level, if provided by the model), plus the frontend
validation form component used prior to saving.

Constraints: The AI ​​NEVER records the sale directly; it only proposes data. The user must be
able to edit any detected field before confirming. If a field cannot be detected (e.g., due to
illegible handwriting), it must remain empty and flagged for manual completion by the user—
never invented by the model. Log what was detected automatically versus corrected manually
to measure the digitizer's accuracy over time.
```