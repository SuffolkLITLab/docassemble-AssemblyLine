# Demographic Data Fields

This document describes the demographic data collection fields available in the AssemblyLine library.

## Overview

The AssemblyLine library now includes methods for collecting demographic information from users. These methods follow the same pattern as existing field methods like `gender_fields()` and `language_fields()`.

## Available Methods

### `race_and_ethnicity_fields()`

Collects race and ethnicity information using checkboxes to allow multiple selections.

**Attributes:**
- `race_ethnicity`: DACheckboxes object containing selected race/ethnicity values
- `race_ethnicity_other`: Text field for custom race/ethnicity when "Other" is selected

**Possible Values:**
- `american_indian_alaska_native`: American Indian or Alaska Native
- `asian`: Asian
- `black_african_american`: Black or African American
- `hispanic_latino`: Hispanic or Latino
- `native_hawaiian_pacific_islander`: Native Hawaiian or Other Pacific Islander
- `white`: White
- `two_or_more_races`: Two or more races
- `other`: Other (enables text field for specification)
- `prefer_not_to_say`: Prefer not to say

**Usage:**
```yaml
fields:
  - code: |
      users[0].race_and_ethnicity_fields(show_help=True)
```

### `age_range_fields()`

Collects age range information using radio buttons.

**Attributes:**
- `age_range`: Single value representing the selected age range

**Possible Values:**
- `under_18`: Under 18
- `18_24`: 18-24
- `25_34`: 25-34
- `35_44`: 35-44
- `45_54`: 45-54
- `55_64`: 55-64
- `65_74`: 65-74
- `75_and_over`: 75 and over
- `prefer_not_to_say`: Prefer not to say

**Usage:**
```yaml
fields:
  - code: |
      users[0].age_range_fields(show_help=True)
```

### `income_range_fields()`

Collects household income range information using radio buttons.

**Attributes:**
- `income_range`: Single value representing the selected income range

**Possible Values:**
- `under_15k`: Less than $15,000
- `15k_24k`: $15,000 - $24,999
- `25k_34k`: $25,000 - $34,999
- `35k_49k`: $35,000 - $49,999
- `50k_74k`: $50,000 - $74,999
- `75k_99k`: $75,000 - $99,999
- `100k_149k`: $100,000 - $149,999
- `150k_and_over`: $150,000 or more
- `prefer_not_to_say`: Prefer not to say

**Usage:**
```yaml
fields:
  - code: |
      users[0].income_range_fields(show_help=True)
```

### `occupation_fields()`

Collects occupation classification information using radio buttons.

**Attributes:**
- `occupation`: Single value representing the selected occupation category
- `occupation_other`: Text field for custom occupation when "Other" is selected

**Possible Values:**
- `management_business_science_arts`: Management, business, science, and arts
- `service`: Service
- `sales_office`: Sales and office
- `natural_resources_construction_maintenance`: Natural resources, construction, and maintenance
- `production_transportation_material_moving`: Production, transportation, and material moving
- `military`: Military
- `student`: Student
- `retired`: Retired
- `unemployed`: Unemployed
- `other`: Other (enables text field for specification)
- `prefer_not_to_say`: Prefer not to say

**Usage:**
```yaml
fields:
  - code: |
      users[0].occupation_fields(show_help=True)
```

## Method Parameters

All demographic field methods support the following parameters:

- `show_help` (bool): Whether to show additional help text. Defaults to False.
- `show_if` (Union[str, Dict[str, str], None]): Condition to determine if the field should be shown. Defaults to None.
- `maxlengths` (Dict[str, int], optional): A dictionary of field names and their maximum lengths. Default is None.
- `choices` (Optional[Union[List[Dict[str, str]], Callable]]): Custom choices or a callable that returns choices. Defaults to standard options.

## Example Usage

### Single Demographics Question

```yaml
---
sets:
  - users[0].race_ethnicity
  - users[0].age_range
  - users[0].income_range
  - users[0].occupation
id: demographic information
question: |
  Tell us about yourself
subquestion: |
  This information helps us understand who we serve. All questions are optional.
fields:
  - code: |
      users[0].race_and_ethnicity_fields(show_help=True)
  - code: |
      users[0].age_range_fields(show_help=True)
  - code: |
      users[0].income_range_fields(show_help=True)
  - code: |
      users[0].occupation_fields(show_help=True)
```

### Individual Questions

```yaml
---
sets:
  - users[0].race_ethnicity
question: |
  What is your race and ethnicity?
fields:
  - code: |
      users[0].race_and_ethnicity_fields(show_help=True)
```

## Integration with Weaver

The demographic fields are designed to be compatible with the Assembly Line Weaver. The field methods can be used in Weaver-generated interviews by adding them to the appropriate question blocks.

## Privacy Considerations

All demographic questions include "Prefer not to say" options to respect user privacy. The questions are designed to be optional and can be conditionally shown using the `show_if` parameter.

## Customization

All field methods accept custom choices through the `choices` parameter, allowing developers to adapt the categories to their specific needs or jurisdictional requirements.