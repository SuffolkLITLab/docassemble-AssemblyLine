# Document Assembly Line - Runtime Code

A jurisdiction-agnostic runtime package that supports rapidly automating forms
with a controlled style. Saves time over using just the base docassemble
platform.

This is the run-time code that supports the interviews at https://courtformsonline.org

This package supersedes [MAVirtualCourt](https://github.com/SuffolkLITLab/docassemble-MAVirtualCourt).

# Migration

* Remove any references to MAVirtualCourt. Add an include block like this at the top
  of your interview YAML file

```
include:
  - docassemble.AssemblyLine:al_package.yml
  - docassemble.MassAccess:massaccess.yml
```

* Change references to `basic_questions_intro_screen` to `al_intro_screen`
* Change references to `courts[0]` to trial_court