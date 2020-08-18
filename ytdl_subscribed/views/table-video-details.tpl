<table class="no-border left-align">
    <tr>
        <td><b>Title:</b></td>
        <td><i>{{item['title']}}</i></td>
    </tr>
    <tr>
        <td><b>Duration:</b></td>
        %if (item['duration_s']):
        <td>{{item['duration_s']}}s</td>
        %end
    </tr>
    <tr>
        <td><b>Source:</b></td>
        <td><a href="{{item['url']}}" target="_blank">{{item['extractor']}}</a></td>
    </tr>
    <tr>
        <td><b>Uploader:</b></td>
        <td>
            <a href="/collection/{{item['uploader_id']}}">{{item['uploader_name']}}</a>
            %if (item['uploader_url']):
            [<a href="{{item['uploader_url']}}" target="_blank">{{item['extractor']}}</a>]
            %end
        </td>
    </tr>
    <tr>
        <td><b>Uploaded:</b></td>
        %if (item['upload_date']):
        <td>{{item['upload_date']}}</td>
        %end
    </tr>
    <tr>
        <td><b>Downloaded:</b></td>
        %if (item['download_datetime']):
        <td>{{item['download_datetime']}}</td>
        %end
    </tr>
    <tr>
        <td><b>File:</b></td>
        <td>
            <a href="/video/{{item['id']}}/download" download>
                <code>{{item['filepath']}}</code>
            </a>
        </td>
    </tr>
    <tr>
        <td><b>File exists:</b></td>
        <td>
            %if (item['filepath_exists']):
            Yes
            %else:
            No
            %end
        </td>
    </tr>
    <tr>
        <td><b>Last checked:</b></td>
        %if (item['filepath_last_checked']):
        <td>{{item['filepath_last_checked']}}</td>
        %end
    </tr>
</table>
