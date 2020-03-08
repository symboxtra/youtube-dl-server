<table class="no-border left-align">
    <tr>
        <td><b>Title:</b></td>
        <td><i>{{item['title']}}</i></td>
    </tr>
    <tr>
        <td><b>Duration:</b></td>
        <td>{{item['duration_s']}}s</td>
    </tr>
    <tr>
        <td><b>Source:</b></td>
        <td><a href="{{item['url']}}" target="_blank">{{item['extractor']}}</a></td>
    </tr>
    <tr>
        <td><b>Uploader:</b></td>
        <td>
            <a href="/collection/{{item['uploader_id']}}">{{item['uploader_name']}}</a>
            [<a href="{{item['uploader_url']}}" target="_blank">{{item['extractor']}}</a>]
        </td>
    </tr>
    <tr>
        <td><b>Uploaded:</b></td>
        <td>{{item['upload_date']}}</td>
    </tr>
    <tr>
        <td><b>Downloaded:</b></td>
        <td>{{item['download_datetime']}}</td>
    </tr>
    <tr>
        <td><b>File:</b></td>
        <td><code>{{item['filepath']}}</code></td>
    </tr>
    <tr>
        <td><b>File exists:</b></td>
        <td>
            %if (item['filepath_exists']):
            Yes
            %else:
            No
        </td>
    </tr>
    <tr>
        <td><b>Last checked:</b></td>
        <td>{{item['filepath_last_checked']}}</td>
    </tr>
</table>
