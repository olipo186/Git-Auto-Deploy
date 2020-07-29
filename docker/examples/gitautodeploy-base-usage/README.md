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

Look at [--init](https://docs.docker.com/engine/reference/run/#specify-an-init-process) flag in the snippet above.
I think it's important to use it because GAD is supposed to run deployment scripts,
that means we have a lot of child processes in the container
that should be utilized properly.

## Structure

The example consists of `app` and `image` folders.
`image` is the image context.
`app` is an app that GAD pulls and deploys
