[![Build Status](https://dev.azure.com/jlnostr/youtube-dl-server/_apis/build/status/jlnostr.youtube-dl-server?branchName=master)](https://dev.azure.com/jlnostr/youtube-dl-server/_build/latest?definitionId=9&branchName=master)

# youtube-dl-server
This fork of `youtube-dl-server` has some changes made to the original.

Some of them (not complete list):

- Reachable directly under the port (not under the `youtube-dl` subpath, example usage is shown below)
- Removed bootstrap cause it's not necessary for such a small application
- Saves and displays a queue and a history (only in RAM, it's list after a restart)

## Running

### Docker CLI

This example uses the docker run command to create the container to run the app. Here we also use host networking for simplicity. Also note the `-v` argument. This directory will be used to output the resulting videos

```shell
docker run -d --net="host" --name youtube-dl -v /home/core/youtube-dl:/youtube-dl jlnostr/youtube-dl-server
```


### Without docker
You need to have Python 3 and pip (the package manager of python) installed. If that's the case, you can download a copy of this code and execute it locally.

```shell
wget https://github.com/jlnostr/youtube-dl-server/archive/master.zip
unzip master.zip
mv youtube-dl-server-master youtube-dl
cd youtube-dl
```

There are two ways of editing the config. First, by setting the environment variables that are defined in `youtube-dl-server.py`, for example:


```shell
# This would save the files in a 'data' subdirectory
export YDL_OUTPUT_TEMPLATE="./data/%(title)s [%(id)s].%(ext)s"
```

or by editing the `app_defaults` property of `youtube-dl-server.py` directly as a permanent solution.


## Usage

### Start a download remotely

Downloads can be triggered by supplying the `{{url}}` of the requested video through the Web UI or through the REST interface via curl, etc.

#### HTML

Just navigate to `http://{{host}}:8080/` and enter the requested `{{url}}`.

#### Curl

```shell
curl -X POST --data-urlencode "url={{url}}" http://{{host}}:8080/
```

#### Fetch

```javascript
fetch(`http://${host}:8080/`, {
  method: "POST",
  body: new URLSearchParams({
    url: url,
    format: "bestvideo"
  }),
});
```

#### Bookmarklet

Add the following bookmarklet to your bookmark bar so you can conviently send the current page url to your youtube-dl-server instance.

```javascript
javascript:!function(){fetch("http://${host}:8080/",{body:new URLSearchParams({url:window.location.href,format:"bestvideo"}),method:"POST"})}();
```

## Implementation

The server uses [`bottle`](https://github.com/bottlepy/bottle) for the web framework and [`youtube-dl`](https://github.com/rg3/youtube-dl) to handle the downloading. The integration with youtube-dl makes use of their [python api](https://github.com/rg3/youtube-dl#embedding-youtube-dl).

This docker image is based on [`python:alpine`](https://registry.hub.docker.com/_/python/) and consequently [`alpine:3.8`](https://hub.docker.com/_/alpine/).
