# github flow
This repository is maintained according to [github flow] (http://scottchacon.com/2011/08/31/github-flow.html). The naming convention for pull request branches in github flow is as follows

Feature type/$(git describe --tags)/Feature name

For example, use a branch name such as Feature/2.2.12/support-bonding-NIC.

## Feature type
For the feature type, specify one of the following.

## Feature
If you want to implement a new feature, specify "Feature" as the feature type.

### Support
To support new versions of OS, middleware, libraries, frameworks, etc., specify "Support" for the feature type.

### Fix
To fix a bug, specify "Fix" as the feature type.

### Docs
To fix documents and samples, specify "Docs" as the feature type.

### Dev
If you want to fix something that only affects hive-builder's own development, specify "Dev" as the feature type.

## Feature name
The feature name is a short English sentence. Use a hyphen (-) instead of a space.