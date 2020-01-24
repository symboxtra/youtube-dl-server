%include('header.tpl', title='youtube-dl')

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
						<option value="{{format['id']}}" title="{{format['value']}}">{{format['label']}}</option>
						%end
					</optgroup>
					%end
				</select>

				<button class="input__btn" type="submit" id="button-submit">Submit</button>
			</div>
		</form>

		%if (len(failed) > 0):
		<div id="failed">
			<h2>Failed</h2>
			%include('table.tpl', iter=failed)
		</div>
		%end

		<div id="queued">
			<h2>Queued</h2>
			%include('table.tpl', iter=queue)
		</div>

		<div id="Recent">
			<h2>Recent</h2>
			%include('table.tpl', iter=history)
		</div>

	</main>

%include('footer.tpl')
