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
			Provide a <a href="https://rg3.github.io/youtube-dl/supportedsites.html">youtube-dl supported</a> video URL
			to download the video to the server.
		</p>
	</header>
	<main>

		<form method="POST">
			<div class="input">
				<input class="input__url" name="url" type="url" placeholder="URL" aria-label="URL"
					aria-describedby="button-submit">
				<button class="input__btn" type="submit" id="button-submit">Submit</button>
			</div>
		</form>

		<div>
			<h2>History</h2>
			<ul class="queue">
				%for item in history:
				<li><a href="{{item["url"]}}" target="blank">{{item["title"]}}</a></li>
				%end
			</ul>
		</div>
	</main>

	<footer>
		<p>Web frontend for <a href="https://rg3.github.io/youtube-dl/">youtube-dl</a>,
			by <a href="https://twitter.com/manbearwiz">@manbearwiz</a>, adapted by <a
				href="https://github.com/jlnostr">@jlnostr</a>.</p>
	</footer>
</body>

</html>
