# github flow
This repository is maintained according to [github flow](https://scottchacon.com/2011/08/31/github-flow.html). The naming convention for pull request branches in github flow is as follows

Feature type/derived revision/feature name

For example, use a branch name such as Feature/2.2.12-3-g371b837/support-bonding-NIC.

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

# Procedure
The following are the steps to merge your modifications into the master branch.

## 1. Create a branch
When you start to modify, first create a branch in your local repository by running the following command.

```shell
git checkout -b branch-name
```
For example, if you want to add support for bonded NICs, your command might look something like this
```shell
git checkout -b Feature/$(git describe --tags)/support-bonding-NIC
```

#### Note
> You can create a branch even if you've already started modifying on the master branch, as long as you haven't done add/commit.
> In that case, your modifications will not be lost by the above command. If you have mixed up your modifications with those for other purposes, you can choose which files to include in the pull request at the Staging step described below. If you get mixed up within a file, you may need to use git stash or something similar to separate the modifications.

## 2. Modification & Test
Repeat mofying and testing in your local repository.

## 3. Staging
Move your modified files and files to be added to staging.

#### Note
> If you have no additional files and want to commit all modified files, you can skip this step by adding the -a option to the commit command of the next step.

### 3-A. Specifying a file name
Use the following command to specify a file and move it to staging.
```shell
git add file_name1 file_name2
```
For example, to move GITHUB-FLOW-ja.md and examples/pdns/inventory/hive.yml to staging, issue the following command
```shell
git add GITHUB-FLOW-ja.md examples/pdns/inventory/hive.yml
```

### 3-B. If you want to move all the files to staging
Use the following command to move all the added and modified files to staging.
```shell
git add -A
```

## 4. Commit
Commit the staged files with the following command
```shell
git commit -m 'commit description'
```
The commit description should be a short description of the commit. For example, if you're committing a feature for a bonded NIC, you can use something like this
```shell
git commit -m 'support bonding NICs'
```

## 5. Push
To push the staged file, use the following command
```shell
git push origin branch-name
```
For example, if you added functionality to 2.2.12 to support bonded NICs, your command would look something like this
```
git push origin Feature/2.2.12/support-bonding-NIC
```

## 6. Create a pull request
After step 5, browse to [Repository](https://github.com/procube-open/hive-builder) on the web, you will see the branch as "Your recent pushed branch", and click "Compare & pull request" button.
This will create a pull request.

The name of the pre-request will be automatically created from the branch name, but you should add the feature type by enclosing it in [] at the beginning. For example, a pull request for the branch "Feature/2.2.12/support-bonding-NIC" will automatically be named "support bonding NIC", but please modify it to "[Feature] support bonding NIC".

After that, click Create pull request.

## 7. Review and fix
If you need to modify the request due to review, please modify your local repository and push it. In other words, repeat steps 2 to 5 to commit and push the modification, which will automatically be included in the pull request. Open your pull request from [Pull requests](https://github.com/procube-open/hive-builder/pulls) on the web and enter your comments to continue the discussion.

#### Note
> If more than one person is working on the pull request, pull the branch to their local repository and modify it.

## 8. Merge
Click on "Squash and merge" to merge the pull requests that have been reviewed.
#### Note
> After you merge, the pull request is complete and closed. If you need to make a new modification, even if it is related to the previous pull request, start this procedure over from the beginning and make it a new pull request.

## 9. Deleting a branch
Delete branches that have been merged.

## 9-1. Deleting a branch in your local repository
Delete the branch in your local repository with the following command.
```shell
git branch -D branch-name
```
For example, if you've just finished merging in the pull request that adds support for bonded NICs derived from 2.2.12, your command should look something like this
```shell
git branch -D Feature/2.2.12/support-bonding-NIC
```

## 9-2. Deleting a repository branch
Open the pull request you finished merging in the web and click ``Delete branch'' to delete the branch.
#### Note
> Pull requests that have been merged are not shown in [Pull requests](https://github.com/procube-open/hive-builder/pulls) by default. Remove "is:open" from "Filters" by default and search again to find and open the target pull request.
