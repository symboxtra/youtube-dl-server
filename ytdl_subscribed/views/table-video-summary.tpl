<table class="data-table video-summary-table">
    <tr>
        <th>Title</th>
        <th>Uploader</th>
        <th>Source</th>
        <th>Date/Time</th>
        <th>Status</th>
    </tr>

    %for item in iter:
    <tr id="{{item['id']}}">
        <td><a href="video/{{item['id']}}">{{item['title']}}</a></td>
        <td><a href="collection/{{item['uploader_id']}}">{{item['uploader_name']}}</a></td>
        <td><a href="{{item['url']}}" target="blank">{{item['extractor']}}</a></td>
        <td>{{item['download_datetime']}}</td>
        <td>
            %if (item['failed']):
            <span title="Download failed!">❌</span>
            %elif (item['in_progress']):
            <img src="static/loading.svg" alt="Loading..." width="24px">
            %else:
            <span title="Green is good">✅</span>
            %end
        </td>
    </tr>
    %end

</table>
