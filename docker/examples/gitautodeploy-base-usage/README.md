# Example of "git-auto-deploy" usage

This is an example of usage of "git-auto-deploy" docker image.

Example docker image extends "git-auto-deploy"
by adding a non-root user and configuration.
Also it specifies addition run option `--ssh-keyscan` in CMD that attaches
to ENTRYPOINT of the parent image. `--ssh-keyscan` isn't actually used but
it's addef for example only.

## How to run the example

    cd docker/example/gitautodeploy-base-usage/image
    docker build -t the-example .
    docker run --init --rm -p 8080:8080 the-example

## Structure

The example consists of `app` and `image` folders.
`image` is the image context.
`app` is an app that GAD pulls and deploys
