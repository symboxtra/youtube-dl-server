<table class="no-border left-align">
    <tr>
        <td><b>Title:</b></td>
        <td>{{item['title']}}</td>
    </tr>
    <tr>
        <td><b>Original Title:</b></td>
        <td>{{item['online_title']}}</td>
    </tr>
    <tr>
        <td><b>Collection type:</b></td>
        <td>{{item['type']}}</td>
    </tr>
    <tr>
        <td><b>Source:</b></td>
        %if (item['url']):
        <td><a href="{{item['url']}}" target="_blank">{{item['extractor']}}</a></td>
        %else:
        <td><span title="Link not available">{{item['extractor']}}</span></td>
        %end
    </tr>
    <tr>
        <td><b>Inclusion/exclusion criteria:</b></td>
        <td><span title="{{item['setting_description']}}">{{item['setting_title']}}</span></td>
    </tr>
    <tr>
        <td><b>Update schedule:</b></td>
        <td><span title="{{item['schedule_description']}}">{{item['schedule_name']}}</span></td>
    </tr>
    <tr>
        <td><b>Last update:</b></td>
        <td>{{item['last_update_datetime']}}</td>
    </tr>
    <tr>
        <td><b>First download:</b></td>
        <td>{{item['first_download_datetime']}}</td>
    </tr>
    <tr>
        <td><b>Latest download:</b></td>
        <td>{{item['last_download_datetime']}}</td>
    </tr>
</table>
