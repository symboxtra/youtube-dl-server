%include('header.tpl', title=item['title'])

<table class="data-table">
    <tr>
        <th>Title</th>
        <th>Source</th>
        <th>Date/Time</th>
        <th>Status</th>
    </tr>

    <tr id="{{item['video_id']}}">
        <td><a href="video/{{item['video_id']}}">{{item['title']}}</a></td>
        <td><a href="{{item['url']}}" target="blank">{{item['name']}}</a></td>
        <td>{{item['datetime']}}</td>
        <td>
            %if (item['in_progress']):
            <img src="/static/loading.svg" alt="Loading..." width="24px">
            %elif (item['failed']):
            ❌
            %else:
            ✅
            %end
        </td>
    </tr>

</table>

%include('footer.tpl')
