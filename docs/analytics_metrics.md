# Mausam Mitra Analytics & Intelligence Metrics

This document centralizes the definitions of the key operational metrics surfaced in the Analytics API.

## 1. Correlation Rate
- **Definition**: Percentage of eligible reports that have been linked to a correlated incident.
- **Source Table**: `reports`
- **Calculation**: `(reports where incident_id IS NOT NULL) / (total reports) * 100`
- **Interpretation**: Shows how effectively raw report signals are being associated with real, recognized incidents.
- **Limitations**: This is NOT a measure of truth, accuracy, or incident severity. It simply measures correlation algorithm coverage and volume.

## 2. Average Classifier Confidence
- **Definition**: The average match strength of the language model assigning a category to a report text.
- **Source Table**: `reports`
- **Calculation**: `AVG(classifier_confidence)` where `classifier_confidence` is present.
- **Interpretation**: Indicates the model's confidence in its text categorization.
- **Limitations**: This is purely a natural language processing metric. It does NOT indicate the truth, authenticity, or human verification of the report itself. It is not an "accuracy" metric as there is no labeled evaluation dataset.

## 3. Verified Reports
- **Definition**: Reports that have been manually confirmed by a Verifier or Analyst.
- **Source Table**: `reports`
- **Calculation**: `COUNT(id)` where `verification_status = 'VERIFIED'`.
- **Interpretation**: Signals that have been successfully corroborated and trusted by operational staff.
- **Limitations**: A verified report does not mean it is a massive incident; it simply means the signal itself was genuine.

## 4. Correlated Incidents
- **Definition**: Operational incidents that were automatically generated or correlated by the system (as opposed to SEEDED or MANUAL ones).
- **Source Table**: `incidents`
- **Calculation**: `COUNT(id)` where `origin = 'CORRELATED'`.
- **Interpretation**: Represents the real automated workload and intelligence output of the platform.
- **Limitations**: Excludes seeded and manual incidents, so it may be lower than the `Total Incidents` metric.

## 5. Active Incidents
- **Definition**: Correlated incidents currently in an active, ongoing state.
- **Source Table**: `incidents`
- **Calculation**: `COUNT(id)` where `origin = 'CORRELATED'` AND `status = 'ACTIVE'`.
- **Interpretation**: The immediate operational priority queue.

## 6. Weather Averages
- **Definition**: Average environmental observations across the given time period.
- **Source Table**: `weather_observations`
- **Calculation**: `AVG(temperature)`, `AVG(humidity)`, etc., for observations in the time bucket.
- **Interpretation**: Gives regional weather context.
- **Limitations**: Only aggregates available local telemetry. If live weather ingestion is failing (e.g. 401 Unauthorized from provider), this will show as "Data not available" rather than a zero or fake data point.
