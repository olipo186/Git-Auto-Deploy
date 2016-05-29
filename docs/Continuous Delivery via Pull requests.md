# Continuous Delivery via Pull requests (GitHub only)

![Workflow](./graphics/continuous_delivery_process.png)

If you use continious delivery (such as this workflow) you may want to trigger deploy event when pull request is opened or closed.
You can follow next steps to implement CD process:
* Set repo "url" to ```"https://api.github.com"```
* Add filter type "pull-request-filter" as described below
* Configure "action" that you want to listen
* Configure branch in which pull request trying to merge (variable "ref" below)

Example
```json
"url": "https://api.github.com/repos/olipo186/Git-Auto-Deploy",
"deploy": "echo deploying after pull request",
"filters": [
{
    "action": "closed",
    "pull_request": true,
    "pull_request.base.ref": "testing-branch"
}
]
```
