# diagrams-repo-runner
Source [Github](https://github.com/aegis-fate-gh/diagrams-repo-runner)

## Description
When given a valid github repo and appropriate credentials, this runs python code that pulls from the git repo and uses the [Diagrams](https://diagrams.mingrammer.com) python library to create png images. It does this based on a matching pattern that can be set as needed. As noted in the Diagrams docs, it also utilizes python files. Examples of this can be found in my [ArgoCD](https://github.com/aegis-fate-gh/homelab-argocd) repo.

From there, when 'No' is set via the DRY_RUN environment variable, it pushes the files back up to the selected repo.

## Process Flow
1. The script runs checks to ensure valid environment variables and credentials were entered
2. The folder used by cloning process is deleted, preventing any added complexity
2. The remote repo cloned in full
3. Git pull initiated against the selected branch
4. All files matching the pattern are found
5. Diagrams is run against all of them
6. If dry run is set to yes, the script exits gracefully. The cloned repo files and created diagrams are available until the next run.
7. If dry run is set to no, the script then commits and pushes the changes with the desired commit message

## Environment Variables
This image takes up to 7 environment variables:

| Variable | Default | Type | Valid Inputs
| ----------- | ----------- | ----------- | ----------- |
| GIT_REPO | None | Required | Any valid Github repo |
| GIT_TOKEN | None | Required | Any valid Github token |
| GIT_USERNAME | None | Required | Any valid Github username |
| MATCH_PATTERN | *-diagram.py | Optional | Strings |
| REPO_BRANCH | main | Optional | Any valid branch |
| COMMIT_MESSAGE | docs: automated diagram updates from diagrams script | Optional | Any valid commit message |
| DRY_RUN | yes | Optional | yes / no |

- GIT_REPO: The name of the Github repo to pull from
- GIT_TOKEN: Your Github personal access token
- GIT_USERNAME: Your github username
- MATCH_PATTERN: The pattern to use when determining what files to run Diagrams against.
- REPO_BRANCH: Use this to set which branch the script should pull from, and push back up to.
- COMMIT_MESSAGE: Any valid commit message can be entered.
- DRY_RUN: Tells the script whether to commit and push the images it created. On exit, the files will be available within the container

## Example compose files
This example shows the minimum set of environment variables in order for the script to run. The dry run variable shouldn't be uncommented unless you want the script to push the images back up to github.
```
---
version: '3.8'

services:
  media-metadata-mover:
    image: aegisfatedh/diagrams-repo-runner:latest
    container_name: diagrams-repo-runner
    environment:
      - GIT_REPO=Repo_Here
      - GIT_TOKEN=Token_Here
      - GIT_USERNAME=Git_Username_Here
      # - DRY_RUN=no
```

The below example shows how to mount a persistent volume. While this container is fully self contained, if there's a need to more easily see the files during dry runs, this is one way. The container mount location is fixed, as the script only clones into that directory.
```
---
version: '3.8'

services:
  media-metadata-mover:
    image: aegisfatedh/diagrams-repo-runner:latest
    container_name: diagrams-repo-runner
    environment:
      - GIT_REPO=Repo_Here
      - GIT_TOKEN=Token_Here
      - GIT_USERNAME=Git_Username_Here
      # - DRY_RUN=no
    volumes:
      - <Local Volume>:/app/github
```
