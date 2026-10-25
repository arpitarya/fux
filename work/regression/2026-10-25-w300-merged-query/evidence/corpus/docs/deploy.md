# Deploying our widget service

Our deploy pipeline builds the widget image, pushes it to the registry and
promotes it from staging to production after the smoke tests pass.
