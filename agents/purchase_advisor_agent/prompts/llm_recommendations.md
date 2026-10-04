Role: Act as a senior AI engineer responsible for the natural language generation layer and API integration built upon the proprietary ML model's results.

Context: The ultimate goal is to generate a purchase recommendation readable by a non-technical user (visible only to the Administrator). Example of expected output:

Upcoming holiday: Holy Week
Product: Religious candles
Current stock: 18
Estimated demand: 45
Recommended quantity: 30 units
Reason: historical increase in sales during this holiday.

Task: Implement the natural language translation and API endpoint layer:
(1) A call to a language model to convert the numerical result and features provided by the trained ML model into a recommendation text formatted like the example.
(2) Backend endpoint `GET /recomendaciones` that returns the list of recommendations already phrased in natural language, following the example format.

Format:
1. Backend endpoint `GET /recomendaciones` that returns the list of recommendations formatted in natural language.

Constraints: This endpoint is accessible only to the Administrator role. Do not replace your custom ML model with a direct call to an LLM that "guesses" the recommendation without going through the trained model—the LLM only handles phrasing, while the ML model makes the decision.