# gitlab-job-performance

Visualize the duration of GitLab jobs.

This tool uses the GitLab API to retrieve job duration information from a project, and graphs it.

You can filter by date, stage, or individual job.

Not extensively tested, but it's pretty simple so if you hit edge cases I didn't, it should be easy to fix-up! Pull
requests welcome.

## Examples

Setup:

```bash
pip install -r requirements.txt
 export GITLAB_TOKEN=<my personal access token>
```

Show job duration over time, for all jobs in the build stage, excluding jobs that took over 10 minutes:

```bash
./gitlab-job-perf.py https://gitlab.example.com mygroup/myproj --cache=myproj.json --stage=build --ignore-over=600
```

![Duration over time](https://raw.githubusercontent.com/mykter/gitlab-job-performance/master/time.png)

Show distribution of the test job (exact name match) since 2020:

```bash
./gitlab-job-perf.py https://gitlab.example.com mygroup/myproj --dist --cache=myproj.json --job=^test$ --since=2020-01-01
```

![Duration distribution](https://raw.githubusercontent.com/mykter/gitlab-job-performance/master/dist.png)

For additional options, run `./gitlab-job-perf.py --help`
