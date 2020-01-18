<!doctype html>
<html lang="en">

<head>
	<!-- Required meta tags -->
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
	<meta name="Description" content="Web frontend for youtube-dl">

	<link href="static/style.css" rel="stylesheet">

	<title>youtube-dl</title>
</head>

<body>
	<header>
		<h1>Multimedia content archival</h1>
		<p class="lead">
			Provide a <a href="https://rg3.github.io/youtube-dl/supportedsites.html">youtube-dl supported</a>
			video URL to download the video to the server.
		</p>
	</header>
	<main>

		<form action="api/queue" method="POST">
			<div class="input">
				<input class="input__url" name="url" type="url" placeholder="URL" aria-label="URL" aria-describedby="button-submit">

				<select class="custom-select" name="format">
					%for category, formats in format_options.items():
					<optgroup label="{{category}}">
						%for format in formats:
						<option value="{{format['value']}}" title="{{format['value']}}">{{format['label']}}</option>
						%end
					</optgroup>
					%end
				</select>

				<button class="input__btn" type="submit" id="button-submit">Submit</button>
			</div>
		</form>

		%if (len(failed) > 0):
		<div>
			<h2>Failed</h2>
			<table class="failed">
				<tr>
					<th>Date/Time</th>
					<th>Source</th>
					<th>Title</th>
					<th>Status</th>
				</tr>
				%for item in failed:
				<tr id="{{item['video_id']}}">
					<td>{{item["datetime"]}}</td>
					<td>{{item["extractor"]}}</td>
					<td><a href="{{item["url"]}}" target="blank">{{item["title"]}}</a></td>
					<td>❌</td>
				</tr>
				%end
			</table>
		</div>
		%end

		<div>
			<h2>Queued</h2>
			<table class="queue">
				<tr>
					<th>Date/Time</th>
					<th>Source</th>
					<th>Title</th>
					<th>Status</th>
				</tr>
				%for item in queue:
				<tr id="{{item['video_id']}}">
					<td>{{item["datetime"]}}</td>
					<td>{{item["extractor"]}}</td>
					<td><a href="{{item["url"]}}" target="blank">{{item["title"]}}</a></td>
					<td><img src="static/loading.svg" alt="Loading..." width="32px"></td>
				</tr>
				%end
			</table>
		</div>

		<div>
			<h2>History</h2>
			<table class="history">
				<tr>
					<th>Date/Time</th>
					<th>Source</th>
					<th>Title</th>
					<th>Status</th>
				</tr>
				%for item in history:
				<tr id="{{item['video_id']}}">
					<td>{{item["datetime"]}}</td>
					<td>{{item["extractor"]}}</td>
					<td><a href="{{item["url"]}}" target="blank">{{item["title"]}}</a></td>
					<td>✅</td>
				</tr>
				%end
			</table>
		</div>
	</main>

	<footer>
		<p>
			Web frontend for <a href="https://rg3.github.io/youtube-dl/">youtube-dl</a>
			by <a href="https://twitter.com/manbearwiz">@manbearwiz</a>,
			adapted by <a href="https://github.com/jlnostr">@jlnostr</a>,
			extended by <a href="https://github.com/jmcker">@jmcker</a>.
		</p>
	</footer>
</body>

</html>
